"""M1.6: bounded organism-owned consultation policy on M1.4 task streams.

No dynamic code or model-provided policy changes. The organism's *data* state
(visits, tried consultations, measured net energy) changes from experience.
The separate referee, provider gateway and budget admission remain trusted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from random import Random

from .core import Action, POLICIES, Observation
from .gateway import GatewayError
from .m14 import (
    BENCHMARK_VERSION, BenchmarkArena, MAX_CASES, _arm, _can_afford, _digest,
    _gateway, _prompt, _summarize, make_cases, verify_report,
)
from .storage import canonical

POLICY_VERSION = "m16-v1"
BUCKETS = ("uncertain", "routine")
RATE_LIMITS = ("http_429", "provider_error_429")


def initial_state() -> dict:
    return {b: {"visits": 0, "trials": 0, "gain": 0} for b in BUCKETS}


def validate_state(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != set(BUCKETS):
        raise ValueError("invalid cognition state buckets")
    for b in BUCKETS:
        item = value[b]
        if (not isinstance(item, dict) or set(item) != {"visits", "trials", "gain"}
                or any(type(item.get(k)) is not int for k in item)
                or not 0 <= item["trials"] <= item["visits"] <= 100_000
                or abs(item["gain"]) > 1_000_000):
            raise ValueError("invalid bounded cognition state")
    return {b: dict(value[b]) for b in BUCKETS}


class AdaptivePolicy:
    """Conservative two-context online bandit; all features are observable.

    Initial exploration, then exploit positive observed net energy; periodically
    probe again if prior consultation was not profitable. Never see oracle,
    generated trap labels, the opponent's private state, or future tasks.
    """

    def __init__(self, state: dict | None = None):
        self.state = validate_state(state if state is not None else initial_state())

    @staticmethod
    def bucket(obs: Observation) -> str:
        greedy = POLICIES["greedy"](obs, Random(0)).mask
        score = obs.task.score(greedy)
        best_single = max((reward for cost, reward in obs.task.items
                           if cost <= obs.task.capacity), default=0)
        return "uncertain" if 5 * best_single >= 4 * max(1, score) else "routine"

    def choose(self, obs: Observation, available: int, affordable: bool) -> dict:
        bucket = self.bucket(obs)
        cell = self.state[bucket]
        cell["visits"] += 1
        if cell["visits"] > 100_000:
            raise ValueError("cognition state visit ceiling reached")
        desire = (cell["trials"] == 0 or
                  cell["gain"] > 0 and cell["gain"] >= cell["trials"] or
                  cell["visits"] % 5 == 0)
        consult = bool(desire and available > 0 and affordable and obs.own_energy >= 6)
        return {"bucket": bucket, "consult": consult,
                "visits": cell["visits"], "trials_before": cell["trials"],
                "gain_before": cell["gain"]}

    def learn(self, bucket: str, net_energy: int) -> None:
        if bucket not in BUCKETS or type(net_energy) is not int or not -10 <= net_energy <= 10:
            raise ValueError("invalid cognition feedback")
        item = self.state[bucket]
        item["trials"] += 1
        item["gain"] += net_energy
        validate_state(self.state)

    def snapshot(self) -> dict:
        return validate_state(self.state)


def _shadow_gain(arena: BenchmarkArena, cases: list[dict], cheap: Action,
                 opponent: Action, actual: dict) -> int:
    """Matched one-tick *post-outcome* counterfactual with identical starting state.

    No shadow outcome is exposed to the policy until AFTER the real action.
    The cheap baseline is the actual policy's no-call action, not an oracle.
    """
    shadow = BenchmarkArena(arena.seed, cases)
    shadow.tick = actual["tick"]
    shadow.balances = dict(actual["before"])
    baseline = shadow.step({"a": cheap, "b": opponent})
    return actual["after"]["a"] - baseline["after"]["a"]


def adaptive_arm(seed: int, cases: list[dict], args, gateway, state: dict | None = None) -> list[dict]:
    arena = BenchmarkArena(seed, cases)
    policy = AdaptivePolicy(state)
    records = []
    rate_limited = False
    for _ in cases:
        obs = arena.observations()
        own = obs["a"]
        opponent = (POLICIES["greedy"](obs["b"], Random(0))
                    if obs["b"].own_energy else Action(None))
        cheap = POLICIES["greedy"](own, Random(0)) if own.own_energy else Action(None)
        info = {}
        charges = {}
        if not own.own_energy:
            act = Action(None)
            info["source"] = "dead"
            decision = None
        else:
            decision = policy.choose(own, gateway.remaining, _can_afford(arena, own))
            info["source"] = "greedy_rate_limited" if rate_limited else "greedy_no_inference"
            act = cheap
            if decision["consult"] and not rate_limited:
                prior = gateway.calls
                try:
                    reply = gateway.ask(_prompt(own), mode="benchmark",
                                        benchmark_items=len(own.task.items))
                    if args.provider in ("openrouter", "google") and reply.model != args.model:
                        mismatch = GatewayError("routed model mismatch", "routed_model_mismatch")
                        mismatch.model, mismatch.usage = reply.model, reply.usage
                        raise mismatch
                    act = Action(reply.mask)
                    info.update({"source": "llm", "status": "ok",
                                 "model": reply.model, "usage": reply.usage})
                except GatewayError as exc:
                    if exc.reason in RATE_LIMITS:
                        rate_limited = True
                    info.update({"source": "greedy_provider_fallback", "status": "failed",
                                 "failure_reason": exc.reason,
                                 "model": exc.model or gateway.model, "usage": exc.usage})
                    details = getattr(exc, "generation_diagnostics", None)
                    if isinstance(details, dict):
                        info["generation_diagnostics"] = details
                if gateway.calls > prior:
                    charges["a"] = 1
                elif info["source"] == "greedy_provider_fallback":
                    # Local preflight failures are not charged and do not update
                    # learning; source must agree with m14's audit verifier.
                    info["source"] = "greedy_no_inference"
                    info["status"] = "preflight_failed"
        result = arena.step({"a": act, "b": opponent}, charges)
        if decision is not None:
            info["policy_decision"] = decision
            if charges.get("a"):
                delta = _shadow_gain(arena, cases, cheap, opponent, result)
                policy.learn(decision["bucket"], delta)
                info["net_energy_vs_greedy"] = delta
            info["policy_after"] = policy.snapshot()
        case = cases[result["tick"]]
        info.update({"greedy_mask": case["greedy_mask"], "greedy_score": case["greedy_score"],
                     "dp_mask": case["dp_mask"], "dp_score": case["dp_score"],
                     "oracle_mask": case["oracle_mask"], "oracle_score": case["oracle_score"],
                     "gap": case["gap"], "task_family": case["kind"],
                     "selected_legal": result["scores"]["a"] is not None
                     and result["scores"]["a"] >= 0})
        result["benchmark"] = info
        records.append(result)
    return records


def build_report(args, state: dict | None = None) -> dict:
    if args.a != "llm" or args.b != "greedy":
        raise ValueError("M1.6 requires --a llm --b greedy")
    if type(args.max_requests) is not int or not 1 <= args.max_requests <= MAX_CASES:
        raise ValueError("M1.6 request cap must be between 1 and 48")
    state = validate_state(state if state is not None else initial_state())
    cases = make_cases(args.seed, args.benchmark_cases, args.benchmark_items,
                       args.benchmark_profile)
    gateway = _gateway(args)
    manifest = {"benchmark_rules": BENCHMARK_VERSION, "experiment": POLICY_VERSION,
                "referee_rules": "m0-v2", "seed": args.seed,
                "cases": args.benchmark_cases, "items": args.benchmark_items,
                "profile": args.benchmark_profile, "challenger": "llm",
                "opponent": "greedy", "provider": args.provider,
                "requested_model": args.model if args.provider != "fake" else None,
                "cognition": "adaptive", "request_cap": args.max_requests,
                "policy_initial": state}
    arms = {"greedy": _arm(args.seed, cases, "greedy", args),
            "dp": _arm(args.seed, cases, "dp", args),
            "oracle": _arm(args.seed, cases, "oracle", args),
            "llm": adaptive_arm(args.seed, cases, args, gateway, state)}
    summary = _summarize(manifest, arms)
    report = {"manifest": manifest, "arms": arms, "summary": summary}
    report["head"] = _digest(manifest, arms, summary)
    verify_adaptive_report(report)
    return report


def verify_adaptive_report(report: dict) -> dict:
    """Independent policy-decision + accounting replay, on top of M1.4 referee replay."""
    verified = verify_report(report)
    m = report["manifest"]
    if m.get("experiment") != POLICY_VERSION or m.get("cognition") != "adaptive":
        raise ValueError("not an M1.6 adaptive cognition report")
    policy = AdaptivePolicy(m.get("policy_initial"))
    cases = make_cases(m["seed"], m["cases"], m["items"], m["profile"])
    arena = BenchmarkArena(m["seed"], cases)
    used, blocked = 0, False
    for rec in report["arms"]["llm"]:
        info = rec["benchmark"]
        obs = arena.observations()["a"]
        charged = rec["consultations"]["a"]
        cheap = POLICIES["greedy"](obs, Random(0)) if obs.own_energy else Action(None)
        opponent = Action(rec["actions"]["b"])
        if obs.own_energy:
            decision = policy.choose(obs, m["request_cap"] - used,
                                     _can_afford(arena, obs))
            if info.get("policy_decision") != decision:
                raise ValueError("adaptive policy decision was altered")
            source = info.get("source")
            expected_attempt = decision["consult"] and not blocked
            if charged and not expected_attempt:
                raise ValueError("unchosen consultation was charged")
            if expected_attempt and not charged and info.get("status") != "preflight_failed":
                raise ValueError("chosen consultation vanished from record")
            if source in ("greedy_no_inference", "greedy_rate_limited", "greedy_provider_fallback"):
                if rec["actions"]["a"] != cheap.mask:
                    raise ValueError("cheap fallback action changed")
            if source == "greedy_rate_limited" and not blocked:
                raise ValueError("false rate-limit fallback")
            if charged:
                gain = _shadow_gain(arena, cases, cheap, opponent, rec)
                if gain != info.get("net_energy_vs_greedy"):
                    raise ValueError("adaptive feedback differs from counterfactual")
                policy.learn(decision["bucket"], gain)
                used += 1
                if info.get("failure_reason") in RATE_LIMITS:
                    blocked = True
            elif "net_energy_vs_greedy" in info:
                raise ValueError("uncharged feedback recorded")
            if info.get("policy_after") != policy.snapshot():
                raise ValueError("policy learning state was altered")
        elif "policy_decision" in info or "policy_after" in info:
            raise ValueError("dead organism learned")
        replayed = arena.step({"a": Action(rec["actions"]["a"]),
                               "b": opponent}, rec["consultations"])
        if canonical(replayed) != canonical({k:v for k,v in rec.items() if k!="benchmark"}):
            raise ValueError("policy replay transition mismatch")
    return {**verified, "policy_final": policy.snapshot()}


def write_report(report: dict, filename: str | None) -> None:
    if not filename:
        return
    path = Path(filename)
    if path.exists():
        raise ValueError("benchmark output exists; choose another filename")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as fd:
            json.dump(report, fd, indent=2, sort_keys=True)
            fd.write("\n")
            fd.flush()
            os.fsync(fd.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def run_m16(args) -> dict:
    if args.benchmark_out and Path(args.benchmark_out).exists():
        raise ValueError("benchmark output exists; choose another filename")
    report = build_report(args)
    result = verify_adaptive_report(report)
    write_report(report, args.benchmark_out)
    return {"manifest": report["manifest"], "summary": report["summary"],
            "head": report["head"], "verified": result["verified"],
            "policy_final": result["policy_final"],
            "report_path": args.benchmark_out}


def verify_m16_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 8_000_000:
        raise ValueError("adaptive report unavailable or too large")
    try:
        report = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid adaptive report JSON") from exc
    return verify_adaptive_report(report)
