"""M1.3 contract tests; no network, credentials, or paid models."""
import json
from argparse import Namespace

import pytest

from surlife.action_menu import legal_masks, menu_messages
from surlife.core import Arena
from surlife.evaluation_v2 import evaluate_snapshot_v2
from surlife.gateway import OpenRouterGateway, FakeGateway, Reply
from surlife.m11 import EvolutionSoul, run_m11
from surlife.souls import Soul
from surlife.storage import Journal


def opts(tmp_path, **changes):
    defaults = dict(
        m13=True, a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, ticks=12, max_requests=8, max_output_tokens=512,
        reasoning="off", cognition="selective", action_contract="menu",
        run_id="m13-1", souls_dir=str(tmp_path / "souls"),
        soul_a=None, inherit_soul_a=None,
        evaluate_soul=None, evaluation_seed=3003, evaluation_tasks=2,
        evaluation_cohorts=2, max_evaluation_requests=8, eval_min_gain=2,
    )
    defaults.update(changes)
    return Namespace(**defaults)


def staged(tmp_path, contract="menu"):
    soul = EvolutionSoul(**Soul.new("a").__dict__, action_contract=contract)
    obs = Arena(17).observations()["a"]
    soul.observe_result(obs, 31, -1, obs.task.optimum, 0, 20, "llm_action")
    assert soul.stage("Enumerate legal combinations and choose the largest possible reward.", 0)
    root = tmp_path / "snapshot"
    soul.save(root)
    return root / "a.json"


def test_menu_exposes_feasibility_not_oracle_rewards():
    obs = Arena(17).observations()["a"]
    original = Soul.new("a").messages(obs)
    outgoing, allowed = menu_messages(original, obs)
    assert allowed == legal_masks(obs.task) == sorted(set(allowed))
    assert all(obs.task.score(mask) >= 0 for mask in allowed)
    assert all(obs.task.score(mask) < 0 for mask in range(32) if mask not in allowed)
    data = json.loads(outgoing[-1]["content"])
    assert json.loads(original[-1]["content"]).get("allowed_masks") is None
    assert "optimum" not in data and "optimal_mask" not in data
    assert [x["mask"] for x in data["allowed_masks"]] == allowed
    assert all(set(x) == {"mask", "selected_cost"} for x in data["allowed_masks"])


