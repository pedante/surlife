"""M1.2 offline tests: no real network or API credentials."""
from __future__ import annotations

import json
from argparse import Namespace

import pytest

from surlife.core import Arena
from surlife.evaluation_v2 import evaluate_snapshot_v2
from surlife.gateway import GatewayError, Reply
from surlife.m11 import EvolutionSoul, run_m11, task_fingerprint
from surlife.souls import Soul
from surlife.storage import Journal


def options(tmp_path, **changes):
    args = dict(
        a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, ticks=12, max_requests=8, reasoning="off",
        max_output_tokens=512, cognition="selective", m12=True,
        run_id="m12-1", souls_dir=str(tmp_path / "souls"),
        soul_a=None, inherit_soul_a=None, evaluate_soul=None,
        evaluation_seed=2003, evaluation_tasks=2,
        evaluation_cohorts=2, max_evaluation_requests=24, eval_min_gain=2,
    )
    args.update(changes)
    return Namespace(**args)


def _snapshot(tmp_path):
    root = tmp_path / "independent"
    soul = EvolutionSoul(**Soul.new("a").__dict__)
    obs = Arena(15).observations()["a"]
    soul.observe_result(obs, 31, -1, obs.task.optimum, 0, 20, "llm_action")
    assert soul.stage("Enumerate all feasible subsets before selecting the maximum legal reward.", 0)
    soul.save(root)
    return root / "a.json"


def test_m12_run_records_full_history_and_same_task_shadow_baseline(tmp_path):
    args = options(tmp_path)
    result = run_m11(args, tmp_path / "world.sqlite")
    assert result["kind"] == "m12-observable-evolution"
    assert result["verified"]
    assert result["rounds"] == 12
    assert result["soul_versions"] == {"a": 0}
    assert "llm_action" in result["by_action_source"]
    assert "greedy_fallback" in result["by_action_source"]
    compared = result["llm_vs_shadow_greedy"]
    assert compared["compared"] == result["consultation_modes"]["action"]
    assert sum(compared[name] for name in ("better", "worse", "same")) == compared["compared"]
    assert result["consultations"]["a"] == result["provider_requests"]
    snapshot = tmp_path / "souls" / "m12-1" / "a.json"
    soul = EvolutionSoul.restore("a", str(snapshot))
    assert soul.history_complete
    assert len(soul.seen_task_hashes) == 12
    assert len(soul.memory) == 8
    with Journal(tmp_path / "world.sqlite") as journal:
        assert journal.replay("m12-1")["verified"]
        for (payload,) in journal.db.execute(
            "SELECT payload FROM rounds WHERE run_id=? ORDER BY tick", ("m12-1",)
        ):
            row = json.loads(payload)
            actor = row["model_calls"]["a"]
            obs_task = row["task"]
            assert task_fingerprint(obs_task) in soul.seen_task_hashes
            assert actor["shadow_greedy_score"] >= 0
            if actor["action_source"] == "llm_action":
                assert actor["delta_vs_greedy"] == (
                    row["scores"]["a"] - actor["shadow_greedy_score"]
                )


def test_two_cohort_fake_evaluation_rejects_equal_performance(tmp_path):
    snap = _snapshot(tmp_path)
    result = evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    report = result["evaluation"]
    assert report["protocol"] == "m12-multi-cohort-held-out-v1"
    assert report["expected_requests"] == report["requests"] == 8
    assert report["decision"] == "rejected"
    assert len(report["cohort_results"]) == 2
    assert len(report["pair_results"]) == 2
    assert report["paired_ties"] == 4
    assert not report["accepted"]
    assert len(EvolutionSoul.restore("a", str(snap)).pending) == 0
    assert result["soul_version"] == 0


def test_multi_cohort_evaluation_accepts_consistent_gain(tmp_path, monkeypatch):
    import surlife.evaluation_v2 as evaluator
    snap = _snapshot(tmp_path)

    class Differentiated:
        def __init__(self, max_requests):
            self.calls = 0
            self.model = "fake/differentiated"
        def ask(self, messages):
            self.calls += 1
            data = json.loads(messages[-1]["content"])
            task = data["task"]
            if "Experience note:" in messages[0]["content"]:
                from surlife.core import Task
                t = Task(tuple(tuple(x) for x in task["items"]), task["capacity"])
                mask = max(range(32), key=lambda m: t.score(m))
            else:
                mask = 0
            return Reply(mask, "", self.model, {
                "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
            })
    monkeypatch.setattr(evaluator, "FakeGateway", Differentiated)
    result = evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    e = result["evaluation"]
    assert e["decision"] == "accepted"
    assert e["paired_wins"] == 4 and e["paired_losses"] == 0
    assert all(item["passes"] for item in e["cohort_results"])
    assert e["reported_tokens"]["total_tokens"] == 8 * 15
    assert result["soul_version"] == 1
    saved = EvolutionSoul.restore("a", str(snap))
    assert saved.history_complete and saved.version == 1
    assert not saved.pending


