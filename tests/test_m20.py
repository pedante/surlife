"""M2.0 persistent habitat economy, simultaneous allocation and replay."""
from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest

from surlife.m20 import (
    ACTIONS, MAX_SOIL, MAX_STOCK, START_ENERGY, START_STOCK,
    PersistentArena, build_report, decide, episode,
    run_m20, verify_m20, verify_m20_file,
)


def test_persistent_resource_choice_changes_following_world():
    # Both worlds receive identical deterministic weather. The difference in
    # next-tick stock and soil comes ONLY from earlier organism actions.
    forest = PersistentArena(17)
    ravaged = PersistentArena(17)
    before = forest.observations()
    good = forest.step({"a": "tend", "b": "rest"})
    bad = ravaged.step({"a": "harvest3", "b": "rest"})
    assert good["before"]["stock"] == bad["before"]["stock"] == START_STOCK
    assert good["weather"] == bad["weather"]
    assert good["after"] != bad["after"]
    assert forest.observations()["a"].soil != ravaged.observations()["a"].soil
    assert forest.observations()["a"].stock != ravaged.observations()["a"].stock
    assert bad["allocation"]["a"] == 3
    assert bad["degradation"] == 1
    assert good["cultivation"] == 1


def test_conserved_energy_and_ecological_bounds_many_seeds():
    for seed in (0, 1, 7, 17, 101):
        for a, b in (("steward", "extractive"),
                     ("opportunist", "rest"),
                     ("extractive", "extractive")):
            records = episode(seed, 48, a, b)
            assert len(records) == 48
            for row in records:
                assert sum(row["before"]["balances"].values()) == 0
                assert sum(row["after"]["balances"].values()) == 0
                assert all(row["after"]["balances"][name] >= 0
                           for name in ("a", "b"))
                assert 0 <= row["after"]["stock"] <= MAX_STOCK
                assert 0 <= row["after"]["soil"] <= MAX_SOIL
                assert sum(row["allocation"].values()) <= row["before"]["stock"]
                assert row["after"]["stock"] == (
                    row["before"]["stock"]
                    - sum(row["allocation"].values()) + row["regrown"])
                assert sum(transfer["amount"] for transfer in row["transfers"]
                           if transfer["kind"] == "forage_reward") == sum(
                    row["allocation"][actor]
                    * (3 if row["actions"][actor] == "harvest1" else 2)
                    for actor in ("a", "b"))
            for actor in ("a", "b"):
                deaths = [i for i, row in enumerate(records)
                          if not row["alive"][actor]]
                if deaths:
                    first = deaths[0]
                    assert all(not row["alive"][actor]
                               for row in records[first:])


def test_action_preflight_is_atomic_and_dead_cannot_act():
    arena = PersistentArena(0)
    old = (arena.tick, dict(arena.balances), arena.stock, arena.soil)
    with pytest.raises(ValueError, match="one reviewed action"):
        arena.step({"a": "FORAGE", "b": "rest"})
    with pytest.raises(ValueError, match="one reviewed action"):
        arena.step({"a": "tend"})
    with pytest.raises(ValueError, match="one reviewed action"):
        arena.step({"a": True, "b": "rest"})
    assert (arena.tick, arena.balances, arena.stock, arena.soil) == old
    arena.balances["a"] = 1
    arena.balances["world"] += START_ENERGY - 1
    before = (arena.tick, dict(arena.balances), arena.stock, arena.soil)
    with pytest.raises(ValueError, match="unaffordable"):
        arena.step({"a": "tend", "b": "rest"})
    assert (arena.tick, arena.balances, arena.stock, arena.soil) == before
    arena.balances["a"] = 0
    arena.balances["world"] += 1
    with pytest.raises(ValueError, match="dead"):
        arena.step({"a": "harvest1", "b": "rest"})


