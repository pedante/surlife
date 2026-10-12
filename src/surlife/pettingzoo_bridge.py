"""Optional PettingZoo ParallelEnv bridge for the trusted Surlife task referee.

E01-W02 evaluation only. PettingZoo owns NO account, mutation, LLM, score,
secret, RNG for referee rules, or privilege. The NativeTaskArena remains the
sole world-state/ledger writer. This adapter exposes it as an external RL API.

Install with: pip install -e '.[pettingzoo]'
Pin of tested PettingZoo API: 1.27.0, commit 7221e4b15873a8b16555fda038a77a6ae595e88d.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import spaces
from pettingzoo.utils.env import ParallelEnv

from surlife.core import Action, WORLD, ESCROW
from surlife.population import (
    MAX_AGENTS, MAX_TICKS, MAX_WORK, NativeTaskArena,
)

# The five-item native M0 challenge has masks 0..31; 32 is WAIT (Action(None)).
# Surlife's actual referee independently validates & scores submitted masks.
WAIT_ACTION = 32
WEATHERS = {"normal": 0, "fog": 1, "drought": 2}


class SurlifeParallelEnv(ParallelEnv[str, dict[str, Any], int]):
    """Adapter OUT from Surlife to PettingZoo, never a new referee."""

    metadata = {
        "name": "surlife_task_parallel_v0",
        "render_modes": [],
        "is_parallelizable": True,
    }

    def __init__(
        self, population: int = 2, seed: int = 17, *,
        max_cycles: int = 32, duel: bool = True,
    ):
        if type(population) is not int or not 2 <= population <= MAX_AGENTS:
            raise ValueError("population must be in 2..128")
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be nonnegative")
        if type(max_cycles) is not int or not 1 <= max_cycles <= MAX_TICKS:
            raise ValueError("max_cycles must be in 1..512")
        if population * max_cycles > MAX_WORK:
            raise ValueError("simulation exceeds 4,096 organism ticks")
        self.population = population
        self.initial_seed = seed
        self.seed = seed
        self.duel = duel
        self.max_cycles = max_cycles
        self.possible_agents = [
            f"org-{i:04d}" for i in range(1, population + 1)
        ]
        self.agents: list[str] = []
        # Spaces are created only once and do not change with episode state.
        self.action_spaces = {
            agent: spaces.Discrete(WAIT_ACTION + 1)
            for agent in self.possible_agents
        }
        self.observation_spaces = {
            agent: spaces.Dict({
                "items": spaces.Box(low=0, high=100, shape=(5, 2), dtype=np.int64),
                "capacity": spaces.Discrete(100),
                "weather": spaces.Discrete(len(WEATHERS)),
                "own_energy": spaces.Box(
                    low=0, high=2**31 - 1, shape=(1,), dtype=np.int64
                ),
                "tick": spaces.Discrete(MAX_TICKS + 1),
            }) for agent in self.possible_agents
        }
        self.referee: NativeTaskArena | None = None
        self.last_record: dict | None = None

    def action_space(self, agent: str) -> spaces.Discrete:
        return self.action_spaces[agent]

    def observation_space(self, agent: str) -> spaces.Dict:
        return self.observation_spaces[agent]

    def _view(self, actor: str, observation) -> dict[str, Any]:
        return {
            "items": np.asarray(observation.task.items, dtype=np.int64),
            "capacity": int(observation.task.capacity),
            "weather": WEATHERS[observation.weather],
            "own_energy": np.asarray([observation.own_energy], dtype=np.int64),
            "tick": int(observation.tick),
        }

    def reset(
        self, seed: int | None = None, options: dict | None = None
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict]]:
        del options
        self.seed = self.initial_seed if seed is None else seed
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("reset seed must be nonnegative")
        if self.population * self.max_cycles > MAX_WORK:
            raise ValueError("reset would exceed 4,096 organism ticks")
        ids = tuple(self.possible_agents)
        self.referee = NativeTaskArena(self.seed, ids, duel=self.duel)
        self.agents = list(ids)
        self.last_record = None
        observations = self.referee.observations()
        return ({agent: self._view(agent, observations[agent])
                 for agent in self.agents},
                {agent: {} for agent in self.agents})

    def step(
        self, actions: dict[str, int]
    ) -> tuple[
        dict[str, dict[str, Any]], dict[str, float],
        dict[str, bool], dict[str, bool], dict[str, dict],
    ]:
        if self.referee is None or not self.agents:
            raise ValueError("call reset() first; cannot step finished episode")
        if not isinstance(actions, dict) or set(actions) != set(self.agents):
            raise ValueError("one valid action per active organism required")
        # Gymnasium Discrete.sample() returns numpy.integer scalars.
        # Normalize these at the boundary, while rejecting bool, floats,
        # arrays and out-of-range values before the referee is mutated.
        if any(isinstance(value, (bool, np.bool_)) or
               not isinstance(value, (int, np.integer)) or
               not 0 <= value <= WAIT_ACTION
               for value in actions.values()):
            raise ValueError("invalid PettingZoo action value")
        actions = {agent: int(value) for agent, value in actions.items()}
        previous = list(self.agents)
        # Capture CURRENT observations. An organism that dies in this step
        # must not receive the following (still hidden) task in its final view.
        previous_views = self.referee.observations()
        # Every non-active participant remains dead in the inner referee.
        admitted = {
            agent: (Action(None) if agent not in actions or
                    actions[agent] == WAIT_ACTION else Action(actions[agent]))
            for agent in self.possible_agents
        }
        result = self.referee.step(admitted)
        self.last_record = result  # inspectable by the experiment controller only
        exhausted = self.referee.tick >= self.max_cycles
        # Returned rewards are actual net ENERGY changes including upkeep,
        # mint, objective task reward and duels; never a separate minted account.
        rewards = {
            agent: float(result["after"][agent] - result["before"][agent])
            for agent in previous
        }
        terminations = {
            agent: not result["alive"][agent] for agent in previous
        }
        truncations = {
            agent: bool(exhausted and not terminations[agent])
            for agent in previous
        }
        infos = {
            agent: {
                "score": result["scores"][agent],
                "task_reward": result["rewards"][agent],
                "energy_after": result["after"][agent],
                "tick": result["tick"],
            } for agent in previous
        }
        self.agents = [
            agent for agent in previous
            if not (terminations[agent] or truncations[agent])
        ]
        next_observations = self.referee.observations() if self.agents else {}
        # PettingZoo returns terminal observations for agents exiting this
        # step. Keep their prior view rather than leaking the next hidden task.
        observations = {
            agent: self._view(agent, next_observations[agent])
            if agent in self.agents else self._view(agent, previous_views[agent])
            for agent in previous
        }
        return observations, rewards, terminations, truncations, infos

    def render(self):
        return None

    def close(self):
        return None
