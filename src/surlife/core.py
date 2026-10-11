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
RULES_VERSION = "m0-v2"
START_ENERGY = 30
STAKE = 2
COGNITION_COST = 1


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

    def step(self, actions: dict[str, Action], consultations: dict[str, int] | None = None) -> dict:
        """Settle work independently; a duel is optional. Only the referee moves energy."""
        if set(actions) != set(AGENTS) or any(not isinstance(v, Action) for v in actions.values()):
            raise ValueError("exactly one Action required for each actor")
        consultations = consultations or {}
        if any(a not in AGENTS or type(n) is not int or n not in (0, 1) for a, n in consultations.items()):
            raise ValueError("consultations must be 0/1 per actor")
        start = dict(self.balances)
        active = {a: start[a] > 0 for a in AGENTS}
        task, weather = self._puzzle()
        # Prevalidate affordability so a failed call never half-mutates the world.
        upkeep_due = {"normal": 1, "fog": 2, "drought": 3}[weather]
        for a, n in consultations.items():
            if n:
                possible = max(0, start[a] + (1 if self.tick % 4 == 0 and active[a] else 0) - upkeep_due)
                if not active[a] or possible < COGNITION_COST:
                    raise ValueError("consultation not affordable after upkeep")
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

        # Actors that start a tick at zero remain dead: no passive resurrection.
        if self.tick % 4 == 0:
            for a in AGENTS:
                if active[a]:
                    move(WORLD, a, 1, "mint")
        upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
        for a in AGENTS:
            if active[a]:
                move(a, WORLD, min(upkeep, self.balances[a]), "upkeep")
        for a in AGENTS:
            if consultations.get(a, 0):
                if not active[a] or self.balances[a] < COGNITION_COST:
                    raise ValueError("consultation not affordable after upkeep")
                move(a, WORLD, COGNITION_COST, "cognition")

        # Each task earns its own world payment, even if the opponent waits or dies.
        scores: dict[str, int | None] = {a: None for a in AGENTS}
        rewards = {a: 0 for a in AGENTS}
        attempted = {a: active[a] and actions[a].mask is not None for a in AGENTS}
        for a in AGENTS:
            if not attempted[a]:
                continue
            score = task.score(actions[a].mask)
            scores[a] = score
            reward = (3 if score == task.optimum else
                      2 if score >= 0 and 5 * score >= 4 * task.optimum else
                      1 if score > 0 else 0)
            rewards[a] = reward
            move(WORLD, a, reward, "work_reward")

        entered = all(attempted[a] and self.balances[a] >= self.stake for a in AGENTS)
        winner: str | None = None
        if entered:
            for a in AGENTS:
                move(a, ESCROW, self.stake, "stake")
            if scores["a"] != scores["b"]:
                winner = "a" if scores["a"] > scores["b"] else "b"
                move(ESCROW, winner, self.stake * 2, "win")
            else:
                for a in AGENTS:
                    move(ESCROW, a, self.stake, "refund")

        if sum(self.balances.values()) != 0 or any(self.balances[a] < 0 for a in (*AGENTS, ESCROW)):
            raise AssertionError("ledger conservation failure")
        result = {
            "tick": self.tick, "weather": weather, "task": task.as_dict(),
            "optimal_score": task.optimum,
            "actions": {a: actions[a].mask for a in AGENTS},
            "consultations": {a: consultations.get(a, 0) for a in AGENTS},
            "attempted": attempted, "scores": scores, "rewards": rewards,
            "alive": {a: self.balances[a] > 0 for a in AGENTS},
            "winner": winner, "entered": entered,
            "before": start, "after": dict(self.balances), "transfers": transfers,
        }
        self.tick += 1
        return result


def choose_actions(arena: Arena, names: dict[str, str]) -> dict[str, Action]:
    obs = arena.observations()
    for a in AGENTS:
        if names[a] not in POLICIES:
            raise ValueError(f"unknown policy: {names[a]}")
    # Independent deterministic policy RNG; no policy gets the opponent's memory.
    return {a: (POLICIES[names[a]](obs[a], Random(arena.seed * 1_000_003 + arena.tick * 9_176 + (1 if a == "a" else 2))) if obs[a].own_energy else Action(None)) for a in AGENTS}
