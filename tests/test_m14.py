"""M1.4 headroom benchmark: reproducibility, accounting, and gateway bounds."""
from __future__ import annotations

import copy
import json
from argparse import Namespace
from random import Random

import pytest

from surlife.core import Arena, Observation, POLICIES, Task
from surlife.gateway import GatewayError, OpenRouterGateway, Reply, benchmark_action_schema
from surlife.m14 import (
    BenchmarkArena, make_cases, run_m14, verify_report, verify_report_file,
)


def opts(tmp_path, **kw):
    d = dict(
        m14=True, a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, benchmark_cases=12, benchmark_items=12,
        benchmark_profile="mixed", max_requests=8,
        max_output_tokens=512, reasoning="off",
        cognition="selective", benchmark_out=str(tmp_path / "m14.json"),
    )
    d.update(kw)
    return Namespace(**d)


def test_constructed_headroom_is_real_and_not_random_scoring_luck():
    cases = make_cases(17, 12, 12, "mixed")
    again = make_cases(17, 12, 12, "mixed")
    assert [x["task"].as_dict() for x in cases] == [x["task"].as_dict() for x in again]
    assert [x["oracle_mask"] for x in cases] == [x["oracle_mask"] for x in again]
    assert len(cases) == 12
    traps = [x for x in cases if x["kind"] == "trap"]
    assert len(traps) == 6
    for c in traps:
        assert c["gap"] > 0
        assert c["gap"] / c["oracle_score"] >= .12
        assert c["task"].score(c["oracle_mask"]) == c["oracle_score"]
        assert c["task"].score(c["dp_mask"]) == c["oracle_score"]
        assert c["task"].score(c["greedy_mask"]) == c["greedy_score"]


@pytest.mark.parametrize("items", [8, 10, 12, 14])
def test_exact_oracle_is_reproducible_with_more_than_five_items(items):
    cases = make_cases(41, 3, items, "trap")
    for case in cases:
        task = case["task"]
        obs = Observation(0, "normal", task, 30)
        greedy = POLICIES["greedy"](obs, Random(0))
        assert task.score(greedy.mask) < task.optimum
        assert task.score(case["oracle_mask"]) == task.optimum
        assert task.score(case["dp_mask"]) == task.optimum
        assert task.score(1 << items) == -1


def test_standalone_fake_run_has_real_headroom_and_verified_audit(tmp_path):
    args = opts(tmp_path)
    summary = run_m14(args)
    assert summary["verified"]
    assert summary["manifest"]["referee_rules"] == "m0-v2"
    assert summary["manifest"]["benchmark_rules"] == "m14-v1"
    assert summary["summary"]["headroom"]["trap_cases"] == 6
    assert summary["summary"]["headroom"]["positive_gap_cases"] >= 6
    assert summary["summary"]["headroom"]["greedy_gap"] > 0
    arms = summary["summary"]["arms"]
    assert set(arms) == {"greedy", "dp", "oracle", "llm"}
    assert arms["greedy"]["consultations"] == arms["dp"]["consultations"] == arms["oracle"]["consultations"] == 0
    assert arms["llm"]["consultations"] == 4
    assert arms["llm"]["model_actions"] == 4
    assert arms["llm"]["provider_failures"] == 0
    assert arms["llm"]["reported_tokens"]["total_tokens"] == 0
    assert arms["llm"]["energy_delta_vs_no_inference"] <= 0
    assert arms["oracle"]["task_score_sum"] == arms["dp"]["task_score_sum"]
    assert arms["dp"]["task_score_sum"] >= arms["greedy"]["task_score_sum"]
    assert summary["summary"]["headroom"]["dp_total"] == summary["summary"]["headroom"]["oracle_total"]
    assert verify_report_file(args.benchmark_out)["head"] == summary["head"]


