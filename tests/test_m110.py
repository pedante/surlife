"""M1.10 shared-response TaskPack trial, audit, quota and provider isolation."""
from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest

from surlife.core import Observation, START_ENERGY
from surlife.gateway import GatewayError, Reply
from surlife.m19 import TaskPackArena, make_pack_cases
from surlife.m110 import (
    _assemble, _digest, _prompt, run_m110, verify_m110, verify_m110_file,
)


def opts(tmp_path, **changes):
    config = dict(
        a="llm", b="greedy", provider="fake",
        model="dots-studio/dots-3-note-preview:free",
        seed=17, benchmark_cases=4, benchmark_items=9,
        m110_pack="mixed", max_requests=4,
        m110_virtual_cap=4, m110_bank_in=None, policy_in=None,
        benchmark_out=str(tmp_path / "m110.json"),
        max_output_tokens=512, reasoning="off", google_timeout_seconds=45,
    )
    config.update(changes)
    return Namespace(**config)


@pytest.mark.parametrize("pack", ["coverage", "synergy", "mixed"])
def test_fake_bank_and_strong_baselines(tmp_path, pack):
    args = opts(tmp_path, m110_pack=pack)
    outcome = run_m110(args)
    assert outcome["verified"]
    assert verify_m110_file(args.benchmark_out)["verified"]
    assert outcome["manifest"]["taskpack_rules"] == "m19-v1"
    assert outcome["manifest"]["prompt_version"] == "taskpack-prompt-v1"
    summary = outcome["summary"]
    bank = summary["bank_sampling"]
    assert bank["provider_requests"] == 4
    assert bank["successful_responses"] == 4
    assert bank["failed_responses"] == 0
    stats = summary["arms"]
    assert stats["never"]["energy"] == stats["marginal"]["energy"]
    assert stats["never"]["task_score_sum"] == stats["marginal"]["task_score_sum"]
    assert stats["always"]["consultations"] == 4
    assert stats["always"]["task_score_sum"] == stats["greedy"]["task_score_sum"]
    assert stats["always"]["energy"] == stats["greedy"]["energy"] - 4
    assert stats["oracle"]["task_score_sum"] >= stats["beam"]["task_score_sum"]
    assert stats["oracle"]["task_score_sum"] >= stats["marginal"]["task_score_sum"]
    assert stats["adaptive_fresh"]["consultations"] <= 4
    assert stats["always"]["invalid"] == 0
    report = json.loads((tmp_path / "m110.json").read_text())
    assert set(report["arms"]) == {
        "greedy", "marginal", "beam", "oracle",
        "never", "always", "selective", "adaptive_fresh",
    }
    for tick, row in enumerate(report["arms"]["always"]):
        assert row["consultations"]["a"] == 1
        assert row["actions"]["a"] == report["bank"][tick]["mask"]
    assert sum(group["cases"] for group in summary["families"].values()) == 4


@pytest.mark.parametrize("pack", ["coverage", "synergy"])
def test_prompt_fully_describes_pack_without_answer_leak(pack):
    cases = make_pack_cases(17, 1, 8, pack)
    arena = TaskPackArena(17, cases)
    obs = arena.observations()["a"]
    neutral = Observation(0, obs.weather, cases[0]["task"], START_ENERGY)
    prompt = _prompt(neutral)
    assert len(prompt) == 2
    data = json.loads(prompt[1]["content"])
    assert data["own_energy"] == START_ENERGY
    assert data["task"] == cases[0]["task"].as_dict()
    assert "optimal" not in prompt[1]["content"]
    assert "oracle" not in prompt[1]["content"]
    assert "greedy_mask" not in prompt[1]["content"]
    if pack == "coverage":
        assert "unique" in prompt[0]["content"].lower()
        assert "feature_masks" in data["task"]
        assert "pair_bonuses" not in data["task"]
    else:
        assert "both" in prompt[0]["content"].lower()
        assert "pair_bonuses" in data["task"]
        assert "feature_masks" not in data["task"]


