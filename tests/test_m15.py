"""M1.5 Gemini interactions adapter regression; all tests run without Google keys."""
from __future__ import annotations
import json
from argparse import Namespace
from types import SimpleNamespace
import pytest
from surlife.gemini_gateway import (
    GeminiGateway, check_gemini_model, _schema,
)
from surlife.gateway import GatewayError
from surlife.m14 import run_m14, verify_report_file


def answer(text='{"mask":257,"soul_update":""}', model="gemini-3.8-flash",
           usage=True, status="completed"):
    tokens = SimpleNamespace(total_input_tokens=43, total_output_tokens=12,
                             total_thought_tokens=6, total_tokens=61) if usage else None
    return SimpleNamespace(output_text=text, model=model, usage=tokens, status=status)


def arguments(tmp_path, **kw):
    a = dict(
        a="llm", b="greedy", provider="google", model="gemini-3.8-flash",
        seed=17, benchmark_cases=4, benchmark_items=12,
        benchmark_profile="mixed", cognition="always",
        max_requests=1, max_output_tokens=256, reasoning="off",
        benchmark_out=str(tmp_path / "google.json"),
    )
    a.update(kw)
    return Namespace(**a)


def test_google_free_tier_allowlist_and_deprecated_alias():
    assert check_gemini_model("gemini-3.8-flash")["free_tier_listed"]
    assert check_gemini_model("gemini-3.8-flash")["account_billing_verified"] is False
    assert check_gemini_model("gemini-3.5-flash-lite")["free_tier_listed"]
    for wrong in ("gemini-3.7-flash", "gemini-3.1-pro", "gemini-3.8-flash-unknown"):
        with pytest.raises(ValueError):
            check_gemini_model(wrong)


def test_gemini_benchmark_schema_and_credential_isolation(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "SECRET_DO_NOT_LOG")
    calls = []
    def send(**kw):
        calls.append(kw)
        return answer()
    gateway = GeminiGateway(max_requests=1, max_output_tokens=256,
                            transport=send, reasoning="off")
    response = gateway.ask([{"role": "user", "content": "{}"}],
                           mode="benchmark", benchmark_items=12)
    assert response.mask == 257
    assert response.model == "gemini-3.8-flash"
    assert response.usage == {
        "prompt_tokens": 43, "completion_tokens": 12, "total_tokens": 61,
        "thought_tokens": 6,
    }
    assert gateway.remaining == 0
    call = calls[0]
    assert call["store"] is False
    assert call["model"] == "gemini-3.8-flash"
    assert call["generation_config"] == {
        "max_output_tokens": 256, "thinking_level": "low",
    }
    assert call["response_format"]["mime_type"] == "application/json"
    assert call["response_format"]["schema"]["properties"]["mask"] == {
        "type": "integer", "minimum": 0, "maximum": 4095,
    }
    without_key = {k:v for k,v in call.items() if k != "api_key"}
    assert "SECRET_DO_NOT_LOG" not in json.dumps(without_key)
    assert call["input"].startswith("USER:")


