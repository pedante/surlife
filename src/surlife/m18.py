"""M1.8: one bounded response bank, many priced counterfactual cognition policies.

The same immutable, pre-sampled provider answer is available to every arm at
a given tick. Only the original sampling pass sends real provider requests.
No agent sees the bank before deciding, and no model output can edit referee
code. M0-v2 world rules and the M1.4 task generator are unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from random import Random
from time import monotonic

from .core import Action, Observation, POLICIES, RULES_VERSION, START_ENERGY
from .gateway import GatewayError
from .m14 import (BENCHMARK_VERSION, BenchmarkArena, MAX_CASES, _arm,
                  _can_afford, _gateway, _prompt, _summarize, make_cases)
from .m16 import (AdaptivePolicy, _policy_identity, _shadow_gain,
                  initial_state, load_promoted_policy, validate_state, write_report)
from .storage import canonical

VERSION = "m18-v1"
MAX_LIVE_CASES = 12
MAX_REPORT_BYTES = 8_000_000
BANK_FAILURE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
LIMIT_ERRORS = {"http_429", "provider_error_429"}
POLICIES_M18 = ("never", "always", "selective", "adaptive_fresh",
                "adaptive_inherited")
TOKEN_FIELDS = {"prompt_tokens", "completion_tokens", "total_tokens", "thought_tokens"}


def _identity(manifest: dict) -> dict:
    provider = manifest.get("provider")
    model = ("surlife/fake-model" if provider == "fake"
             else manifest.get("requested_model"))
    generation = manifest.get("generation")
    if provider not in ("fake", "google", "openrouter"):
        raise ValueError("unsupported bank provider")
    if (not isinstance(model, str) or not 1 <= len(model) <= 140
            or not isinstance(generation, dict)
            or set(generation) != {"reasoning", "max_output_tokens"}
            or generation["reasoning"] not in ("off", "low", "auto")
            or type(generation["max_output_tokens"]) is not int
            or not 16 <= generation["max_output_tokens"] <= 8192):
        raise ValueError("invalid bank model/generation identity")
    return {"provider": provider, "model": model, "generation": generation}


def _check_usage(usage) -> None:
    if usage is None:
        return
    if not isinstance(usage, dict) or not set(usage).issubset(TOKEN_FIELDS):
        raise ValueError("invalid sampled token usage")
    if any(v is not None and (type(v) is not int or v < 0)
           for v in usage.values()):
        raise ValueError("invalid sampled token counter")


def _check_bank(bank: list[dict], manifest: dict) -> None:
    if not isinstance(bank, list) or len(bank) != manifest["cases"]:
        raise ValueError("bank must have exactly one record per case")
    model = _identity(manifest)["model"]
    blocked = False
    for tick, sample in enumerate(bank):
        if not isinstance(sample, dict) or sample.get("tick") != tick:
            raise ValueError("sampled response bank tick mismatch")
        status = sample.get("status")
        if status == "ok":
            if (blocked or set(sample) != {"tick", "status", "mask", "model", "usage"}
                    or type(sample["mask"]) is not int
                    or not 0 <= sample["mask"] < (1 << manifest["items"])
                    or sample["model"] != model):
                raise ValueError("invalid sampled model action")
            _check_usage(sample["usage"])
        elif status == "failed":
            if (blocked or set(sample) != {"tick", "status", "reason", "model", "usage"}
                    or sample["model"] != model
                    or not isinstance(sample["reason"], str)
                    or not BANK_FAILURE.fullmatch(sample["reason"])):
                raise ValueError("invalid sampled provider failure")
            _check_usage(sample["usage"])
            if sample["reason"] in LIMIT_ERRORS:
                blocked = True
        elif status == "unavailable":
            if (not blocked or set(sample) != {"tick", "status", "reason"}
                    or sample["reason"] != "rate_limited"):
                raise ValueError("unavailable samples require prior 429")
        else:
            raise ValueError("unknown sampled response status")


def _collect(args, cases: list[dict]) -> list[dict]:
    """Sample fixed neutral-energy task prompts; never sample adaptive prompts."""
    gateway = _gateway(args)
    arena = BenchmarkArena(args.seed, cases)
    bank = []
    blocked = False
    for tick, case in enumerate(cases):
        if blocked:
            bank.append({"tick": tick, "status": "unavailable",
                         "reason": "rate_limited"})
            continue
        # This is a STANDARDIZED reference observation, not the later
        # counterfactual organism's energy. Prompt can't depend on which arm
        # uses its result. The weather and task remain deterministic.
        arena.tick = tick
        actual = arena.observations()["a"]
        neutral = Observation(tick, actual.weather, case["task"], START_ENERGY)
        before = gateway.calls
        expected = "surlife/fake-model" if args.provider == "fake" else args.model
        started = monotonic()
        if args.provider != "fake":
            print(f"[M1.8] sampling {tick + 1}/{len(cases)}: {args.provider}",
                  file=sys.stderr, flush=True)
        try:
            reply = gateway.ask(_prompt(neutral), mode="benchmark",
                                benchmark_items=len(case["task"].items))
            if reply.model != expected:
                mismatch = GatewayError("unreviewed model substitution",
                                        "routed_model_mismatch")
                mismatch.model, mismatch.usage = reply.model, reply.usage
                raise mismatch
            sample = {"tick": tick, "status": "ok",
                      "mask": reply.mask, "model": expected, "usage": reply.usage}
        except GatewayError as error:
            # A local preflight error should not produce a paid sample.
            if gateway.calls == before:
                raise ValueError("bank provider failed before request") from None
            reason = error.reason
            if not isinstance(reason, str) or not BANK_FAILURE.fullmatch(reason):
                reason = "provider_failure"
            blocked = reason in LIMIT_ERRORS
            sample = {"tick": tick, "status": "failed", "reason": reason,
                      "model": expected, "usage": error.usage}
        if gateway.calls != before + 1:
            raise ValueError("gateway did not debit exactly one sampled request")
        if args.provider != "fake":
            print(f"[M1.8] sample {tick + 1}: {sample['status']} "
                  f"in {monotonic() - started:.1f}s",
                  file=sys.stderr, flush=True)
        bank.append(sample)
    return bank


def _simulate(seed: int, cases: list[dict], bank: list[dict],
              strategy: str, cap: int, inherited: dict) -> list[dict]:
    if strategy not in POLICIES_M18:
        raise ValueError("unrecognized counterfactual arm")
    arena = BenchmarkArena(seed, cases)
    learner = AdaptivePolicy(inherited if strategy == "adaptive_inherited"
                             else None) if strategy.startswith("adaptive") else None
    used = 0
    records = []
    for tick, sample in enumerate(bank):
        obs = arena.observations()
        own = obs["a"]
        b = (POLICIES["greedy"](obs["b"], Random(0))
             if obs["b"].own_energy else Action(None))
        cheap = POLICIES["greedy"](own, Random(0)) if own.own_energy else Action(None)
        decision = None
        charge = False
        attempt = False
        available = sample["status"] != "unavailable"
        affordable = _can_afford(arena, own)
        if own.own_energy:
            if learner is not None:
                # The policy receives only a Boolean opportunity and its own
                # observation; it is not told the bank's mask or success.
                decision = learner.choose(own, cap - used if available else 0,
                                          affordable)
                attempt = decision["consult"]
            elif available and used < cap and affordable:
                if strategy == "always":
                    attempt = True
                elif strategy == "selective":
                    attempt = tick % 3 == 0 and own.own_energy >= 9
        action = cheap
        info = {"bank_tick": tick, "source": (
            "dead" if not own.own_energy else
            "greedy_bank_unavailable" if not available else
            "greedy_no_inference"
        )}
        if attempt:
            # A selected, sampled failure consumes virtual energy like a
            # failed hosted consultation. It does NOT teach reasoning value.
            used += 1
            charge = True
            info["model"] = sample["model"]
            info["usage"] = sample["usage"]
            if sample["status"] == "ok":
                action = Action(sample["mask"])
                info.update({"source": "llm", "status": "ok"})
            else:
                info.update({"source": "greedy_provider_fallback",
                             "status": "failed", "failure_reason": sample["reason"]})
        result = arena.step({"a": action, "b": b},
                            {"a": 1} if charge else {})
        if learner is not None and own.own_energy:
            info["policy_decision"] = decision
            if charge:
                gain = _shadow_gain(arena, cases, cheap, b, result)
                info["net_energy_vs_greedy"] = gain
                info["feedback_kind"] = (
                    "model_success" if sample["status"] == "ok"
                    else "provider_failure"
                )
                if sample["status"] == "ok":
                    learner.learn(decision["bucket"], gain)
            info["policy_after"] = learner.snapshot()
        case = cases[tick]
        info.update({
            "greedy_mask": case["greedy_mask"],
            "greedy_score": case["greedy_score"],
            "dp_mask": case["dp_mask"],
            "dp_score": case["dp_score"],
            "oracle_mask": case["oracle_mask"],
            "oracle_score": case["oracle_score"],
            "gap": case["gap"], "task_family": case["kind"],
            "selected_legal": result["scores"]["a"] is not None
            and result["scores"]["a"] >= 0,
        })
        result["benchmark"] = info
        records.append(result)
    return records


def _digest(manifest: dict, bank: list[dict], arms: dict, summary: dict) -> str:
    return hashlib.sha256(canonical({
        "manifest": manifest, "bank": bank, "arms": arms,
        "summary": summary,
    }).encode("utf-8")).hexdigest()


def _summary(manifest: dict, bank: list[dict], arms: dict) -> dict:
    result = _summarize(manifest, arms)
    tally = {status: sum(sample["status"] == status for sample in bank)
             for status in ("ok", "failed", "unavailable")}
    result["bank_sampling"] = {
        "provider_requests": tally["ok"] + tally["failed"],
        "successful_responses": tally["ok"],
        "failed_responses": tally["failed"],
        "not_requested": tally["unavailable"],
        "sampling_mode": manifest["sampling_mode"],
        "note": ("Real provider calls happen once while making the bank, "
                 "not once per simulated arm. Each arm separately pays "
                 "virtual cognition energy for the bank responses it uses."),
    }
    result["comparison"] = {
        name: {"energy_delta_vs_greedy": stat["energy_delta_vs_no_inference"],
               "consultations": stat["consultations"],
               "successful_model_actions": stat["model_actions"]}
        for name, stat in result["arms"].items()
        if name in POLICIES_M18
    }
    return result


def _assemble(manifest: dict, bank: list[dict]) -> dict:
    cases = make_cases(manifest["seed"], manifest["cases"],
                       manifest["items"], manifest["profile"])
    _check_bank(bank, manifest)
    seed = manifest["seed"]
    arms = {name: _arm(seed, cases, name, None)
            for name in ("greedy", "dp", "oracle")}
    for name in POLICIES_M18:
        if name == "adaptive_inherited" and not manifest["inherit_policy"]:
            continue
        arms[name] = _simulate(seed, cases, bank, name, manifest["virtual_cap"],
                               manifest["policy_initial"])
    summary = _summary(manifest, bank, arms)
    report = {"manifest": manifest, "bank": bank, "arms": arms, "summary": summary}
    report["head"] = _digest(manifest, bank, arms, summary)
    return report


def verify_m18(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
        raise ValueError("invalid M1.8 report")
    m = report["manifest"]
    if (set(m) != {"experiment", "benchmark_rules", "referee_rules",
                    "seed", "cases", "items", "profile", "provider",
                    "requested_model", "generation", "sampling_mode",
                    "bank_source_head", "virtual_cap", "policy_initial",
                    "inherit_policy", "bank_prompt_energy"}
            or m["experiment"] != VERSION
            or m["benchmark_rules"] != BENCHMARK_VERSION
            or m["referee_rules"] != RULES_VERSION
            or m["bank_prompt_energy"] != START_ENERGY
            or m["sampling_mode"] not in ("fresh", "reused")
            or not isinstance(m["inherit_policy"], bool)
            or type(m["virtual_cap"]) is not int
            or not 0 <= m["virtual_cap"] <= m["cases"]):
        raise ValueError("unsupported M1.8 manifest")
    if (m["sampling_mode"] == "fresh" and m["bank_source_head"] is not None
            or m["sampling_mode"] == "reused" and (
                not isinstance(m["bank_source_head"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", m["bank_source_head"]))):
        raise ValueError("invalid response-bank provenance")
    _identity(m)
    validate_state(m["policy_initial"])
    if not m["inherit_policy"] and m["policy_initial"] != initial_state():
        raise ValueError("fresh comparison has nonempty inherited policy")
    # Completely regenerate the arena and every arm from the bank. This
    # additionally verifies budget, strategy, charge, feedback and replay.
    expected = _assemble(m, report.get("bank"))
    if (canonical(expected["arms"]) != canonical(report.get("arms"))
            or canonical(expected["summary"]) != canonical(report.get("summary"))
            or expected["head"] != report.get("head")):
        raise ValueError("M1.8 replay/budget/policy summary or digest mismatch")
    return {"verified": True, "head": expected["head"],
            "summary": expected["summary"]}


def _read_report(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("M1.8 report missing or too large")
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid M1.8 JSON") from exc
    verify_m18(value)
    return value


def verify_m18_file(path: str) -> dict:
    return verify_m18(_read_report(path))


def run_m18(args) -> dict:
    if args.a != "llm" or args.b != "greedy":
        raise ValueError("M1.8 requires --a llm --b greedy")
    path = getattr(args, "benchmark_out", None)
    if not path:
        raise ValueError("M1.8 requires --benchmark-out for the audited bank")
    if Path(path).exists():
        raise ValueError("M1.8 output exists; choose a NEW filename")
    count = args.benchmark_cases
    cases = make_cases(args.seed, count, args.benchmark_items,
                       args.benchmark_profile)
    cap = args.m18_virtual_cap
    if type(cap) is not int or not 0 <= cap <= count:
        raise ValueError("M1.8 virtual cap must be between 0 and case count")
    if type(args.max_requests) is not int or not 1 <= args.max_requests <= MAX_CASES:
        raise ValueError("M1.8 max-requests must be between 1 and 48")
    identity = _policy_identity(args)
    inherit = bool(getattr(args, "policy_in", None))
    if inherit:
        state, saved_identity = load_promoted_policy(args.policy_in)
        if saved_identity != identity:
            raise ValueError("M1.8 inherited policy/provider/model/config mismatch")
    else:
        state = initial_state()
    reused = getattr(args, "m18_bank_in", None)
    source = None
    if reused:
        old = _read_report(reused)
        prev = old["manifest"]
        compare = {
            "seed": args.seed, "cases": count, "items": args.benchmark_items,
            "profile": args.benchmark_profile, "provider": args.provider,
            "requested_model": args.model if args.provider != "fake" else None,
            "generation": identity["generation"],
        }
        if any(prev[key] != value for key, value in compare.items()):
            raise ValueError("M1.8 replay bank task/model/generation mismatch")
        bank = old["bank"]
        source = old["head"]
    else:
        if args.max_requests < count:
            raise ValueError("M1.8 requires max-requests >= benchmark-cases "
                             "to sample each task exactly once")
        if args.provider != "fake" and count > MAX_LIVE_CASES:
            raise ValueError("M1.8 live sampling is limited to 12 real requests")
        bank = _collect(args, cases)
    manifest = {
        "experiment": VERSION, "benchmark_rules": BENCHMARK_VERSION,
        "referee_rules": RULES_VERSION,
        "seed": args.seed, "cases": count, "items": args.benchmark_items,
        "profile": args.benchmark_profile, "provider": args.provider,
        "requested_model": args.model if args.provider != "fake" else None,
        "generation": identity["generation"],
        "sampling_mode": "reused" if reused else "fresh",
        "bank_source_head": source, "virtual_cap": cap,
        "policy_initial": state, "inherit_policy": inherit,
        "bank_prompt_energy": START_ENERGY,
    }
    report = _assemble(manifest, bank)
    verify_m18(report)
    write_report(report, path)
    return {"verified": True, "head": report["head"],
            "report_path": path, "summary": report["summary"],
            "manifest": manifest}
