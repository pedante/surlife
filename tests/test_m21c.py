"""M2.1-C provider-ready paired prompt trials: all tests offline."""
import argparse
import copy
import json

import pytest

from surlife.core import Observation, Task, greedy, optimal
from surlife.gateway import GatewayError, OpenRouterGateway, Reply
from surlife.m21c import (
    FIXTURE_MODEL, FixtureGateway, MARKER, build_report, verify_file,
    verify_report, run_m21c,
)


def test_fixture_promotes_only_paired_model_gain_and_charges_every_call():
    report = build_report(17, 24)
    assert verify_report(report)["verified"]
    ep = report["episodes"]["primary"]
    organism = ep["organisms"]["a"]
    events = organism["revision_events"]
    assert [event["decision"] for event in events] == ["staged", "activated"]
    assert organism["soul_version"] == 1
    assert ep["organisms"]["b"]["soul_version"] == 0
    assert events[-1]["paid_trial_requests"] == 4
    assert events[-1]["candidate_hash"] == organism["soul_hash"]
    bank = report["bank"]
    kinds = [entry["kind"] for entry in bank]
    assert kinds[:5] == ["reflection", "baseline", "candidate",
                         "baseline", "candidate"]
    assert len(bank) <= report["manifest"]["max_requests"]
    charged = sum(sum(row["consultations"].values()) for row in ep["ticks"])
    assert charged == len(bank)
    assert report["summary"]["external_request_attempts"] == 0
    assert report["summary"]["reported_tokens"]["total_tokens"] == 0
    assert report["summary"]["promotion_is_economic_proof"] is False


def test_disjoint_identical_task_for_each_paired_comparison():
    report = build_report(17, 24, "evolving", "evolving", 12)
    live = {entry["task_hash"] for entry in report["bank"]
            if entry["kind"] == "work"}
    from surlife.m21c import digest
    live |= {digest(row["task"]) for row in report["episodes"]["primary"]["ticks"]}
    holdouts = []
    # Different organisms may interleave baseline requests. Pair within actor.
    unfinished = {}
    for entry in report["bank"]:
        if entry["kind"] == "baseline":
            assert entry["actor"] not in unfinished
            unfinished[entry["actor"]] = entry["task_hash"]
            assert entry["task_hash"] not in live
            holdouts.append(entry["task_hash"])
        elif entry["kind"] == "candidate":
            assert unfinished.pop(entry["actor"]) == entry["task_hash"]
    assert not unfinished
    assert len(holdouts) == len(set(holdouts))
    assert verify_report(report)["verified"]


def test_entire_replay_never_needs_gateway_and_detects_forgery():
    original = build_report(17, 24)
    altered = copy.deepcopy(original)
    altered["bank"][0]["response"]["note"] = "FORGED"
    with pytest.raises(ValueError, match="mismatch|unused"):
        verify_report(altered)
    altered = copy.deepcopy(original)
    altered["bank"][0]["messages_hash"] = "wrong"
    with pytest.raises(ValueError, match="bank context"):
        verify_report(altered)
    altered = copy.deepcopy(original)
    altered["episodes"]["primary"]["ticks"][3]["after"]["a"] += 5
    with pytest.raises(ValueError, match="mismatch"):
        verify_report(altered)
    altered = copy.deepcopy(original)
    altered["bank"].append(copy.deepcopy(altered["bank"][-1]))
    with pytest.raises(ValueError, match="unused|exhausted|mismatch"):
        verify_report(altered)


def test_report_file_verify_only(tmp_path):
    output = tmp_path / "bank.json"
    output.write_text(json.dumps(build_report(29, 20)), encoding="utf-8")
    assert verify_file(str(output))["verified"]
    output.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        verify_file(str(output))


class NonImproving:
    def ask(self, messages, *, mode):
        if mode == "reflection":
            return Reply(None, "Please review task costs carefully.", FIXTURE_MODEL,
                         {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5})
        task = json.loads(messages[-1]["content"])["task"]
        data = Task(tuple(tuple(item) for item in task["items"]), task["capacity"])
        observation = Observation(0, "normal", data, 30)
        mask = greedy(observation, None).mask
        return Reply(mask, "", FIXTURE_MODEL,
                     {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5})


def test_real_usage_shape_on_mock_and_rejected_candidate():
    result = build_report(17, 24, gateway=NonImproving())
    assert result["episodes"]["primary"]["organisms"]["a"]["soul_version"] == 0
    assert [e["decision"] for e in result["episodes"]["primary"]["organisms"]["a"]["revision_events"]] == [
        "staged", "rejected"]
    assert result["summary"]["reported_tokens"]["total_tokens"] == 25
    assert verify_report(result)["verified"]


class FailsDuringCandidate:
    def __init__(self):
        self.calls = 0

    def ask(self, messages, *, mode):
        self.calls += 1
        if self.calls == 3:
            error = GatewayError("provider interruption", "completion_truncated")
            error.usage = {"prompt_tokens": 13, "completion_tokens": 5, "total_tokens": 18}
            raise error
        return FixtureGateway().ask(messages, mode=mode)


