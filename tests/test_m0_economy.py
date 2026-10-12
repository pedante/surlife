"""M0-v2 economy regression tests: useful work sustains an individual actor."""
from surlife.core import Action, Arena, COGNITION_COST, choose_actions
from surlife.storage import Journal
from surlife.core import RULES_VERSION, START_ENERGY, STAKE


def test_individual_work_survives_opponent_wait():
    arena = Arena(seed=7)
    for _ in range(30):
        actions = choose_actions(arena, {"a": "optimal", "b": "wait"})
        record = arena.step(actions)
        assert record["attempted"]["a"]
        assert not record["attempted"]["b"]
        assert record["scores"]["a"] == record["optimal_score"]
        assert record["rewards"]["a"] == 3
        assert not record["entered"]
        assert sum(record["after"].values()) == 0
    assert arena.balances["a"] > 0
    assert arena.balances["b"] == 0


def test_dead_actor_cannot_collect_or_revive():
    arena = Arena(seed=4, energy=1)
    for _ in range(5):
        record = arena.step({"a": Action(None), "b": Action(None)})
    assert arena.balances["a"] == 0
    later = arena.step({"a": Action(0), "b": Action(0)})
    assert not later["attempted"]["a"]
    assert later["rewards"]["a"] == 0


def test_consultation_is_metered_and_replayable(tmp_path):
    arena = Arena(seed=8)
    with Journal(tmp_path / "journal.sqlite") as db:
        db.create_run("m0-v2", {"rules": RULES_VERSION, "seed": 8, "start_energy": START_ENERGY,
                                "stake": STAKE, "policies": {"a": "optimal", "b": "wait"}})
        record = arena.step({"a": Action(0), "b": Action(None)}, consultations={"a": 1})
        db.append("m0-v2", record)
        assert sum(t["amount"] for t in record["transfers"] if t["kind"] == "cognition") == COGNITION_COST
        result = db.replay("m0-v2")
        assert result["consultations"]["a"] == 1
        assert result["attempts"] == {"a": 1, "b": 0}
        assert result["verified"]
