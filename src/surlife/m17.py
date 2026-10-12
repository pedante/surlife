"""M1.7: bounded cross-run cognition inheritance and matched held-out gate.

M1.6 policy state is data (not generated Python). Training reports are verified,
used once, and their task fingerprints excluded from held-out cohorts. This is
controlled policy selection, not autonomous code mutation or proof of ALife.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

from .m14 import make_cases
from .m16 import (
    POLICY_VERSION, build_report, initial_state, validate_state,
    verify_adaptive_report, write_report,
)
from .storage import canonical

EXPERIMENT = "m17-v1"
MAX_TRAIN = 4
MAX_HOLDOUT = 4
MAX_LIVE_CALLS = 24
MAX_FILE_BYTES = 8_000_000


def _read_json(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("training / evaluation report unavailable or too large")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid report JSON") from exc
    if not isinstance(obj, dict):
        raise ValueError("invalid report object")
    return obj


def _task_hashes(manifest: dict) -> set[str]:
    cases = make_cases(manifest["seed"], manifest["cases"],
                       manifest["items"], manifest["profile"])
    return {hashlib.sha256(canonical(c["task"].as_dict()).encode("utf-8")).hexdigest()
            for c in cases}


def _state_delta(report: dict) -> dict:
    start = validate_state(report["manifest"]["policy_initial"])
    final = validate_state(verify_adaptive_report(report)["policy_final"])
    change = initial_state()
    for bucket in change:
        for key in ("visits", "trials", "gain"):
            change[bucket][key] = final[bucket][key] - start[bucket][key]
        if change[bucket]["visits"] < change[bucket]["trials"] or change[bucket]["trials"] < 0:
            raise ValueError("training policy has nonmonotone counts")
    return change


def aggregate_training(reports: list[dict]) -> dict:
    if not 1 <= len(reports) <= MAX_TRAIN:
        raise ValueError("M1.7 requires 1 to 4 training reports")
    result = initial_state()
    fingerprints: set[str] = set()
    for report in reports:
        verify_adaptive_report(report)
        if report["manifest"]["experiment"] != POLICY_VERSION:
            raise ValueError("training report has wrong protocol")
        hashes = _task_hashes(report["manifest"])
        if fingerprints & hashes:
            raise ValueError("duplicate puzzle in training reports")
        fingerprints |= hashes
        increments = _state_delta(report)
        for bucket in result:
            for key in result[bucket]:
                result[bucket][key] += increments[bucket][key]
    return validate_state(result)


def _scoring(episodes: list[dict]) -> dict:
    improvements = []
    out = []
    for entry in episodes:
        fresh, inherited = entry["fresh"]["summary"]["arms"]["llm"], entry["inherited"]["summary"]["arms"]["llm"]
        diff = inherited["energy"] - fresh["energy"]
        improvements.append(diff)
        out.append({
            "seed": entry["seed"], "fresh_energy": fresh["energy"],
            "inherited_energy": inherited["energy"], "energy_delta": diff,
            "fresh_score": fresh["task_score_sum"],
            "inherited_score": inherited["task_score_sum"],
            "fresh_consultations": fresh["consultations"],
            "inherited_consultations": inherited["consultations"],
            "fresh_failures": fresh["provider_failures"],
            "inherited_failures": inherited["provider_failures"],
        })
    failures = sum(row["fresh_failures"] + row["inherited_failures"] for row in out)
    accepted = bool(improvements and all(x >= 0 for x in improvements)
                    and sum(improvements) > 0 and failures == 0)
    return {
        "cohorts": out, "total_energy_gain": sum(improvements),
        "wins": sum(x > 0 for x in improvements),
        "losses": sum(x < 0 for x in improvements),
        "ties": sum(x == 0 for x in improvements),
        "provider_failures": failures,
        "accepted": accepted,
        "note": ("Acceptance is a conservative deterministic cohort gate, not a "
                 "statistical significance claim. Two live inference arms do "
                 "not share identical model outputs; classical DP remains "
                 "an unpriced exact comparison.")
    }


def _head(report: dict) -> str:
    return hashlib.sha256(canonical({
        key: report[key] for key in ("protocol", "training", "policy",
                                     "holdout_seeds", "episodes", "summary")
    }).encode("utf-8")).hexdigest()


def _validate_sets(training: list[dict], holdout_seeds: list[int],
                   case_count: int, items: int, profile: str) -> None:
    if not 2 <= len(holdout_seeds) <= MAX_HOLDOUT:
        raise ValueError("M1.7 requires 2 to 4 held-out seeds")
    if any(type(s) is not int or s < 0 for s in holdout_seeds):
        raise ValueError("held-out seeds must be nonnegative integers")
    if len(set(holdout_seeds)) != len(holdout_seeds):
        raise ValueError("duplicate held-out seeds")
    fingerprints: set[str] = set()
    for item in training:
        hashes = _task_hashes(item["manifest"])
        if fingerprints & hashes:
            raise ValueError("duplicate training puzzle")
        fingerprints |= hashes
    for seed in holdout_seeds:
        hashes = _task_hashes({
            "seed": seed, "cases": case_count,
            "items": items, "profile": profile,
        })
        if fingerprints & hashes:
            raise ValueError("training / holdout puzzle overlap")
        fingerprints |= hashes


def build_m17(args, training: list[dict]) -> dict:
    if args.a != "llm" or args.b != "greedy":
        raise ValueError("M1.7 requires --a llm --b greedy")
    seeds = [int(part.strip()) for part in args.holdout_seeds.split(",")
             if part.strip().isascii() and part.strip().isdigit()]
    if len(seeds) != len(args.holdout_seeds.split(",")):
        raise ValueError("--holdout-seeds must be comma-separated integers")
    trained = aggregate_training(training)
    _validate_sets(training, seeds, args.benchmark_cases,
                   args.benchmark_items, args.benchmark_profile)
    if args.provider != "fake" and 2 * len(seeds) * args.max_requests > MAX_LIVE_CALLS:
        raise ValueError("M1.7 live holdout exceeds 24 worst-case calls; reduce seeds or --max-requests")
    episodes = []
    for seed in seeds:
        child = copy.copy(args)
        child.seed = seed
        child.benchmark_out = None
        # Independent arms, independent provider counters and quota.
        fresh = build_report(child, initial_state())
        inherited = build_report(child, trained)
        episodes.append({"seed": seed, "fresh": fresh, "inherited": inherited})
    report = {"protocol": EXPERIMENT, "training": training,
              "policy": trained, "holdout_seeds": seeds,
              "episodes": episodes, "summary": _scoring(episodes)}
    report["head"] = _head(report)
    verify_m17(report)
    return report


def verify_m17(report: dict) -> dict:
    if not isinstance(report, dict) or report.get("protocol") != EXPERIMENT:
        raise ValueError("unsupported M1.7 report")
    training = report.get("training")
    if not isinstance(training, list):
        raise ValueError("training reports missing")
    policy = aggregate_training(training)
    if policy != report.get("policy"):
        raise ValueError("inherited policy does not match training")
    episodes = report.get("episodes")
    seeds = report.get("holdout_seeds")
    if not isinstance(episodes, list) or not isinstance(seeds, list) or len(episodes) != len(seeds):
        raise ValueError("invalid M1.7 cohort list")
    if not episodes:
        raise ValueError("empty held-out comparison")
    reference = episodes[0]["fresh"]["manifest"]
    _validate_sets(training, seeds, reference["cases"], reference["items"],
                   reference["profile"])
    for seed, entry in zip(seeds, episodes):
        if entry.get("seed") != seed:
            raise ValueError("M1.7 cohort seed mismatch")
        fresh, inherited = entry["fresh"], entry["inherited"]
        verify_adaptive_report(fresh)
        verify_adaptive_report(inherited)
        f, i = fresh["manifest"], inherited["manifest"]
        if (f["seed"] != seed or i["seed"] != seed
                or f["policy_initial"] != initial_state()
                or i["policy_initial"] != policy
                or {k:v for k,v in f.items() if k != "policy_initial"}
                != {k:v for k,v in i.items() if k != "policy_initial"}):
            raise ValueError("unpaired or incorrectly inherited M1.7 arms")
        if any(f[k] != reference[k] for k in
               ("cases", "items", "profile", "requested_model", "provider",
                "request_cap")):
            raise ValueError("inconsistent evaluation cohort settings")
    if _scoring(episodes) != report.get("summary"):
        raise ValueError("M1.7 summary mismatch")
    if _head(report) != report.get("head"):
        raise ValueError("M1.7 report digest mismatch")
    return {"verified": True, "head": report["head"], "summary": report["summary"],
            "policy": policy}


def run_m17(args) -> dict:
    if not args.train_report:
        raise ValueError("M1.7 requires one or more --train-report M1.6 JSON files")
    if not 1 <= len(args.train_report) <= MAX_TRAIN:
        raise ValueError("M1.7 accepts at most 4 training reports")
    if args.benchmark_out and Path(args.benchmark_out).exists():
        raise ValueError("benchmark output exists; choose another filename")
    if args.promote_policy_out and Path(args.promote_policy_out).exists():
        raise ValueError("policy output already exists; choose another filename")
    training = [_read_json(path) for path in args.train_report]
    report = build_m17(args, training)
    write_report(report, args.benchmark_out)
    promoted = False
    if report["summary"]["accepted"] and args.promote_policy_out:
        snapshot = {"version": POLICY_VERSION, "state": report["policy"],
                    "training_heads": [r["head"] for r in training],
                    "gate_report_head": report["head"]}
        write_report(snapshot, args.promote_policy_out)
        promoted = True
    return {"verified": True, "head": report["head"],
            "summary": report["summary"], "report_path": args.benchmark_out,
            "policy": report["policy"], "policy_promoted": promoted,
            "promotion_path": args.promote_policy_out if promoted else None}


def verify_m17_file(path: str) -> dict:
    return verify_m17(_read_json(path))