def test_verified_bank_reuse_is_network_free_and_virtual_budget_changes(tmp_path, monkeypatch):
    import surlife.m110 as m110
    old = run_m110(opts(tmp_path))
    monkeypatch.setattr(m110, "_gateway", lambda *_: (_ for _ in ()).throw(
        AssertionError("bank reuse must make zero actual model calls")
    ))
    new = run_m110(opts(
        tmp_path, m110_virtual_cap=1,
        m110_bank_in=old["report_path"],
        benchmark_out=str(tmp_path / "reused.json"),
    ))
    assert new["verified"]
    assert new["summary"]["bank_sampling"]["sampling_mode"] == "reused"
    assert new["summary"]["arms"]["always"]["consultations"] == 1
    assert new["summary"]["arms"]["never"]["consultations"] == 0
    assert new["summary"]["arms"]["never"]["energy"] == (
        old["summary"]["arms"]["never"]["energy"])
    assert new["manifest"]["bank_source_head"] == old["head"]
    assert verify_m110_file(new["report_path"])["verified"]


def test_provider_429_is_charged_once_and_never_taught_as_bad_reasoning(tmp_path, monkeypatch):
    import surlife.m110 as m110

    class Broken:
        model = "surlife/fake-model"

        def __init__(self, max_requests=4):
            self.calls = 0
            self.limit = max_requests

        @property
        def remaining(self):
            return max(0, self.limit - self.calls)

        def ask(self, *_args, **_kw):
            self.calls += 1
            raise GatewayError("quota", "http_429")

    monkeypatch.setattr(m110, "_gateway", lambda args: Broken(args.max_requests))
    report = run_m110(opts(tmp_path))
    saved = json.loads((tmp_path / "m110.json").read_text())
    assert [item["status"] for item in saved["bank"]] == [
        "failed", "unavailable", "unavailable", "unavailable",
    ]
    assert report["summary"]["bank_sampling"]["provider_requests"] == 1
    assert report["summary"]["arms"]["always"]["provider_failures"] == 1
    assert report["summary"]["arms"]["always"]["consultations"] == 1
    assert report["summary"]["arms"]["never"]["consultations"] == 0
    result = saved["arms"]["adaptive_fresh"][0]["benchmark"]
    assert result["feedback_kind"] == "provider_failure"
    assert all(state["trials"] == 0 for state in result["policy_after"].values())
    assert verify_m110(saved)["verified"]


def test_model_can_improve_puzzle_quality_if_it_selects_oracle_masks(tmp_path, monkeypatch):
    import surlife.m110 as m110
    cases = make_pack_cases(17, 8, 9, "mixed")

    class OracleReplyGateway:
        model = "surlife/fake-model"

        def __init__(self):
            self.calls = 0

        @property
        def remaining(self):
            return 8 - self.calls

        def ask(self, messages, **kw):
            tick = json.loads(messages[-1]["content"])["tick"]
            self.calls += 1
            return Reply(mask=cases[tick]["oracle_mask"], soul_update="",
                         model=self.model,
                         usage={"prompt_tokens": 0, "completion_tokens": 0,
                                "total_tokens": 0})

    monkeypatch.setattr(m110, "_gateway", lambda _args: OracleReplyGateway())
    result = run_m110(opts(tmp_path, benchmark_cases=8,
                           max_requests=8, m110_virtual_cap=8))
    scores = result["summary"]["arms"]
    assert scores["always"]["task_score_sum"] == scores["oracle"]["task_score_sum"]
    assert scores["always"]["consultations"] == 8
    assert scores["always"]["energy"] <= scores["oracle"]["energy"]
    assert result["summary"]["headroom"]["oracle_total"] >= (
        result["summary"]["headroom"]["marginal_total"])
    assert verify_m110_file(result["report_path"])["verified"]


def test_replay_rejects_tampering_even_if_surface_hash_is_recomputed(tmp_path):
    run_m110(opts(tmp_path))
    saved = json.loads((tmp_path / "m110.json").read_text())
    altered = copy.deepcopy(saved)
    altered["arms"]["always"][0]["consultations"]["a"] = 0
    with pytest.raises(ValueError, match="replay"):
        verify_m110(altered)
    altered = copy.deepcopy(saved)
    altered["bank"][0]["mask"] = 1 << 9
    with pytest.raises(ValueError, match="sampled"):
        verify_m110(altered)
    altered = copy.deepcopy(saved)
    altered["bank"][0]["mask"] = 0
    altered["head"] = _digest(
        altered["manifest"], altered["bank"], altered["arms"],
        altered["summary"],
    )
    with pytest.raises(ValueError, match="replay"):
        verify_m110(altered)
    altered = copy.deepcopy(saved)
    altered["arms"]["adaptive_fresh"][0]["benchmark"]["policy_after"]["routine"]["visits"] += 1
    with pytest.raises(ValueError, match="replay"):
        verify_m110(altered)
    altered = copy.deepcopy(saved)
    altered["summary"]["families"]["synergy"]["oracle_total"] = 0
    with pytest.raises(ValueError, match="replay"):
        verify_m110(altered)