def test_request_cap_and_invalid_arguments_do_not_call_provider(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    calls = []
    gateway = GeminiGateway(max_requests=1, transport=lambda **kw: calls.append(kw) or answer())
    for args in [
        dict(mode="benchmark", benchmark_items=7),
        dict(mode="benchmark", benchmark_items=15),
        dict(mode="reflection", benchmark_items=12),
        dict(mode="action", allowed_masks=[2, 1]),
    ]:
        with pytest.raises(ValueError):
            gateway.ask([{"role": "user", "content": "{}"}], **args)
    assert calls == [] and gateway.calls == 0
    gateway.ask([{"role": "user", "content": "{}"}],
                mode="benchmark", benchmark_items=12)
    with pytest.raises(GatewayError):
        gateway.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert len(calls) == 1


def test_missing_key_does_not_consume_request(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    gateway = GeminiGateway(transport=lambda **kw: (_ for _ in ()).throw(
        AssertionError("should not invoke provider")))
    with pytest.raises(GatewayError) as exc:
        gateway.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert exc.value.reason == "missing_google_api_key"
    assert gateway.calls == 0


def test_model_mismatch_fails_closed_with_usage(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    gateway = GeminiGateway(transport=lambda **kw: answer(model="other-model"))
    with pytest.raises(GatewayError) as err:
        gateway.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert err.value.reason == "routed_model_mismatch"
    assert err.value.usage["total_tokens"] == 61
    assert err.value.model == "other-model"


def test_unusable_response_preserves_usage_and_rejects_bad_mask(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    gateway = GeminiGateway(transport=lambda **kw: answer(
        text='{"mask":4096,"soul_update":""}'))
    with pytest.raises(GatewayError) as err:
        gateway.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert err.value.reason == "invalid_mask"
    assert err.value.usage["total_tokens"] == 61


def test_provider_http_error_is_sanitized_and_charged(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    class GoogleRateLimit(Exception):
        code = 429
    def err(**kw):
        raise GoogleRateLimit("PRIVATE_PROVIDER_DETAIL")
    gateway = GeminiGateway(max_requests=1, transport=err)
    with pytest.raises(GatewayError) as info:
        gateway.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert info.value.reason == "http_429"
    assert "PRIVATE_PROVIDER_DETAIL" not in str(info.value)
    assert gateway.calls == 1


def test_reasoning_auto_maps_medium_and_no_output_tools(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    seen = {}
    def transport(**kw):
        seen.update(kw)
        return answer()
    GeminiGateway(reasoning="auto", transport=transport).ask(
        [{"role": "user", "content": "test"}],
        mode="benchmark", benchmark_items=12,
    )
    assert seen["generation_config"]["thinking_level"] == "medium"
    assert "tools" not in seen and "previous_interaction_id" not in seen


def test_reflection_and_raw_action_schemas(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    replies = iter([
        answer(text='{"soul_update":"Check capacity before committing."}'),
        answer(text='{"mask":7,"soul_update":""}'),
    ])
    gateway = GeminiGateway(max_requests=2, transport=lambda **kw: next(replies))
    reflection = gateway.ask([{"role": "user", "content": "{}"}], mode="reflection")
    assert reflection.mask is None and reflection.soul_update
    action = gateway.ask([{"role": "user", "content": "{}"}], mode="action")
    assert action.mask == 7
    assert _schema("benchmark", None, 12)["properties"]["mask"]["maximum"] == 4095


def test_missing_usage_is_unknown_not_zero(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    response = GeminiGateway(transport=lambda **kw: answer(usage=False)).ask(
        [{"role": "user", "content": "{}"}], mode="benchmark", benchmark_items=12
    )
    assert response.usage["total_tokens"] is None


def test_m14_integration_with_injected_google_sdk_transport(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    import surlife.m14 as benchmark
    def gateway(**kw):
        return GeminiGateway(transport=lambda **_kw: answer(text='{"mask":0,"soul_update":""}'), **kw)
    monkeypatch.setattr(benchmark, "GeminiGateway", gateway)
    result = run_m14(arguments(tmp_path))
    arm = result["summary"]["arms"]["llm"]
    assert result["manifest"]["provider"] == "google"
    assert result["manifest"]["requested_model"] == "gemini-3.8-flash"
    assert arm["model_actions"] == 1
    assert arm["consultations"] == 1
    assert arm["reported_tokens"]["total_tokens"] == 61
    assert result["verified"]
    assert verify_report_file(tmp_path / "google.json")["verified"]


def test_m14_google_429_stops_inference_for_remaining_turns(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    import surlife.m14 as benchmark
    calls = []
    class TooMany(Exception):
        code = 429
    def transport(**kw):
        calls.append(1)
        raise TooMany("never persist this error")
    monkeypatch.setattr(
        benchmark, "GeminiGateway",
        lambda **kw: GeminiGateway(transport=transport, **kw),
    )
    result = run_m14(arguments(tmp_path))
    assert calls == [1]
    assert result["failure_reasons"] == {"http_429": 1}
    assert result["rate_limited_skips"] == 3
    assert result["summary"]["arms"]["llm"]["provider_failures"] == 1
    assert verify_report_file(tmp_path / "google.json")["verified"]


def test_m14_missing_google_key_rejects_before_file_creation(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        run_m14(arguments(tmp_path))
    assert not (tmp_path / "google.json").exists()



def test_actual_google_sdk_wiring_is_stateless_v1_and_closes(monkeypatch):
    genai = pytest.importorskip("google.genai")
    import surlife.gemini_gateway as adapter
    calls = {}
    class ClientStub:
        def __init__(self, api_key=None, http_options=None):
            calls["client_key"] = api_key
            calls["http_options"] = http_options
            self.interactions = SimpleNamespace(create=self.create)
        def create(self, **kwargs):
            calls["body"] = kwargs
            return answer()
        def close(self):
            calls["closed"] = True
    monkeypatch.setattr(genai, "Client", ClientStub)
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    gateway = adapter.GeminiGateway(max_requests=1)
    reply = gateway.ask([{"role": "user", "content": "{}"}],
                        mode="benchmark", benchmark_items=12)
    assert reply.mask == 257
    assert calls["client_key"] == "DUMMY"
    assert calls["http_options"] == {
        "api_version": "v1", "timeout": 90000,
        "retry_options": {"attempts": 0},
    }
    assert calls["body"]["store"] is False
    assert calls["closed"] is True
    assert "tools" not in calls["body"]



def test_gemini_timeout_is_validated_and_forwarded(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    observed = {}
    gw = GeminiGateway(timeout_seconds=45, transport=lambda **kw: observed.update(kw) or answer())
    gw.ask([{"role": "user", "content": "{}"}], mode="benchmark", benchmark_items=12)
    assert observed["timeout_seconds"] == 45
    assert gw.calls == 1
    for bad in [0, 1, 9, 181, "90", True]:
        with pytest.raises(ValueError, match="timeout"):
            GeminiGateway(timeout_seconds=bad, transport=lambda **kw: answer())


def test_gemini_higher_default_and_hard_ceiling_for_thinking():
    from surlife.gemini_gateway import GEMINI_DEFAULT_OUTPUT_TOKENS
    gateway = GeminiGateway(transport=lambda **kw: answer())
    assert gateway.max_output_tokens == 4096 == GEMINI_DEFAULT_OUTPUT_TOKENS
    GeminiGateway(max_output_tokens=8192, transport=lambda **kw: answer())
    with pytest.raises(ValueError, match="includes thought tokens"):
        GeminiGateway(max_output_tokens=8193, transport=lambda **kw: answer())


def test_incomplete_budget_preserves_thinking_metadata_and_one_charged_call(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    # Mirrors Google's incomplete status after max_output_tokens is consumed
    # by reasoning before enough visible output is produced.
    output = SimpleNamespace(output_text=None, model="gemini-3.8-flash",
                             status="incomplete",
                             usage=SimpleNamespace(
                                 total_input_tokens=210,
                                 total_output_tokens=0,
                                 total_thought_tokens=512,
                                 total_tokens=722))
    calls = []
    def transport(**kwargs):
        calls.append(kwargs)
        return output
    gw = GeminiGateway(max_requests=1, max_output_tokens=512, transport=transport)
    with pytest.raises(GatewayError) as err:
        gw.ask([{"role": "user", "content": "task"}],
               mode="benchmark", benchmark_items=12)
    exc = err.value
    assert exc.reason == "incomplete_interaction"
    assert exc.usage == {
        "prompt_tokens": 210, "completion_tokens": 0,
        "total_tokens": 722, "thought_tokens": 512,
    }
    assert exc.generation_diagnostics == {
        "status": "incomplete", "output_token_limit": 512,
        "reported_output_tokens": 0, "reported_thought_tokens": 512,
    }
    assert gw.calls == 1 and gw.remaining == 0 and len(calls) == 1


def test_m14_incomplete_metadata_and_replay_is_consistent(tmp_path, monkeypatch):
    import surlife.m14 as benchmark
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    def incomplete(**kwargs):
        return SimpleNamespace(
            model="gemini-3.8-flash", output_text=None, status="incomplete",
            usage=SimpleNamespace(total_input_tokens=210,
                                  total_output_tokens=0,
                                  total_thought_tokens=512,
                                  total_tokens=722))
    monkeypatch.setattr(benchmark, "GeminiGateway", lambda **kw: GeminiGateway(
        transport=incomplete, **kw))
    report = run_m14(arguments(tmp_path, max_output_tokens=512))
    assert report["verified"]
    assert report["failure_reasons"] == {"incomplete_interaction": 1}
    assert report["google_generation"] == {
        "output_token_limit": 512,
        "reported_thought_tokens": 512,
        "unknown_thought_usage": 0,
    }
    audit = json.loads((tmp_path / "google.json").read_text())
    meta = audit["arms"]["llm"][0]["benchmark"]
    assert meta["generation_diagnostics"]["status"] == "incomplete"
    assert meta["generation_diagnostics"]["reported_thought_tokens"] == 512
    assert meta["generation_diagnostics"]["output_token_limit"] == 512
    assert meta["usage"]["total_tokens"] == 722
    assert "google_generation" not in audit["summary"]
    assert verify_report_file(tmp_path / "google.json")["head"] == report["head"]


def test_no_incomplete_when_sufficient_budget_and_same_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "DUMMY")
    gw = GeminiGateway(
        max_output_tokens=4096, transport=lambda **kw: answer(),
    )
    actual = gw.ask([{"role": "user", "content": "{}"}],
                    mode="benchmark", benchmark_items=12)
    assert actual.mask == 257
    assert actual.usage["thought_tokens"] == 6
