"""population-v1: multi-organism contracts, interchangeable arenas and replay."""
from __future__ import annotations

import copy
import json
from argparse import Namespace
from random import Random

import pytest

from surlife.core import Action, Arena, greedy, optimal
from surlife.m20 import PersistentArena, decide
from surlife.population import (
    ARENAS, HABITAT_CONTRACT, TASK_CONTRACT, BuiltinOrganism, LegacyM0Adapter,
    LegacyM20Adapter, NativeTaskArena, OrganismSpec, PopulationSession,
    _round_robin, build_report, make_arena, make_specs, run_population,
    verify_file, verify_report,
)


@pytest.mark.parametrize("population", [2, 3, 4, 5, 8, 16, 64, 128])
@pytest.mark.parametrize("arena", ["task-duel", "task-work"])
def test_multiple_population_sizes_with_ledger_and_replay(population, arena):
    brains = tuple(("greedy", "optimal", "random", "wait")[i % 4]
                   for i in range(population))
    report = build_report(17, max(2, min(16, 2048 // population)), arena, brains)
    assert verify_report(report)["verified"]
    assert report["summary"]["population"] == population
    assert report["summary"]["actual_provider_calls"] == 0
    assert report["summary"]["actual_provider_tokens"] == 0
    for event in report["events"]:
        raw = event["referee"]
        assert len(event["energy"]) == population
        assert len(raw["actions"]) == population
        assert sum(raw["before"].values()) == 0
        assert sum(raw["after"].values()) == 0
        assert raw["after"]["escrow"] == 0
        assert all(x >= 0 for x in event["energy"].values())
        assert all(t["amount"] >= 0 for t in raw["transfers"])
        if arena == "task-work":
            assert raw["pairs"] == []
        else:
            assert len(raw["pairs"]) == population // 2


def test_native_two_agent_referee_matches_original_m0_exactly():
    ids = ("org-0001", "org-0002")
    native = NativeTaskArena(17, ids)
    original = Arena(17)
    for tick in range(32):
        no = native.observations()
        old = original.observations()
        acts = {
            ids[0]: greedy(no[ids[0]], Random(0)),
            ids[1]: optimal(no[ids[1]], Random(0)),
        }
        actual = native.step(acts)
        original_row = original.step({
            "a": greedy(old["a"], Random(0)),
            "b": optimal(old["b"], Random(0)),
        })
        assert actual["weather"] == original_row["weather"]
        assert actual["task"] == original_row["task"]
        assert actual["optimal_score"] == original_row["optimal_score"]
        assert actual["scores"][ids[0]] == original_row["scores"]["a"]
        assert actual["scores"][ids[1]] == original_row["scores"]["b"]
        assert actual["rewards"][ids[0]] == original_row["rewards"]["a"]
        assert actual["rewards"][ids[1]] == original_row["rewards"]["b"]
        assert actual["after"][ids[0]] == original_row["after"]["a"]
        assert actual["after"][ids[1]] == original_row["after"]["b"]
        assert actual["after"]["world"] == original_row["after"]["world"]
        assert actual["after"]["escrow"] == original_row["after"]["escrow"]


def test_legacy_m0_adapter_wraps_original_without_changing_rules():
    ids = ("indigo", "amber")
    adapted = LegacyM0Adapter(23, ids)
    original = Arena(23)
    for tick in range(24):
        chosen = {
            ids[0]: greedy(adapted.observations()[ids[0]], Random(0)),
            ids[1]: optimal(adapted.observations()[ids[1]], Random(0)),
        }
        native = original.observations()
        expected = original.step({
            "a": greedy(native["a"], Random(0)),
            "b": optimal(native["b"], Random(0)),
        })
        actual = adapted.step(chosen)
        assert actual["after"][ids[0]] == expected["after"]["a"]
        assert actual["after"][ids[1]] == expected["after"]["b"]
        assert actual["winner"] == (
            {"a": ids[0], "b": ids[1]}.get(expected["winner"])
        )
        assert actual["pairs"][0]["winner"] == actual["winner"] if actual["entered"] else actual["pairs"] == []
        assert all(x["from"] not in ("a", "b") and
                   x["to"] not in ("a", "b") for x in actual["transfers"])


def test_legacy_m20_works_via_same_controller_without_becoming_default():
    report = build_report(17, 16, "legacy-m20", ("steward", "extractive"))
    assert verify_report(report)["verified"]
    for event in report["events"]:
        raw = event["referee"]
        assert "stock" in raw["before"] and "soil" in raw["after"]
        assert sum(raw["after"]["balances"].values()) == 0
        assert raw["actions"]["org-0001"] in ("rest", "tend", "harvest1", "harvest3")
    assert report["manifest"]["arena"] == "legacy-m20"
    assert report["summary"]["population"] == 2


def test_legacy_m20_adapter_does_not_admit_paid_llm_calls():
    adapter = LegacyM20Adapter(17, ("first", "second"))
    with pytest.raises(ValueError, match="does not support"):
        adapter.step({"first": "rest", "second": "rest"},
                     {"first": 1})
    assert adapter.tick == 0


def test_step_controller_is_pausable_without_time_dependency():
    specs = make_specs(("greedy", "optimal", "random", "wait", "greedy"))
    session = PopulationSession(seed=7, arena_name="task-duel", organisms=specs)
    assert session.arena.tick == 0
    first = session.step()
    assert session.arena.tick == 1
    assert len(session.events) == 1
    assert first["previous_hash"] == build_report(7, 1, "task-duel",
                                                   tuple(s.brain for s in specs))["events"][0]["previous_hash"]
    # The event/history isn't changed while a web UI is paused.
    before = json.dumps(session.report(), sort_keys=True)
    assert json.dumps(session.report(), sort_keys=True) == before
    second = session.step()
    assert second["previous_hash"] == first["event_hash"]
    assert verify_report(session.report())["verified"]


def test_round_robin_pairs_cover_every_opponent_and_rotate_byes():
    ids = tuple(f"org-{i:04d}" for i in range(1, 7))
    pairs = [_round_robin(ids, 9, tick) for tick in range(5)]
    all_pairs = {frozenset(pair) for round_pairs in pairs for pair in round_pairs}
    assert len(all_pairs) == 15  # complete K6 over five rounds
    assert all(len(p) == 3 for p in pairs)
    ids5 = ids[:5]
    rounds = [_round_robin(ids5, 9, tick) for tick in range(5)]
    missing = [
        (set(ids5) - {x for pair in round_pairs for x in pair}).pop()
        for round_pairs in rounds
    ]
    assert len(set(missing)) == 5


def test_actor_random_stream_is_stable_across_population_size():
    b4 = build_report(37, 8, "task-work",
                      ("random", "greedy", "optimal", "wait"))
    b8 = build_report(37, 8, "task-work",
                      ("random", "greedy", "optimal", "wait",
                       "greedy", "greedy", "greedy", "greedy"))
    for first, second in zip(b4["events"], b8["events"]):
        assert first["referee"]["actions"]["org-0001"] == \
               second["referee"]["actions"]["org-0001"]


def test_frozen_isolated_organism_memories_and_sandbox_boundary():
    specs = make_specs(("greedy", "random", "wait"))
    session = PopulationSession(seed=17, arena_name="task-work", organisms=specs)
    for i in range(15):
        session.step()
    assert all(len(b.recent_outcomes) == 8 for b in session.brains.values())
    assert session.brains["org-0001"].recent_outcomes is not \
           session.brains["org-0002"].recent_outcomes
    assert all(set(x) == {"tick", "score", "reward", "energy_after"}
               for agent in session.brains.values() for x in agent.recent_outcomes)
    assert all("code" not in x and "api_key" not in x
               for event in session.events for x in event)
    assert all(s["genome_hash"] == specs[i].genome_hash
               for i, s in enumerate(session.report()["manifest"]["organisms"]))


def test_bad_actions_fail_before_mutating_world():
    native = NativeTaskArena(0, ("foo", "bar", "baz"))
    before = (native.tick, dict(native.balances))
    with pytest.raises(ValueError, match="one submitted"):
        native.step({"foo": Action(1), "bar": Action(1)})
    with pytest.raises(ValueError, match="structured Action"):
        native.step({"foo": Action(1), "bar": "anything", "baz": Action(2)})
    with pytest.raises(ValueError, match="consultation"):
        native.step({a: Action(None) for a in native.ids}, {"foo": 2})
    assert (native.tick, native.balances) == before


def test_not_resurrecting_agents_at_zero_and_no_negative_balances():
    arena = NativeTaskArena(0, ("foo", "bar", "baz"), duel=True)
    arena.balances["foo"] = 0
    arena.balances[WORLD] += 30
    before = arena.balances["foo"]
    for _ in range(8):
        arena.step({actor: Action(1) for actor in arena.ids})
        assert arena.balances["foo"] == before == 0
        assert sum(arena.balances.values()) == 0


@pytest.mark.parametrize("arena,brains", [
    ("legacy-m0", ("greedy", "optimal", "random")),
    ("legacy-m20", ("steward", "extractive", "rest")),
    ("task-duel", ("steward", "greedy")),
    ("legacy-m20", ("greedy", "optimal")),
    ("not-an-arena", ("greedy", "optimal")),
])
def test_refuse_unsupported_or_mismatched_arena_and_brains(arena, brains):
    with pytest.raises(ValueError):
        build_report(17, 6, arena, brains)


@pytest.mark.parametrize("brain", ["", "bad", "python:/tmp/evil.py", "llm"])
def test_do_not_import_arbitrary_organism_code(brain):
    with pytest.raises(ValueError, match="unknown or untrusted"):
        make_specs(("greedy", brain))


def test_manifest_event_or_balances_forgery_is_rejected():
    report = build_report(17, 12, "task-duel",
                          ("greedy", "optimal", "random", "wait"))
    mutations = [
        lambda r: r["events"][2]["energy"].__setitem__("org-0001", 900),
        lambda r: r["manifest"]["organisms"][0].__setitem__("genome_hash", "bad"),
        lambda r: r["events"][5].__setitem__("event_hash", "forged"),
        lambda r: r["events"][5]["referee"]["actions"].__setitem__("org-0002", 999),
        lambda r: r["summary"].__setitem__("survivors", 999),
    ]
    for mutate in mutations:
        changed = copy.deepcopy(report)
        mutate(changed)
        with pytest.raises(ValueError, match="mismatch"):
            verify_report(changed)


def test_file_and_cli_offline_smoke(tmp_path):
    out = tmp_path / "population.json"
    args = Namespace(
        seed=17, ticks=12, provider="fake", benchmark_out=str(out),
        population=8, population_brains="greedy,optimal,random,wait",
        population_arena="task-duel",
    )
    result = run_population(args)
    assert result["verified"]
    assert verify_file(str(out))["verified"]
    with pytest.raises(ValueError, match="overwrite"):
        run_population(args)
    args.provider = "openrouter"
    args.benchmark_out = str(tmp_path / "provider.json")
    with pytest.raises(ValueError, match="offline"):
        run_population(args)
    assert not (tmp_path / "provider.json").exists()


@pytest.mark.parametrize("n,ticks", [(1,2),(129,1),(128,33),(2,513)])
def test_population_size_and_work_caps(n, ticks):
    brains = tuple("greedy" for _ in range(n))
    with pytest.raises(ValueError):
        build_report(7, ticks, "task-duel", brains)
