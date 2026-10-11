"""M1 tests never contact OpenRouter or require a real API key."""
from argparse import Namespace
import json

import pytest

from surlife.core import Arena
from surlife.gateway import GatewayError, OpenRouterGateway, FakeGateway, parse_answer
from surlife.runner import can_consult, run_m1
from surlife.souls import Soul
from surlife.storage import Journal


def options(tmp_path, **kw):
    defaults = dict(
        provider="fake", model="openrouter/free", max_requests=4,
        max_output_tokens=64, a="llm", b="greedy", run_id="test-1",
        seed=7, ticks=8, souls_dir=str(tmp_path / "souls"), soul_a=None, soul_b=None,
    )
    defaults.update(kw)
    return Namespace(**defaults)


def test_only_free_router_or_explicit_free_model():
    OpenRouterGateway("openrouter/free")
    OpenRouterGateway("some-provider/model:free")
    for slug in ("openai/gpt-4", "deepseek/deepseek-chat", "bad model:free"):
        with pytest.raises(ValueError):
            OpenRouterGateway(slug)


def test_response_schema_is_data_only():
    value = parse_answer('{"mask":5,"soul_update":"Re-evaluate combos"}',
                         "model/free", {"prompt_tokens": 21, "completion_tokens": 7, "total_tokens": 28})
    assert value.mask == 5
    assert value.usage["total_tokens"] == 28
    assert len(value.soul_update) > 0
    for text in ('{"mask":true}', '{"mask":999}', '{"mask":"7"}', "shell('rm -rf /')", "{}"):
        with pytest.raises(GatewayError):
            parse_answer(text, "m", {})


