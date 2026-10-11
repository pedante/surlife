"""M1.2 conservative multi-cohort evaluation of one pending soul change.

The evaluator uses one fixed frozen memory and matched unseen objective tasks.
All new provider calls are explicitly capped and isolated from arena energy.
No provider output can modify program code or referee rules.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .core import Arena
from .gateway import FakeGateway, GatewayError, OpenRouterGateway
from .m11 import EvolutionSoul, task_fingerprint
from .model_registry import check_model


MAX_EVAL_REQUESTS = 24
COHORT_STRIDE = 100_003
TASK_STRIDE = 17_931


def _validated_plan(args, soul: EvolutionSoul) -> dict:
    tasks = args.evaluation_tasks
    cohorts = args.evaluation_cohorts
    if type(tasks) is not int or not 2 <= tasks <= 12:
        raise ValueError("evaluation-tasks must be an integer from 2 to 12")
    if type(cohorts) is not int or not 2 <= cohorts <= 6:
        raise ValueError("M1.2 requires at least 2 and at most 6 independent cohorts")
    if type(args.evaluation_seed) is not int or args.evaluation_seed < 0:
        raise ValueError("evaluation-seed must be nonnegative")
    if type(args.eval_min_gain) is not int or args.eval_min_gain < 1:
        raise ValueError("eval-min-gain must be positive")
    calls = 2 * tasks * cohorts
    cap = getattr(args, "max_evaluation_requests", MAX_EVAL_REQUESTS)
    if type(cap) is not int or not 4 <= cap <= MAX_EVAL_REQUESTS or calls > cap:
        raise ValueError(
            f"evaluation needs {calls} requests, exceeding configured hard cap "
            f"{cap}; reduce evaluation-cohorts/tasks or increase cap (max {MAX_EVAL_REQUESTS})"
        )
    if not soul.history_complete:
        raise ValueError(
            "lineage lacks complete task fingerprints; use a fresh M1.2 run "
            "for contamination-aware holdout evaluation"
        )
    # A generation cannot validate itself repeatedly on memorized trial tasks.
    for prior in soul.evaluation_history:
        if prior.get("seed") == args.evaluation_seed:
            raise ValueError("this evaluation seed has already been used in this lineage")
    return {"seed": args.evaluation_seed, "tasks_per_cohort": tasks,
            "cohorts": cohorts, "expected_requests": calls,
            "max_evaluation_requests": cap, "min_gain_per_cohort": args.eval_min_gain}


def _make_holdouts(plan: dict, excluded: set[str]) -> list[list]:
    """Deterministic distinct puzzles disjoint from ALL recorded lineage hashes."""
    sampled = set(excluded)
    batches = []
    for cohort in range(plan["cohorts"]):
        observations = []
        for i in range(500):
            seed = plan["seed"] + cohort * COHORT_STRIDE + i * TASK_STRIDE
            obs = Arena(seed).observations()["a"]
            key = task_fingerprint(obs.task.as_dict())
            if key in sampled:
                continue
            sampled.add(key)
            observations.append((key, obs))
            if len(observations) == plan["tasks_per_cohort"]:
                break
        if len(observations) < plan["tasks_per_cohort"]:
            raise ValueError("could not sample enough distinct held-out tasks")
        batches.append(observations)
    return batches


def evaluate_snapshot_v2(args) -> dict:
    snapshot = Path(args.evaluate_soul)
    if not snapshot.is_file():
        raise ValueError("evaluation requires an existing soul snapshot")
    soul = EvolutionSoul.restore("a", str(snapshot))
    if len(soul.pending) != 1:
        raise ValueError("snapshot does not contain one pending soul revision")
    if soul.pending[0]["baseline_hash"] != soul.sha256:
        raise ValueError("pending revision does not match active prompt")
    plan = _validated_plan(args, soul)
    cohorts = _make_holdouts(plan, set(soul.seen_task_hashes))

    # Explicit preflight BEFORE any model API request.
    if args.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required for --provider openrouter")
        check_model(args.model)
    gw = (OpenRouterGateway(model=args.model,
                            max_requests=plan["expected_requests"],
                            max_output_tokens=args.max_output_tokens,
                            reasoning=args.reasoning)
          if args.provider == "openrouter" else
          FakeGateway(max_requests=plan["expected_requests"]))
    note = soul.pending[0]["note"]
    candidate = EvolutionSoul(
        actor="a", base=soul.base, version=soul.version,
        notes=[*soul.notes, note], memory=[dict(m) for m in soul.memory],
        revisions=[*soul.revisions],
        seen_task_hashes=list(soul.seen_task_hashes),
        history_complete=True,
    )
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    unknown_usage = 0
    models = {}
    outcomes = []
    failure = None
    for cohort_index, batch in enumerate(cohorts):
        pairs = []
        for task_index, (task_hash, obs) in enumerate(batch):
            pair = {"cohort": cohort_index, "task_index": task_index,
                    "task_hash": task_hash, "optimum": obs.task.optimum}
            # Cross-over order reduces, but cannot eliminate, provider drift.
            order = ("baseline", "candidate") if (cohort_index + task_index) % 2 == 0 else (
                "candidate", "baseline"
            )
            for label in order:
                tested = soul if label == "baseline" else candidate
                try:
                    reply = gw.ask(tested.messages(obs))
                except GatewayError as error:
                    failure = {"cohort": cohort_index, "task_index": task_index,
                               "variant": label, "reason": error.reason}
                    break
                score = obs.task.score(reply.mask) if reply.mask is not None else -1
                pair[label] = {
                    "mask": reply.mask, "score": score, "legal": score >= 0,
                    "model": reply.model,
                }
                models[reply.model] = models.get(reply.model, 0) + 1
                if isinstance(reply.usage, dict) and all(
                    type(reply.usage.get(k)) is int for k in usage
                ):
                    for key in usage:
                        usage[key] += reply.usage[key]
                else:
                    unknown_usage += 1
            if failure is not None:
                break
            pairs.append(pair)
        outcomes.append(pairs)
        if failure is not None:
            break

    evaluation = {
        "protocol": "m12-multi-cohort-held-out-v1",
        **plan,
        "provider": args.provider,
        "requested_model": args.model if args.provider == "openrouter" else "surlife/fake-model",
        "requests": gw.calls,
        "reported_tokens": usage,
        "unknown_usage_requests": unknown_usage,
        "routed_models": models,
        "pair_results": outcomes,
        "failure": failure,
    }
    if failure is None:
        breakdown = []
        total_gains, wins, losses, ties = 0, 0, 0, 0
        for i, pairs in enumerate(outcomes):
            baseline_score = sum(p["baseline"]["score"] for p in pairs)
            candidate_score = sum(p["candidate"]["score"] for p in pairs)
            baseline_invalid = sum(not p["baseline"]["legal"] for p in pairs)
            candidate_invalid = sum(not p["candidate"]["legal"] for p in pairs)
            gain = candidate_score - baseline_score
            wins += sum(p["candidate"]["score"] > p["baseline"]["score"] for p in pairs)
            losses += sum(p["candidate"]["score"] < p["baseline"]["score"] for p in pairs)
            ties += sum(p["candidate"]["score"] == p["baseline"]["score"] for p in pairs)
            total_gains += gain
            breakdown.append({
                "cohort": i, "baseline_score": baseline_score,
                "candidate_score": candidate_score, "gain": gain,
                "baseline_invalid": baseline_invalid,
                "candidate_invalid": candidate_invalid,
                "passes": (candidate_invalid <= baseline_invalid and
                           gain >= plan["min_gain_per_cohort"]),
            })
        accepted = all(row["passes"] for row in breakdown) and wins > losses
        evaluation.update({
            "cohort_results": breakdown, "total_gain": total_gains,
            "paired_wins": wins, "paired_losses": losses, "paired_ties": ties,
            "accepted": accepted, "decision": "accepted" if accepted else "rejected",
        })
        # Save the acceptance or rejection as a completed evaluation. Only
        # accepted notes enter the active soul.
        soul.accept_pending(evaluation)
    else:
        # An infrastructure failure is NOT negative evidence about a prompt.
        # Preserve the pending note, record a sanitized aborted attempt, and
        # require a NEW evaluation seed for retry.
        evaluation.update({"accepted": False, "decision": "aborted"})
        soul.evaluation_history.append(evaluation)
        soul.evaluation_history[:] = soul.evaluation_history[-30:]

    soul.save(snapshot.parent)
    return {
        "evaluation": evaluation,
        "soul_path": str(snapshot), "soul_version": soul.version,
        "soul_hash": soul.sha256, "pending_revisions": len(soul.pending),
        "note": ("Matched repeated tests are exploratory, not proof of learning. "
                 "No virtual energy or referee ledger was modified."),
    }
