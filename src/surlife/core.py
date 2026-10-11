"""Pure deterministic two-organism arena with a separately conserved virtual ledger.

No LLM calls, dynamically loaded organism Python, network or secret access are
required. Policies are pre-installed trusted functions; self-modification is NOT
implemented. An arena tick is a synchronous snapshot -> choices -> settle step.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Callable

AGENTS = ("a", "b")
WORLD = "world"
ESCROW = "escrow"
RULES_VERSION = "m0-v1"
START_ENERGY = 30
STAKE = 2


@dataclass(frozen=True)
class Task:
    items: tuple[tuple[int, int], ...]  # (cost, reward)
    capacity: int

    def score(self, mask: int) -> int:
        """Return -1 for invalid actions, else reward of selected subset."""
        if type(mask) is not int or mask < 0 or mask >= (1 << len(self.items)):
            return -1
        cost = sum(c for i, (c, _) in enumerate(self.items) if mask & (1 << i))
        if cost > self.capacity:
            return -1
        return sum(v for i, (_, v) in enumerate(self.items) if mask & (1 << i))

    @property
    def optimum(self) -> int:
        return max(self.score(mask) for mask in range(1 << len(self.items)))

    def as_dict(self) -> dict:
        return {"items": [list(item) for item in self.items], "capacity": self.capacity}


@dataclass(frozen=True)
class Observation:
    tick: int
    weather: str
    task: Task
    own_energy: int


@dataclass(frozen=True)
class Action:
    mask: int | None  # None means wait; all integers validated by the referee


Policy = Callable[[Observation, Random], Action]


def optimal(obs: Observation, rng: Random) -> Action:
    del rng
    return Action(max(range(1 << len(obs.task.items)), key=lambda m: (obs.task.score(m), -m)))


def greedy(obs: Observation, rng: Random) -> Action:
    del rng
    # Predictable imperfect ratio heuristic. Selection is still capacity-safe.
    mask, remaining = 0, obs.task.capacity
    order = sorted(range(len(obs.task.items)),
                   key=lambda i: (-obs.task.items[i][1] / obs.task.items[i][0], i))
    for i in order:
        cost, _ = obs.task.items[i]
        if cost <= remaining:
            mask |= 1 << i
            remaining -= cost
    return Action(mask)


def random_policy(obs: Observation, rng: Random) -> Action:
    legal = [m for m in range(1 << len(obs.task.items)) if obs.task.score(m) >= 0]
    return Action(rng.choice(legal))


def wait(obs: Observation, rng: Random) -> Action:
    del obs, rng
    return Action(None)


POLICIES: dict[str, Policy] = {"optimal": optimal, "greedy": greedy, "random": random_policy, "wait": wait}


class Arena:
    """Single-writer referee; actors cannot call transfer or select hidden tasks."""

    def __init__(self, seed: int, energy: int = START_ENERGY, stake: int = STAKE):
        if type(seed) is not int or seed < 0 or type(energy) is not int or energy < 0:
            raise ValueError("seed/energy must be nonnegative integers")
        if type(stake) is not int or stake <= 0:
            raise ValueError("stake must be a positive integer")
        self.seed = seed
        self.stake = stake
        self.tick = 0
        self.balances = {"a": energy, "b": energy, WORLD: -2 * energy, ESCROW: 0}

    def _puzzle(self) -> tuple[Task, str]:
        # This stream depends only on seed and tick, not scheduling or actions.
        r = Random(self.seed * 1_000_003 + self.tick * 9_176 + 17)
        task = Task(tuple((r.randint(1, 7), r.randint(1, 14)) for _ in range(5)), r.randint(7, 13))
        return task, r.choice(("normal", "fog", "drought"))

    def observations(self) -> dict[str, Observation]:
        task, weather = self._puzzle()
        return {a: Observation(self.tick, weather, task, self.balances[a]) for a in AGENTS}

    def step(self, actions: dict[str, Action]) -> dict:
        """Deterministic synchronous settlement; account movements are double-entry.

        Invalid submitted masks lose to any legal mask. There are no LLMs, hidden
        rewards to query, asynchronous deadlines, weather purchases or code edits.
        """
        if set(actions) != set(AGENTS) or any(not isinstance(v, Action) for v in actions.values()):
            raise ValueError("exactly one Action required for each actor")
        start = dict(self.balances)
        task, weather = self._puzzle()
        transfers: list[dict] = []

        def move(src: str, dst: str, amount: int, kind: str) -> None:
            if type(amount) is not int or amount < 0:
                raise ValueError("invalid transfer")
            if src != WORLD and self.balances[src] < amount:
                raise AssertionError("unfunded transfer")
            self.balances[src] -= amount
            self.balances[dst] += amount
            if amount:
                transfers.append({"from": src, "to": dst, "amount": amount, "kind": kind})

        # Phase 1: periodic world mint, followed by maintenance (both deterministic).
        if self.tick % 4 == 0:
            for actor in AGENTS:
                move(WORLD, actor, 1, "mint")
        upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
        for actor in AGENTS:
            move(actor, WORLD, min(upkeep, self.balances[actor]), "upkeep")

        # Phase 2: both must enter and afford equal escrowed stakes.
        entered = all(actions[a].mask is not None and self.balances[a] >= self.stake for a in AGENTS)
        scores: dict[str, int | None] = {a: None for a in AGENTS}
        winner: str | None = None
        if entered:
            for actor in AGENTS:
                move(actor, ESCROW, self.stake, "stake")
                scores[actor] = task.score(actions[actor].mask)
            if scores["a"] != scores["b"]:
                winner = "a" if scores["a"] > scores["b"] else "b"
                move(ESCROW, winner, self.stake * 2, "win")
            else:
                for actor in AGENTS:
                    move(ESCROW, actor, self.stake, "refund")

        if sum(self.balances.values()) != 0 or any(self.balances[a] < 0 for a in (*AGENTS, ESCROW)):
            raise AssertionError("ledger conservation failure")
        result = {
            "tick": self.tick,
            "weather": weather,
            "task": task.as_dict(),
            "optimal_score": task.optimum,
            "actions": {a: actions[a].mask for a in AGENTS},
            "scores": scores,
            "winner": winner,
            "entered": entered,
            "before": start,
            "after": dict(self.balances),
            "transfers": transfers,
        }
        self.tick += 1
        return result


def choose_actions(arena: Arena, names: dict[str, str]) -> dict[str, Action]:
    obs = arena.observations()
    for a in AGENTS:
        if names[a] not in POLICIES:
            raise ValueError(f"unknown policy: {names[a]}")
    # Independent deterministic policy RNG; no policy gets the opponent's memory.
    return {a: POLICIES[names[a]](obs[a], Random(arena.seed * 1_000_003 + arena.tick * 9_176 + (1 if a == "a" else 2))) for a in AGENTS}