def test_one_bad_cohort_blocks_adoption_even_with_early_gain(tmp_path, monkeypatch):
    import surlife.evaluation_v2 as evaluator
    from surlife.core import Task
    snap = _snapshot(tmp_path)

    class Regressing:
        def __init__(self, max_requests):
            self.calls = 0
            self.model = "fake/regressing"
        def ask(self, messages):
            pair = self.calls // 2
            self.calls += 1
            task = json.loads(messages[-1]["content"])["task"]
            t = Task(tuple(tuple(x) for x in task["items"]), task["capacity"])
            is_candidate = "Experience note:" in messages[0]["content"]
            # Clear win on first cohort, clear loss on second cohort.
            mask = (max(range(32), key=lambda m: t.score(m))
                    if is_candidate == (pair < 2) else 0)
            return Reply(mask, "", self.model, {
                "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2,
            })
    monkeypatch.setattr(evaluator, "FakeGateway", Regressing)
    result = evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    e = result["evaluation"]
    assert e["cohort_results"][0]["passes"] is True
    assert e["cohort_results"][1]["passes"] is False
    assert e["decision"] == "rejected"
    assert result["soul_version"] == 0


def test_real_provider_failure_keeps_pending_for_new_seed(tmp_path, monkeypatch):
    import surlife.evaluation_v2 as evaluator
    snap = _snapshot(tmp_path)

    class Down:
        def __init__(self, max_requests):
            self.calls = 0
            self.model = "fake/down"
        def ask(self, messages):
            self.calls += 1
            raise GatewayError("provider unavailable", reason="network_failure")
    monkeypatch.setattr(evaluator, "FakeGateway", Down)
    result = evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    assert result["evaluation"]["decision"] == "aborted"
    assert result["evaluation"]["requests"] == 1
    assert result["pending_revisions"] == 1
    assert result["soul_version"] == 0
    assert result["evaluation"]["failure"]["reason"] == "network_failure"
    with pytest.raises(ValueError, match="already been used"):
        evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    # A fresh evaluation seed is permitted; the proposal hasn't been discarded.
    retry = evaluate_snapshot_v2(options(
        tmp_path, evaluate_soul=str(snap), evaluation_seed=3003
    ))
    assert retry["evaluation"]["decision"] == "aborted"
    assert retry["pending_revisions"] == 1


def test_preflight_caps_requests_before_any_provider_access(tmp_path, monkeypatch):
    import surlife.evaluation_v2 as evaluator
    snap = _snapshot(tmp_path)
    def unexpected(**kwargs):
        raise AssertionError("provider should never be initialized")
    monkeypatch.setattr(evaluator, "OpenRouterGateway", unexpected)
    with pytest.raises(ValueError, match="hard cap"):
        evaluate_snapshot_v2(options(
            tmp_path, evaluate_soul=str(snap), provider="openrouter",
            evaluation_tasks=10, evaluation_cohorts=2,
        ))
    original = EvolutionSoul.restore("a", str(snap))
    assert original.pending and not original.evaluation_history


def test_single_cohort_is_not_enough_for_m12_acceptance(tmp_path):
    snap = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="at least 2"):
        evaluate_snapshot_v2(options(
            tmp_path, evaluate_soul=str(snap), evaluation_cohorts=1
        ))


def test_all_previous_tasks_excluded_not_only_last_eight(tmp_path):
    args = options(tmp_path, ticks=13)
    run_m11(args, tmp_path / "world.sqlite")
    source = tmp_path / "souls" / "m12-1" / "a.json"
    soul = EvolutionSoul.restore("a", str(source))
    assert len(soul.seen_task_hashes) == 13
    assert len(soul.memory) == 8
    from surlife.evaluation_v2 import _make_holdouts, _validated_plan
    plan = _validated_plan(options(tmp_path, evaluate_soul=str(source)), soul)
    batches = _make_holdouts(plan, set(soul.seen_task_hashes))
    selected = [h for cohort in batches for h, _ in cohort]
    assert not set(selected).intersection(soul.seen_task_hashes)
    assert len(set(selected)) == len(selected)


