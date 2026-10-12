"""E01-W02 PettingZoo 1.27.0 real-package evaluation, offline only.

Install optional extras; no model calls, code mutation or world rewriting.
"""
from __future__ import annotations

from random import Random

import pytest

pytest.importorskip("pettingzoo", reason="optional PettingZoo evaluation extra")
np = pytest.importorskip("numpy", reason="numpy belongs to optional PettingZoo extra")
from pettingzoo.test import parallel_api_test
from pettingzoo.utils.env import ParallelEnv

from surlife.core import Action, greedy, optimal
from surlife.population import NativeTaskArena
from surlife.pettingzoo_bridge import SurlifeParallelEnv, WAIT_ACTION


def test_actual_package_parallel_api_compliance():
    env = SurlifeParallelEnv(population=3, max_cycles=25, duel=True)
    assert isinstance(env, ParallelEnv)
    parallel_api_test(env, num_cycles=25)
    env.close()


@pytest.mark.parametrize("n", [2, 3, 4, 8, 16])
@pytest.mark.parametrize("duel", [True, False])
@pytest.mark.parametrize("seed", [0, 17, 101])
def test_identical_native_referee_actions_scores_and_balances(n, duel, seed):
    env = SurlifeParallelEnv(population=n, seed=seed, max_cycles=12, duel=duel)
    observations, infos = env.reset(seed=seed)
    native = NativeTaskArena(seed, tuple(env.possible_agents), duel=duel)
    assert set(observations) == set(env.possible_agents)
    assert len(infos) == n
    for tick in range(12):
        # Comparison uses identical masks for both paths, not model-generated.
        raw_obs = native.observations()
        masks = {}
        actions = {}
        for idx, agent in enumerate(env.possible_agents):
            mask = (greedy if idx % 2 else optimal)(
                raw_obs[agent], Random(idx + 4000 + tick)
            ).mask
            actions[agent] = Action(mask) if agent in env.agents else Action(None)
            if agent in env.agents:
                masks[agent] = mask
        before = dict(native.balances)
        expected = native.step(actions)
        observed, rewards, terminated, truncated, infos = env.step(masks)
        assert env.last_record == expected
        for agent in masks:
            assert rewards[agent] == float(expected["after"][agent] - before[agent])
            assert infos[agent]["task_reward"] == expected["rewards"][agent]
            assert terminated[agent] is (expected["after"][agent] <= 0)
            assert truncated[agent] is (tick == 11 and not terminated[agent])
        assert env.referee.balances == native.balances
        assert sum(env.referee.balances.values()) == 0
        if not env.agents:
            break


def test_spaces_validate_observations_and_action_wait():
    env = SurlifeParallelEnv(population=4, max_cycles=3)
    observations, _ = env.reset(17)
    for agent, obs in observations.items():
        assert env.observation_space(agent).contains(obs)
        assert env.action_space(agent).contains(WAIT_ACTION)
        assert "opponent_energy" not in obs
        assert "balances" not in obs
        assert "api_key" not in obs
        assert obs["items"].shape == (5, 2)
    for i in range(3):
        current = dict.fromkeys(env.agents, WAIT_ACTION)
        obs, rewards, terminated, truncated, infos = env.step(current)
        assert sum(env.referee.balances.values()) == 0
        for agent in current:
            assert rewards[agent] <= 1  # paying upkeep with no work
        if not env.agents:
            break
    assert env.agents == []


def test_terminal_observation_never_discloses_next_hidden_task():
    # A finished organism must not receive a puzzle from tick 1.
    env = SurlifeParallelEnv(population=2, seed=17, max_cycles=1)
    initial, _ = env.reset(seed=17)
    terminal, rewards, terminations, truncations, _ = env.step({
        agent: WAIT_ACTION for agent in env.agents
    })
    assert not env.agents
    assert set(terminal) == set(initial)
    for agent in terminal:
        assert np.array_equal(terminal[agent]["items"], initial[agent]["items"])
        assert terminal[agent]["tick"] == initial[agent]["tick"]
        assert terminations[agent] or truncations[agent]


def test_finished_organism_is_not_resurrected():
    env = SurlifeParallelEnv(population=3, max_cycles=6)
    env.reset()
    # Controlled referee fixture: force one death and balance it from WORLD.
    env.referee.balances["org-0001"] = 0
    env.referee.balances["world"] += 30
    returned, rewards, terminated, truncated, info = env.step({
        name: WAIT_ACTION for name in env.agents
    })
    assert terminated["org-0001"] is True
    assert "org-0001" not in env.agents
    assert sum(env.referee.balances.values()) == 0
    for _ in range(2):
        env.step({name: WAIT_ACTION for name in env.agents})
    assert env.referee.balances["org-0001"] == 0
    with pytest.raises(ValueError, match="one valid action"):
        env.step({**{name: WAIT_ACTION for name in env.agents},
                  "org-0001": WAIT_ACTION})


@pytest.mark.parametrize("bad", [True, -1, 33, 99, 2.0, "0", None])
def test_bad_actions_rejected_before_settlement(bad):
    env = SurlifeParallelEnv(population=3, max_cycles=4)
    env.reset()
    previous = env.referee.tick, dict(env.referee.balances)
    actions = {agent: 0 for agent in env.agents}
    actions[env.agents[0]] = bad
    with pytest.raises(ValueError, match="invalid PettingZoo action"):
        env.step(actions)
    assert (env.referee.tick, env.referee.balances) == previous


def test_missing_extra_or_unknown_agent_cannot_be_stepped():
    env = SurlifeParallelEnv(population=2)
    env.reset()
    with pytest.raises(ValueError, match="one valid action"):
        env.step({"org-0001": 1})
    with pytest.raises(ValueError, match="one valid action"):
        env.step({"org-0001": 1, "org-0002": 1, "unknown": 3})
    assert env.referee.tick == 0


def test_repeated_reset_reproducible_and_isolated():
    env = SurlifeParallelEnv(population=4, seed=11, max_cycles=8)
    def episode():
        obs, _ = env.reset(seed=11)
        trace = []
        for _ in range(8):
            acts = {agent: env.action_space(agent).n - 1
                    for agent in env.agents}
            obs, reward, term, trunc, info = env.step(acts)
            trace.append((reward, term, trunc, dict(env.referee.balances)))
            if not env.agents:
                break
        return trace
    assert episode() == episode()


def test_nonstrategy_environment_does_not_get_mutation_or_secrets():
    env = SurlifeParallelEnv(population=2)
    obs, _ = env.reset()
    assert all(set(o) == {"items", "capacity", "weather", "own_energy", "tick"}
               for o in obs.values())
    assert env.referee is not None
    assert not hasattr(env, "model")
    assert not hasattr(env, "api_key")
    assert all(value >= 0 for key, value in env.referee.balances.items()
               if key not in ("world",))


@pytest.mark.parametrize("kwargs", [
    {"population": 1}, {"population": 129}, {"population": True},
    {"max_cycles": 0}, {"max_cycles": 513}, {"max_cycles": True},
    {"population": 128, "max_cycles": 40}, {"seed": -1}, {"seed": True},
])
def test_factory_limit_guards(kwargs):
    with pytest.raises(ValueError):
        SurlifeParallelEnv(**kwargs)