def test_simultaneous_scarce_resource_allocation_rotates_priority():
    arena = PersistentArena(0)
    arena.stock = 1
    one = arena.step({"a": "harvest1", "b": "harvest1"})
    assert one["allocation"] == {"a": 1, "b": 0}
    arena.stock = 1
    two = arena.step({"a": "harvest1", "b": "harvest1"})
    assert two["allocation"] == {"a": 0, "b": 1}
    another = PersistentArena(1)
    another.stock = 1
    first = another.step({"a": "harvest1", "b": "harvest1"})
    assert first["allocation"] == {"a": 0, "b": 1}


def test_no_action_leaks_future_weather_or_competitor_private_state():
    obs = PersistentArena(17).observations()
    assert set(vars(obs["a"])) == {
        "tick", "weather", "stock", "soil", "own_energy"}
    assert vars(obs["a"]) == vars(obs["b"])
    for policy in ("extractive", "steward", "opportunist", "rest"):
        assert decide(policy, obs["a"]) in ACTIONS
    with pytest.raises(ValueError, match="unknown"):
        decide("malicious_python", obs["a"])


def test_report_mirrors_policies_and_replays(tmp_path):
    report = build_report(17, 16, "steward", "extractive")
    assert verify_m20(report)["verified"]
    assert report["manifest"]["provider"] == "none"
    assert report["manifest"]["model_calls"] == 0
    assert len(report["episodes"]["primary"]) == 16
    assert len(report["episodes"]["mirror"]) == 16
    assert report["summary"]["sessions"]["primary"]["agents"]["a"]["policy"] == "steward"
    assert report["summary"]["sessions"]["mirror"]["agents"]["a"]["policy"] == "extractive"
    assert report["summary"]["sessions"]["primary"]["agents"]["b"]["policy"] == "extractive"
    assert set(report["summary"]["policy_comparison"]) == {"steward", "extractive"}
    output = tmp_path / "m20.json"
    done = run_m20(Namespace(
        provider="fake", seed=17, ticks=16, m20_a="steward",
        m20_b="extractive", benchmark_out=str(output)))
    assert done["verified"]
    assert verify_m20_file(str(output))["verified"]
    assert json.loads(output.read_text())["head"] == report["head"]
    with pytest.raises(ValueError, match="exists"):
        run_m20(Namespace(
            provider="fake", seed=17, ticks=16, m20_a="steward",
            m20_b="extractive", benchmark_out=str(output)))


def test_replay_detects_falsified_ecology_transfer_action_and_digest():
    report = build_report(19, 8, "steward", "opportunist")
    corruptions = [
        ("episodes", "primary", 0, "allocation", "a"),
        ("episodes", "primary", 0, "after", "stock"),
        ("episodes", "mirror", 1, "after", "soil"),
        ("episodes", "primary", 0, "actions", "a"),
    ]
    for path in corruptions:
        changed = copy.deepcopy(report)
        cursor = changed
        for key in path[:-1]:
            cursor = cursor[key]
        old = cursor[path[-1]]
        cursor[path[-1]] = ("rest" if old != "rest" else "harvest1") if isinstance(old, str) else old + 1
        with pytest.raises(ValueError, match="replay"):
            verify_m20(changed)
    changed = copy.deepcopy(report)
    changed["summary"]["sessions"]["primary"]["final_stock"] += 1
    with pytest.raises(ValueError, match="replay"):
        verify_m20(changed)


def test_validation_boundaries_and_offline_only(tmp_path):
    for seed, ticks in ((-1, 4), (True, 4), (17, 0), (17, 257), (17, True)):
        with pytest.raises(ValueError):
            build_report(seed, ticks, "steward", "extractive")
    with pytest.raises(ValueError, match="unknown"):
        build_report(17, 4, "python_code", "extractive")
    with pytest.raises(ValueError, match="offline only"):
        run_m20(Namespace(
            provider="google", seed=17, ticks=4, m20_a="steward",
            m20_b="extractive",
            benchmark_out=str(tmp_path / "never.json")))
    assert not (tmp_path / "never.json").exists()