def test_openrouter_menu_schema_and_key_isolation(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_PRIVATE")
    obs = Arena(17).observations()["a"]
    outgoing, allowed = menu_messages(Soul.new("a").messages(obs), obs)
    sent = []
    def fake(payload, key, timeout):
        assert key == "DUMMY_PRIVATE"
        sent.append(payload)
        return {"model": "dots-studio/dots-3-note-preview:free",
                "choices": [{"message": {"content": json.dumps({
                    "mask": allowed[0], "soul_update": "",
                })}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
    gateway = OpenRouterGateway(transport=fake, max_requests=1)
    assert gateway.ask(outgoing, allowed_masks=allowed).mask == allowed[0]
    schema = sent[0]["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["mask"] == {"type": "integer", "enum": allowed}
    assert schema["properties"]["soul_update"] == {"type": "string", "enum": [""]}
    assert sent[0]["provider"]["require_parameters"] is True
    assert "DUMMY_PRIVATE" not in json.dumps(sent[0])


def test_invalid_menu_fails_before_debit(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_PRIVATE")
    gateway = OpenRouterGateway(transport=lambda *_: {}, max_requests=1)
    for allowed in ([2, 1], [0, 0], [True], [256], [], [0, "1"]):
        with pytest.raises(ValueError, match="legal-action menu"):
            gateway.ask([{"role": "user", "content": "{}"}], allowed_masks=allowed)
    with pytest.raises(ValueError, match="only valid for action"):
        gateway.ask([{"role": "user", "content": "{}"}], mode="reflection", allowed_masks=[0])
    assert gateway.calls == 0


def test_offline_menu_lifecycle_replays_and_records_contract(tmp_path):
    result = run_m11(opts(tmp_path), tmp_path / "world.sqlite")
    assert result["verified"] and result["kind"] == "m13-admissible-actions"
    assert result["action_contract"] == "menu"
    assert result["action_contract_stats"]["menu_actions"] > 0
    assert result["action_contract_stats"]["menu_violations"] == 0
    assert result["provider_requests"] == result["consultations"]["a"]
    assert EvolutionSoul.restore("a", str(tmp_path / "souls" / "m13-1" / "a.json")).action_contract == "menu"
    with Journal(tmp_path / "world.sqlite") as journal:
        assert journal.replay("m13-1")["verified"]


def test_model_ignoring_menu_is_not_silently_repaired(tmp_path, monkeypatch):
    import surlife.m11 as module
    class Wrong(FakeGateway):
        def ask(self, messages, *, mode="action", allowed_masks=None):
            assert self.remaining
            self.calls += 1
            if mode == "reflection":
                return Reply(None, "Check total cost before choosing an action.",
                             "fake/wrong", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            assert allowed_masks is not None and 31 not in allowed_masks
            return Reply(31, "", "fake/wrong", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    monkeypatch.setattr(module, "FakeGateway", Wrong)
    r = run_m11(opts(tmp_path, ticks=5, cognition="always"), tmp_path / "invalid.sqlite")
    assert r["verified"]
    assert r["action_contract_stats"]["menu_violations"] > 0
    assert r["by_action_source"]["llm_action"]["invalid"] > 0
    with Journal(tmp_path / "invalid.sqlite") as journal:
        rows = [json.loads(v) for (v,) in journal.db.execute(
            "SELECT payload FROM rounds WHERE run_id=?", ("m13-1",)
        )]
    illegal = [r for r in rows if r["model_calls"].get("a", {}).get("contract_violation")]
    assert illegal
    assert all(r["actions"]["a"] == 31 and r["scores"]["a"] == -1 and
               r["consultations"]["a"] == 1 for r in illegal)


def test_raw_control_and_no_inference_modes(tmp_path):
    r = run_m11(opts(tmp_path, action_contract="raw"), tmp_path / "raw.sqlite")
    assert r["action_contract"] == "raw"
    assert r["action_contract_stats"]["menu_actions"] == 0
    r2 = run_m11(opts(tmp_path, run_id="cheap", cognition="never"), tmp_path / "cheap.sqlite")
    assert r2["model_requests"] == 0
    assert r2["action_contract_stats"]["menu_actions"] == 0


def test_paired_menu_holdout_rejects_equal_fake_prompts(tmp_path):
    snap = staged(tmp_path)
    r = evaluate_snapshot_v2(opts(tmp_path, evaluate_soul=str(snap)))
    e = r["evaluation"]
    assert e["protocol"] == "m13-admissible-menu-holdout-v1"
    assert e["action_contract"] == "menu"
    assert e["requests"] == 8 and e["decision"] == "rejected"
    assert e["paired_ties"] == 4
    assert all(
        p["baseline"]["contract_violation"] is False and
        p["candidate"]["contract_violation"] is False
        for cohort in e["pair_results"] for p in cohort
    )


def test_inheritance_and_evaluation_cannot_switch_contract(tmp_path):
    snap = staged(tmp_path, contract="raw")
    with pytest.raises(ValueError, match="different action contract"):
        evaluate_snapshot_v2(opts(tmp_path, evaluate_soul=str(snap)))
    with pytest.raises(ValueError, match="action contract differs"):
        run_m11(opts(tmp_path, inherit_soul_a=str(snap)), tmp_path / "never.sqlite")
    assert not (tmp_path / "never.sqlite").exists()


def test_inherited_menu_lineage_retains_protocol(tmp_path):
    run_m11(opts(tmp_path), tmp_path / "world.sqlite")
    inherited = tmp_path / "souls" / "m13-1" / "a.json"
    r = run_m11(opts(tmp_path, run_id="child", inherit_soul_a=str(inherited),
                       ticks=4), tmp_path / "world.sqlite")
    assert r["verified"] and r["action_contract"] == "menu"
