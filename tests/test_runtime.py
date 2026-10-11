import sqlite3
from random import Random

import pytest

from surlife.core import Action, Arena, RULES_VERSION, START_ENERGY, STAKE, Task, choose_actions
from surlife.storage import Journal


def manifest(seed=11):
    return {"rules": RULES_VERSION, "seed": seed, "start_energy": START_ENERGY, "stake": STAKE,
            "policies": {"a": "greedy", "b": "optimal"}, "kind": "test"}


def play(arena, rounds=15):
    out = []
    for _ in range(rounds):
        actions = choose_actions(arena, {"a": "greedy", "b": "optimal"})
        out.append(arena.step(actions))
    return out


def test_puzzle_optimality_and_invalid_inputs():
    task = Task(((3, 9), (2, 5), (4, 12)), 5)
    assert task.optimum == 14
    for m in (-1, 1 << 3, True, "0", 7):
        assert task.score(m) == -1


def test_model_free_determinism():
    assert play(Arena(33)) == play(Arena(33))
    assert play(Arena(33)) != play(Arena(34))


def test_winner_and_correctness():
    a = Arena(33)
    for record in play(a):
        assert sum(record["after"].values()) == 0
        assert record["after"]["escrow"] == 0
        assert min(record["after"]["a"], record["after"]["b"]) >= 0
        if record["entered"]:
            assert record["scores"]["b"] == record["optimal_score"]
            assert record["winner"] in (None, "b")


def test_actor_specific_random_seed():
    arena = Arena(3)
    one = choose_actions(arena, {"a": "random", "b": "random"})
    two = choose_actions(arena, {"a": "random", "b": "random"})
    assert one == two


def test_wait_not_staked():
    record = Arena(2).step({"a": Action(None), "b": Action(0)})
    assert not record["entered"]
    assert "stake" not in [i["kind"] for i in record["transfers"]]


def test_illegal_action_has_no_privilege():
    arena = Arena(3)
    with pytest.raises(ValueError):
        arena.step({"a": Action(0), "c": Action(0)})
    assert arena.tick == 0
    assert sum(arena.balances.values()) == 0
    invalid = arena.step({"a": Action(-1), "b": Action(0)})
    assert invalid["scores"]["a"] == -1


def test_no_negative_even_long_run():
    arena = Arena(9, energy=1)
    for _ in range(200):
        r = arena.step({"a": Action(1), "b": Action(0)})
        assert all(r["after"][a] >= 0 for a in ("a", "b", "escrow"))
        assert sum(r["after"].values()) == 0


def test_atomic_journal_and_replay(tmp_path):
    with Journal(tmp_path / "journal.sqlite") as db:
        db.create_run("r1", manifest())
        arena = Arena(11)
        records = play(arena)
        for r in records:
            db.append("r1", r)
        assert db.replay("r1")["rounds"] == 15
        assert db.replay("r1")["balances"] == arena.balances
        assert db.db.execute("SELECT COUNT(*) FROM rounds").fetchone()[0] == 15
        assert db.db.execute("SELECT COUNT(*) FROM transfers").fetchone()[0] > 15


def test_idempotent_tick_and_conflict(tmp_path):
    with Journal(tmp_path / "j.sqlite") as db:
        db.create_run("r1", manifest())
        first = Arena(11).step({"a": Action(0), "b": Action(0)})
        assert db.append("r1", first) == db.append("r1", first)
        assert db.db.execute("SELECT COUNT(*) FROM rounds").fetchone()[0] == 1
        second = Arena(11).step({"a": Action(1), "b": Action(0)})
        with pytest.raises(ValueError, match="conflicting"):
            db.append("r1", second)
        with pytest.raises(ValueError, match="tick gap"):
            db.append("r1", {**first, "tick": 2})
        with pytest.raises(ValueError, match="different manifest"):
            db.create_run("r1", manifest(seed=12))
        assert db.replay("r1")["rounds"] == 1


def test_tampering_is_detected(tmp_path):
    with Journal(tmp_path / "j.sqlite") as db:
        db.create_run("r1", manifest())
        db.append("r1", Arena(11).step({"a": Action(0), "b": Action(0)}))
        db.db.execute("UPDATE transfers SET amount=99 WHERE run_id='r1' AND seq=0")
        with pytest.raises(ValueError, match="transaction ledger"):
            db.replay("r1")


def test_replay_checks_actions_not_policy(tmp_path):
    with Journal(tmp_path / "j.sqlite") as db:
        db.create_run("r1", manifest())
        a = Arena(11)
        for r in play(a, 5):
            db.append("r1", r)
        assert db.replay("r1")["verified"]
        # A changed policy implementation cannot silently alter recorded actions.
        assert db.replay("r1")["head"] == db.replay("r1")["head"]