def test_key_is_host_only_and_cap_enforced(monkeypatch):
    captured = []
    monkeypatch.setenv("OPENROUTER_API_KEY", "TEST_PRIVATE_KEY")
    def transport(payload, key, timeout):
        captured.append((payload, key, timeout))
        return {"model": "example/free", "choices": [{"message": {"content": '{"mask":0}'}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 5, "total_tokens": 9}}
    gateway = OpenRouterGateway(max_requests=1, transport=transport)
    assert gateway.ask([{"role": "user", "content": "{}"}]).mask == 0
    assert gateway.calls == 1
    assert captured[0][1] == "TEST_PRIVATE_KEY"
    assert "TEST_PRIVATE_KEY" not in json.dumps(captured[0][0])
    with pytest.raises(GatewayError, match="cap"):
        gateway.ask([{"role": "user", "content": "{}"}])


def test_failed_model_request_still_counts(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "TEST_KEY")
    def broken(*args):
        raise GatewayError("provider unavailable")
    gateway = OpenRouterGateway(max_requests=1, transport=broken)
    with pytest.raises(GatewayError):
        gateway.ask([{"role": "user", "content": "{}"}])
    assert gateway.remaining == 0


def test_soul_versions_only_after_imperfect_feedback(tmp_path):
    soul = Soul.new("a")
    assert not soul.propose("always use more energy", tick=0)
    soul.observe(0, 4, 10, 1, 29)
    assert soul.propose("Enumerate more alternatives.", tick=0)
    assert soul.version == 1
    assert not soul.propose("Enumerate more alternatives.", tick=1)
    soul.save(tmp_path)
    content = json.loads((tmp_path / "a.json").read_text())
    assert content["version"] == 1
    assert len(content["revisions"]) == 1
    assert "private" not in content


def test_m1_fake_run_replays_without_secret(tmp_path):
    args = options(tmp_path)
    path = tmp_path / "world.sqlite"
    result = run_m1(args, path)
    assert result["verified"] is True
    assert result["rounds"] == 8
    assert result["model_requests"] == 4
    assert result["consultations"]["a"] == 4
    assert result["consultations"]["b"] == 0
    assert result["attempts"]["a"] == 8
    assert (tmp_path / "souls" / "test-1" / "a.json").exists()
    with Journal(path) as journal:
        again = journal.replay("test-1")
        assert again["verified"]
        assert again["consultations"]["a"] == 4
        assert journal.db.execute("SELECT count(*) FROM rounds").fetchone()[0] == 8


def test_no_duplicate_run_id_clobbers_soul(tmp_path):
    args = options(tmp_path)
    run_m1(args, tmp_path / "world.sqlite")
    with pytest.raises(ValueError, match="exists"):
        run_m1(args, tmp_path / "world.sqlite")


def test_openrouter_requires_key_without_network(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        run_m1(options(tmp_path, provider="openrouter"), tmp_path / "world.sqlite")


def test_preflight_for_affordable_cognition():
    arena = Arena(seed=1, energy=1)
    weather = arena.observations()["a"].weather
    assert can_consult(arena, "a", weather) in (True, False)
    assert not can_consult(Arena(seed=1, energy=0), "a", weather)


def test_inherit_snapshot_across_runs_and_detect_tampering(tmp_path):
    first = options(tmp_path, run_id="ancestor", ticks=4)
    run_m1(first, tmp_path / "world.sqlite")
    snapshot = tmp_path / "souls" / "ancestor" / "a.json"
    prior = Soul.restore("a", str(snapshot))
    assert prior.memory
    assert prior.sha256
    child = options(tmp_path, run_id="descendant", ticks=2, inherit_soul_a=str(snapshot))
    result = run_m1(child, tmp_path / "world.sqlite")
    assert result["verified"]
    continued = Soul.restore("a", str(tmp_path / "souls" / "descendant" / "a.json"))
    assert len(continued.memory) >= len(prior.memory)
    data = json.loads(snapshot.read_text())
    data["base"] = "unrecorded mutation"
    snapshot.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash mismatch"):
        Soul.restore("a", str(snapshot))
    with pytest.raises(ValueError, match="another actor"):
        Soul.restore("b", str(tmp_path / "souls" / "descendant" / "a.json"))


def test_replay_with_llm_flags_cannot_trigger_live_provider(tmp_path, monkeypatch, capsys):
    import sys
    from surlife.cli import main
    from surlife.core import RULES_VERSION, START_ENERGY, STAKE
    from surlife.core import Action
    with Journal(tmp_path / "world.sqlite") as db:
        db.create_run("prior", {"rules": RULES_VERSION, "seed": 1,
                                "start_energy": START_ENERGY, "stake": STAKE})
        db.append("prior", Arena(1).step({"a": Action(0), "b": Action(None)}))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["surlife", "--db", str(tmp_path / "world.sqlite"),
                                      "--a", "llm", "--provider", "openrouter", "--replay", "prior"])
    main()
    data = json.loads(capsys.readouterr().out)
    assert data["verified"] and data["rounds"] == 1



def test_free_model_can_return_json_after_markdown_or_prose():
    wrapped = 'Sure! Here is the move:\n```json\n{"mask": 6, "soul_update": "Watch capacity"}\n```'
    assert parse_answer(wrapped, "test:free", {}).mask == 6
    assert parse_answer('{"mask":0}', "test:free", {}).mask == 0


@pytest.mark.parametrize(("reply", "expected_reason"), [
    ({"error": {"code": 429, "message": "potentially unsafe body"}},
     "provider_error_429"),
    ({"choices": []}, "missing_choice"),
    ({"choices": [{"finish_reason": "error", "error": {"code": 503}}]},
     "completion_error_503"),
    ({"choices": [{"finish_reason": "length", "message": {"content": '{"mask":0}'}}]},
     "completion_truncated"),
    ({"choices": [{"message": {"content": ""}}]}, "empty_content"),
    ({"choices": [{"message": {"content": "not json"}}]}, "invalid_json"),
    ({"choices": [{"message": {"content": '{"mask":true}'}}]}, "invalid_mask"),
])
def test_safe_provider_failure_categories(monkeypatch, reply, expected_reason):
    monkeypatch.setenv("OPENROUTER_API_KEY", "TOP_SECRET_TEST_KEY")
    gateway = OpenRouterGateway(max_requests=1, transport=lambda *args: reply)
    with pytest.raises(GatewayError) as exc_info:
        gateway.ask([{"role": "user", "content": "one task"}])
    assert exc_info.value.reason == expected_reason
    assert "TOP_SECRET_TEST_KEY" not in str(exc_info.value)
    assert gateway.calls == 1


def test_http_429_is_classified_without_leaking_body(monkeypatch):
    import io
    import urllib.error
    import surlife.gateway as gateway_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "TOP_SECRET_TEST_KEY")

    def rate_limited(_request, timeout=30):
        raise urllib.error.HTTPError(
            "https://openrouter.ai/api/v1/chat/completions",
            429, "rate limited TOP_SECRET_TEST_KEY", {}, io.BytesIO(b"PRIVATE BODY")
        )

    monkeypatch.setattr(gateway_module.urllib.request, "urlopen", rate_limited)
    gateway = OpenRouterGateway(max_requests=1)
    with pytest.raises(GatewayError) as exc_info:
        gateway.ask([{"role": "user", "content": "task"}])
    assert exc_info.value.reason == "http_429"
    assert "TOP_SECRET_TEST_KEY" not in str(exc_info.value)
    assert gateway.calls == 1