def test_gateway_failures_debit_energy_and_block_promotion():
    gateway = FailsDuringCandidate()
    result = build_report(17, 24, gateway=gateway)
    assert gateway.calls == 3
    assert result["summary"]["primary_requests"] == 3
    assert result["summary"]["failed_or_aborted"] is True
    assert result["summary"]["failure_reason"] == "completion_truncated"
    assert result["episodes"]["primary"]["organisms"]["a"]["soul_version"] == 0
    assert sum(sum(row["consultations"].values()) for row in
               result["episodes"]["primary"]["ticks"]) == 3
    assert verify_report(result)["verified"]


class UnknownUsage:
    def ask(self, messages, *, mode):
        return Reply(None, "", FIXTURE_MODEL, {"prompt_tokens": None,
                                               "completion_tokens": None,
                                               "total_tokens": None})


def test_unknown_token_usage_aborts_fail_closed():
    result = build_report(17, 24, gateway=UnknownUsage())
    assert result["summary"]["unknown_usage_requests"] == 1
    assert result["summary"]["primary_requests"] == 1
    assert result["summary"]["failure_reason"] == "unknown_usage"
    assert result["episodes"]["primary"]["organisms"]["a"]["soul_version"] == 0
    assert verify_report(result)["verified"]


class WrongModel:
    def ask(self, messages, *, mode):
        return Reply(None, "", "wrong/route", {k: 0 for k in (
            "prompt_tokens", "completion_tokens", "total_tokens"
        )})


def test_model_substitution_blocks_other_requests_and_mutation():
    result = build_report(17, 24, gateway=WrongModel())
    assert result["summary"]["failure_reason"] == "routed_model_mismatch"
    assert result["summary"]["primary_requests"] == 1
    assert verify_report(result)["verified"]


def test_real_gateway_mock_transport_and_schema(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-non-network-test")
    seen = []
    def transport(payload, key, timeout):
        assert key == "dummy-non-network-test"
        assert timeout == 30
        seen.append(payload["messages"])
        if payload["response_format"]["json_schema"]["name"] == "surlife_reflection":
            content = json.dumps({"soul_update":
                "Enumerate legal subsets and compare total reward before selecting a mask."})
        else:
            data = json.loads(payload["messages"][-1]["content"])
            d = data["task"]
            obs = Observation(0, "normal", Task(
                tuple(tuple(x) for x in d["items"]), d["capacity"]), 30)
            strategy = optimal if MARKER in payload["messages"][0]["content"] else greedy
            content = json.dumps({"mask": strategy(obs, None).mask, "soul_update": ""})
        return {"model": "test-model:free",
                "choices": [{"finish_reason": "stop", "message": {"content": content}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12}}
    gw = OpenRouterGateway(model="test-model:free", max_requests=8,
                           transport=transport)
    report = build_report(17, 24, provider="openrouter-free",
                          model="test-model:free", gateway=gw)
    assert gw.calls == len(report["bank"])
    assert report["summary"]["external_request_attempts"] == gw.calls
    assert report["summary"]["reported_tokens"]["total_tokens"] == gw.calls * 12
    assert report["episodes"]["primary"]["organisms"]["a"]["soul_version"] == 1
    assert len(seen) == gw.calls
    assert verify_report(report)["verified"]


@pytest.mark.parametrize("kwargs", [
    {"ticks": 1}, {"ticks": 65}, {"seed": -1}, {"max_requests": 0},
    {"max_requests": True}, {"max_requests": 13}, {"a": "unknown"},
    {"provider": "openrouter-free", "model": "not-free"},
    {"provider": "openrouter-free", "model": "openrouter/free"},
    {"provider": "openrouter-free", "model": "x:free", "max_requests": 9},
])
def test_input_validation(kwargs):
    data = {"seed": 17, "ticks": 20}
    data.update(kwargs)
    with pytest.raises(ValueError):
        build_report(**data)


def test_live_gateway_denied_without_explicit_both_approvals(tmp_path, monkeypatch):
    monkeypatch.delenv("SURLIFE_M21C_APPROVE_LIVE", raising=False)
    args = argparse.Namespace(
        benchmark_out=str(tmp_path / "live.json"), provider="openrouter",
        model="test-model:free", seed=17, ticks=20, m21_a="evolving",
        m21_b="frozen", max_requests=4, max_output_tokens=128,
        reasoning="off", m21c_confirm_live=False,
    )
    with pytest.raises(ValueError, match="real provider disabled"):
        run_m21c(args)
    assert not (tmp_path / "live.json").exists()


def test_fake_mode_from_runner_and_output_no_overwrite(tmp_path):
    args = argparse.Namespace(
        benchmark_out=str(tmp_path / "fixture.json"), provider="fake",
        model=None, seed=17, ticks=20, m21_a="evolving",
        m21_b="frozen", max_requests=8, max_output_tokens=128,
        reasoning="off", m21c_confirm_live=False,
    )
    result = run_m21c(args)
    assert result["verified"]
    assert verify_file(result["report_path"])["verified"]
    with pytest.raises(ValueError, match="overwrite"):
        run_m21c(args)
