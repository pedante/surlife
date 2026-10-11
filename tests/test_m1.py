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