def test_no_inference_matches_greedy_energy_even_with_llm_selected(tmp_path):
    result = run_m14(opts(tmp_path, cognition="never"))
    arms = result["summary"]["arms"]
    assert arms["llm"]["consultations"] == 0
    assert arms["llm"]["model_actions"] == 0
    assert arms["llm"]["energy"] == arms["greedy"]["energy"]
    assert arms["llm"]["energy_delta_vs_no_inference"] == 0


def test_greedy_only_benchmark_does_not_open_gateway(tmp_path, monkeypatch):
    import surlife.m14 as m14
    monkeypatch.setattr(m14, "_gateway", lambda _: (_ for _ in ()).throw(
        AssertionError("unexpected real gateway")))
    result = run_m14(opts(tmp_path, a="greedy", provider="openrouter"))
    assert set(result["summary"]["arms"]) == {"greedy", "dp", "oracle"}
    assert result["summary"]["arms"]["greedy"]["energy_delta_vs_no_inference"] == 0


def test_invalid_large_mask_is_not_repaired_by_arena(tmp_path, monkeypatch):
    import surlife.m14 as m14
    class FakeBad:
        def __init__(self, max_requests):
            self.calls = 0
            self.limit = max_requests
            self.model = "fake/bad"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action", benchmark_items=None):
            assert mode == "benchmark" and benchmark_items == 12
            self.calls += 1
            return Reply(mask=(1 << benchmark_items) - 1, soul_update="",
                         model=self.model,
                         usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2})
    monkeypatch.setattr(m14, "FakeGateway", FakeBad)
    summary = run_m14(opts(tmp_path, cognition="always", max_requests=3))
    stats = summary["summary"]["arms"]["llm"]
    assert stats["invalid"] >= 1
    assert stats["consultations"] == 3
    report = json.loads((tmp_path / "m14.json").read_text())
    llm = [r for r in report["arms"]["llm"] if r["benchmark"]["source"] == "llm"]
    assert llm and any(r["scores"]["a"] == -1 for r in llm)
    assert verify_report(report)["verified"]


