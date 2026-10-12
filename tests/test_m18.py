"""M1.8 response-bank fairness, replay and provider-budget tests."""
from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest

from surlife.gateway import GatewayError, Reply
from surlife.m18 import _assemble, _digest, run_m18, verify_m18, verify_m18_file


def opts(tmp_path, **changes):
    values = dict(
        a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, benchmark_cases=4, benchmark_items=12,
        benchmark_profile="mixed", max_requests=4,
        max_output_tokens=512, reasoning="off",
        google_timeout_seconds=45, m18_virtual_cap=4,
        m18_bank_in=None, policy_in=None,
        benchmark_out=str(tmp_path / "m18.json"),
    )
    values.update(changes)
    return Namespace(**values)


def test_fake_bank_same_actions_with_zero_extraneous_calls(tmp_path):
    args = opts(tmp_path)
    done = run_m18(args)
    assert done["verified"]
    assert done["summary"]["bank_sampling"]["provider_requests"] == 4
    assert done["summary"]["bank_sampling"]["successful_responses"] == 4
    assert verify_m18_file(args.benchmark_out)["verified"]
    report = json.loads((tmp_path / "m18.json").read_text())
    assert {r["status"] for r in report["bank"]} == {"ok"}
    stats = done["summary"]["arms"]
    assert stats["never"]["energy"] == stats["greedy"]["energy"]
    assert stats["always"]["consultations"] == 4
    assert stats["always"]["energy"] == stats["greedy"]["energy"] - 4
    assert stats["adaptive_fresh"]["model_actions"] <= 4
    assert stats["dp"]["task_score_sum"] == stats["oracle"]["task_score_sum"]
    assert done["summary"]["comparison"]["always"]["energy_delta_vs_greedy"] == -4
    for name in ("always", "selective", "adaptive_fresh"):
        for tick, record in enumerate(report["arms"][name]):
            if record["consultations"]["a"]:
                assert record["actions"]["a"] == report["bank"][tick]["mask"]


def test_offline_bank_reuse_never_reconnects_and_changes_virtual_budget(tmp_path, monkeypatch):
    import surlife.m18 as m18
    original = run_m18(opts(tmp_path))
    monkeypatch.setattr(m18, "_gateway", lambda *_: (_ for _ in ()).throw(
        AssertionError("bank reuse must be fully offline")))
    reused = run_m18(opts(
        tmp_path, benchmark_out=str(tmp_path / "replayed.json"),
        m18_bank_in=original["report_path"], m18_virtual_cap=1,
    ))
    assert reused["verified"]
    assert reused["summary"]["bank_sampling"]["provider_requests"] == 4
    assert reused["summary"]["bank_sampling"]["sampling_mode"] == "reused"
    assert reused["summary"]["arms"]["always"]["consultations"] == 1
    assert reused["summary"]["arms"]["never"]["consultations"] == 0
    assert verify_m18_file(reused["report_path"])["verified"]


def test_tamper_bank_or_charges_fails_independent_replay(tmp_path):
    result = run_m18(opts(tmp_path))
    report = json.loads((tmp_path / "m18.json").read_text())
    wrong = copy.deepcopy(report)
    wrong["arms"]["always"][0]["consultations"]["a"] = 0
    with pytest.raises(ValueError, match="replay"):
        verify_m18(wrong)
    wrong = copy.deepcopy(report)
    wrong["bank"][0]["mask"] = 1 << 12
    with pytest.raises(ValueError, match="sampled"):
        verify_m18(wrong)
    wrong = copy.deepcopy(report)
    wrong["bank"][0]["mask"] = 0
    # Recomputing a superficial content digest cannot evade referee replay.
    wrong["head"] = _digest(wrong["manifest"], wrong["bank"],
                            wrong["arms"], wrong["summary"])
    with pytest.raises(ValueError, match="replay"):
        verify_m18(wrong)
    wrong = copy.deepcopy(report)
    wrong["arms"]["adaptive_fresh"][0]["benchmark"]["policy_after"]["uncertain"]["gain"] += 1
    with pytest.raises(ValueError, match="replay"):
        verify_m18(wrong)
    wrong = copy.deepcopy(report)
    wrong["summary"]["bank_sampling"]["provider_requests"] = 999
    with pytest.raises(ValueError, match="replay"):
        verify_m18(wrong)


