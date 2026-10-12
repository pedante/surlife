"""Reproducible E01-W02 Python benchmark: bare referee vs PettingZoo bridge.

This measures API overhead, not organism intelligence or real model calls.
Median over repeated identical seeded step sequences; environment specs in JSON.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from importlib.metadata import version
from time import perf_counter_ns

from surlife.core import Arena, greedy, optimal
from surlife.population import NativeTaskArena
from surlife.pettingzoo_bridge import SurlifeParallelEnv

BENCHMARK_VERSION = "e01-w02-benchmark-v1"


def one(seed: int, population: int, ticks: int, use_bridge: bool):
    ids = tuple(f"org-{i:04d}" for i in range(1, population + 1))
    reference = Arena(seed)
    masks = []
    for tick in range(ticks):
        reference.tick = tick
        obs = reference.observations()["a"]
        # Same precomputed actions in both paths, no LLM or random sampling.
        masks.append({
            agent: (greedy if j % 2 else optimal)(obs, None).mask
            for j, agent in enumerate(ids)
        })
    if use_bridge:
        env = SurlifeParallelEnv(population=population, seed=seed,
                                 max_cycles=ticks)
        env.reset(seed=seed)
    else:
        native = NativeTaskArena(seed, ids)
    started = perf_counter_ns()
    for mask in masks:
        if use_bridge:
            live = {agent: mask[agent] for agent in env.agents}
            if not live:
                break
            env.step(live)
        else:
            from surlife.core import Action
            native.step({agent: Action(mask[agent]) for agent in ids})
    duration = perf_counter_ns() - started
    balances = env.referee.balances if use_bridge else native.balances
    return duration, dict(balances)


def run(repeats: int = 7, ticks: int = 12) -> dict:
    if type(repeats) is not int or not 2 <= repeats <= 100:
        raise ValueError("repeats must be 2..100")
    if type(ticks) is not int or not 2 <= ticks <= 32:
        raise ValueError("ticks must be 2..32")
    result = {
        "benchmark": BENCHMARK_VERSION,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pettingzoo": version("pettingzoo"),
            "gymnasium": version("gymnasium"),
            "numpy": version("numpy"),
            "surlife": version("surlife"),
        },
        "repeats": repeats, "ticks": ticks,
        "llm_requests": 0, "cases": [],
    }
    for count in (2, 8):
        native_ns, bridge_ns = [], []
        for i in range(repeats):
            seed = (17, 101, 313)[i % 3]
            # Alternate measurement order to reduce systematic warmup effects.
            order = (False, True) if i % 2 == 0 else (True, False)
            observations = {}
            for with_bridge in order:
                elapsed, balances = one(seed, count, ticks, with_bridge)
                observations[with_bridge] = (elapsed, balances)
            assert observations[False][1] == observations[True][1], (
                "PettingZoo bridge and native referee have divergent ledgers"
            )
            native_ns.append(observations[False][0])
            bridge_ns.append(observations[True][0])
        native = statistics.median(native_ns) / (ticks * 1_000_000)
        bridge = statistics.median(bridge_ns) / (ticks * 1_000_000)
        result["cases"].append({
            "population": count, "ticks": ticks,
            "native_median_ms_per_tick": round(native, 4),
            "pettingzoo_median_ms_per_tick": round(bridge, 4),
            "pettingzoo_over_native": round(bridge / native, 3)
            if native else None,
            "full_ledger_equivalence_each_repeat": True,
        })
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--ticks", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(run(args.repeats, args.ticks), indent=2, sort_keys=True))
