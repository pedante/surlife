"""Paired held-out soul evaluation outside the arena.

Explicitly requested model consultations only. They do not debit virtual energy
or alter referee history, but use a separate *bounded* real provider request
budget. On any provider failure do not approve the candidate.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .core import Arena
from .gateway import FakeGateway, GatewayError, OpenRouterGateway
from .m11 import EvolutionSoul
from .model_registry import check_model


def _task_hash(task: dict) -> str:
    return hashlib.sha256(
        json.dumps(task, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_snapshot(args) -> dict:
    if args.evaluation_tasks < 2 or args.evaluation_tasks > 12:
        raise ValueError("evaluation-tasks must be between 2 and 12")
    if args.evaluation_seed < 0:
        raise ValueError("evaluation-seed must be nonnegative")
    if args.eval_min_gain < 1:
        raise ValueError("eval-min-gain must be positive")
    snapshot = Path(args.evaluate_soul)
    if not snapshot.is_file():
        raise ValueError("evaluation requires an existing soul snapshot")
    soul = EvolutionSoul.restore("a", str(snapshot))
    if len(soul.pending) != 1:
        raise ValueError("soul has no single pending revision to evaluate")
    if any(entry.get("seed") == args.evaluation_seed for entry in soul.evaluation_history):
        raise ValueError("this evaluation seed has already been used for this lineage")
    if args.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required for --provider openrouter")
        check_model(args.model)
    max_calls = args.evaluation_tasks * 2
    gateway = (OpenRouterGateway(model=args.model, max_requests=max_calls,
                                 max_output_tokens=args.max_output_tokens,
                                 reasoning=args.reasoning)
               if args.provider == "openrouter" else FakeGateway(max_requests=max_calls))

    note = soul.pending[0]["note"]
    candidate = EvolutionSoul(
        actor="a", base=soul.base, version=soul.version + 1,
        notes=[*soul.notes, note],
        memory=[dict(m) for m in soul.memory],
        revisions=[*soul.revisions],
    )
    # Exclude every task previously shown in the organism's feedback memory.
    # This is a deterministic holdout, not statistically independent proof.
    seen = {_task_hash({"items": m["items"], "capacity": m["capacity"]})
            for m in soul.memory if "items" in m and "capacity" in m}
    observations = []
    idx = 0
    while len(observations) < args.evaluation_tasks and idx < 500:
        obs = Arena(args.evaluation_seed + idx * 17_931).observations()["a"]
        idx += 1
        key = _task_hash(obs.task.as_dict())
        if key in seen:
            continue
        seen.add(key)
        observations.append(obs)
    if len(observations) != args.evaluation_tasks:
        raise ValueError("could not find enough unseen tasks")

    results = {"baseline": [], "candidate": []}
    failures = []
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    missing_usage = 0
    routed_models = {}
    for i, obs in enumerate(observations):
        # Interleave old and candidate in opposite order each round to reduce
        # provider drift bias. Prompts share identical frozen feedback and tasks.
        order = ("baseline", "candidate") if i % 2 == 0 else ("candidate", "baseline")
        for label in order:
            tested = soul if label == "baseline" else candidate
            try:
                reply = gateway.ask(tested.messages(obs))
                score = obs.task.score(reply.mask) if reply.mask is not None else -1
                usage = reply.usage
                model = reply.model
            except GatewayError as exc:
                score = -1
                usage = exc.usage
                model = exc.model or gateway.model
                failures.append({"task_index": i, "variant": label, "reason": exc.reason})
            if isinstance(usage, dict) and all(
                type(usage.get(k)) is int for k in totals
            ):
                for k in totals:
                    totals[k] += usage[k]
            else:
                missing_usage += 1
            routed_models[model] = routed_models.get(model, 0) + 1
            results[label].append({
                "task_hash": _task_hash(obs.task.as_dict()),
                "score": score, "optimum": obs.task.optimum,
                "legal": score >= 0,
            })

    old_total = sum(x["score"] for x in results["baseline"])
    new_total = sum(x["score"] for x in results["candidate"])
    old_invalid = sum(not x["legal"] for x in results["baseline"])
    new_invalid = sum(not x["legal"] for x in results["candidate"])
    improved = (
        not failures and new_invalid <= old_invalid
        and new_total - old_total >= args.eval_min_gain
    )
    evaluation = {
        "seed": args.evaluation_seed, "tasks": args.evaluation_tasks,
        "min_gain": args.eval_min_gain, "baseline_score": old_total,
        "candidate_score": new_total,
        "baseline_invalid": old_invalid, "candidate_invalid": new_invalid,
        "accepted": improved,
        "model": args.model if args.provider == "openrouter" else "surlife/fake-model",
        "provider": args.provider, "requests": gateway.calls,
        "reported_tokens": totals, "unknown_usage_requests": missing_usage,
        "routed_models": routed_models, "failures": failures,
        "matched_task_hashes": [x["task_hash"] for x in results["baseline"]],
    }
    soul.accept_pending(evaluation)
    # Always snapshot the decision, even if rejected. The unvalidated
    # candidate is removed; only winning evaluated notes enter the prompt.
    soul.save(snapshot.parent)
    return {
        "evaluation": evaluation, "soul_path": str(snapshot),
        "soul_version": soul.version, "soul_hash": soul.sha256,
        "pending_revisions": len(soul.pending),
        "note": ("Paired holdout result is preliminary, not statistically proven learning; "
                 "arena energy and journal were not modified."),
    }