def test_missing_bank_or_invalid_budget_preflight(tmp_path):
    for kw, pattern in [
        ({"benchmark_cases": 5, "max_requests": 4}, "max-requests"),
        ({"m18_virtual_cap": 5}, "virtual cap"),
        ({"m18_virtual_cap": -1}, "virtual cap"),
        ({"benchmark_out": None}, "benchmark-out"),
        ({"a": "greedy"}, "requires --a llm"),
    ]:
        with pytest.raises(ValueError, match=pattern):
            run_m18(opts(tmp_path, **kw))
    first = run_m18(opts(tmp_path))
    with pytest.raises(ValueError, match="exists"):
        run_m18(opts(tmp_path))
    with pytest.raises(ValueError, match="task/model/generation mismatch"):
        run_m18(opts(tmp_path,
            benchmark_out=str(tmp_path / "other.json"),
            m18_bank_in=first["report_path"], seed=19))


def test_429_stops_bank_sampling_and_arms_do_not_charge_unavailable(tmp_path, monkeypatch):
    import surlife.m14 as m14

    class Failure:
        model = "surlife/fake-model"
        limit = 4
        calls = 0

        @property
        def remaining(self):
            return self.limit - self.calls

        def ask(self, *args, **kwargs):
            self.calls += 1
            raise GatewayError("rate limited", "http_429")

    monkeypatch.setattr(m14, "FakeGateway", lambda **kw: Failure())
    done = run_m18(opts(tmp_path))
    report = json.loads((tmp_path / "m18.json").read_text())
    assert [e["status"] for e in report["bank"]] == [
        "failed", "unavailable", "unavailable", "unavailable"]
    assert done["summary"]["bank_sampling"]["provider_requests"] == 1
    assert done["summary"]["bank_sampling"]["not_requested"] == 3
    assert done["summary"]["arms"]["always"]["consultations"] == 1
    assert done["summary"]["arms"]["always"]["provider_failures"] == 1
    assert done["summary"]["arms"]["adaptive_fresh"]["consultations"] == 1
    policy = report["arms"]["adaptive_fresh"][0]["benchmark"]
    assert policy["feedback_kind"] == "provider_failure"
    assert all(v["trials"] == 0 for v in policy["policy_after"].values())
    assert verify_m18(report)["verified"]


def test_inherit_promoted_state_and_limit_model_scope(tmp_path):
    from surlife.m16 import POLICY_VERSION
    state = {
        "uncertain": {"visits": 5, "trials": 1, "gain": 2},
        "routine": {"visits": 3, "trials": 1, "gain": -1},
    }
    snapshot = {
        "version": POLICY_VERSION, "state": state,
        "training_heads": ["a" * 64], "gate_report_head": "b" * 64,
        "evaluation_protocol": "m17-v2", "provider": "fake",
        "model": "surlife/fake-model",
        "generation": {"reasoning": "off", "max_output_tokens": 512},
    }
    source = tmp_path / "accepted.json"
    source.write_text(json.dumps(snapshot))
    report = run_m18(opts(tmp_path, policy_in=str(source)))
    assert report["verified"]
    manifest = json.loads((tmp_path / "m18.json").read_text())["manifest"]
    assert manifest["inherit_policy"]
    assert manifest["policy_initial"] == state
    stats = report["summary"]["arms"]
    assert "adaptive_inherited" in stats
    with pytest.raises(ValueError, match="mismatch"):
        run_m18(opts(tmp_path, benchmark_out=str(tmp_path / "other.json"),
                     policy_in=str(source), max_output_tokens=256))


def test_reused_real_bank_never_uses_api_credentials(tmp_path, monkeypatch):
    import surlife.m18 as m18
    args = opts(tmp_path)
    base = run_m18(args)
    # Simulate a bank from a live provider by updating its provenance and
    # reproducing every arm/referee transition; no actual requests are made.
    data = json.loads((tmp_path / "m18.json").read_text())
    data["manifest"]["provider"] = "google"
    data["manifest"]["requested_model"] = "gemini-3.8-flash"
    data["manifest"]["generation"]["max_output_tokens"] = 4096
    for row in data["bank"]:
        row["model"] = "gemini-3.8-flash"
    bank = _assemble(data["manifest"], data["bank"])
    path = tmp_path / "reference-google.json"
    path.write_text(json.dumps(bank))
    monkeypatch.setattr(m18, "_gateway", lambda *_: (_ for _ in ()).throw(
        AssertionError("network gateway should not initialize")))
    reused = run_m18(opts(
        tmp_path, benchmark_out=str(tmp_path / "google-reuse.json"),
        m18_bank_in=str(path), provider="google",
        model="gemini-3.8-flash", max_output_tokens=4096,
    ))
    assert reused["verified"]
    assert reused["summary"]["bank_sampling"]["provider_requests"] == 4
