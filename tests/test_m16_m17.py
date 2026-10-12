"""M1.6–M1.7: cognition learning, audit replay, holdout isolation, budgets."""
import copy
import json
from argparse import Namespace

import pytest

from surlife.core import Observation, Task
from surlife.m16 import (AdaptivePolicy, build_report, initial_state, run_m16,
                         validate_state, verify_adaptive_report, verify_m16_file)
from surlife.m17 import (aggregate_training, build_m17, verify_m17,
                         verify_m17_file, run_m17, _scoring, _legacy_scoring, _head)


def opts(tmp_path, **changes):
    values = dict(
        a="llm", b="greedy", provider="fake", model="surlife/fake-model",
        max_requests=4, max_output_tokens=512, reasoning="off",
        seed=17, benchmark_cases=12, benchmark_items=12,
        benchmark_profile="mixed", benchmark_out=str(tmp_path / "m16.json"),
        holdout_seeds="101,103", train_report=[],
        promote_policy_out=str(tmp_path / "promoted.json"),
    )
    values.update(changes)
    return Namespace(**values)


def test_adaptive_fake_learning_and_full_offline_replay(tmp_path):
    args = opts(tmp_path)
    done = run_m16(args)
    assert done["verified"]
    assert done["manifest"]["experiment"] == "m16-v2"
    assert done["summary"]["arms"]["llm"]["consultations"] <= args.max_requests
    assert done["summary"]["arms"]["llm"]["provider_failures"] == 0
    assert verify_m16_file(args.benchmark_out)["policy_final"] == done["policy_final"]
    report = json.loads((tmp_path / "m16.json").read_text())
    assert report["arms"]["dp"][-1]["after"]["a"] == report["arms"]["oracle"][-1]["after"]["a"]
    charged = [r for r in report["arms"]["llm"] if r["consultations"]["a"]]
    assert charged
    for rec in charged:
        assert isinstance(rec["benchmark"]["net_energy_vs_greedy"], int)
        assert rec["benchmark"]["policy_decision"]["consult"]
        assert rec["benchmark"]["feedback_kind"] == "model_success"


def test_adaptive_state_evolves_on_result_but_no_generated_program():
    p = AdaptivePolicy()
    obs = Observation(0, "normal", Task(((1, 6), (12, 60),
                                        (2, 4), (3, 8)), 12), 30)
    choice = p.choose(obs, available=3, affordable=True)
    assert choice["consult"]
    before = p.snapshot()
    assert before[choice["bucket"]]["trials"] == 0
    p.learn(choice["bucket"], -1)
    after = p.snapshot()
    assert after[choice["bucket"]]["trials"] == 1
    assert after[choice["bucket"]]["gain"] == -1
    with pytest.raises(ValueError):
        validate_state({**initial_state(), "extra": {"program": "exec('x')"}})
    with pytest.raises(ValueError):
        p.learn(choice["bucket"], 999)


def test_budget_and_low_energy_do_not_trigger_query(tmp_path):
    args = opts(tmp_path, max_requests=1)
    report = build_report(args)
    assert report["summary"]["arms"]["llm"]["consultations"] <= 1
    assert verify_adaptive_report(report)["verified"]
    p = AdaptivePolicy()
    obs = Observation(0, "drought", Task(((1, 6), (12, 60)), 12), 5)
    assert not p.choose(obs, available=1, affordable=True)["consult"]


def test_policy_audit_rejects_modified_choice_and_feedback(tmp_path):
    report = build_report(opts(tmp_path))
    changed = copy.deepcopy(report)
    row = next(x for x in changed["arms"]["llm"] if x["benchmark"].get("policy_decision"))
    row["benchmark"]["policy_decision"]["bucket"] = "forged"
    with pytest.raises(ValueError):
        verify_adaptive_report(changed)
    changed = copy.deepcopy(report)
    row = next(x for x in changed["arms"]["llm"] if x["consultations"]["a"])
    row["benchmark"]["net_energy_vs_greedy"] += 1
    # Even a recomputed digest cannot pass the independent policy replay.
    from surlife.m14 import _digest
    changed["head"] = _digest(changed["manifest"], changed["arms"], changed["summary"])
    with pytest.raises(ValueError, match="feedback"):
        verify_adaptive_report(changed)


