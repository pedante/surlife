"""M1.1 regression tests: no real provider calls or secrets required."""
from __future__ import annotations

import json
import sqlite3
from argparse import Namespace

import pytest

from surlife.core import Arena
from surlife.gateway import FakeGateway, GatewayError, OpenRouterGateway, Reply
from surlife.m11 import EvolutionSoul, choose_mode, run_m11
from surlife.evaluation import evaluate_snapshot
from surlife.souls import Soul
from surlife.storage import Journal


def opts(tmp_path, **kw):
    values = dict(
        a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        reasoning="off", cognition="selective",
        seed=11, ticks=8, max_requests=8, max_output_tokens=512,
        run_id="m11-1", souls_dir=str(tmp_path / "souls"),
        soul_a=None, inherit_soul_a=None,
        evaluate_soul=None, evaluation_seed=1009, evaluation_tasks=4,
        eval_min_gain=2,
    )
    values.update(kw)
    return Namespace(**values)


def test_reflection_is_a_distinct_one_call_schema(monkeypatch):
    from surlife.gateway import REFLECTION_SCHEMA
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_SECRET")
    captured = []
    def transport(payload, key, timeout):
        captured.append(payload)
        assert key == "DUMMY_SECRET"
        return {
            "model": "dots-studio/dots-3-note-preview:free",
            "choices": [{"message": {"content": (
                '{"soul_update":"Check the capacity before submitting a solution."}'
            )}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
        }
    gw = OpenRouterGateway(max_requests=1, transport=transport)
    answer = gw.ask([{"role": "user", "content": "{}"}], mode="reflection")
    assert answer.mask is None
    assert answer.soul_update.startswith("Check the capacity")
    assert gw.calls == 1 and gw.remaining == 0
    assert captured[0]["response_format"] == REFLECTION_SCHEMA
    assert "DUMMY_SECRET" not in json.dumps(captured[0])


def test_reflection_rejects_action_only_reply(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_SECRET")
    gw = OpenRouterGateway(max_requests=1, transport=lambda *_: {
        "choices": [{"message": {"content": '{"mask":4}'}}]
    })
    with pytest.raises(GatewayError) as info:
        gw.ask([{"role": "user", "content": "{}"}], mode="reflection")
    assert info.value.reason == "missing_reflection"


def test_staged_revision_rejects_puzzle_examples_and_does_not_mutate_prompt():
    base = Soul.new("a")
    soul = EvolutionSoul(**base.__dict__)
    obs = Arena(11).observations()["a"]
    action = 31
    score = obs.task.score(action)
    assert score < obs.task.optimum
    soul.observe_result(obs, action, score, obs.task.optimum, 0, 24, "llm_action")
    original_hash = soul.sha256
    assert not soul.stage("bit 0 has reward 14, so prefer it.", 0)
    assert soul.stage("Always check total selected cost against capacity before submitting.", 0)
    assert soul.version == 0
    assert soul.sha256 == original_hash
    assert soul.notes == []
    assert len(soul.pending) == 1
    assert not soul.stage("Another valid strategy note that conflicts.", 1)


def test_selective_fake_reflects_separately_without_automatic_adoption(tmp_path):
    args = opts(tmp_path)
    db = tmp_path / "world.sqlite"
    result = run_m11(args, db)
    assert result["verified"]
    assert result["rounds"] == 8
    assert result["soul_versions"] == {"a": 0}
    assert result["consultations"]["a"] == result["model_requests"]
    assert result["provider_requests"] == result["model_requests"]
    assert result["consultation_modes"]["action"] > 0
    assert result["consultation_modes"]["reflection"] > 0
    assert result["staged_revisions"] == 1
    assert result["pending_revisions"] == 1
    saved = EvolutionSoul.restore("a", str(tmp_path / "souls" / "m11-1" / "a.json"))
    assert saved.version == 0 and len(saved.pending) == 1
    assert "task" not in json.dumps(result)
    with Journal(db) as journal:
        rows = [json.loads(x[0]) for x in journal.db.execute(
            "SELECT payload FROM rounds WHERE run_id=? ORDER BY tick", ("m11-1",)
        )]
        assert journal.replay("m11-1")["verified"]
    assert all(row["consultations"]["a"] in (0, 1) for row in rows)
    reflections = [row for row in rows if row["model_calls"].get("a", {}).get("mode") == "reflection"]
    assert reflections and all(
        row["model_calls"]["a"]["action_source"] == "greedy_during_reflection"
        for row in reflections
    )
    assert any("optimal_mask" in item for item in saved.memory)
    assert all("capacity" in item and "legal" in item for item in saved.memory)


def test_never_think_is_an_explicit_cheap_control(tmp_path):
    args = opts(tmp_path, cognition="never", max_requests=8, ticks=8)
    result = run_m11(args, tmp_path / "cheap.sqlite")
    assert result["model_requests"] == 0
    assert result["consultations"]["a"] == 0
    assert result["pending_revisions"] == 0
    assert result["alive"]["a"] is True
    assert result["correct"]["a"] == 7
    assert result["invalid_attempts"]["a"] == 0


def test_always_think_bounded_by_request_budget(tmp_path):
    args = opts(tmp_path, cognition="always", max_requests=2)
    result = run_m11(args, tmp_path / "every.sqlite")
    assert result["provider_requests"] == 2
    assert result["consultations"]["a"] == 2
    assert result["legal_attempts"]["a"] + result["invalid_attempts"]["a"] == 8


def test_selected_cognition_is_a_host_proxy_not_claimed_as_learning():
    base = Soul.new("a")
    soul = EvolutionSoul(**base.__dict__)
    arena = Arena(11)
    weather = arena.observations()["a"].weather
    assert choose_mode(soul, arena, "a", weather, "never", 8) == "cheap"
    assert choose_mode(soul, arena, "a", weather, "always", 8) == "action"
    assert choose_mode(soul, arena, "a", weather, "selective", 8) == "action"
    assert choose_mode(soul, arena, "a", weather, "always", 0) == "cheap"


def _staged_soul(tmp_path):
    base = Soul.new("a")
    soul = EvolutionSoul(**base.__dict__)
    obs = Arena(11).observations()["a"]
    soul.observe_result(obs, 31, -1, obs.task.optimum, 0, 25, "llm_action")
    assert soul.stage("Enumerate all feasible subsets and select the largest legal reward.", 0)
    soul.save(tmp_path)
    return tmp_path / "a.json"


def test_paired_evaluation_rejects_equal_fake_outcomes_without_energy(tmp_path):
    snapshot = _staged_soul(tmp_path)
    result = evaluate_snapshot(opts(tmp_path, evaluate_soul=str(snapshot)))
    evaluation = result["evaluation"]
    assert evaluation["requests"] == 8
    assert evaluation["baseline_score"] == evaluation["candidate_score"]
    assert evaluation["accepted"] is False
    assert result["soul_version"] == 0
    restored = EvolutionSoul.restore("a", str(snapshot))
    assert not restored.pending and len(restored.evaluation_history) == 1
    with pytest.raises(ValueError, match="already been used"):
        # Stage another hypothesis only to exercise reuse guard.
        restored.observe_result(Arena(12).observations()["a"], 31, -1, 30, 0, 20, "llm_action")
        assert restored.stage("Prefer valid high-reward combinations over guesses.", 1)
        restored.save(tmp_path)
        evaluate_snapshot(opts(tmp_path, evaluate_soul=str(snapshot)))


def test_evaluation_accepts_only_strictly_better_candidate(tmp_path, monkeypatch):
    import surlife.evaluation as evaluation_module
    snapshot = _staged_soul(tmp_path)
    class KnownGateway:
        def __init__(self, max_requests):
            self.calls = 0
            self.limit = max_requests
            self.model = "fake/differential"
        def ask(self, messages):
            self.calls += 1
            data = json.loads(messages[-1]["content"])
            task = data["task"]
            if "Experience note:" not in messages[0]["content"]:
                mask = 0
            else:
                cap = task["capacity"]
                items = task["items"]
                def value(m):
                    return sum(v for i, (c, v) in enumerate(items) if m & (1 << i))
                legal = [m for m in range(32)
                         if sum(c for i, (c, _) in enumerate(items) if m & (1 << i)) <= cap]
                mask = max(legal, key=value)
            return Reply(mask=mask, soul_update="", model=self.model,
                         usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2})
    monkeypatch.setattr(evaluation_module, "FakeGateway", KnownGateway)
    response = evaluate_snapshot(opts(tmp_path, evaluate_soul=str(snapshot)))
    assert response["evaluation"]["accepted"]
    assert response["soul_version"] == 1
    assert response["evaluation"]["requests"] == 8
    assert response["evaluation"]["candidate_score"] > response["evaluation"]["baseline_score"]
    adopted = EvolutionSoul.restore("a", str(snapshot))
    assert not adopted.pending and len(adopted.notes) == 1
    assert adopted.sha256 == response["soul_hash"]


def test_evaluation_failure_never_adopts_candidate(tmp_path, monkeypatch):
    import surlife.evaluation as evaluation_module
    snapshot = _staged_soul(tmp_path)
    class Broken:
        def __init__(self, max_requests):
            self.calls = 0
            self.model = "fake/broken"
        def ask(self, messages):
            self.calls += 1
            raise GatewayError("test fail", "invalid_json")
    monkeypatch.setattr(evaluation_module, "FakeGateway", Broken)
    result = evaluate_snapshot(opts(tmp_path, evaluate_soul=str(snapshot)))
    assert result["evaluation"]["failures"]
    assert not result["evaluation"]["accepted"]
    assert EvolutionSoul.restore("a", str(snapshot)).version == 0


def test_inherit_m11_snapshot_with_pending_proposal(tmp_path):
    first = run_m11(opts(tmp_path), tmp_path / "world.sqlite")
    assert first["pending_revisions"] == 1
    prior = str(tmp_path / "souls" / "m11-1" / "a.json")
    next_result = run_m11(
        opts(tmp_path, run_id="descendant", ticks=3, inherit_soul_a=prior),
        tmp_path / "world.sqlite",
    )
    assert next_result["verified"]
    assert next_result["pending_revisions"] == 1
    assert next_result["soul_versions"]["a"] == 0


def test_m11_provider_requires_key_before_any_run(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        run_m11(opts(tmp_path, provider="openrouter"), tmp_path / "world.sqlite")
    assert not (tmp_path / "world.sqlite").exists()