def test_gateway_benchmark_mask_bounds_without_enumerating_legal_menu(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_NOT_LOGGED")
    captured = []
    def transport(payload, key, timeout):
        assert key == "DUMMY_NOT_LOGGED"
        captured.append(payload)
        return {"model": "dots-studio/dots-3-note-preview:free",
                "choices": [{"message": {
                    "content": '{"mask":1024,"soul_update":""}',
                }}],
                "usage": {"prompt_tokens": 22, "completion_tokens": 5,
                          "total_tokens": 27}}
    gw = OpenRouterGateway(max_requests=1, transport=transport)
    reply = gw.ask([{"role": "user", "content": "{}"}],
                   mode="benchmark", benchmark_items=12)
    assert reply.mask == 1024
    assert gw.calls == 1
    schema = captured[0]["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["mask"] == {
        "type": "integer", "minimum": 0, "maximum": 4095,
    }
    assert "DUMMY_NOT_LOGGED" not in json.dumps(captured)


def test_gateway_rejects_invalid_large_mask_and_logs_no_response_body(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY")
    gw = OpenRouterGateway(max_requests=1, transport=lambda *_: {
        "model": "dots-studio/dots-3-note-preview:free",
        "choices": [{"message": {"content": '{"mask":4096,"soul_update":""}'}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
    })
    with pytest.raises(GatewayError) as error:
        gw.ask([{"role": "user", "content": "{}"}],
               mode="benchmark", benchmark_items=12)
    assert error.value.reason == "invalid_mask"
    assert error.value.usage["total_tokens"] == 7


@pytest.mark.parametrize("cases,items", [(0, 12), (49, 12), (1, 7), (1, 15)])
def test_benchmark_input_bounded_before_provider(tmp_path, cases, items, monkeypatch):
    import surlife.m14 as m14
    monkeypatch.setattr(m14, "_gateway", lambda _: (_ for _ in ()).throw(
        AssertionError("should not reach provider")))
    with pytest.raises(ValueError, match="benchmark (cases|items)"):
        run_m14(opts(tmp_path, benchmark_cases=cases, benchmark_items=items))


def test_refuses_duplicate_file_before_spending_model_calls(tmp_path, monkeypatch):
    import surlife.m14 as m14
    destination = tmp_path / "exists.json"
    destination.write_text("ORIGINAL")
    monkeypatch.setattr(m14, "_gateway", lambda _: (_ for _ in ()).throw(
        AssertionError("should not spend provider quota")))
    with pytest.raises(ValueError, match="output exists"):
        run_m14(opts(tmp_path, benchmark_out=str(destination)))
    assert destination.read_text() == "ORIGINAL"


def test_offline_replay_detects_modified_action_and_modified_summary(tmp_path):
    run_m14(opts(tmp_path))
    original = json.loads((tmp_path / "m14.json").read_text())
    corrupt = copy.deepcopy(original)
    corrupt["arms"]["greedy"][0]["actions"]["a"] = 0
    with pytest.raises(ValueError, match="transition mismatch|baseline deviated"):
        verify_report(corrupt)
    corrupt = copy.deepcopy(original)
    corrupt["summary"]["headroom"]["greedy_gap"] = 0
    with pytest.raises(ValueError, match="summary mismatch"):
        verify_report(corrupt)
    corrupt = copy.deepcopy(original)
    corrupt["head"] = "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_report(corrupt)


def test_benchmark_arena_does_not_change_original_puzzle_stream():
    original = Arena(17)
    before = original.observations()["a"].task.as_dict()
    cases = make_cases(17, 3, 12, "trap")
    bench = BenchmarkArena(17, cases)
    assert len(bench.observations()["a"].task.items) == 12
    assert original.observations()["a"].task.as_dict() == before
    assert len(original.observations()["a"].task.items) == 5
    assert original.observations()["a"].weather == bench.observations()["a"].weather


def test_profile_and_seed_must_match_for_valid_replay(tmp_path):
    run_m14(opts(tmp_path))
    report = json.loads((tmp_path / "m14.json").read_text())
    report["manifest"]["seed"] = 18
    with pytest.raises(ValueError, match="transition mismatch|task metadata mismatch"):
        verify_report(report)



def test_unexpected_served_model_is_charged_and_excluded_from_model_actions(tmp_path, monkeypatch):
    import surlife.m14 as m14
    class SwappedModel:
        def __init__(self):
            self.calls = 0
            self.limit = 1
            self.model = "dots-studio/dots-3-note-preview:free"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action", benchmark_items=None):
            self.calls += 1
            return Reply(0, "", "other/unknown-free:free",
                         {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19})
    monkeypatch.setattr(m14, "_gateway", lambda _: SwappedModel())
    result = run_m14(opts(
        tmp_path, provider="openrouter", benchmark_cases=2,
        cognition="always", max_requests=1,
    ))
    arm = result["summary"]["arms"]["llm"]
    assert arm["consultations"] == 1
    assert arm["model_actions"] == 0
    assert arm["provider_failures"] == 1
    assert result["failure_reasons"] == {"routed_model_mismatch": 1}
    assert arm["reported_tokens"]["total_tokens"] == 19
    assert arm["unknown_usage_requests"] == 0
    saved = json.loads((tmp_path / "m14.json").read_text())
    fail = saved["arms"]["llm"][0]
    assert fail["benchmark"]["source"] == "greedy_provider_fallback"
    assert fail["benchmark"]["failure_reason"] == "routed_model_mismatch"
    assert fail["scores"]["a"] == fail["benchmark"]["greedy_score"]
    assert verify_report(saved)["verified"]



def test_dp_baseline_also_replays_and_detects_tampering(tmp_path):
    run_m14(opts(tmp_path))
    record = json.loads((tmp_path / "m14.json").read_text())
    assert record["summary"]["arms"]["dp"]["task_score_sum"] == (
        record["summary"]["arms"]["oracle"]["task_score_sum"]
    )
    assert record["summary"]["arms"]["dp"]["consultations"] == 0
    wrong = copy.deepcopy(record)
    wrong["arms"]["dp"][0]["actions"]["a"] = 0
    with pytest.raises(ValueError, match="transition mismatch|DP baseline deviated"):
        verify_report(wrong)


def test_safe_failure_summary_preserves_historical_replay(tmp_path, monkeypatch):
    import surlife.m14 as m14
    class Unavailable:
        def __init__(self):
            self.calls = 0
            self.limit = 1
            self.model = "fake/down"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action", benchmark_items=None):
            self.calls += 1
            raise GatewayError("an untrusted provider message", "http_400")
    monkeypatch.setattr(m14, "_gateway", lambda _: Unavailable())
    result = run_m14(opts(tmp_path, max_requests=1, benchmark_cases=2))
    assert result["failure_reasons"] == {"http_400": 1}
    persisted = json.loads((tmp_path / "m14.json").read_text())
    assert "failure_reasons" not in persisted["summary"]
    assert verify_report(persisted)["head"] == result["head"]
    assert "an untrusted provider message" not in json.dumps(result)


def test_http_429_stops_future_requests_and_keeps_replay_valid(tmp_path, monkeypatch):
    import surlife.m14 as m14
    calls = []
    class RateLimited:
        def __init__(self):
            self.calls = 0
            self.limit = 8
            self.model = "fake/rate-limited"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action", benchmark_items=None):
            self.calls += 1
            calls.append(self.calls)
            raise GatewayError("provider rate limited", "http_429")
    monkeypatch.setattr(m14, "_gateway", lambda _: RateLimited())
    report = run_m14(opts(
        tmp_path, benchmark_cases=8, cognition="always", max_requests=8
    ))
    llm = report["summary"]["arms"]["llm"]
    assert calls == [1]
    assert llm["consultations"] == 1
    assert llm["provider_failures"] == 1
    assert llm["model_actions"] == 0
    assert report["rate_limited_skips"] >= 1
    assert report["failure_reasons"] == {"http_429": 1}
    assert llm["unknown_usage_requests"] == 1
    saved = json.loads((tmp_path / "m14.json").read_text())
    later = saved["arms"]["llm"][1:]
    assert all(row["consultations"]["a"] == 0 for row in later)
    assert all(row["benchmark"]["source"] == "greedy_rate_limited"
               for row in later if row["attempted"]["a"])
    assert verify_report(saved)["verified"]


def test_other_gateway_errors_do_not_trigger_429_circuit_breaker(tmp_path, monkeypatch):
    import surlife.m14 as m14
    calls = []
    class OccasionalFailure:
        def __init__(self):
            self.calls = 0
            self.limit = 2
            self.model = "fake/unavailable"
        @property
        def remaining(self):
            return self.limit - self.calls
        def ask(self, messages, *, mode="action", benchmark_items=None):
            self.calls += 1
            calls.append(self.calls)
            if self.calls == 1:
                raise GatewayError("provider problem", "http_503")
            return Reply(mask=0, soul_update="", model=self.model,
                         usage={"prompt_tokens": 1, "completion_tokens": 1,
                                "total_tokens": 2})
    monkeypatch.setattr(m14, "_gateway", lambda _: OccasionalFailure())
    report = run_m14(opts(
        tmp_path, benchmark_cases=5, cognition="always", max_requests=2
    ))
    llm = report["summary"]["arms"]["llm"]
    assert calls == [1, 2]
    assert llm["consultations"] == 2
    assert report["rate_limited_skips"] == 0
    assert llm["provider_failures"] == 1
    assert llm["model_actions"] == 1
    assert report["failure_reasons"] == {"http_503": 1}
    assert verify_report_file(tmp_path / "m14.json")["verified"]