def test_m17_matched_offline_cohorts_and_training_lineage(tmp_path):
    training = [build_report(opts(tmp_path, seed=17)),
                build_report(opts(tmp_path, seed=19))]
    args = opts(tmp_path, benchmark_out=str(tmp_path / "m17.json"))
    result = build_m17(args, training)
    verified = verify_m17(result)
    assert verified["verified"]
    assert len(result["episodes"]) == 2
    assert result["protocol"] == "m17-v2"
    assert result["identity"]["provider"] == "fake"
    assert not result["summary"]["accepted"]
    assert "no_positive_gain_vs_greedy" in result["summary"]["rejection_reasons"]
    assert result["policy"] == aggregate_training(training)
    for ep in result["episodes"]:
        assert ep["fresh"]["manifest"]["seed"] == ep["inherited"]["manifest"]["seed"]
        assert ep["fresh"]["manifest"]["policy_initial"] == initial_state()
        assert ep["inherited"]["manifest"]["policy_initial"] == result["policy"]
        assert ep["fresh"]["summary"]["arms"]["llm"]["consultations"] <= 4
        assert ep["inherited"]["summary"]["arms"]["llm"]["consultations"] <= 4
    changed = copy.deepcopy(result)
    changed["policy"]["uncertain"]["gain"] += 1
    with pytest.raises(ValueError):
        verify_m17(changed)


def test_m17_rejects_training_overlap_before_inference(tmp_path, monkeypatch):
    a = build_report(opts(tmp_path, seed=17))
    with pytest.raises(ValueError, match="duplicate"):
        build_m17(opts(tmp_path), [a, copy.deepcopy(a)])
    with pytest.raises(ValueError, match="overlap"):
        build_m17(opts(tmp_path, holdout_seeds="17,103"), [a])
    with pytest.raises(ValueError, match="provider/model/config"):
        build_m17(opts(tmp_path, provider="google", max_requests=4), [a])
    # A live evaluation with matched training would additionally be bounded
    # by 2 * cohorts * per-arm requests <= 24.


def test_m17_file_and_gated_snapshot(tmp_path):
    args = opts(tmp_path, benchmark_out=str(tmp_path / "m17.json"),
                train_report=[str(tmp_path / "train.json")])
    training = build_report(opts(tmp_path))
    (tmp_path / "train.json").write_text(json.dumps(training))
    result = run_m17(args)
    assert result["verified"]
    assert verify_m17_file(args.benchmark_out)["verified"]
    policy_path = tmp_path / "promoted.json"
    assert policy_path.exists() == result["policy_promoted"]
    assert not result["summary"]["accepted"]
    assert not policy_path.exists()
    assert "no_positive_gain_vs_greedy" in result["summary"]["rejection_reasons"]
    with pytest.raises(ValueError, match="exists"):
        run_m17(args)


def test_promoted_snapshot_is_data_only_and_model_scoped(tmp_path):
    from surlife.m16 import load_promoted_policy
    training = build_report(opts(tmp_path, seed=17))
    state = aggregate_training([training])
    snapshot = {
        "version": "m16-v2", "state": state,
        "training_heads": [training["head"]],
        "gate_report_head": "a" * 64,
        "evaluation_protocol": "m17-v2",
        "provider": "fake", "model": "surlife/fake-model",
        "generation": {"reasoning": "off", "max_output_tokens": 512},
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(snapshot))
    restored, identity = load_promoted_policy(str(path))
    assert restored == state
    assert identity["provider"] == "fake"
    inherited = run_m16(opts(tmp_path, policy_in=str(path)))
    assert inherited["manifest"]["policy_initial"] == state
    with pytest.raises(ValueError, match="provider/model/config mismatch"):
        run_m16(opts(tmp_path, policy_in=str(path), provider="google",
                     model="gemini-3.8-flash", max_output_tokens=4096,
                     benchmark_out=str(tmp_path / "not_written.json")))
    snapshot["state"]["routine"]["visits"] = -1
    path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):
        load_promoted_policy(str(path))


def test_m16_failure_is_accounted_but_does_not_train(tmp_path, monkeypatch):
    import surlife.m14 as m14
    from surlife.gateway import GatewayError

    class BrokenProvider:
        model = "surlife/fake-model"

        def __init__(self, max_requests):
            self.limit = max_requests
            self.calls = 0

        @property
        def remaining(self):
            return max(0, self.limit - self.calls)

        def ask(self, *_args, **_kwargs):
            self.calls += 1
            raise GatewayError("service unavailable", "http_429")

    monkeypatch.setattr(m14, "FakeGateway", BrokenProvider)
    report = build_report(opts(tmp_path))
    assert verify_adaptive_report(report)["verified"]
    row = next(r for r in report["arms"]["llm"] if r["consultations"]["a"])
    assert row["benchmark"]["feedback_kind"] == "provider_failure"
    assert row["benchmark"]["net_energy_vs_greedy"] == -1
    assert all(stats["trials"] == 0 for stats in
               verify_adaptive_report(report)["policy_final"].values())
    assert report["summary"]["arms"]["llm"]["provider_failures"] == 1
    with pytest.raises(ValueError, match="provider failures in training"):
        aggregate_training([report])


