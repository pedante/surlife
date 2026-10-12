"""M2.1 fake-provider safety, accounting, prompt ownership and replay tests."""
import copy
import json

import pytest

from surlife.m21 import build_report, verify_file, verify_report


def test_reproducible_and_independently_rebuilds():
    first = build_report(17, 24, "evolving", "frozen", 8)
    second = build_report(17, 24, "evolving", "frozen", 8)
    assert first == second
    assert verify_report(first)["verified"]
    assert first["summary"]["actual_provider_requests"] == 0
    assert first["summary"]["actual_provider_tokens"] == 0
    assert first["manifest"]["provider"] == "scripted-fake"
    assert len(first["episodes"]["primary"]["ticks"]) == 24


def test_candidate_is_owned_staged_and_gated():
    report = build_report(17, 24, "evolving", "frozen", 12)
    episode = report["episodes"]["primary"]
    a = episode["organisms"]["a"]
    b = episode["organisms"]["b"]
    assert b["soul_version"] == 0
    assert b["revision_events"] == []
    assert b["consultations"] == 0
    assert a["consultations"] == episode["fake_requests"]
    stages = [e for e in a["revision_events"] if e["decision"] == "staged"]
    outcomes = [e for e in a["revision_events"]
                if e["decision"] in ("activated", "rejected")]
    assert len(stages) <= 1
    assert len(outcomes) <= 1
    if outcomes:
        assert stages
        assert outcomes[0]["parent_hash"] == stages[0]["parent_hash"]
        assert outcomes[0]["candidate_hash"] == stages[0]["candidate_hash"]
        assert outcomes[0]["trial_count"] == 3
        assert outcomes[0]["paid_trial_requests"] == 3
        assert a["soul_version"] == int(outcomes[0]["decision"] == "activated")
        if a["soul_version"]:
            assert a["soul_hash"] == stages[0]["candidate_hash"]
    for row in episode["ticks"]:
        assert row["genomes_before"]["b"] == row["genomes_after"]["b"]
        assert sum(row["after"].values()) == 0
        assert sum(t["amount"] for t in row["transfers"]
                   if t["kind"] == "cognition") == sum(row["consultations"].values())
        assert row["consultations"]["a"] in (0, 1)
        assert row["consultations"]["b"] == 0


def test_holdout_is_disjoint_and_has_no_direct_candidate_authority():
    report = build_report(29, 24, "evolving", "frozen", 8)
    episode = report["episodes"]["primary"]
    from surlife.m21 import digest
    live = {digest(row["task"]) for row in episode["ticks"]}
    trial_hashes = []
    for row in episode["ticks"]:
        for mutation in row["mutations"]:
            if mutation["decision"] == "trial":
                assert mutation["task_hash"] not in live
                trial_hashes.append(mutation["task_hash"])
    assert len(trial_hashes) == len(set(trial_hashes))
    staged = next((i for row in episode["ticks"] for i in row["mutations"]
                   if i["decision"] == "staged"), None)
    if staged:
        staged_tick = next(row["tick"] for row in episode["ticks"]
                           if any(m.get("decision") == "staged" for m in row["mutations"]))
        assert episode["ticks"][staged_tick]["genomes_before"]["a"] == \
               episode["ticks"][staged_tick]["genomes_after"]["a"]


def test_seed_17_exercises_actual_activation():
    report = build_report(17, 24, "evolving", "frozen", 8)
    organism = report["episodes"]["primary"]["organisms"]["a"]
    events = organism["revision_events"]
    assert [event["decision"] for event in events] == ["staged", "activated"]
    assert organism["soul_version"] == 1
    assert events[1]["candidate_hash"] == organism["soul_hash"]
    assert report["summary"]["a_energy_difference_vs_frozen"] <= 0


def test_nonimproving_candidate_is_rejected(monkeypatch):
    import surlife.m21 as m21
    monkeypatch.setattr(m21, "SUGGESTION",
                        "Try to check the subset cost carefully before committing.")
    report = m21.build_report(17, 24, "evolving", "frozen", 8)
    organism = report["episodes"]["primary"]["organisms"]["a"]
    assert [e["decision"] for e in organism["revision_events"]] == ["staged", "rejected"]
    assert organism["soul_version"] == 0
    assert report["episodes"]["primary"]["fake_requests"] == 4


def test_budget_cap_including_trials():
    report = build_report(17, 32, "evolving", "frozen", 1)
    ep = report["episodes"]["primary"]
    assert ep["fake_requests"] <= 1
    assert len(ep["consultations"]) == ep["fake_requests"]
    assert ep["organisms"]["a"]["soul_version"] == 0
    assert all(row["after"]["a"] >= 0 for row in ep["ticks"])


def test_both_organisms_own_private_versions():
    report = build_report(4, 28, "evolving", "evolving", 16)
    ep = report["episodes"]["primary"]
    assert ep["fake_requests"] <= 16
    assert ep["organisms"]["a"]["consultations"] + ep["organisms"]["b"]["consultations"] == ep["fake_requests"]
    for actor in ("a", "b"):
        for event in ep["organisms"][actor]["revision_events"]:
            assert event["decision"] in ("staged", "activated", "rejected")
        assert ep["organisms"][actor]["soul_version"] in (0, 1)
    assert verify_report(report)["verified"]


def test_tampering_is_detected_even_if_attacker_does_not_change_digest():
    report = build_report(17, 24)
    manipulated = copy.deepcopy(report)
    manipulated["episodes"]["primary"]["ticks"][0]["after"]["a"] += 100
    with pytest.raises(ValueError, match="mismatch"):
        verify_report(manipulated)
    manipulated = copy.deepcopy(report)
    manipulated["episodes"]["primary"]["organisms"]["a"]["active_prompt"] = "FORGED"
    with pytest.raises(ValueError, match="mismatch"):
        verify_report(manipulated)


def test_file_verification(tmp_path):
    output = tmp_path / "m21.json"
    output.write_text(json.dumps(build_report(11, 12)), encoding="utf-8")
    assert verify_file(str(output))["verified"]
    output.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON"):
        verify_file(str(output))


@pytest.mark.parametrize("kwargs", [
    {"seed": -1}, {"ticks": 1}, {"ticks": 65},
    {"a": "bad"}, {"b": "bad"}, {"max_requests": 0},
    {"max_requests": 25}, {"max_requests": True},
])
def test_invalid_inputs_fail_closed(kwargs):
    with pytest.raises(ValueError):
        options = {"seed": 17, "ticks": 12}
        options.update(kwargs)
        build_report(**options)


def test_frozen_baseline_and_no_organism_prompt_changes():
    report = build_report(5, 16, "frozen", "frozen", 6)
    assert report["summary"]["primary_fake_requests"] == 0
    assert report["episodes"]["primary"] == report["episodes"]["frozen_control"]
