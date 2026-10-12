"""M2.0 persistent shared-resource ecology: audited, deterministic and offline.

This is a NEW versioned world, not a change to the historical M0-v2
knapsack referee. The same trusted, conserved virtual-energy ledger pattern
is reused, while shared habitat/stock has multi-tick consequences. Organism
policies cannot edit the ecology or transfer balances directly.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from random import Random

from .core import AGENTS, WORLD
from .storage import canonical

VERSION = "m20-v1"
START_ENERGY = 14
START_STOCK = 8
START_SOIL = 4
MAX_STOCK = 14
MAX_SOIL = 8
MAX_TICKS = 256
MAX_REPORT_BYTES = 4_000_000
ACTIONS = ("rest", "harvest1", "harvest3", "tend")
COSTS = {"rest": 0, "harvest1": 0, "harvest3": 1, "tend": 2}
STRATEGIES = ("extractive", "steward", "opportunist", "rest")
WEATHERS = ("normal", "rain", "drought")


@dataclass(frozen=True)
class View:
    tick: int
    weather: str
    stock: int
    soil: int
    own_energy: int


def decide(strategy: str, view: View) -> str:
    """Trusted organism, only its public observation and private energy."""
    if strategy not in STRATEGIES:
        raise ValueError("unknown persistent-world strategy")
    if view.own_energy <= 0 or strategy == "rest":
        return "rest"
    if strategy == "extractive":
        return "harvest3" if view.stock and view.own_energy >= 2 else (
            "harvest1" if view.stock else "rest")
    if strategy == "steward":
        if view.soil < 5 and view.own_energy >= 4:
            return "tend"
        return "harvest1" if view.stock else "rest"
    if view.stock >= 5 and view.own_energy >= 2:
        return "harvest3"
    if view.stock:
        return "harvest1"
    return "tend" if view.soil < 4 and view.own_energy >= 4 else "rest"


class PersistentArena:
    """One referee owns stock, fertility and balances across all ticks."""

    def __init__(self, seed: int):
        if type(seed) is not int or seed < 0:
            raise ValueError("nonnegative integer seed required")
        self.seed = seed
        self.tick = 0
        self.stock = START_STOCK
        self.soil = START_SOIL
        self.balances = {"a": START_ENERGY, "b": START_ENERGY,
                         WORLD: -2 * START_ENERGY}

    def weather(self) -> str:
        return Random(self.seed * 1_000_003 + self.tick * 9_176 + 101).choice(WEATHERS)

    def observations(self) -> dict[str, View]:
        weather = self.weather()
        return {actor: View(self.tick, weather, self.stock, self.soil,
                            self.balances[actor]) for actor in AGENTS}

    def step(self, actions: dict[str, str]) -> dict:
        """Snapshot both decisions; preflight ALL admissions; settle atomically.

        The priority order alternates by tick+seed and applies to individual
        resource units (not entire requests), so one actor cannot capture the
        common pool by dict ordering. No inactive organism is resurrected.
        """
        if (not isinstance(actions, dict) or set(actions) != set(AGENTS)
                or any(type(value) is not str or value not in ACTIONS
                       for value in actions.values())):
            raise ValueError("exactly one reviewed action per organism required")
        previous = dict(self.balances)
        before = {"stock": self.stock, "soil": self.soil}
        active = {actor: previous[actor] > 0 for actor in AGENTS}
        for actor in AGENTS:
            if not active[actor] and actions[actor] != "rest":
                raise ValueError("dead organism cannot mutate the ecology")
            if active[actor] and previous[actor] - 1 < COSTS[actions[actor]]:
                raise ValueError("action unaffordable AFTER mandatory upkeep")
        weather = self.weather()
        transfers: list[dict] = []

        def transfer(src: str, dst: str, amount: int, kind: str) -> None:
            if type(amount) is not int or amount < 0:
                raise AssertionError("invalid ledger amount")
            if src != WORLD and self.balances[src] < amount:
                raise AssertionError("insufficient virtual energy")
            self.balances[src] -= amount
            self.balances[dst] += amount
            if amount:
                transfers.append({"from": src, "to": dst,
                                  "amount": amount, "kind": kind})

        for actor in AGENTS:
            if active[actor]:
                transfer(actor, WORLD, 1, "upkeep")
        for actor in AGENTS:
            if active[actor] and COSTS[actions[actor]]:
                transfer(actor, WORLD, COSTS[actions[actor]], "action_cost")

        # All harvesters request scarce units at the same time.
        wants = {actor: (
            1 if actions[actor] == "harvest1" and active[actor]
            else 3 if actions[actor] == "harvest3" and active[actor]
            else 0) for actor in AGENTS}
        allocation = {actor: 0 for actor in AGENTS}
        first = AGENTS[(self.tick + self.seed) % len(AGENTS)]
        second = AGENTS[1 - ((self.tick + self.seed) % len(AGENTS))]
        remaining = self.stock
        while remaining and any(allocation[a] < wants[a] for a in AGENTS):
            for actor in (first, second):
                if remaining and allocation[actor] < wants[actor]:
                    allocation[actor] += 1
                    remaining -= 1
        self.stock = remaining

        for actor in AGENTS:
            if allocation[actor]:
                reward = allocation[actor] * (
                    3 if actions[actor] == "harvest1" else 2)
                transfer(WORLD, actor, reward, "forage_reward")

        degradation = sum(
            allocation[a] >= 2 and actions[a] == "harvest3"
            for a in AGENTS)
        self.soil = max(0, self.soil - degradation)
        cultivation = sum(active[a] and actions[a] == "tend" for a in AGENTS)
        self.soil = min(MAX_SOIL, self.soil + cultivation * 2)
        if weather == "drought":
            self.soil = max(0, self.soil - 1)
        # Growth happens AFTER exploitation/repair, shaping the NEXT tick.
        regrown = (
            max(1, self.soil // 2) if weather == "rain"
            else self.soil // 3 if weather == "normal" else 0)
        regrown = min(MAX_STOCK - self.stock, regrown)
        self.stock += regrown
        if (sum(self.balances.values()) != 0
                or any(self.balances[a] < 0 for a in AGENTS)
                or not 0 <= self.stock <= MAX_STOCK
                or not 0 <= self.soil <= MAX_SOIL):
            raise AssertionError("persistent-world conservation/bounds failed")
        record = {
            "tick": self.tick, "weather": weather,
            "observations": {a: vars(v) for a, v in
                             {a: View(self.tick, weather, before["stock"],
                                      before["soil"], previous[a])
                              for a in AGENTS}.items()},
            "actions": dict(actions), "before": {
                "balances": previous, **before},
            "allocation": allocation,
            "cultivation": cultivation,
            "degradation": degradation,
            "regrown": regrown,
            "after": {
                "balances": dict(self.balances),
                "stock": self.stock, "soil": self.soil},
            "alive": {a: self.balances[a] > 0 for a in AGENTS},
            "transfers": transfers,
        }
        self.tick += 1
        return record


def episode(seed: int, ticks: int, a: str, b: str) -> list[dict]:
    if type(ticks) is not int or not 1 <= ticks <= MAX_TICKS:
        raise ValueError("M2.0 ticks must be between 1 and 256")
    if a not in STRATEGIES or b not in STRATEGIES:
        raise ValueError("unknown reviewed organism policy")
    arena = PersistentArena(seed)
    rows = []
    for _ in range(ticks):
        views = arena.observations()
        actions = {"a": decide(a, views["a"]), "b": decide(b, views["b"])}
        rows.append(arena.step(actions))
    return rows


def _stats(rows: list[dict], names: dict) -> dict:
    last = rows[-1]
    result = {"final_stock": last["after"]["stock"],
              "final_soil": last["after"]["soil"],
              "stock_empty_ticks": sum(r["before"]["stock"] == 0 for r in rows),
              "total_regrowth": sum(r["regrown"] for r in rows),
              "total_cultivation": sum(r["cultivation"] for r in rows),
              "total_harvested": sum(sum(r["allocation"].values()) for r in rows),
              "agents": {}}
    for actor in AGENTS:
        result["agents"][actor] = {
            "policy": names[actor],
            "final_energy": last["after"]["balances"][actor],
            "alive": last["alive"][actor],
            "alive_ticks": sum(row["before"]["balances"][actor] > 0 for row in rows),
            "harvested": sum(r["allocation"][actor] for r in rows),
            "cultivations": sum(r["actions"][actor] == "tend" for r in rows),
            "aggressive_actions": sum(r["actions"][actor] == "harvest3" for r in rows),
        }
    return result


def _summarize(episodes: dict, policies: dict) -> dict:
    sessions = {}
    policy_groups = {name: [] for name in set(policies.values())}
    for name in ("primary", "mirror"):
        actors = policies if name == "primary" else {"a": policies["b"],
                                                       "b": policies["a"]}
        data = _stats(episodes[name], actors)
        sessions[name] = data
        for actor in AGENTS:
            policy_groups[actors[actor]].append(data["agents"][actor])
    aggregate = {
        policy: {
            "mean_final_energy": round(sum(x["final_energy"] for x in records)
                                       / len(records), 4),
            "survival_episodes": sum(x["alive"] for x in records),
            "mean_harvested": round(sum(x["harvested"] for x in records)
                                   / len(records), 4),
        }
        for policy, records in policy_groups.items()}
    return {
        "sessions": sessions, "policy_comparison": aggregate,
        "note": ("Two mirrored seat assignments reuse the same seed/weather "
                 "sequence but have genuinely shared resources within each "
                 "episode. Energy ledger transfers sum to zero. Soil and "
                 "stock represent renewable ecology, not currency or "
                 "independently conserved energy. Policies are trusted "
                 "offline functions, not learning LLM organisms."),
    }


def _hash(report: dict) -> str:
    return hashlib.sha256(canonical({
        name: report[name] for name in ("manifest", "episodes", "summary")
    }).encode("utf-8")).hexdigest()


def build_report(seed: int, ticks: int, a: str, b: str) -> dict:
    primary = episode(seed, ticks, a, b)
    mirror = episode(seed, ticks, b, a)
    manifest = {"experiment": VERSION, "seed": seed, "ticks": ticks,
                "a": a, "b": b, "provider": "none", "model_calls": 0,
                "start_energy": START_ENERGY, "start_stock": START_STOCK,
                "start_soil": START_SOIL, "max_stock": MAX_STOCK,
                "max_soil": MAX_SOIL, "referee": "m20-persistent-v1"}
    episodes = {"primary": primary, "mirror": mirror}
    report = {"manifest": manifest, "episodes": episodes,
              "summary": _summarize(episodes, {"a": a, "b": b})}
    report["head"] = _hash(report)
    return report


def verify_m20(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
        raise ValueError("invalid persistent-world report")
    m = report["manifest"]
    if (set(m) != {"experiment", "seed", "ticks", "a", "b", "provider",
                   "model_calls", "start_energy", "start_stock",
                   "start_soil", "max_stock", "max_soil", "referee"}
            or m["experiment"] != VERSION or m["provider"] != "none"
            or m["model_calls"] != 0
            or m["start_energy"] != START_ENERGY
            or m["start_stock"] != START_STOCK
            or m["start_soil"] != START_SOIL
            or m["max_stock"] != MAX_STOCK or m["max_soil"] != MAX_SOIL
            or m["referee"] != "m20-persistent-v1"):
        raise ValueError("unsupported persistent-world manifest")
    expected = build_report(m["seed"], m["ticks"], m["a"], m["b"])
    if (canonical(report.get("episodes")) != canonical(expected["episodes"])
            or canonical(report.get("summary")) != canonical(expected["summary"])
            or report.get("head") != expected["head"]):
        raise ValueError("M2.0 ecology, actions, ledger or digest replay mismatch")
    return {"verified": True, "head": expected["head"],
            "summary": expected["summary"]}


def verify_m20_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("M2.0 report missing or too large")
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid persistent-world JSON") from exc
    return verify_m20(value)


def run_m20(args) -> dict:
    if args.provider != "fake":
        raise ValueError("M2.0 offline only: --provider fake")
    path = getattr(args, "benchmark_out", None)
    if not path:
        raise ValueError("M2.0 requires --benchmark-out")
    if Path(path).exists():
        raise ValueError("M2.0 output exists; choose a NEW filename")
    report = build_report(args.seed, args.ticks, args.m20_a, args.m20_b)
    verify_m20(report)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8")
    return {"verified": True, "head": report["head"],
            "report_path": str(p), "manifest": report["manifest"],
            "summary": report["summary"]}
