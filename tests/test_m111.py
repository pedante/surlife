"""M1.11 family-specific inherited learning and held-out response-bank audit."""
from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest

from surlife.m110 import _assemble as assemble_m110, run_m110
from surlife.m111 import (
    FamilyPolicy, _head, _score, _check_inputs, build_m111,
    initial_family_state, run_m111, simulate,
    validate_family_state, verify_m111, verify_m111_file,
)


def args(tmp_path, **changes):
    params = dict(
        a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, benchmark_cases=4, benchmark_items=9,
        m110_pack="mixed", max_requests=4, m110_virtual_cap=4,
        m110_bank_in=None, max_output_tokens=512, reasoning="off",
        google_timeout_seconds=45, policy_in=None,
        benchmark_out=str(tmp_path / "base.json"),
        m111_train_bank=[], m111_holdout_bank=[],
        m111_virtual_cap=4,
        m111_promote_policy_out=str(tmp_path / "policy.json"),
    )
    params.update(changes)
    return Namespace(**params)


def banks(tmp_path, seeds=(17, 19, 101, 103)):
    files, reports = [], []
    for seed in seeds:
        path = str(tmp_path / f"m110-bank-{seed}.json")
        run_m110(args(tmp_path, seed=seed, benchmark_out=path))
        files.append(path)
        reports.append(json.loads((tmp_path / f"m110-bank-{seed}.json").read_text()))
    return files, reports


def test_m111_fake_training_and_holdouts_reject_weak_policy(tmp_path):
    files, reports = banks(tmp_path)
    params = args(
        tmp_path, benchmark_out=str(tmp_path / "m111-eval.json"),
        m111_train_bank=files[:2],
        m111_holdout_bank=files[2:],
    )
    done = run_m111(params)
    assert done["verified"]
    assert not done["policy_promoted"]
    assert done["promotion_path"] is None
    assert not (tmp_path / "policy.json").exists()
    assert verify_m111_file(done["report_path"])["verified"]
    assert done["identity"]["provider"] == "fake"
    assert done["identity"]["pack"] == "mixed"
    assert "no_positive_gain_vs_marginal" in done["summary"]["rejection_reasons"]
    assert len(done["summary"]["cohorts"]) == 2
    for row in done["summary"]["cohorts"]:
        assert row["beam_energy"] >= row["marginal_energy"]
        assert row["inherited_energy"] <= row["marginal_energy"]
    for family in ("coverage", "synergy"):
        assert sum(v["visits"] for v in done["policy"][family].values()) > 0
    saved = json.loads((tmp_path / "m111-eval.json").read_text())
    assert len(saved["training"]) == 2
    assert len(saved["cohorts"]) == 2
    assert saved["cohorts"][0]["bank"]["head"] == reports[2]["head"]
    assert saved["cohorts"][0]["fresh"] != saved["cohorts"][0]["bank"]["arms"]["adaptive_fresh"]


def test_family_policy_keeps_independent_visits_and_learning(tmp_path):
    _, reports = banks(tmp_path, (17,))
    report = reports[0]
    rows, final = simulate(report, None, 4)
    assert rows[0]["benchmark"]["policy_decision"]["family"] == "coverage"
    assert rows[1]["benchmark"]["policy_decision"]["family"] == "synergy"
    assert final["coverage"] != initial_family_state()["coverage"]
    assert final["synergy"] != initial_family_state()["synergy"]
    assert sum(x["trials"] for x in final["coverage"].values()) > 0
    assert sum(x["trials"] for x in final["synergy"].values()) > 0
    cell = FamilyPolicy(final)
    assert cell.snapshot() == final
    invalid = copy.deepcopy(final)
    invalid["coverage"]["routine"]["visits"] = -1
    with pytest.raises(ValueError, match="state"):
        validate_family_state(invalid)
    with pytest.raises(ValueError, match="families"):
        validate_family_state({"coverage": final["coverage"]})


def test_model_response_is_same_for_all_bank_cohorts(tmp_path):
    _, reports = banks(tmp_path, (17, 19, 101, 103))
    report = build_m111(reports[:2], reports[2:])
    assert report["summary"]["accepted"] is False
    for cohort in report["cohorts"]:
        bank = cohort["bank"]["bank"]
        for arm in ("fresh", "inherited"):
            for tick, rec in enumerate(cohort[arm]):
                if rec["consultations"]["a"]:
                    assert rec["actions"]["a"] == bank[tick]["mask"]
                assert rec["benchmark"]["family"] == (
                    "coverage" if tick % 2 == 0 else "synergy")
    assert verify_m111(report)["verified"]


def test_training_overlap_and_wrong_model_are_rejected(tmp_path):
    _, reports = banks(tmp_path)
    a, b, c, d = reports
    with pytest.raises(ValueError, match="seed"):
        build_m111([a, copy.deepcopy(a)], [c, d])
    with pytest.raises(ValueError, match="seed"):
        build_m111([a], [copy.deepcopy(a), d])
    broken = copy.deepcopy(b)
    broken["manifest"]["generation"]["reasoning"] = "low"
    broken = assemble_m110(broken["manifest"], broken["bank"])
    with pytest.raises(ValueError, match="mixed provider"):
        build_m111([a, broken], [c, d])
    with pytest.raises(ValueError, match="2–4"):
        build_m111([a, b], [c])
    with pytest.raises(ValueError, match="1–4"):
        build_m111([], [c, d])


