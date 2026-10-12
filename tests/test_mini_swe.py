"""E04-G01 actual upstream DefaultAgent, never local shell or external models.

This optional suite is run in clean GitHub CI with only narrow upstream core
runtime deps, no API keys and isolated MSWEA_GLOBAL_CONFIG_DIR. Default Surlife
test installations skip it without importing the third-party package.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from random import Random

import pytest

if importlib.util.find_spec("minisweagent") is None:
    pytest.skip("optional mini-swe-agent not installed", allow_module_level=True)

from surlife.core import Action, POLICIES
from surlife.population import BuiltinOrganism, NativeTaskArena, OrganismSpec
from surlife.mini_swe_bridge import (
    BoundedActionSink, MiniSWEOrganism, ScriptedNoProviderModel,
    component_versions,
)


def test_real_upstream_import_without_shell_environment():
    from minisweagent.agents.default import DefaultAgent
    assert component_versions()["mini_swe_agent"] == "2.4.6"
    organism = MiniSWEOrganism("org-0001", "greedy", max_calls=3)
    assert isinstance(organism.agent, DefaultAgent)
    assert isinstance(organism.agent.env, BoundedActionSink)
    assert organism.agent.config.output_path is None
    assert organism.agent.config.step_limit == 3
    assert organism.agent.model is organism.model


@pytest.mark.parametrize("n", [2, 3, 8])
@pytest.mark.parametrize("seed", [0, 17, 101])
def test_real_defaultagent_matches_native_actions_and_referee(seed, n):
    ids = tuple(f"org-{i:04d}" for i in range(1, n + 1))
    strategies = ("optimal", "greedy", "random", "wait")
    mini = {
        name: MiniSWEOrganism(name, strategies[i % len(strategies)], max_calls=6)
        for i, name in enumerate(ids)
    }
    plain = {
        name: BuiltinOrganism(OrganismSpec(name, strategies[i % len(strategies)]))
        for i, name in enumerate(ids)
    }
    m_arena = NativeTaskArena(seed, ids)
    p_arena = NativeTaskArena(seed, ids)
    for tick in range(6):
        aobs, bobs = m_arena.observations(), p_arena.observations()
        actions_m, actions_p, meter = {}, {}, {}
        for idx, agent in enumerate(ids):
            rng_seed = seed * 9176 + tick * 101 + idx
            actions_m[agent] = mini[agent].decide(aobs[agent], Random(rng_seed))
            actions_p[agent] = plain[agent].decide(bobs[agent], Random(rng_seed))
            assert actions_m[agent] == actions_p[agent]
            if aobs[agent].own_energy:
                meter[agent] = 1
        row_m = m_arena.step(actions_m, meter)
        row_p = p_arena.step(actions_p, meter)
        assert row_m == row_p
        assert sum(m_arena.balances.values()) == 0
        assert row_m["consultations"] == row_p["consultations"]
        for agent in ids:
            outcome = {
                "tick": tick,
                "score": row_m["scores"][agent],
                "reward": row_m["rewards"][agent],
                "energy_after": row_m["after"][agent],
            }
            mini[agent].feedback(outcome)
            plain[agent].feedback(outcome)
            assert mini[agent].recent_outcomes == plain[agent].recent_outcomes
    for agent in ids:
        assert mini[agent].agent.n_calls == mini[agent].model.calls
        assert mini[agent].model.calls <= 6
        assert len(mini[agent].agent.messages) <= 8


def test_mutation_and_shell_tool_calls_are_denied_without_side_effects(tmp_path):
    env = BoundedActionSink()
    forbidden = [
        {"command": "touch /tmp/anything"},
        {"mask": 1, "command": "echo SECRET"},
        {"mask": True},
        {"mask": -1},
        {"mask": 32},
        {"mask": 2.5},
        {"mask": "31"},
        {"mask": 2, "soul_update": "change host"},
        {"mask": 1, "python": "import os"},
        {},
        "echo hello",
        None,
    ]
    for action in forbidden:
        with pytest.raises(ValueError, match="rejected"):
            env.execute(action)
        assert env.count == 0
        assert env.pending is None
    assert env.execute({"mask": 3})["returncode"] == 0
    with pytest.raises(ValueError, match="rejected"):
        env.execute({"mask": 4})
    assert env.pending == 3


def test_host_cap_prevents_further_model_calls_before_provider_access():
    from minisweagent.exceptions import LimitsExceeded
    arena = NativeTaskArena(17, ("org-0001", "org-0002"))
    organism = MiniSWEOrganism("org-0001", "optimal", max_calls=1)
    obs = arena.observations()["org-0001"]
    assert organism.decide(obs, Random(0)).mask is not None
    assert organism.model.calls == 1
    with pytest.raises(ValueError, match="cap exhausted"):
        organism.decide(obs, Random(0))
    assert organism.model.calls == 1
    with pytest.raises(LimitsExceeded):
        organism.agent.query()
    assert organism.model.calls == 1
    assert arena.tick == 0
    assert sum(arena.balances.values()) == 0


def test_untrusted_model_action_rejected_without_referee_step():
    arena = NativeTaskArena(17, ("org-0001", "org-0002"))
    o = MiniSWEOrganism("org-0001", "greedy", max_calls=2)
    # Inject one malformed command into the fake model; the actual upstream
    # DefaultAgent.execute_actions runs, but its environment cannot shell out.
    def malicious(messages, **kwargs):
        o.model.calls += 1
        return {
            "role": "assistant", "content": "attack",
            "extra": {"actions": [{"command": "echo $OPENAI_API_KEY"}],
                      "cost": 0.0},
        }
    o.model.query = malicious
    balances = dict(arena.balances)
    with pytest.raises(ValueError, match="rejected"):
        o.decide(arena.observations()["org-0001"], Random(0))
    assert arena.tick == 0
    assert arena.balances == balances


def test_agents_separate_model_state_and_no_rival_memory():
    arena = NativeTaskArena(37, ("org-0001", "org-0002"))
    a = MiniSWEOrganism("org-0001", "greedy")
    b = MiniSWEOrganism("org-0002", "optimal")
    first = arena.observations()
    a.decide(first["org-0001"], Random(0))
    b.decide(first["org-0002"], Random(0))
    assert a.agent.messages is not b.agent.messages
    assert a.model is not b.model
    a.feedback({"tick": 0, "score": 1, "reward": 0, "energy_after": 29})
    assert b.recent_outcomes == []
    contents = json.dumps(b.agent.messages)
    assert "org-0001" not in contents
    assert "api_key" not in contents.lower()
    assert "OPENAI_API_KEY" not in contents


def test_cheap_baseline_pays_no_consultation_fee_but_miniswe_does():
    ids = ("org-0001", "org-0002")
    script = NativeTaskArena(17, ids, duel=False)
    costly = NativeTaskArena(17, ids, duel=False)
    brain = MiniSWEOrganism(ids[0], "greedy", max_calls=4)
    for tick in range(4):
        aobs, bobs = costly.observations(), script.observations()
        decision = brain.decide(aobs[ids[0]], Random(0))
        ordinary = POLICIES["greedy"](bobs[ids[0]], Random(0))
        assert decision == ordinary
        actions = {ids[0]: decision, ids[1]: Action(None)}
        paid = costly.step(actions, {ids[0]: 1})
        free = script.step(actions)
        assert paid["scores"] == free["scores"]
    assert costly.balances[ids[0]] < script.balances[ids[0]]
    assert costly.balances[ids[0]] == script.balances[ids[0]] - 4


def test_scripted_model_does_not_run_without_observation_or_autospawn():
    model = ScriptedNoProviderModel()
    with pytest.raises(ValueError, match="observation"):
        model.query([])
    assert model.calls == 0
