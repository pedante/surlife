"""M1.10: audited shared-response cognition tournament for M1.9 TaskPacks.

One model sample per visible task (or verified bank reuse), then price that
same answer against several cheap strategies in the original M0-v2 referee.
No LLM calls occur during policy simulations or independent report replay.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from random import Random
from time import monotonic

from .core import Action, Observation, POLICIES, RULES_VERSION, START_ENERGY
from .gateway import GatewayError
from .m14 import MAX_CASES, _can_afford, _gateway
from .m16 import AdaptivePolicy, _policy_identity, initial_state, write_report
from .m18 import (_check_bank, _digest, _identity, LIMIT_ERRORS,
                  MAX_LIVE_CASES, MAX_REPORT_BYTES)
from .m19 import (BEAM_WIDTH, VERSION as TASKPACK_VERSION, PACKS,
                  TaskPackArena, make_pack_cases, rollout)
from .storage import canonical

VERSION = "m110-v1"
PROMPT_VERSION = "taskpack-prompt-v1"
STRATEGIES = ("never", "always", "selective", "adaptive_fresh")
CHEAP_FALLBACK = "marginal"
BASELINES = ("greedy", "marginal", "beam", "oracle")


def _prompt(obs: Observation) -> list[dict]:
    """Only live observation data, no oracle score or precomputed actions."""
    task = obs.task.as_dict()
    if task.get("pack") == "coverage":
        rules = (
            "You select a subset of items. Each item has [cost, standalone_value], "
            "but TRUE reward is the sum of feature_weights for the UNIQUE "
            "features covered by any selected items. Item feature_masks are "
            "bitsets; bit j indicates feature j. Never count a shared feature "
            "twice. Standalone values overestimate combinations with overlap."
        )
    elif task.get("pack") == "synergy":
        rules = (
            "You select a subset of items. TRUE reward is the sum of selected "
            "items' base values PLUS every pair bonus [i,j,bonus] for which "
            "BOTH item i and item j are selected. Item values alone can miss "
            "valuable complementary pairs."
        )
    else:
        raise ValueError("M1.10 requires a reviewed M1.9 task pack")
    return [
        {"role": "system", "content": (
            "You are a virtual organism solving a constrained resource task. "
            + rules +
            " The sum of selected item costs MUST NOT exceed capacity. "
            "Item indexing starts at 0. Return integer mask: bit i selects "
            "item i. Respond ONLY as JSON with mask and an exactly empty "
            "soul_update. No external tools or code execution."
        )},
        {"role": "user", "content": json.dumps({
            "tick": obs.tick,
            "weather": obs.weather,
            "own_energy": obs.own_energy,
            "task": task,
        }, sort_keys=True)},
    ]


def _collect(args, cases: list[dict]) -> list[dict]:
    gateway = _gateway(args)
    arena = TaskPackArena(args.seed, cases)
    bank = []
    blocked = False
    expected = _policy_identity(args)["model"]
    for tick, case in enumerate(cases):
        if blocked:
            bank.append({"tick": tick, "status": "unavailable",
                         "reason": "rate_limited"})
            continue
        arena.tick = tick
        observation = arena.observations()["a"]
        # Crucial for fair reuse: every strategy would be offered a response
        # to the SAME standardized reference observation, independent of
        # its own energy history and cognition choices.
        neutral = Observation(tick, observation.weather, case["task"],
                              START_ENERGY)
        before = gateway.calls
        started = monotonic()
        if args.provider != "fake":
            print(f"[M1.10] sampling {tick + 1}/{len(cases)}: {args.provider}",
                  file=sys.stderr, flush=True)
        try:
            reply = gateway.ask(_prompt(neutral), mode="benchmark",
                                benchmark_items=len(case["task"].items))
            if reply.model != expected:
                mismatch = GatewayError("unreviewed model substitution",
                                        "routed_model_mismatch")
                mismatch.model, mismatch.usage = reply.model, reply.usage
                raise mismatch
            sample = {"tick": tick, "status": "ok", "mask": reply.mask,
                      "model": expected, "usage": reply.usage}
        except GatewayError as exc:
            if gateway.calls == before:
                raise ValueError("bank provider failed before a chargeable request") from None
            reason = exc.reason
            if not isinstance(reason, str) or not re.fullmatch(
                r"[a-z][a-z0-9_]{0,63}", reason
            ):
                reason = "provider_failure"
            blocked = reason in LIMIT_ERRORS
            sample = {"tick": tick, "status": "failed", "reason": reason,
                      "model": expected, "usage": exc.usage}
        if gateway.calls != before + 1:
            raise ValueError("gateway must debit exactly one request per sampled task")
        if args.provider != "fake":
            print(f"[M1.10] sample {tick + 1}: {sample['status']} "
                  f"in {monotonic() - started:.1f}s",
                  file=sys.stderr, flush=True)
        bank.append(sample)
    return bank


def _shadow_gain(arena: TaskPackArena, cases: list[dict],
                 cheap: Action, opponent: Action, actual: dict) -> int:
    """Measure post-outcome virtual energy against the SAME marginal fallback.

    Referee rules and opponent action are identical to the actual episode.
    The policy sees this result only AFTER the real decision is settled.
    """
    shadow = TaskPackArena(arena.seed, cases)
    shadow.tick = actual["tick"]
    shadow.balances = dict(actual["before"])
    baseline = shadow.step({"a": cheap, "b": opponent})
    return actual["after"]["a"] - baseline["after"]["a"]


def _simulate(seed: int, cases: list[dict], bank: list[dict],
              strategy: str, cap: int) -> list[dict]:
    if strategy not in STRATEGIES:
        raise ValueError("unsupported M1.10 cognition strategy")
    arena = TaskPackArena(seed, cases)
    learner = AdaptivePolicy() if strategy == "adaptive_fresh" else None
    used = 0
    records = []
    for tick, (case, sample) in enumerate(zip(cases, bank)):
        obs = arena.observations()
        own = obs["a"]
        other = (POLICIES["greedy"](obs["b"], Random(0))
                 if obs["b"].own_energy else Action(None))
        cheap = Action(case["marginal_mask"]) if own.own_energy else Action(None)
        available = sample["status"] != "unavailable"
        decision = None
        attempt = False
        if own.own_energy:
            if learner is not None:
                # Never reveal the bank mask or successful/failed status
                # to a policy before it has decided to consult.
                decision = learner.choose(
                    own, max(0, cap - used) if available else 0,
                    _can_afford(arena, own),
                )
                attempt = decision["consult"]
            elif available and used < cap and _can_afford(arena, own):
                if strategy == "always":
                    attempt = True
                elif strategy == "selective":
                    attempt = tick % 3 == 0 and own.own_energy >= 9
        action = cheap
        info = {"bank_tick": tick,
                "source": ("dead" if not own.own_energy
                           else "marginal_bank_unavailable" if not available
                           else "marginal_no_inference")}
        if attempt:
            used += 1
            info["model"] = sample["model"]
            info["usage"] = sample["usage"]
            if sample["status"] == "ok":
                action = Action(sample["mask"])
                info.update({"source": "llm", "status": "ok"})
            else:
                info.update({"source": "marginal_provider_fallback",
                             "status": "failed",
                             "failure_reason": sample["reason"]})
        rec = arena.step({"a": action, "b": other},
                         {"a": 1} if attempt else {})
        if learner is not None and own.own_energy:
            info["policy_decision"] = decision
            if attempt:
                delta = _shadow_gain(arena, cases, cheap, other, rec)
                info["net_energy_vs_marginal"] = delta
                info["feedback_kind"] = (
                    "model_success" if sample["status"] == "ok"
                    else "provider_failure"
                )
                if sample["status"] == "ok":
                    learner.learn(decision["bucket"], delta)
            info["policy_after"] = learner.snapshot()
        info.update({
            "pack": case["kind"],
            "cheap_baseline": CHEAP_FALLBACK,
            "greedy_mask": case["greedy_mask"],
            "greedy_score": case["greedy_score"],
            "marginal_mask": case["marginal_mask"],
            "marginal_score": case["marginal_score"],
            "beam_mask": case["beam_mask"],
            "beam_score": case["beam_score"],
            "oracle_mask": case["oracle_mask"],
            "oracle_score": case["oracle_score"],
            "selected_legal": rec["scores"]["a"] is not None
            and rec["scores"]["a"] >= 0,
        })
        rec["benchmark"] = info
        records.append(rec)
    return records


def _summarize(manifest: dict, bank: list[dict], arms: dict) -> dict:
    cases = make_pack_cases(manifest["seed"], manifest["cases"],
                            manifest["items"], manifest["pack"])
    result = {}
    for name, rows in arms.items():
        records = [row for row in rows if row["attempted"]["a"]]
        charged = [row for row in rows if row["consultations"]["a"]]
        failures = [row for row in rows
                    if row["benchmark"].get("status") == "failed"]
        model = [row for row in rows
                 if row["benchmark"].get("source") == "llm"]
        token_totals = {name: 0 for name in
                        ("prompt_tokens", "completion_tokens", "total_tokens")}
        unknown = 0
        for row in charged:
            usage = row["benchmark"].get("usage")
            if not isinstance(usage, dict) or any(
                type(usage.get(field)) is not int for field in token_totals
            ):
                unknown += 1
            else:
                for field in token_totals:
                    token_totals[field] += usage[field]
        result[name] = {
            "actions": len(records),
            "alive": rows[-1]["after"]["a"] > 0,
            "energy": rows[-1]["after"]["a"],
            "task_score_sum": sum(row["scores"]["a"] for row in records
                                  if row["scores"]["a"] is not None),
            "legal": sum(row["scores"]["a"] is not None
                         and row["scores"]["a"] >= 0 for row in records),
            "invalid": sum(row["scores"]["a"] == -1 for row in records),
            "optimal": sum(row["scores"]["a"] == row["optimal_score"]
                           for row in records),
            "wins": sum(row["winner"] == "a" for row in rows),
            "consultations": len(charged),
            "model_actions": len(model),
            "provider_failures": len(failures),
            "reported_tokens": token_totals,
            "unknown_usage_requests": unknown,
        }
    # All static controls have unpriced computation, and their energy,
    # not just their raw score, is visible to avoid inflated LLM claims.
    for data in result.values():
        for baseline in BASELINES:
            data["energy_delta_vs_" + baseline] = (
                data["energy"] - result[baseline]["energy"]
            )
    families = {}
    for family in ("coverage", "synergy"):
        selected = [i for i, case in enumerate(cases) if case["kind"] == family]
        families[family] = {
            "cases": len(selected),
            "oracle_total": sum(cases[i]["oracle_score"] for i in selected),
            "greedy_total": sum(cases[i]["greedy_score"] for i in selected),
            "marginal_total": sum(cases[i]["marginal_score"] for i in selected),
            "beam_total": sum(cases[i]["beam_score"] for i in selected),
            "model_successful_samples": sum(
                bank[i]["status"] == "ok" for i in selected),
            "policies": {
                name: {
                    "score_sum": sum(
                        recs[i]["scores"]["a"] for i in selected
                        if recs[i]["scores"]["a"] is not None),
                    "consultations": sum(
                        recs[i]["consultations"]["a"] for i in selected),
                    "invalid": sum(
                        recs[i]["scores"]["a"] == -1 for i in selected),
                }
                for name, recs in arms.items()
            },
        }
    stats = {state: sum(entry["status"] == state for entry in bank)
             for state in ("ok", "failed", "unavailable")}
    return {
        "arms": result,
        "families": families,
        "bank_sampling": {
            "provider_requests": stats["ok"] + stats["failed"],
            "successful_responses": stats["ok"],
            "failed_responses": stats["failed"],
            "not_requested": stats["unavailable"],
            "sampling_mode": manifest["sampling_mode"],
            "note": (
                "Provider requests were performed only while creating the "
                "bank, never per simulated policy. Counts in reused reports "
                "describe the ORIGINAL collection, not new API calls."
            ),
        },
        "headroom": {
            "cases": len(cases),
            "oracle_total": sum(c["oracle_score"] for c in cases),
            "greedy_total": sum(c["greedy_score"] for c in cases),
            "marginal_total": sum(c["marginal_score"] for c in cases),
            "beam_total": sum(c["beam_score"] for c in cases),
            "positive_gap_vs_marginal": sum(
                c["oracle_score"] > c["marginal_score"] for c in cases),
            "positive_gap_vs_beam": sum(
                c["oracle_score"] > c["beam_score"] for c in cases),
        },
        "note": (
            "Trusted Greedy, marginal, beam and oracle computations are "
            "UNPRICED; model consultations cost one virtual energy when "
            "selected. Responses were elicited at constant reference "
            "energy 30, not from each policy's own history. This is a "
            "counterfactual task-pack experiment, not a persistent world "
            "or proof of LLM superiority."
        ),
    }


def _assemble(manifest: dict, bank: list[dict]) -> dict:
    cases = make_pack_cases(manifest["seed"], manifest["cases"],
                            manifest["items"], manifest["pack"])
    _check_bank(bank, manifest)
    arms = {name: rollout(manifest["seed"], cases, name)
            for name in BASELINES}
    for strategy in STRATEGIES:
        arms[strategy] = _simulate(manifest["seed"], cases, bank, strategy,
                                   manifest["virtual_cap"])
    summary = _summarize(manifest, bank, arms)
    report = {"manifest": manifest, "bank": bank,
              "arms": arms, "summary": summary}
    report["head"] = _digest(manifest, bank, arms, summary)
    return report


def verify_m110(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(
        report.get("manifest"), dict
    ):
        raise ValueError("invalid M1.10 report")
    m = report["manifest"]
    if (set(m) != {
            "experiment", "referee_rules", "taskpack_rules", "prompt_version",
            "seed", "cases", "items", "pack", "beam_width", "provider",
            "requested_model", "generation", "sampling_mode",
            "bank_source_head", "virtual_cap", "bank_prompt_energy",
            "fallback",
        } or m["experiment"] != VERSION
            or m["referee_rules"] != RULES_VERSION
            or m["taskpack_rules"] != TASKPACK_VERSION
            or m["prompt_version"] != PROMPT_VERSION
            or m["beam_width"] != BEAM_WIDTH
            or m["bank_prompt_energy"] != START_ENERGY
            or m["fallback"] != CHEAP_FALLBACK
            or m["pack"] not in PACKS
            or type(m["virtual_cap"]) is not int
            or not 0 <= m["virtual_cap"] <= m["cases"]
            or m["sampling_mode"] not in ("fresh", "reused")):
        raise ValueError("unsupported M1.10 manifest")
    if (m["sampling_mode"] == "fresh"
            and m["bank_source_head"] is not None
            or m["sampling_mode"] == "reused"
            and (not isinstance(m["bank_source_head"], str)
                 or not re.fullmatch(r"[0-9a-f]{64}",
                                     m["bank_source_head"]))):
        raise ValueError("invalid M1.10 bank provenance")
    _identity(m)
    # Rebuild from a private code-defined task generator. Not just verifying
    # hash equality: replay every decision and original Arena.step transfer.
    expected = _assemble(m, report.get("bank"))
    if (canonical(expected["arms"]) != canonical(report.get("arms"))
            or canonical(expected["summary"]) != canonical(report.get("summary"))
            or expected["head"] != report.get("head")):
        raise ValueError("M1.10 bank, policy or referee replay mismatch")
    return {"verified": True, "head": expected["head"],
            "summary": expected["summary"]}


def _read_report(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("M1.10 report missing or too large")
    try:
        report = json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid M1.10 JSON") from exc
    verify_m110(report)
    return report


def verify_m110_file(path: str) -> dict:
    return verify_m110(_read_report(path))


def run_m110(args) -> dict:
    if args.a != "llm" or args.b != "greedy":
        raise ValueError("M1.10 requires --a llm --b greedy")
    output = getattr(args, "benchmark_out", None)
    if not output:
        raise ValueError("M1.10 requires --benchmark-out")
    if Path(output).exists():
        raise ValueError("M1.10 output exists; choose a NEW filename")
    if getattr(args, "policy_in", None):
        # Old M1.7 snapshots were trained on additive knapsack with a ratio
        # Greedy counterfactual. Their gain units/contexts are not
        # scientifically exchangeable with marginal-vs-LLM TaskPack feedback.
        raise ValueError("M1.10 does not import knapsack-trained --policy-in; "
                         "new task-pack-specific training is required")
    count = args.benchmark_cases
    cases = make_pack_cases(args.seed, count, args.benchmark_items,
                            args.m110_pack)
    cap = args.m110_virtual_cap
    if type(cap) is not int or not 0 <= cap <= count:
        raise ValueError("M1.10 virtual cap must be between 0 and case count")
    if type(args.max_requests) is not int or not 1 <= args.max_requests <= MAX_CASES:
        raise ValueError("M1.10 max-requests must be between 1 and 48")
    identity = _policy_identity(args)
    prior = getattr(args, "m110_bank_in", None)
    parent_head = None
    if prior:
        old = _read_report(prior)
        existing = old["manifest"]
        expected = {
            "seed": args.seed, "cases": count,
            "items": args.benchmark_items,
            "pack": args.m110_pack,
            "taskpack_rules": TASKPACK_VERSION,
            "prompt_version": PROMPT_VERSION,
            "provider": args.provider,
            "requested_model": None if args.provider == "fake" else args.model,
            "generation": identity["generation"],
        }
        if any(existing[key] != value for key, value in expected.items()):
            raise ValueError("M1.10 bank taskpack/seed/model/generation mismatch")
        bank = old["bank"]
        parent_head = old["head"]
    else:
        if args.max_requests < count:
            raise ValueError("M1.10 max-requests must cover ALL sampled cases")
        if args.provider != "fake" and count > MAX_LIVE_CASES:
            raise ValueError("M1.10 live sampling limited to 12 provider calls")
        bank = _collect(args, cases)
    m = {
        "experiment": VERSION, "referee_rules": RULES_VERSION,
        "taskpack_rules": TASKPACK_VERSION, "prompt_version": PROMPT_VERSION,
        "seed": args.seed, "cases": count, "items": args.benchmark_items,
        "pack": args.m110_pack, "beam_width": BEAM_WIDTH,
        "provider": args.provider,
        "requested_model": None if args.provider == "fake" else args.model,
        "generation": identity["generation"],
        "sampling_mode": "reused" if prior else "fresh",
        "bank_source_head": parent_head, "virtual_cap": cap,
        "bank_prompt_energy": START_ENERGY, "fallback": CHEAP_FALLBACK,
    }
    report = _assemble(m, bank)
    verify_m110(report)
    write_report(report, output)
    return {"verified": True, "head": report["head"],
            "manifest": m, "summary": report["summary"],
            "report_path": output}
