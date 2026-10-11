"""M1.4 controlled headroom benchmark, separate from M0-v2 journal/replay.

Reuses the *actual* Arena.step energy/duel rules with deterministic injected
tasks. No changes to the historical M0-M1.3 puzzle stream or its SQLite replay.
The benchmark has its own offline JSON audit with replay of all settled moves.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from random import Random
from typing import Any

from .core import Action, Arena, Observation, POLICIES, RULES_VERSION, START_ENERGY, STAKE, Task
from .gateway import FakeGateway, GatewayError, OpenRouterGateway
from .model_registry import check_model
from .storage import canonical

BENCHMARK_VERSION = "m14-v1"
MAX_CASES = 48
MAX_ITEMS = 14


class CachedTask(Task):
    """Precompute the exact oracle once; Arena.step accesses optimum many times."""

    @property
    def optimum(self) -> int:
        return self._benchmark_optimum


def _exact(task: Task) -> tuple[int, int]:
    """For <=14 items, enumerate every mask with stable smallest-mask ties."""
    optimum_mask = max(range(1 << len(task.items)),
                       key=lambda m: (task.score(m), -m))
    return optimum_mask, task.score(optimum_mask)


def make_cases(seed: int, count: int, items: int, profile: str) -> list[dict]:
    if type(seed) is not int or seed < 0:
        raise ValueError("benchmark seed must be nonnegative")
    if type(count) is not int or not 1 <= count <= MAX_CASES:
        raise ValueError(f"benchmark cases must be between 1 and {MAX_CASES}")
    if type(items) is not int or not 8 <= items <= MAX_ITEMS:
        raise ValueError("benchmark items must be between 8 and 14")
    if profile not in ("mixed", "trap", "random"):
        raise ValueError("benchmark profile must be mixed, trap, or random")
    generated = []
    for tick in range(count):
        # Independent task RNG. No player or provider output can influence it.
        rng = Random(seed * 1_000_003 + tick * 9_176 + 491)
        kind = ("trap" if profile == "trap" or
                profile == "mixed" and tick % 2 == 0 else "random")
        capacity = rng.randint(11, 18)
        if kind == "trap":
            # High ratio bait consumes capacity; only an exact full-size item
            # earns the highest reward. Every decoy has ratio <5.
            pairs = [(1, 6), (capacity, 5 * capacity)]
            for _ in range(items - 2):
                cost = rng.randint(1, min(8, capacity - 1))
                reward = rng.randint(2 * cost, 4 * cost)
                pairs.append((cost, reward))
            rng.shuffle(pairs)
        else:
            pairs = [(rng.randint(1, 9), rng.randint(2, 27))
                     for _ in range(items)]
        plain = Task(tuple(pairs), capacity)
        oracle_mask, oracle_score = _exact(plain)
        cached = CachedTask(plain.items, plain.capacity)
        object.__setattr__(cached, "_benchmark_optimum", oracle_score)
        obs = Observation(tick, "normal", cached, START_ENERGY)
        greedy_mask = POLICIES["greedy"](obs, Random(0)).mask
        greedy_score = cached.score(greedy_mask)
        gap = oracle_score - greedy_score
        if kind == "trap" and (gap <= 0 or gap / oracle_score < 0.12):
            raise AssertionError("constructed headroom task lost its guaranteed Greedy gap")
        generated.append({
            "task": cached, "kind": kind,
            "oracle_mask": oracle_mask, "oracle_score": oracle_score,
            "greedy_mask": greedy_mask, "greedy_score": greedy_score,
            "gap": gap,
        })
    return generated


class BenchmarkArena(Arena):
    """Inject a new benchmark stream but preserve all M0-v2 settlement rules."""

    def __init__(self, seed: int, cases: list[dict]):
        super().__init__(seed)
        self.cases = cases

    def _puzzle(self) -> tuple[Task, str]:
        _, weather = super()._puzzle()
        return self.cases[self.tick]["task"], weather


def _prompt(obs: Observation) -> list[dict]:
    """Data only; no precomputed oracle, Greedy mask or legal-mask menu."""
    return [
        {"role": "system", "content": (
            "You control a virtual organism. Select a subset of the listed "
            "items, indexed from 0, to maximize total reward. Bit i of integer "
            "mask selects item i. Sum of selected costs must not exceed "
            "capacity; otherwise the whole action is invalid. Think about "
            "feasibility before choosing. Respond ONLY with JSON keys mask "
            "(a nonnegative integer) and soul_update (exactly empty string). "
            "No code, no external tools or further requests."
        )},
        {"role": "user", "content": json.dumps({
            "tick": obs.tick, "weather": obs.weather, "own_energy": obs.own_energy,
            "task": obs.task.as_dict(),
        }, sort_keys=True)},
    ]


def _can_afford(arena: Arena, obs: Observation) -> bool:
    if obs.own_energy <= 0:
        return False
    upkeep = {"normal": 1, "fog": 2, "drought": 3}[obs.weather]
    mint = 1 if arena.tick % 4 == 0 else 0
    return obs.own_energy + mint - upkeep >= 1


def _should_call(arena: Arena, obs: Observation, cognition: str, remaining: int) -> bool:
    if not remaining or not _can_afford(arena, obs) or cognition == "never":
        return False
    if cognition == "always":
        return True
    if cognition == "selective":
        # Deliberately HOST-owned fixed schedule. No oracle lookahead.
        return arena.tick % 3 == 0 and obs.own_energy >= 9
    raise ValueError("unknown cognition mode")


def _gateway(args):
    if args.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required for --provider openrouter")
        if args.model == "openrouter/free":
            raise ValueError("M1.4 requires a pinned :free model, not random router")
        check_model(args.model)
        return OpenRouterGateway(model=args.model,
                                 max_requests=args.max_requests,
                                 max_output_tokens=args.max_output_tokens,
                                 reasoning=args.reasoning)
    return FakeGateway(max_requests=args.max_requests)


def _arm(seed: int, cases: list[dict], name: str, args, gateway=None) -> list[dict]:
    arena = BenchmarkArena(seed, cases)
    records = []
    for _ in cases:
        obs = arena.observations()
        act_b = (POLICIES["greedy"](obs["b"], Random(0))
                 if obs["b"].own_energy else Action(None))
        info: dict[str, Any] = {}
        charges = {}
        if obs["a"].own_energy <= 0:
            act_a = Action(None)
            info["source"] = "dead"
        elif name == "greedy":
            act_a = POLICIES["greedy"](obs["a"], Random(0))
            info["source"] = "greedy"
        elif name == "oracle":
            act_a = Action(cases[arena.tick]["oracle_mask"])
            info["source"] = "unpriced_exact_oracle"
        elif name == "llm":
            act_a = POLICIES["greedy"](obs["a"], Random(0))
            info["source"] = "greedy_no_inference"
            if _should_call(arena, obs["a"], args.cognition, gateway.remaining):
                prior = gateway.calls
                try:
                    reply = gateway.ask(_prompt(obs["a"]), mode="benchmark",
                                        benchmark_items=len(obs["a"].task.items))
                    act_a = Action(reply.mask)
                    info.update({
                        "source": "llm", "status": "ok",
                        "model": reply.model, "usage": reply.usage,
                    })
                except GatewayError as exc:
                    info.update({
                        "source": "greedy_provider_fallback", "status": "failed",
                        "failure_reason": exc.reason,
                        "model": exc.model or gateway.model,
                        "usage": exc.usage,
                    })
                if gateway.calls > prior:
                    charges["a"] = 1
        else:
            raise ValueError("unsupported benchmark arm")
        case = cases[arena.tick]
        result = arena.step({"a": act_a, "b": act_b}, charges)
        info.update({
            "greedy_mask": case["greedy_mask"],
            "greedy_score": case["greedy_score"],
            "oracle_mask": case["oracle_mask"],
            "oracle_score": case["oracle_score"],
            "gap": case["gap"], "task_family": case["kind"],
            "selected_legal": result["scores"]["a"] is not None
            and result["scores"]["a"] >= 0,
        })
        result["benchmark"] = info
        records.append(result)
    return records


def _summarize(manifest: dict, arms: dict[str, list[dict]]) -> dict:
    first = arms["greedy"]
    opportunities = [{
        "tick": rec["tick"],
        "family": rec["benchmark"]["task_family"],
        "oracle_score": rec["optimal_score"],
        "greedy_score": rec["scores"]["a"],
        "headroom": rec["optimal_score"] - rec["scores"]["a"],
    } for rec in first]
    total_oracle = sum(x["oracle_score"] for x in opportunities)
    total_greedy = sum(x["greedy_score"] for x in opportunities)
    arm_stats = {}
    for name, records in arms.items():
        actions = [r for r in records if r["attempted"]["a"]]
        last = records[-1]
        model_records = [r for r in records if r.get("benchmark", {}).get("source") == "llm"]
        charged = [r for r in records if r["consultations"]["a"]]
        failures = [r for r in records if r.get("benchmark", {}).get("status") == "failed"]
        tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        unknown_usage = 0
        for record in charged:
            usage = record.get("benchmark", {}).get("usage")
            if not isinstance(usage, dict) or any(type(usage.get(k)) is not int
                                                  for k in tokens):
                unknown_usage += 1
            else:
                for k in tokens:
                    tokens[k] += usage[k]
        arm_stats[name] = {
            "actions": len(actions),
            "legal": sum(r["scores"]["a"] is not None and r["scores"]["a"] >= 0 for r in actions),
            "invalid": sum(r["scores"]["a"] == -1 for r in actions),
            "optimal": sum(r["scores"]["a"] == r["optimal_score"] for r in actions),
            "task_score_sum": sum(r["scores"]["a"] for r in actions if r["scores"]["a"] is not None),
            "earned": sum(r["rewards"]["a"] for r in records),
            "wins": sum(r["winner"] == "a" for r in records),
            "energy": last["after"]["a"],
            "alive": last["after"]["a"] > 0,
            "consultations": len(charged),
            "model_actions": len(model_records),
            "provider_failures": len(failures),
            "reported_tokens": tokens,
            "unknown_usage_requests": unknown_usage,
        }
    base_energy = arm_stats["greedy"]["energy"]
    for values in arm_stats.values():
        values["energy_delta_vs_no_inference"] = values["energy"] - base_energy
    return {
        "headroom": {
            "cases": len(opportunities),
            "trap_cases": sum(p["family"] == "trap" for p in opportunities),
            "greedy_optimal": sum(p["headroom"] == 0 for p in opportunities),
            "positive_gap_cases": sum(p["headroom"] > 0 for p in opportunities),
            "greedy_total": total_greedy,
            "oracle_total": total_oracle,
            "greedy_gap": total_oracle - total_greedy,
            "relative_headroom": round(
                (total_oracle - total_greedy) / total_oracle, 4
            ) if total_oracle else 0,
        },
        "arms": arm_stats,
        "note": (
            "The exact oracle is an UNPRICED diagnostic upper bound, not a "
            "deployable free policy. Each actual provider consultation costs "
            "one virtual energy unit, independently of token usage."
        ),
    }


def _digest(manifest: dict, arms: dict[str, list[dict]], summary: dict) -> str:
    return hashlib.sha256(canonical({
        "manifest": manifest, "arms": arms, "summary": summary,
    }).encode("utf-8")).hexdigest()


def run_m14(args) -> dict:
    if args.b != "greedy":
        raise ValueError("M1.4 uses --b greedy as fixed opponent")
    if args.a not in ("greedy", "llm"):
        raise ValueError("M1.4 uses --a greedy or --a llm")
    if args.cognition not in ("always", "selective", "never"):
        raise ValueError("invalid M1.4 cognition schedule")
    if type(args.max_requests) is not int or not 1 <= args.max_requests <= MAX_CASES:
        raise ValueError("M1.4 max-requests must be from 1 to 48")
    cases = make_cases(args.seed, args.benchmark_cases,
                       args.benchmark_items, args.benchmark_profile)
    gateway = _gateway(args) if args.a == "llm" and args.cognition != "never" else None
    manifest = {
        "benchmark_rules": BENCHMARK_VERSION, "referee_rules": RULES_VERSION,
        "seed": args.seed, "cases": args.benchmark_cases,
        "items": args.benchmark_items, "profile": args.benchmark_profile,
        "challenger": args.a, "opponent": args.b,
        "provider": args.provider if gateway else "none",
        "requested_model": args.model if args.provider == "openrouter" and gateway else None,
        "cognition": args.cognition,
        "request_cap": args.max_requests if gateway else 0,
    }
    arms = {"greedy": _arm(args.seed, cases, "greedy", args),
            "oracle": _arm(args.seed, cases, "oracle", args)}
    if args.a == "llm":
        # No provider gateway needed when cognition is explicitly disabled.
        if gateway is None:
            class NoRequests:
                remaining = 0
            gateway = NoRequests()
        arms["llm"] = _arm(args.seed, cases, "llm", args, gateway)
    summary = _summarize(manifest, arms)
    report = {"manifest": manifest, "arms": arms, "summary": summary}
    report["head"] = _digest(manifest, arms, summary)
    verified = verify_report(report)
    if not verified["verified"]:
        raise AssertionError("generated benchmark report failed replay")
    filename = getattr(args, "benchmark_out", None)
    if filename:
        path = Path(filename)
        if path.exists():
            raise ValueError("benchmark output exists; choose another filename")
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        try:
            with temp.open("x", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()
    return {
        "manifest": manifest, "summary": summary, "head": report["head"],
        "verified": True, "report_path": filename,
    }


def verify_report(report: dict) -> dict:
    """Offline full replay. Detect inconsistencies, not hostile report rewriting."""
    if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
        raise ValueError("invalid benchmark report")
    manifest = report["manifest"]
    if (manifest.get("benchmark_rules") != BENCHMARK_VERSION
            or manifest.get("referee_rules") != RULES_VERSION
            or manifest.get("opponent") != "greedy"):
        raise ValueError("unsupported benchmark report version")
    cases = make_cases(manifest["seed"], manifest["cases"],
                       manifest["items"], manifest["profile"])
    arms = report.get("arms")
    expected_arms = {"greedy", "oracle"} | (
        {"llm"} if manifest.get("challenger") == "llm" else set()
    )
    if not isinstance(arms, dict) or set(arms) != expected_arms:
        raise ValueError("incorrect benchmark arms")
    for name in sorted(expected_arms):
        records = arms[name]
        if not isinstance(records, list) or len(records) != len(cases):
            raise ValueError("benchmark record count mismatch")
        arena = BenchmarkArena(manifest["seed"], cases)
        for tick, record in enumerate(records):
            if not isinstance(record, dict) or record.get("tick") != tick:
                raise ValueError("benchmark tick mismatch")
            if set(record.get("actions", {})) != {"a", "b"}:
                raise ValueError("benchmark action malformed")
            try:
                replayed = arena.step(
                    {actor: Action(record["actions"][actor]) for actor in ("a", "b")},
                    record.get("consultations"),
                )
            except (ValueError, AssertionError, KeyError, TypeError) as exc:
                raise ValueError("benchmark referee replay failed") from exc
            metadata = record.get("benchmark")
            if not isinstance(metadata, dict):
                raise ValueError("benchmark metadata absent")
            extra = dict(record)
            extra.pop("benchmark", None)
            if canonical(replayed) != canonical(extra):
                raise ValueError("benchmark referee transition mismatch")
            case = cases[tick]
            if any(metadata.get(key) != expected for key, expected in (
                ("greedy_mask", case["greedy_mask"]),
                ("greedy_score", case["greedy_score"]),
                ("oracle_mask", case["oracle_mask"]),
                ("oracle_score", case["oracle_score"]),
                ("gap", case["gap"]),
                ("task_family", case["kind"]),
                ("selected_legal", record["scores"]["a"] is not None
                 and record["scores"]["a"] >= 0),
            )):
                raise ValueError("benchmark task metadata mismatch")
            if name == "greedy" and record["actions"]["a"] != case["greedy_mask"]:
                raise ValueError("greedy baseline deviated from deterministic policy")
            if name == "oracle" and record["actions"]["a"] != case["oracle_mask"]:
                raise ValueError("oracle baseline deviated from optimal policy")
            if name == "llm":
                charged = record["consultations"]["a"]
                source = metadata.get("source")
                if charged != int(source in ("llm", "greedy_provider_fallback")):
                    raise ValueError("model consultation / source accounting mismatch")
    recomputed = _summarize(manifest, arms)
    if canonical(recomputed) != canonical(report.get("summary")):
        raise ValueError("benchmark summary mismatch")
    head = _digest(manifest, arms, recomputed)
    if head != report.get("head"):
        raise ValueError("benchmark content digest mismatch")
    return {"verified": True, "head": head, "summary": recomputed}


def verify_report_file(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 8_000_000:
        raise ValueError("benchmark report unavailable or too large")
    try:
        report = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid benchmark JSON") from exc
    return verify_report(report)
