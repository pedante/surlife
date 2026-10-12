"""E04-G01: compare native decision loop vs ACTUAL mini-SWE DefaultAgent.

No shell, network, tokens, provider/model SDK, unsafe code execution. These are
small indicative local CPU timings with the SAME scripted policy and scores.
"""
from __future__ import annotations

import json
import platform
import statistics
import sys
from importlib.metadata import version
from random import Random
from time import perf_counter_ns

from .core import POLICIES
from .mini_swe_bridge import MiniSWEOrganism
from .population import NativeTaskArena


def measure(repeats: int = 7, ticks: int = 6) -> dict:
    if type(repeats) is not int or not 3 <= repeats <= 50:
        raise ValueError("repeats must be 3..50")
    if type(ticks) is not int or not 1 <= ticks <= 16:
        raise ValueError("ticks must be 1..16")
    result = {
        "kind": "e04-g01-cpu-loop-v1",
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "mini_swe_agent": version("mini-swe-agent"),
            "pydantic": version("pydantic"),
            "jinja2": version("jinja2"),
        },
        "provider_calls": 0, "model_tokens": 0,
        "repeats": repeats, "ticks": ticks, "cases": [],
    }
    for n in (2, 8):
        baseline_times: list[int] = []
        mini_times: list[int] = []
        for run in range(repeats):
            seed = (7, 17, 101)[run % 3]
            arena = NativeTaskArena(seed, tuple(f"org-{i:04d}" for i in range(1, n + 1)))
            observations = []
            for tick in range(ticks):
                observations.append(arena.observations())
                arena.step({
                    actor: POLICIES["greedy"](obs, Random(0))
                    for actor, obs in observations[-1].items()
                })
            before = perf_counter_ns()
            expected = [
                {actor: POLICIES["greedy"](obs, Random(0))
                 for actor, obs in row.items()} for row in observations
            ]
            native_ns = perf_counter_ns() - before
            organisms = {actor: MiniSWEOrganism(actor, "greedy", max_calls=ticks)
                         for actor in arena.ids}
            before = perf_counter_ns()
            computed = [
                {actor: organisms[actor].decide(obs, Random(0))
                 for actor, obs in row.items()} for row in observations
            ]
            mini_ns = perf_counter_ns() - before
            assert expected == computed, "mini-SWE did not preserve objective decisions"
            baseline_times.append(native_ns)
            mini_times.append(mini_ns)
        native = statistics.median(baseline_times) / (n * ticks * 1e6)
        mini = statistics.median(mini_times) / (n * ticks * 1e6)
        result["cases"].append({
            "organisms": n,
            "native_median_ms_per_decision": round(native, 4),
            "mini_swe_median_ms_per_decision": round(mini, 4),
            "mini_swe_over_native": round(mini / native, 1) if native else None,
            "identical_scripted_actions": True,
        })
    return result


if __name__ == "__main__":
    print(json.dumps(measure(7, 6), sort_keys=True, indent=2))