def test_preflight_guards_model_calls_and_prevents_cross_pack_banks(tmp_path, monkeypatch):
    for kwargs, message in (
        ({"max_requests": 3}, "cover ALL sampled cases"),
        ({"m110_virtual_cap": 5}, "virtual cap"),
        ({"m110_virtual_cap": -1}, "virtual cap"),
        ({"benchmark_out": None}, "--benchmark-out"),
        ({"a": "greedy"}, "requires --a llm"),
        ({"policy_in": "do-not-read.json"}, "does not import"),
    ):
        with pytest.raises(ValueError, match=message):
            run_m110(opts(tmp_path, **kwargs))
    saved = run_m110(opts(tmp_path))
    with pytest.raises(ValueError, match="exists"):
        run_m110(opts(tmp_path))
    # Reusing an M1.8 bank is impossible: versioned manifest and scorer differ.
    with pytest.raises(ValueError):
        verify_m110({"manifest": {"experiment": "m18-v1"}, "bank": []})
    monkeypatch.setattr("surlife.m110._gateway", lambda _args: (_ for _ in ()).throw(
        AssertionError("a mismatched bank must be rejected before any provider call")
    ))
    for kw in ({"m110_pack": "synergy"}, {"seed": 19},
               {"max_output_tokens": 4096}):
        with pytest.raises(ValueError, match="mismatch"):
            run_m110(opts(
                tmp_path, m110_bank_in=saved["report_path"],
                benchmark_out=str(tmp_path / "other.json"), **kw
            ))


def test_reuse_of_simulated_google_bank_requires_no_key(tmp_path, monkeypatch):
    import surlife.m110 as m110
    fake = run_m110(opts(tmp_path))
    report = json.loads((tmp_path / "m110.json").read_text())
    report["manifest"]["provider"] = "google"
    report["manifest"]["requested_model"] = "gemini-3.8-flash"
    report["manifest"]["generation"]["max_output_tokens"] = 4096
    for sample in report["bank"]:
        sample["model"] = "gemini-3.8-flash"
    recreated = _assemble(report["manifest"], report["bank"])
    path = tmp_path / "sampled-google.json"
    path.write_text(json.dumps(recreated))
    monkeypatch.setattr(m110, "_gateway", lambda *_: (_ for _ in ()).throw(
        AssertionError("not allowed to connect while reusing a bank")
    ))
    answer = run_m110(opts(
        tmp_path, provider="google", model="gemini-3.8-flash",
        max_output_tokens=4096, m110_bank_in=str(path),
        benchmark_out=str(tmp_path / "google-replay.json"),
    ))
    assert answer["verified"]
    assert answer["manifest"]["sampling_mode"] == "reused"


def test_invalid_but_in_range_mask_is_audited_without_silent_fallback(tmp_path, monkeypatch):
    import surlife.m110 as m110

    class AllItems:
        def __init__(self):
            self.calls = 0

        def ask(self, messages, **kwargs):
            self.calls += 1
            count = len(json.loads(messages[-1]["content"])["task"]["items"])
            return Reply(mask=(1 << count) - 1, soul_update="",
                         model="surlife/fake-model",
                         usage={"prompt_tokens": 0, "completion_tokens": 0,
                                "total_tokens": 0})

    monkeypatch.setattr(m110, "_gateway", lambda _args: AllItems())
    done = run_m110(opts(tmp_path))
    stats = done["summary"]["arms"]
    assert stats["always"]["consultations"] == 4
    assert stats["always"]["invalid"] == 4
    assert stats["always"]["task_score_sum"] == -4
    assert stats["never"]["invalid"] == 0
    assert verify_m110_file(done["report_path"])["verified"]
