"""M1.6–M1.7: cognition learning, audit replay, holdout isolation, budgets."""
import copy
import json
from argparse import Namespace

import pytest

from surlife.core import Observation, Task
from surlife.m16 import (AdaptivePolicy, build_report, initial_state, run_m16,
                         validate_state, verify_adaptive_report, verify_m16_file)
from surlife.m17 import (aggregate_training, build_m17, verify_m17,
                         verify_m17_file, run_m17)


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
    assert done["manifest"]["experiment"] == "m16-v1"
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
    with pytest.raises(ValueError, match="24"):
        build_m17(opts(tmp_path, provider="google", max_requests=8), [a])


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
    if policy_path.exists():
        snapshot = json.loads(policy_path.read_text())
        assert snapshot["version"] == "m16-v1"
        assert snapshot["state"] == result["policy"]
    with pytest.raises(ValueError, match="exists"):
        run_m17(args)