def test_m16_legacy_report_still_replays(tmp_path):
    from surlife.m14 import _digest
    original = build_report(opts(tmp_path))
    old = copy.deepcopy(original)
    old["manifest"]["experiment"] = "m16-v1"
    old["manifest"].pop("generation")
    for r in old["arms"]["llm"]:
        r["benchmark"].pop("feedback_kind", None)
    old["head"] = _digest(old["manifest"], old["arms"], old["summary"])
    assert verify_adaptive_report(old)["verified"]
    with pytest.raises(ValueError, match="m16-v2 training"):
        aggregate_training([old])


def test_training_rejects_mixed_model_generation_before_live_calls(tmp_path):
    a = build_report(opts(tmp_path, seed=17))
    b = build_report(opts(tmp_path, seed=19, reasoning="low"))
    with pytest.raises(ValueError, match="mixed training providers"):
        aggregate_training([a, b])
    bad = copy.deepcopy(a)
    bad["manifest"]["generation"]["reasoning"] = "auto"
    from surlife.m14 import _digest
    bad["head"] = _digest(bad["manifest"], bad["arms"], bad["summary"])
    with pytest.raises(ValueError, match="provider/model/config"):
        build_m17(opts(tmp_path), [bad])


def test_dual_control_scoring_rejects_saving_energy_alone():
    def arm(energy, *, consultations, failures=0, invalid=0):
        return {
            "energy": energy, "task_score_sum": 100,
            "consultations": consultations, "provider_failures": failures,
            "invalid": invalid,
        }

    def pair(seed, fresh, inherited, greedy, *, failures=0, invalid=0):
        control = arm(greedy, consultations=0)
        return {"seed": seed,
                "fresh": {"summary": {"arms": {
                    "llm": arm(fresh, consultations=4, failures=failures),
                    "greedy": control}}},
                "inherited": {"summary": {"arms": {
                    "llm": arm(inherited, consultations=2, invalid=invalid),
                    "greedy": dict(control)}}}}

    fake = _scoring([pair(101, 27, 29, 31), pair(103, 27, 29, 31)])
    assert not fake["accepted"]
    assert fake["wins"] == 2
    assert "no_positive_gain_vs_greedy" in fake["rejection_reasons"]
    success = _scoring([pair(101, 34, 37, 31),
                        pair(103, 34, 36, 31)])
    assert success["accepted"]
    assert success["total_energy_gain"] == 5
    assert success["total_energy_gain_vs_greedy"] == 11
    degraded = _scoring([pair(101, 34, 37, 31),
                         pair(103, 34, 30, 31)])
    assert not degraded["accepted"]
    assert "regression_vs_greedy" in degraded["rejection_reasons"]
    flaky = _scoring([pair(101, 34, 37, 31, failures=1),
                      pair(103, 34, 36, 31)])
    assert not flaky["accepted"]
    assert "provider_failures" in flaky["rejection_reasons"]
    illegal = _scoring([pair(101, 34, 37, 31, invalid=1),
                        pair(103, 34, 36, 31)])
    assert "legality_regression" in illegal["rejection_reasons"]


def test_legacy_m17_scoring_audit_is_preserved(tmp_path):
    from surlife.m14 import _digest
    reports = []
    for seed in (17, 19):
        old = copy.deepcopy(build_report(opts(tmp_path, seed=seed)))
        old["manifest"]["experiment"] = "m16-v1"
        old["manifest"].pop("generation")
        for row in old["arms"]["llm"]:
            row["benchmark"].pop("feedback_kind", None)
        old["head"] = _digest(old["manifest"], old["arms"], old["summary"])
        reports.append(old)
    # Reconstruct old protocol report from the same deterministic fake arms.
    result = build_m17(opts(tmp_path), [
        build_report(opts(tmp_path, seed=17)),
        build_report(opts(tmp_path, seed=19)),
    ])
    old = copy.deepcopy(result)
    old["protocol"] = "m17-v1"
    old.pop("identity")
    old["training"] = reports
    old["policy"] = aggregate_training(reports, legacy=True)
    for ep in old["episodes"]:
        for role in ("fresh", "inherited"):
            ref = ep[role]
            ref["manifest"]["experiment"] = "m16-v1"
            ref["manifest"].pop("generation")
            for row in ref["arms"]["llm"]:
                row["benchmark"].pop("feedback_kind", None)
            ref["head"] = _digest(ref["manifest"], ref["arms"], ref["summary"])
    old["summary"] = _legacy_scoring(old["episodes"])
    old["head"] = _head(old)
    assert verify_m17(old)["verified"]