def test_failed_json_still_carries_routed_model_and_usage(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "TOP_SECRET_TEST_KEY")
    result = {
        "model": "provider/actual-free-model",
        "choices": [{"message": {"content": "I choose item 2."}}],
        "usage": {"prompt_tokens": 210, "completion_tokens": 512, "total_tokens": 722},
    }
    gateway = OpenRouterGateway(max_requests=1, transport=lambda *_: result)
    with pytest.raises(GatewayError) as exc_info:
        gateway.ask([{"role": "user", "content": "task"}])
    assert exc_info.value.reason == "invalid_json"
    assert exc_info.value.model == "provider/actual-free-model"
    assert exc_info.value.usage["total_tokens"] == 722


def test_m1_journal_records_reason_without_provider_body(tmp_path, monkeypatch):
    import surlife.runner as runner_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "TOP_SECRET_TEST_KEY")
    response = {
        "error": {"code": 503, "message": "TOP_SECRET_TEST_KEY: provider internal issue"}
    }
    def mocked_gateway(**settings):
        return OpenRouterGateway(transport=lambda *_: response, **settings)

    monkeypatch.setattr(runner_module, "OpenRouterGateway", mocked_gateway)
    args = options(tmp_path, provider="openrouter", max_requests=2, ticks=4)
    db_path = tmp_path / "world.sqlite"
    result = run_m1(args, db_path)
    assert result["failure_reasons"] == {"provider_error_503": 2}
    assert result["consultations"]["a"] == 2
    assert result["verified"]
    with Journal(db_path) as journal:
        first = journal.db.execute(
            "SELECT payload FROM rounds WHERE run_id=? AND tick=0", ("test-1",)
        ).fetchone()[0]
    assert "provider_error_503" in first
    assert "TOP_SECRET_TEST_KEY" not in first
    assert "provider internal issue" not in first


@pytest.mark.parametrize(("reasoning_mode", "expected_reasoning"), [
    ("off", {"enabled": False}),
    ("low", {"effort": "low"}),
    ("auto", None),
])
def test_openrouter_reasoning_configuration(monkeypatch, reasoning_mode, expected_reasoning):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_KEY")
    seen = []
    def transport(payload, _key, _timeout):
        seen.append(payload)
        return {"model": "test/free", "choices": [{"finish_reason": "stop",
                "message": {"content": '{"mask":0}'}}], "usage": {"total_tokens": 10}}
    gateway = OpenRouterGateway(reasoning=reasoning_mode, transport=transport)
    assert gateway.ask([{"role": "user", "content": "one puzzle"}]).mask == 0
    assert seen[0].get("reasoning") == expected_reasoning
    assert seen[0]["max_completion_tokens"] == 512


def test_gateway_rejects_unknown_reasoning_modes():
    with pytest.raises(ValueError, match="reasoning"):
        OpenRouterGateway(reasoning="extended")


def test_truncated_completion_preserves_model_and_token_counts(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_KEY")
    raw = {"model": "provider/underlying-free", "usage": {
        "prompt_tokens": 123, "completion_tokens": 512, "total_tokens": 635,
    }, "choices": [{"finish_reason": "length", "message": {"content": ""}}]}
    gw = OpenRouterGateway(transport=lambda *_: raw)
    with pytest.raises(GatewayError) as caught:
        gw.ask([{"role": "user", "content": "one puzzle"}])
    assert caught.value.reason == "completion_truncated"
    assert caught.value.model == "provider/underlying-free"
    assert caught.value.usage["completion_tokens"] == 512


def test_truncated_calls_keep_usage_in_replay(tmp_path, monkeypatch):
    import surlife.runner as runner_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "DUMMY_KEY")
    raw = {"model": "provider/underlying-free", "usage": {
        "prompt_tokens": 111, "completion_tokens": 512, "total_tokens": 623,
    }, "choices": [{"finish_reason": "length", "message": {"content": ""}}]}
    def patched(**kwargs):
        return OpenRouterGateway(transport=lambda *_: raw, **kwargs)
    monkeypatch.setattr(runner_module, "OpenRouterGateway", patched)
    opts = options(tmp_path, provider="openrouter", max_requests=1, ticks=2, reasoning="off")
    report = run_m1(opts, tmp_path / "truncated.sqlite")
    assert report["verified"] is True
    assert report["failure_reasons"] == {"completion_truncated": 1}
    assert report["reported_tokens"]["total_tokens"] == 623
    assert report["unknown_usage_requests"] == 0
    assert report["routed_models"] == {"provider/underlying-free": 1}
    assert report["reasoning"] == "off"
