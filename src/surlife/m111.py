"""M1.11: TaskPack-specific inherited cognition with shared-bank held-out gates.

All inputs are replay-verified M1.10 response banks. Training and evaluation
use exactly those stored model answers; no gateway is constructed or called.
Policies learn separate public coverage/synergy contexts and remain data only.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from random import Random

from .core import Action, POLICIES
from .m14 import _can_afford
from .m16 import AdaptivePolicy, initial_state, validate_state, write_report
from .m19 import TaskPackArena, make_pack_cases
from .m110 import (_read_report as read_m110, _shadow_gain,
                   _summarize, verify_m110, VERSION as BANK_VERSION,
                   PROMPT_VERSION, CHEAP_FALLBACK, BASELINES)
from .storage import canonical

VERSION = "m111-v1"
SNAPSHOT_VERSION = "m111-policy-v1"
MAX_TRAIN = 4
MAX_HOLDOUT = 4
MAX_BYTES = 48_000_000
FAMILIES = ("coverage", "synergy")


def initial_family_state() -> dict:
    return {family: initial_state() for family in FAMILIES}


def validate_family_state(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != set(FAMILIES):
        raise ValueError("invalid M1.11 cognition families")
    return {family: validate_state(value[family]) for family in FAMILIES}


class FamilyPolicy:
    """Independent M1.6-v2 learners, separated by public task family."""

    def __init__(self, state: dict | None = None):
        state = validate_family_state(
            initial_family_state() if state is None else state)
        self.policies = {family: AdaptivePolicy(state[family])
                         for family in FAMILIES}

    def choose(self, observation, available: int, affordable: bool) -> dict:
        family = observation.task.mode  # public, reviewed task rule
        if family not in self.policies:
            raise ValueError("unrecognized public TaskPack family")
        return {"family": family,
                **self.policies[family].choose(observation, available,
                                               affordable)}

    def learn(self, family: str, bucket: str, gain: int) -> None:
        if family not in self.policies:
            raise ValueError("learning attempted on unreviewed family")
        self.policies[family].learn(bucket, gain)

    def snapshot(self) -> dict:
        return {family: self.policies[family].snapshot()
                for family in FAMILIES}


def simulate(bank_report: dict, state: dict | None, cap: int) -> tuple[list[dict], dict]:
    """Simulate one fully offline organism against the original M0 referee."""
    manifest = bank_report["manifest"]
    cases = make_pack_cases(manifest["seed"], manifest["cases"],
                            manifest["items"], manifest["pack"])
    response_bank = bank_report["bank"]
    policy = FamilyPolicy(state)
    arena = TaskPackArena(manifest["seed"], cases)
    charged = 0
    records = []
    for tick, (case, response) in enumerate(zip(cases, response_bank)):
        obs = arena.observations()
        own = obs["a"]
        enemy = (POLICIES["greedy"](obs["b"], Random(0))
                 if obs["b"].own_energy else Action(None))
        cheap = Action(case["marginal_mask"]) if own.own_energy else Action(None)
        decision = None
        consult = False
        available = response["status"] != "unavailable"
        if own.own_energy:
            # The success status and answer mask are NOT visible until
            # after the policy has chosen to pay.
            decision = policy.choose(
                own, max(0, cap - charged) if available else 0,
                _can_afford(arena, own))
            consult = decision["consult"]
        action = cheap
        info = {"bank_tick": tick, "family": case["kind"],
                "cheap_baseline": CHEAP_FALLBACK,
                "source": ("dead" if not own.own_energy
                           else "marginal_bank_unavailable" if not available
                           else "marginal_no_inference")}
        if consult:
            charged += 1
            info["model"] = response["model"]
            info["usage"] = response["usage"]
            if response["status"] == "ok":
                action = Action(response["mask"])
                info.update({"source": "llm", "status": "ok"})
            else:
                info.update({"source": "marginal_provider_fallback",
                             "status": "failed",
                             "failure_reason": response["reason"]})
        rec = arena.step({"a": action, "b": enemy},
                         {"a": 1} if consult else {})
        if decision is not None:
            info["policy_decision"] = decision
            if consult:
                gain = _shadow_gain(arena, cases, cheap, enemy, rec)
                info["net_energy_vs_marginal"] = gain
                info["feedback_kind"] = (
                    "model_success" if response["status"] == "ok"
                    else "provider_failure")
                if response["status"] == "ok":
                    policy.learn(decision["family"], decision["bucket"], gain)
            info["policy_after"] = policy.snapshot()
        info.update({
            "pack": case["kind"],
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
    return records, policy.snapshot()


def _identity(bank: dict) -> dict:
    m = bank["manifest"]
    return {
        "provider": m["provider"],
        "model": ("surlife/fake-model" if m["provider"] == "fake"
                  else m["requested_model"]),
        "generation": m["generation"],
        "taskpack_rules": m["taskpack_rules"],
        "prompt_version": m["prompt_version"],
        "fallback": m["fallback"],
        "pack": m["pack"],
        "cases": m["cases"],
        "items": m["items"],
    }


def _fingerprints(bank: dict) -> set[str]:
    m = bank["manifest"]
    tasks = make_pack_cases(m["seed"], m["cases"], m["items"], m["pack"])
    return {hashlib.sha256(canonical(case["task"].as_dict())
                           .encode("utf-8")).hexdigest()
            for case in tasks}


def _check_inputs(training: list[dict], holdouts: list[dict],
                  cap: int, *, require_healthy_training: bool = True) -> dict:
    if not isinstance(training, list) or not 1 <= len(training) <= MAX_TRAIN:
        raise ValueError("M1.11 requires 1–4 training M1.10 banks")
    if not isinstance(holdouts, list) or not 2 <= len(holdouts) <= MAX_HOLDOUT:
        raise ValueError("M1.11 requires 2–4 held-out M1.10 banks")
    if type(cap) is not int or not 1 <= cap <= 48:
        raise ValueError("M1.11 virtual consultation cap must be 1–48")
    identity = None
    fingerprints = set()
    seeds = set()
    for role, banks in (("training", training), ("holdout", holdouts)):
        for bank in banks:
            verify_m110(bank)
            m = bank["manifest"]
            if m["experiment"] != BANK_VERSION:
                raise ValueError("wrong response-bank version")
            current = _identity(bank)
            if identity is None:
                identity = current
            elif identity != current:
                raise ValueError("mixed provider/model/generation or TaskPack settings")
            if m["seed"] in seeds:
                raise ValueError("duplicate training/holdout seed")
            seeds.add(m["seed"])
            hashes = _fingerprints(bank)
            if fingerprints & hashes:
                raise ValueError("training/holdout TaskPack puzzle overlap")
            fingerprints |= hashes
            if role == "training" and require_healthy_training:
                if any(sample["status"] != "ok" for sample in bank["bank"]):
                    raise ValueError(
                        "training bank contains provider failures or unavailable "
                        "responses; cannot infer model reasoning quality")
    return identity


def _merge_training(training: list[dict], cap: int) -> tuple[list[dict], dict]:
    combined = initial_family_state()
    history = []
    for bank in training:
        arm, learned = simulate(bank, initial_family_state(), cap)
        stats = _summarize(
            bank["manifest"], bank["bank"],
            {**{key: bank["arms"][key] for key in BASELINES},
             "learner": arm})["arms"]["learner"]
        if stats["model_actions"] == 0:
            raise ValueError("training bank produced no successful policy consultations")
        for family in FAMILIES:
            for bucket in combined[family]:
                for key in ("visits", "trials", "gain"):
                    combined[family][bucket][key] += learned[family][bucket][key]
        history.append({
            "bank": bank, "learner": arm,
            "policy_final": learned, "stats": stats,
        })
    return history, validate_family_state(combined)


def _score(cohorts: list[dict]) -> dict:
    comparisons = []
    diff_fresh = []
    diff_marginal = []
    for cohort in cohorts:
        m = cohort["bank"]["manifest"]
        arms = {**{key: cohort["bank"]["arms"][key] for key in BASELINES},
                "fresh": cohort["fresh"],
                "inherited": cohort["inherited"]}
        stats = _summarize(m, cohort["bank"]["bank"], arms)["arms"]
        fresh, inherited = stats["fresh"], stats["inherited"]
        marginal, beam = stats["marginal"], stats["beam"]
        advantage_fresh = inherited["energy"] - fresh["energy"]
        advantage_marginal = inherited["energy"] - marginal["energy"]
        diff_fresh.append(advantage_fresh)
        diff_marginal.append(advantage_marginal)
        comparisons.append({
            "seed": m["seed"],
            "fresh_energy": fresh["energy"],
            "inherited_energy": inherited["energy"],
            "marginal_energy": marginal["energy"],
            "beam_energy": beam["energy"],
            "delta_vs_fresh": advantage_fresh,
            "delta_vs_marginal": advantage_marginal,
            "delta_vs_beam": inherited["energy"] - beam["energy"],
            "fresh_score": fresh["task_score_sum"],
            "inherited_score": inherited["task_score_sum"],
            "marginal_score": marginal["task_score_sum"],
            "beam_score": beam["task_score_sum"],
            "fresh_consultations": fresh["consultations"],
            "inherited_consultations": inherited["consultations"],
            "fresh_failures": fresh["provider_failures"],
            "inherited_failures": inherited["provider_failures"],
            "fresh_invalid": fresh["invalid"],
            "inherited_invalid": inherited["invalid"],
            "marginal_invalid": marginal["invalid"],
        })
    reasons = []
    if any(c["fresh_failures"] or c["inherited_failures"]
           or any(x["status"] != "ok" for x in cohort["bank"]["bank"])
           for c, cohort in zip(comparisons, cohorts)):
        reasons.append("provider_failures")
    if any(c["inherited_invalid"] > min(c["fresh_invalid"], c["marginal_invalid"])
           for c in comparisons):
        reasons.append("invalid_action_regression")
    if any(delta < 0 for delta in diff_fresh):
        reasons.append("regression_vs_fresh")
    if sum(diff_fresh) <= 0:
        reasons.append("no_positive_gain_vs_fresh")
    if any(delta < 0 for delta in diff_marginal):
        reasons.append("regression_vs_marginal")
    if sum(diff_marginal) <= 0:
        reasons.append("no_positive_gain_vs_marginal")
    return {
        "cohorts": comparisons,
        "total_gain_vs_fresh": sum(diff_fresh),
        "total_gain_vs_marginal": sum(diff_marginal),
        "wins_vs_fresh": sum(x > 0 for x in diff_fresh),
        "losses_vs_fresh": sum(x < 0 for x in diff_fresh),
        "rejection_reasons": reasons,
        "accepted": bool(comparisons and not reasons),
        "note": (
            "Conservative multi-bank dual-control gate: require strictly "
            "positive aggregate inherited final-energy gains vs BOTH fresh "
            "adaptation and no-inference marginal, no cohort regressions, "
            "no provider errors or invalid-action regression. Unpriced beam "
            "is disclosed as a higher classical reference, not a promotion "
            "requirement; beating it can be impossible when it equals the "
            "exact oracle. This deterministic gate is not statistical proof."
        ),
    }


def _head(report: dict) -> str:
    return hashlib.sha256(canonical({
        key: report[key] for key in (
            "protocol", "identity", "cap", "training",
            "policy", "cohorts", "summary")
    }).encode("utf-8")).hexdigest()


def build_m111(training: list[dict], holdouts: list[dict],
               cap: int = 4) -> dict:
    identity = _check_inputs(training, holdouts, cap)
    history, trained = _merge_training(training, cap)
    cohorts = []
    for bank in holdouts:
        cold, _ = simulate(bank, initial_family_state(), cap)
        inherited, _ = simulate(bank, trained, cap)
        cohorts.append({
            "bank": bank, "fresh": cold, "inherited": inherited,
        })
    report = {
        "protocol": VERSION, "identity": identity, "cap": cap,
        "training": history, "policy": trained,
        "cohorts": cohorts, "summary": _score(cohorts),
    }
    report["head"] = _head(report)
    verify_m111(report)
    return report


def verify_m111(report: dict) -> dict:
    if not isinstance(report, dict) or set(report) != {
            "protocol", "identity", "cap", "training", "policy",
            "cohorts", "summary", "head"} or report["protocol"] != VERSION:
        raise ValueError("unsupported M1.11 evaluation report")
    training = report["training"]
    cohorts = report["cohorts"]
    if (not isinstance(training, list) or not isinstance(cohorts, list)
            or any(not isinstance(row, dict) or "bank" not in row
                   for row in training + cohorts)):
        raise ValueError("invalid M1.11 report training/cohort records")
    banks_train = [row["bank"] for row in training]
    banks_eval = [row["bank"] for row in cohorts]
    identity = _check_inputs(banks_train, banks_eval, report["cap"])
    if identity != report["identity"]:
        raise ValueError("M1.11 model/TaskPack provenance altered")
    rebuilt_history, trained = _merge_training(banks_train, report["cap"])
    if (canonical(rebuilt_history) != canonical(training)
            or trained != report["policy"]):
        raise ValueError("M1.11 training or inherited policy replay mismatch")
    recreated = []
    for bank in banks_eval:
        cold, _ = simulate(bank, initial_family_state(), report["cap"])
        inherited, _ = simulate(bank, trained, report["cap"])
        recreated.append({"bank": bank, "fresh": cold, "inherited": inherited})
    if (canonical(cohorts) != canonical(recreated)
            or canonical(report["summary"]) != canonical(_score(recreated))
            or report["head"] != _head(report)):
        raise ValueError("M1.11 held-out cognition/ledger or summary replay mismatch")
    return {"verified": True, "head": report["head"],
            "summary": report["summary"], "policy": trained}


def _read_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise ValueError("M1.11 evaluation file unavailable or oversized")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid M1.11 JSON") from exc
    return obj


def verify_m111_file(path: str) -> dict:
    return verify_m111(_read_file(path))


def run_m111(args) -> dict:
    if args.a != "llm" or args.b != "greedy":
        raise ValueError("M1.11 requires --a llm --b greedy")
    path = getattr(args, "benchmark_out", None)
    if not path:
        raise ValueError("M1.11 requires --benchmark-out")
    if Path(path).exists():
        raise ValueError("M1.11 report exists; choose a NEW output filename")
    policy_output = getattr(args, "m111_promote_policy_out", None)
    if policy_output and Path(policy_output).exists():
        raise ValueError("M1.11 promoted policy output exists; choose a NEW filename")
    if policy_output and Path(policy_output).resolve() == Path(path).resolve():
        raise ValueError("M1.11 report and policy output cannot be the same file")
    files_train = getattr(args, "m111_train_bank", [])
    files_holdout = getattr(args, "m111_holdout_bank", [])
    if not 1 <= len(files_train) <= MAX_TRAIN or not 2 <= len(files_holdout) <= MAX_HOLDOUT:
        raise ValueError("M1.11 needs 1–4 --m111-train-bank and 2–4 --m111-holdout-bank")
    # All response banks must already be sampled. No real API requests or
    # model gateway construction anywhere in M1.11.
    training = [read_m110(name) for name in files_train]
    holdouts = [read_m110(name) for name in files_holdout]
    identity = _check_inputs(training, holdouts, args.m111_virtual_cap)
    expected_model = ("surlife/fake-model" if args.provider == "fake"
                      else args.model)
    if (identity["provider"] != args.provider or
            identity["model"] != expected_model or
            identity["generation"] != {
                "reasoning": args.reasoning,
                "max_output_tokens": args.max_output_tokens,
            }):
        raise ValueError("M1.11 CLI provider/model/generation differs from response banks")
    report = build_m111(training, holdouts, args.m111_virtual_cap)
    outcome = verify_m111(report)
    write_report(report, path)
    promoted = bool(outcome["summary"]["accepted"] and policy_output)
    if promoted:
        snapshot = {
            "version": SNAPSHOT_VERSION,
            "policy": report["policy"],
            "identity": identity,
            "training_heads": [r["bank"]["head"] for r in report["training"]],
            "heldout_heads": [r["bank"]["head"] for r in report["cohorts"]],
            "gate_report_head": report["head"],
            "gate": "fresh-and-marginal-v1",
        }
        write_report(snapshot, policy_output)
    return {
        "verified": True, "head": report["head"], "identity": identity,
        "policy": report["policy"], "summary": outcome["summary"],
        "policy_promoted": promoted,
        "report_path": path,
        "promotion_path": policy_output if promoted else None,
    }
