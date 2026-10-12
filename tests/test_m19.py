"""M1.9 deterministic non-additive taskpacks, baselines, referee audit."""
from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest

from surlife.m19 import (
    InteractionTask, beam_mask, independent_score, make_pack_cases,
    make_report, marginal_mask, run_m19, verify_m19, verify_m19_file,
)


def options(tmp_path, **changes):
    values = {
        "a": "greedy", "b": "greedy", "provider": "fake",
        "seed": 17, "benchmark_cases": 4, "benchmark_items": 10,
        "m19_pack": "mixed", "benchmark_out": str(tmp_path / "m19.json"),
    }
    values.update(changes)
    return Namespace(**values)


@pytest.mark.parametrize("pack", ["coverage", "synergy", "mixed"])
def test_taskpacks_are_seeded_and_independently_scored(pack):
    cases = make_pack_cases(17, 4, 9, pack)
    same = make_pack_cases(17, 4, 9, pack)
    assert [case["task"].as_dict() for case in cases] == [
        case["task"].as_dict() for case in same]
    assert len(cases) == 4
    if pack == "mixed":
        assert [case["kind"] for case in cases] == [
            "coverage", "synergy", "coverage", "synergy"]
    for case in cases:
        task = case["task"]
        assert task.as_dict()["pack"] == case["kind"]
        assert "rule" in task.as_dict()
        for mask in range(1 << len(task.items)):
            assert task.score(mask) == independent_score(task, mask)
        assert task.optimum == case["oracle_score"]
        assert task.score(case["oracle_mask"]) == task.optimum
        for name in ("greedy", "marginal", "beam"):
            assert task.score(case[name + "_mask"]) == case[name + "_score"]
            assert task.score(case[name + "_mask"]) >= 0
            assert task.score(case[name + "_mask"]) <= task.optimum


def test_coverage_does_not_double_count_overlap():
    task = InteractionTask(
        ((2, 9), (2, 9), (2, 7), (6, 16),
         (1, 1), (1, 1), (1, 1), (1, 1)),
        8, "coverage",
        feature_masks=(1, 1, 2, 3, 4, 4, 4, 4),
        feature_weights=(9, 7, 1),
    )
    # Identical feature coverage is paid only once.
    assert task.score(1 | 2) == 9
    assert task.score(1 | 4) == 16
    assert task.score(1 | 8) == 16
    assert task.score(1 | 2 | 4) == 16
    assert task.score(-1) == -1
    assert task.score(1 << 8) == -1
    assert independent_score(task, 1 | 4) == 16


def test_synergy_can_reward_complementary_resources():
    task = InteractionTask(
        ((4, 3), (4, 3), (3, 8), (3, 8),
         (1, 2), (1, 2), (2, 3), (2, 3)),
        8, "synergy", bonuses=((0, 1, 30),),
    )
    assert task.score(1 | 2) == 36
    assert independent_score(task, 1 | 2) == 36
    assert task.optimum >= 36
    assert task.score(1 | 2 | 4) == -1
    assert marginal_mask(task) != 1 | 2
    assert task.score(beam_mask(task)) <= task.optimum


@pytest.mark.parametrize("pack", ["coverage", "synergy", "mixed"])
def test_offline_report_replays_original_referee(pack, tmp_path):
    result = run_m19(options(tmp_path, m19_pack=pack))
    assert result["verified"]
    assert result["manifest"]["provider"] == "none"
    assert result["manifest"]["cognition_requests"] == 0
    assert verify_m19_file(result["report_path"])["verified"]
    data = json.loads((tmp_path / "m19.json").read_text())
    assert set(data["arms"]) == {"greedy", "marginal", "beam", "oracle"}
    for name, arm in data["arms"].items():
        assert len(arm) == 4
        assert all(rec["consultations"] == {"a": 0, "b": 0} for rec in arm)
        assert all(sum(rec["after"].values()) == 0 for rec in arm)
        assert data["summary"]["arms"][name]["invalid"] == 0
    assert data["summary"]["headroom"]["oracle_total"] >= data["summary"]["headroom"]["greedy_total"]


def test_taskpack_generation_across_seeds_has_measurable_gaps():
    total = 0
    for seed in (17, 19, 23, 29):
        report = make_report(seed, 4, 9, "mixed")
        assert verify_m19(report)["verified"]
        total += report["summary"]["headroom"]["positive_gap_cases"]
        for name in ("greedy", "marginal", "beam"):
            assert report["summary"]["arms"][name]["task_score_sum"] <= (
                report["summary"]["arms"]["oracle"]["task_score_sum"])
    assert total > 0


def test_replay_detects_referee_action_and_pack_tampering(tmp_path):
    run_m19(options(tmp_path))
    source = json.loads((tmp_path / "m19.json").read_text())
    tampered = copy.deepcopy(source)
    tampered["arms"]["beam"][0]["actions"]["a"] = 0
    with pytest.raises(ValueError, match="replay"):
        verify_m19(tampered)
    tampered = copy.deepcopy(source)
    tampered["arms"]["greedy"][0]["task"]["feature_weights"] = [99] * 8
    with pytest.raises(ValueError, match="replay"):
        verify_m19(tampered)
    tampered = copy.deepcopy(source)
    tampered["summary"]["arms"]["oracle"]["energy"] = -100
    with pytest.raises(ValueError, match="replay"):
        verify_m19(tampered)


def test_budget_and_type_bounds_are_enforced():
    invalid = [
        (-1, 4, 10, "mixed"),
        (17, 0, 10, "mixed"),
        (17, 49, 10, "mixed"),
        (17, 4, 7, "mixed"),
        (17, 4, 15, "mixed"),
        (17, 4, 10, "unknown"),
    ]
    for params in invalid:
        with pytest.raises(ValueError):
            make_pack_cases(*params)
    case = make_pack_cases(17, 1, 8, "coverage")[0]["task"]
    assert case.score(True) == -1
    assert independent_score(case, True) == -1
    for width in (0, 257, False):
        with pytest.raises(ValueError):
            beam_mask(case, width)


def test_no_hosted_provider_and_existing_report_preflight(tmp_path):
    with pytest.raises(ValueError, match="offline-only"):
        run_m19(options(tmp_path, provider="google"))
    with pytest.raises(ValueError, match="benchmark-out"):
        run_m19(options(tmp_path, benchmark_out=None))
    first = run_m19(options(tmp_path))
    assert first["verified"]
    with pytest.raises(ValueError, match="exists"):
        run_m19(options(tmp_path))