def test_legacy_snapshot_without_provenance_fails_closed(tmp_path):
    snap = _snapshot(tmp_path)
    data = json.loads(snap.read_text())
    data.pop("seen_task_hashes")
    data.pop("history_complete")
    data.pop("task_history_sha256")
    snap.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="complete task fingerprints"):
        evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))


def test_invalid_action_is_not_silently_repaired(tmp_path, monkeypatch):
    import surlife.m11 as m11
    class AlwaysInvalid:
        def __init__(self, max_requests):
            self.calls = 0
            self.limit = max_requests
            self.model = "fake/invalid"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action"):
            self.calls += 1
            return Reply(31 if mode == "action" else None,
                         "Check selected costs against capacity before submitting any subset.",
                         self.model, {"prompt_tokens": 0, "completion_tokens": 0,
                                      "total_tokens": 0})
    monkeypatch.setattr(m11, "FakeGateway", AlwaysInvalid)
    result = run_m11(options(tmp_path), tmp_path / "bad.sqlite")
    assert result["invalid_attempts"]["a"] > 0
    assert result["by_action_source"]["llm_action"]["invalid"] > 0
    assert result["llm_vs_shadow_greedy"]["worse"] > 0


def test_no_posthoc_prompt_history_rewrite_after_rejection(tmp_path):
    snap = _snapshot(tmp_path)
    old = EvolutionSoul.restore("a", str(snap)).sha256
    evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))
    soul = EvolutionSoul.restore("a", str(snap))
    assert soul.sha256 == old
    assert soul.version == 0
    assert soul.evaluation_history[-1]["decision"] == "rejected"



def test_task_history_checksum_detects_accidental_edit(tmp_path):
    snap = _snapshot(tmp_path)
    original = json.loads(snap.read_text())
    original["seen_task_hashes"].clear()
    snap.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="checksum mismatch"):
        EvolutionSoul.restore("a", str(snap))


def test_history_marked_incomplete_when_checksum_absent(tmp_path):
    snap = _snapshot(tmp_path)
    content = json.loads(snap.read_text())
    content.pop("task_history_sha256")
    snap.write_text(json.dumps(content))
    restored = EvolutionSoul.restore("a", str(snap))
    assert not restored.history_complete
    with pytest.raises(ValueError, match="complete task fingerprints"):
        evaluate_snapshot_v2(options(tmp_path, evaluate_soul=str(snap)))


def test_random_router_disallowed_before_provider_calls(tmp_path, monkeypatch):
    snap = _snapshot(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY")
    import surlife.evaluation_v2 as evaluator
    def forbidden(_model):
        raise AssertionError("catalog should not have been queried")
    monkeypatch.setattr(evaluator, "check_model", forbidden)
    with pytest.raises(ValueError, match="pinned"):
        evaluate_snapshot_v2(options(
            tmp_path, evaluate_soul=str(snap), provider="openrouter",
            model="openrouter/free",
        ))
    assert EvolutionSoul.restore("a", str(snap)).pending


def test_model_switch_mid_evaluation_aborts_without_adoption(tmp_path, monkeypatch):
    import surlife.evaluation_v2 as evaluator
    snap = _snapshot(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY")
    monkeypatch.setattr(evaluator, "check_model", lambda _: None)
    class Switched:
        def __init__(self, model, max_requests, max_output_tokens, reasoning):
            self.calls = 0
            self.model = model
        def ask(self, messages):
            self.calls += 1
            return Reply(1, "", "unrelated/free-model:free", {
                "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
            })
    monkeypatch.setattr(evaluator, "OpenRouterGateway", Switched)
    result = evaluate_snapshot_v2(options(
        tmp_path, evaluate_soul=str(snap), provider="openrouter",
    ))
    assert result["evaluation"]["failure"]["reason"] == "routed_model_mismatch"
    assert result["evaluation"]["requests"] == 1
    assert result["evaluation"]["decision"] == "aborted"
    assert result["pending_revisions"] == 1
