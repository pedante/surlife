"""E04-G01 research-only mini-SWE-agent real DefaultAgent integration.

No mini-SWE imports at module import time and no dependency in base Surlife.
Explicitly substitutes a ZERO-CAPABILITY environment and an injected scripted
model. It does not import mini-SWE LocalEnvironment, model factories, shell,
browsers, arbitrary plugins or executable organism-written code. This adapter
does not authorize live-provider use: the output is a fake scripted action.
"""
from __future__ import annotations

import json
from random import Random

from .core import Action, Observation, POLICIES
from .population import TASK_CONTRACT, sha


class BoundedActionSink:
    """Exactly one data-only task action; no host operations whatsoever."""

    def __init__(self):
        self.pending: int | None = None
        self.count = 0

    def execute(self, action: dict, cwd: str = "") -> dict:
        del cwd
        if (not isinstance(action, dict) or set(action) != {"mask"}
                or (action["mask"] is not None and (
                    type(action["mask"]) is not int or
                    not 0 <= action["mask"] < 32))
                or self.count >= 1):
            raise ValueError("rejected untrusted mini-SWE action")
        self.pending = action["mask"]
        self.count += 1
        return {"output": "validated task mask", "returncode": 0,
                "exception_info": ""}

    def get_template_vars(self, **kwargs):
        del kwargs
        return {}

    def serialize(self):
        return {}


class ScriptedNoProviderModel:
    """Fake model: injects trusted scripted answers, never calls an API."""

    def __init__(self):
        self.pending: int | None = None
        self.calls = 0

    def query(self, messages: list[dict], **kwargs) -> dict:
        del kwargs
        if not isinstance(messages, list) or not messages:
            raise ValueError("bounded model requires one scoped observation")
        # Real mini-SWE-agent calls the same protocol, but no provider use.
        self.calls += 1
        return {
            "role": "assistant",
            "content": "scripted benchmark action",
            "extra": {
                "actions": [{"mask": self.pending}],
                "cost": 0.0,
            },
        }

    def format_message(self, **kwargs) -> dict:
        return dict(kwargs)

    def format_observation_messages(
        self, message: dict, outputs: list[dict],
        template_vars: dict | None = None
    ) -> list[dict]:
        del message, template_vars
        return [{"role": "tool", "content": x["output"]} for x in outputs]

    def get_template_vars(self, **kwargs):
        del kwargs
        return {}

    def serialize(self):
        return {}


class MiniSWEOrganism:
    """Upstream DefaultAgent driven ONE action per host-admitted tick.

    decide() models a consultation, but decisions are scripted cheap policies.
    Surlife must charge virtual cognition separately in its own referee map.
    Mini-SWE cost estimates are never authority for Surlife spending.
    """

    contract = TASK_CONTRACT

    def __init__(self, organism_id: str, strategy: str,
                 *, max_calls: int = 8):
        if (type(organism_id) is not str or
                not organism_id.startswith("org-") or
                strategy not in POLICIES or type(max_calls) is not int or
                not 1 <= max_calls <= 16):
            raise ValueError("invalid E04 organism configuration")
        # Only this dependency is imported. Upstream __init__ currently loads
        # global dotenv config and creates a directory at import time;
        # not appropriate for secret-bearing or hostile-code processes.
        from minisweagent.agents.default import DefaultAgent
        self.organism_id = organism_id
        self.strategy = strategy
        self.genome_hash = sha({"mini-swe": "v2.4.6",
                                "strategy": strategy, "fixture": "E04-G01"})
        self.max_calls = max_calls
        self.sink = BoundedActionSink()
        self.model = ScriptedNoProviderModel()
        self.agent = DefaultAgent(
            self.model, self.sink,
            system_template="One bounded action at a time. No tools or shell.",
            instance_template="The referee alone validates actions.",
            step_limit=max_calls,
            cost_limit=0.0,
            output_path=None,
        )
        self.recent_outcomes: list[dict] = []

    def decide(self, observation: Observation, rng: Random) -> Action:
        if not isinstance(observation, Observation):
            raise TypeError("task observation required")
        if observation.own_energy <= 0:
            return Action(None)
        if self.model.calls >= self.max_calls:
            raise ValueError("host fake-request cap exhausted")
        self.model.pending = POLICIES[self.strategy](observation, rng).mask
        self.sink.pending = None
        self.sink.count = 0
        # Never include opponent genomes, secrets, account, host environment
        # or mutable referee. Keep bounded scoped JSON task details only.
        scoped = {
            "tick": observation.tick, "weather": observation.weather,
            "task": observation.task.as_dict(), "own_energy": observation.own_energy
        }
        self.agent.add_messages({
            "role": "user", "content": json.dumps(scoped, sort_keys=True)
        })
        self.agent.step()  # ACTUAL upstream model -> environment feedback cycle
        if self.sink.count != 1:
            raise AssertionError("untrusted model produced zero/multiple actions")
        if self.agent.n_calls != self.model.calls:
            raise AssertionError("mini-SWE calls diverged from fake host meter")
        self.agent.messages = self.agent.messages[-8:]
        return Action(self.sink.pending)

    def feedback(self, own_result: dict) -> None:
        allowed = {"tick", "score", "reward", "energy_after"}
        if not isinstance(own_result, dict) or set(own_result) != allowed:
            raise ValueError("only per-organism feedback is admissible")
        self.recent_outcomes.append(dict(own_result))
        self.recent_outcomes = self.recent_outcomes[-8:]


def component_versions() -> dict:
    from importlib.metadata import version
    return {
        "mini_swe_agent": version("mini-swe-agent"),
        "pydantic": version("pydantic"),
        "jinja2": version("jinja2"),
    }