def test_429_in_training_fails_closed_and_heldout_failure_vetoes(tmp_path):
    _, reports = banks(tmp_path)
    a, b, c, d = reports
    def failed_bank(bank):
        changed = copy.deepcopy(bank)
        changed["bank"][0] = {
            "tick": 0, "status": "failed", "reason": "http_429",
            "model": "surlife/fake-model", "usage": None,
        }
        for tick in range(1, changed["manifest"]["cases"]):
            changed["bank"][tick] = {
                "tick": tick, "status": "unavailable",
                "reason": "rate_limited",
            }
        return assemble_m110(changed["manifest"], changed["bank"])

    bad = failed_bank(b)
    with pytest.raises(ValueError, match="training bank contains provider failures"):
        build_m111([a, bad], [c, d])
    result = build_m111([a, b], [failed_bank(c), d])
    assert not result["summary"]["accepted"]
    assert "provider_failures" in result["summary"]["rejection_reasons"]
    assert verify_m111(result)["verified"]


def test_report_replay_rejects_modified_evidence_even_with_resigned_head(tmp_path):
    _, banks_saved = banks(tmp_path)
    report = build_m111(banks_saved[:2], banks_saved[2:])
    mutated = copy.deepcopy(report)
    mutated["training"][0]["policy_final"]["coverage"]["routine"]["gain"] += 1
    mutated["head"] = _head(mutated)
    with pytest.raises(ValueError, match="training"):
        verify_m111(mutated)
    mutated = copy.deepcopy(report)
    mutated["cohorts"][0]["inherited"][0]["consultations"]["a"] = 0
    mutated["head"] = _head(mutated)
    with pytest.raises(ValueError, match="held-out"):
        verify_m111(mutated)
    mutated = copy.deepcopy(report)
    mutated["summary"]["accepted"] = True
    mutated["head"] = _head(mutated)
    with pytest.raises(ValueError, match="summary"):
        verify_m111(mutated)


def test_scoring_gate_requires_positive_gain_over_fresh_and_marginal(monkeypatch):
    import surlife.m111 as m111

    def arm(energy, invalid=0, failures=0):
        return {
            "energy": energy, "invalid": invalid,
            "provider_failures": failures,
            "task_score_sum": 50, "consultations": 2,
        }

    def cohort(seed):
        return {
            "bank": {
                "manifest": {"seed": seed},
                "bank": [{"status": "ok"}],
                "arms": {key: [] for key in BASELINE_NAMES},
            }, "fresh": [], "inherited": [],
        }
    from surlife.m110 import BASELINES as BASELINE_NAMES
    def good_summary(m, bank, arms):
        return {"arms": {
            "fresh": arm(32),
            "inherited": arm(38),
            "marginal": arm(35),
            "beam": arm(40),
            "greedy": arm(31),
            "oracle": arm(40),
        }}
    monkeypatch.setattr(m111, "_summarize", good_summary)
    success = _score([cohort(101), cohort(103)])
    assert success["accepted"]
    assert success["total_gain_vs_marginal"] == 6
    assert success["cohorts"][0]["delta_vs_beam"] == -2  # reference, not gate
    def bad_summary(m, bank, arms):
        stats = good_summary(m, bank, arms)
        stats["arms"]["inherited"] = arm(34)
        return stats
    monkeypatch.setattr(m111, "_summarize", bad_summary)
    failure = _score([cohort(101), cohort(103)])
    assert not failure["accepted"]
    assert "regression_vs_marginal" in failure["rejection_reasons"]


def test_cli_is_offline_and_provenance_enforced(tmp_path, monkeypatch):
    import surlife.m111 as m111
    files, _ = banks(tmp_path)
    monkeypatch.setattr("surlife.m110._collect", lambda *_: (_ for _ in ()).throw(
        AssertionError("M1.11 must not collect any model responses")))
    params = args(tmp_path, m111_train_bank=files[:2],
                  m111_holdout_bank=files[2:])
    result = run_m111(params)
    assert result["verified"]
    with pytest.raises(ValueError, match="exists"):
        run_m111(params)
    with pytest.raises(ValueError, match="model/generation differs"):
        run_m111(args(
            tmp_path, m111_train_bank=files[:2], m111_holdout_bank=files[2:],
            provider="google", model="gemini-3.8-flash",
            max_output_tokens=4096,
            benchmark_out=str(tmp_path / "wrong.json"),
        ))
    with pytest.raises(ValueError, match="virtual consultation cap"):
        build_m111(
            [json.loads((tmp_path / "m110-bank-17.json").read_text())],
            [json.loads((tmp_path / "m110-bank-101.json").read_text()),
             json.loads((tmp_path / "m110-bank-103.json").read_text())],
            cap=0,
        )
