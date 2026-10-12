"""Population/arena adapter boundary (population-v1), offline and backwards compatible.

M0-M2.1-C keep their original 2-player, versioned protocols. This module adds
a trusted opt-in coordinator for 2..128 distinct organism identities with
interchangeable BUILTIN organism/arena adapters. It is not a Python sandbox,
third-party plugin loader, LLM gateway, or proof of autonomous evolution.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any, Mapping, Protocol, runtime_checkable

from .core import Action, Arena, ESCROW, POLICIES, STAKE, START_ENERGY, WORLD, Observation
from .storage import canonical

VERSION = "population-v1"
MAX_AGENTS = 128
MAX_TICKS = 512
MAX_WORK = 4096  # max agents * ticks; bounds records and replay
MAX_REPORT_BYTES = 32_000_000
TASK_CONTRACT = "task-mask-v1"
HABITAT_CONTRACT = "habitat-action-v1"
ARENAS = ("task-duel", "task-work", "legacy-m0", "legacy-m20")
TASK_BRAINS = tuple(sorted(POLICIES))
HABITAT_BRAINS = ("extractive", "steward", "opportunist", "rest")


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class OrganismSpec:
    """Pure-data organism identity. Untrusted Python code is never imported."""

    id: str
    brain: str

    @property
    def contract(self) -> str:
        if self.brain in TASK_BRAINS:
            return TASK_CONTRACT
        if self.brain in HABITAT_BRAINS:
            return HABITAT_CONTRACT
        raise ValueError("unknown or untrusted organism brain")

    @property
    def genome_hash(self) -> str:
        return sha({"brain": self.brain, "implementation": "builtin-v1"})


@runtime_checkable
class OrganismAdapter(Protocol):
    """Only a scoped observation, isolated per-organism state and own result."""

    organism_id: str
    contract: str
    genome_hash: str

    def decide(self, observation: object, rng: Random) -> object: ...

    def feedback(self, own_result: dict) -> None: ...


@runtime_checkable
class ArenaAdapter(Protocol):
    """Trusted environment; actions are untrusted values admitted by its referee."""

    name: str
    contract: str
    ids: tuple[str, ...]
    tick: int
    balances: dict[str, int]

    def observations(self) -> dict[str, object]: ...

    def step(self, actions: dict[str, object],
             consultations: dict[str, int] | None = None) -> dict: ...


@dataclass
class BuiltinOrganism:
    """Installed trusted strategies, never sourced from an organism workspace."""

    spec: OrganismSpec
    organism_id: str = field(init=False)
    contract: str = field(init=False)
    genome_hash: str = field(init=False)
    recent_outcomes: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.organism_id = self.spec.id
        self.contract = self.spec.contract
        self.genome_hash = self.spec.genome_hash

    def decide(self, observation: object, rng: Random) -> object:
        if self.contract == TASK_CONTRACT:
            if not isinstance(observation, Observation):
                raise TypeError("task brain requires task observation")
            return (POLICIES[self.spec.brain](observation, rng)
                    if observation.own_energy > 0 else Action(None))
        from .m20 import View, decide as habitat_decide
        if not isinstance(observation, View):
            raise TypeError("habitat brain requires habitat observation")
        return habitat_decide(self.spec.brain, observation)

    def feedback(self, own_result: dict) -> None:
        # Memory is independent, bounded and includes NO opponent's private state.
        self.recent_outcomes.append(dict(own_result))
        self.recent_outcomes = self.recent_outcomes[-8:]


def make_specs(brains: tuple[str, ...]) -> tuple[OrganismSpec, ...]:
    if not isinstance(brains, tuple) or not 2 <= len(brains) <= MAX_AGENTS:
        raise ValueError("population must contain 2..128 organisms")
    result = tuple(OrganismSpec(f"org-{i:04d}", brain)
                   for i, brain in enumerate(brains, 1))
    for spec in result:
        _ = spec.contract
    return result


def _validate_ids(ids: tuple[str, ...], *, two_only: bool = False) -> None:
    if (not isinstance(ids, tuple) or not 2 <= len(ids) <= MAX_AGENTS
            or two_only and len(ids) != 2
            or len(ids) != len(set(ids))
            or any(type(x) is not str or not x.isascii() or
                   not 1 <= len(x) <= 64 or not all(
                       char.isalnum() or char in "_-" for char in x
                   ) or x in (WORLD, ESCROW) for x in ids)):
        raise ValueError("invalid population identities for this arena")


def _validate_actions(actions: dict, ids: tuple[str, ...], kind: str) -> None:
    if not isinstance(actions, dict) or set(actions) != set(ids):
        raise ValueError("one submitted action is required per organism")
    if kind == TASK_CONTRACT and any(not isinstance(v, Action)
                                     for v in actions.values()):
        raise ValueError("task arena requires structured Action objects")


def _validate_consultations(consultations: dict | None, ids: tuple[str, ...]) -> dict:
    if consultations is None:
        return {}
    if (not isinstance(consultations, dict) or any(
            actor not in ids or type(n) is not int or n not in (0, 1)
            for actor, n in consultations.items())):
        raise ValueError("consultation count must be 0/1 per known organism")
    return consultations


def _remap_legacy(obj: Any, mapping: dict[str, str]) -> Any:
    """Map M0 fixed ids without changing historical records or referee source."""
    if isinstance(obj, dict):
        return {mapping.get(k, k): _remap_legacy(v, mapping)
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_remap_legacy(x, mapping) for x in obj]
    return obj


class LegacyM0Adapter:
    """Adapter around ORIGINAL two-player M0 referee, no modified rules."""

    name = "legacy-m0"
    contract = TASK_CONTRACT

    def __init__(self, seed: int, ids: tuple[str, ...]):
        _validate_ids(ids, two_only=True)
        self.ids = ids
        self.inner = Arena(seed)

    @property
    def tick(self) -> int:
        return self.inner.tick

    @property
    def balances(self) -> dict[str, int]:
        return _remap_legacy(self.inner.balances, dict(zip(("a", "b"), self.ids)))

    def observations(self) -> dict[str, Observation]:
        source = self.inner.observations()
        return dict(zip(self.ids, (source["a"], source["b"])))

    def step(self, actions: dict[str, Action],
             consultations: dict[str, int] | None = None) -> dict:
        _validate_actions(actions, self.ids, self.contract)
        consultations = _validate_consultations(consultations, self.ids)
        rename = dict(zip(("a", "b"), self.ids))
        acts = {legacy: actions[current] for legacy, current in rename.items()}
        calls = {legacy: consultations.get(current, 0)
                 for legacy, current in rename.items()}
        raw = self.inner.step(acts, calls)
        row = _remap_legacy(raw, rename)
        if row["winner"] is not None:
            row["winner"] = rename[row["winner"]]
        # Transfer endpoint VALUES require remapping, not just mapping keys.
        for transfer in row["transfers"]:
            transfer["from"] = rename.get(transfer["from"], transfer["from"])
            transfer["to"] = rename.get(transfer["to"], transfer["to"])
        row["pairs"] = ([{"participants": list(self.ids), "winner": row["winner"],
                          "entered": row["entered"]}]
                        if row["entered"] else [])
        return row


class LegacyM20Adapter:
    """Optional M2.0 research fixture; no changes to stock/soil referee."""

    name = "legacy-m20"
    contract = HABITAT_CONTRACT

    def __init__(self, seed: int, ids: tuple[str, ...]):
        _validate_ids(ids, two_only=True)
        from .m20 import PersistentArena
        self.ids = ids
        self.inner = PersistentArena(seed)

    @property
    def tick(self) -> int:
        return self.inner.tick

    @property
    def balances(self) -> dict[str, int]:
        return _remap_legacy(self.inner.balances, dict(zip(("a", "b"), self.ids)))

    def observations(self) -> dict[str, object]:
        source = self.inner.observations()
        return dict(zip(self.ids, (source["a"], source["b"])))

    def step(self, actions: dict[str, str],
             consultations: dict[str, int] | None = None) -> dict:
        _validate_actions(actions, self.ids, self.contract)
        calls = _validate_consultations(consultations, self.ids)
        if any(calls.values()):
            raise ValueError("legacy M2.0 does not support consultation charges")
        rename = dict(zip(("a", "b"), self.ids))
        raw = self.inner.step({legacy: actions[current]
                               for legacy, current in rename.items()})
        row = _remap_legacy(raw, rename)
        for transfer in row["transfers"]:
            transfer["from"] = rename.get(transfer["from"], transfer["from"])
            transfer["to"] = rename.get(transfer["to"], transfer["to"])
        return row


def _round_robin(ids: tuple[str, ...], seed: int, tick: int) -> list[tuple[str, str]]:
    """Deterministic circle-method pairing; odd populations get one rotating bye."""
    order: list[str | None] = list(ids)
    Random(seed).shuffle(order)
    if len(order) % 2:
        order.append(None)
    for _ in range(tick % (len(order) - 1)):
        order = [order[0], order[-1], *order[1:-1]]
    return [(a, b) for a, b in zip(order[:len(order)//2],
                                    reversed(order[len(order)//2:]))
            if a is not None and b is not None]


class NativeTaskArena:
    """N-player new arena with shared tasks and optional competitive pair stakes.

    The M0 Task and puzzle RNG are reused exactly; only population accounting
    and rotating matchups are new. The referee, not the organism, owns energy.
    """

    contract = TASK_CONTRACT

    def __init__(self, seed: int, ids: tuple[str, ...], *, duel: bool = True):
        _validate_ids(ids)
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be nonnegative")
        self.name = "task-duel" if duel else "task-work"
        self.ids = ids
        self.seed = seed
        self.duel = duel
        self.tick = 0
        self.balances = {
            **{actor: START_ENERGY for actor in ids},
            WORLD: -len(ids) * START_ENERGY,
            ESCROW: 0,
        }
        self._puzzle_ref = Arena(seed)

    def _puzzle(self) -> Observation:
        self._puzzle_ref.tick = self.tick
        return self._puzzle_ref.observations()["a"]

    def observations(self) -> dict[str, Observation]:
        obs = self._puzzle()
        return {
            actor: Observation(self.tick, obs.weather, obs.task,
                               self.balances[actor])
            for actor in self.ids
        }

    def step(self, actions: dict[str, Action],
             consultations: dict[str, int] | None = None) -> dict:
        _validate_actions(actions, self.ids, self.contract)
        calls = _validate_consultations(consultations, self.ids)
        before = dict(self.balances)
        active = {actor: before[actor] > 0 for actor in self.ids}
        obs = self._puzzle()
        task, weather = obs.task, obs.weather
        upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
        for actor in self.ids:
            if calls.get(actor, 0):
                available = max(
                    0, before[actor] +
                    (1 if active[actor] and self.tick % 4 == 0 else 0)
                    - upkeep)
                if not active[actor] or available < 1:
                    raise ValueError("consultation not affordable after upkeep")
        transfers: list[dict] = []

        def move(src: str, dst: str, amount: int, kind: str) -> None:
            if type(amount) is not int or amount < 0:
                raise AssertionError("invalid virtual transfer")
            if src != WORLD and self.balances[src] < amount:
                raise AssertionError("unfunded transfer")
            self.balances[src] -= amount
            self.balances[dst] += amount
            if amount:
                transfers.append({
                    "from": src, "to": dst, "amount": amount, "kind": kind
                })

        if self.tick % 4 == 0:
            for actor in self.ids:
                if active[actor]:
                    move(WORLD, actor, 1, "mint")
        for actor in self.ids:
            if active[actor]:
                move(actor, WORLD, min(upkeep, self.balances[actor]), "upkeep")
        for actor in self.ids:
            if calls.get(actor, 0):
                move(actor, WORLD, 1, "cognition")

        attempted = {
            actor: active[actor] and actions[actor].mask is not None
            for actor in self.ids
        }
        scores: dict[str, int | None] = {actor: None for actor in self.ids}
        rewards = {actor: 0 for actor in self.ids}
        optimum = task.optimum
        for actor in self.ids:
            if not attempted[actor]:
                continue
            score = task.score(actions[actor].mask)
            scores[actor] = score
            reward = (
                3 if score == optimum else
                2 if score >= 0 and 5 * score >= 4 * optimum else
                1 if score > 0 else 0
            )
            rewards[actor] = reward
            move(WORLD, actor, reward, "work_reward")

        pairs = []
        if self.duel:
            for a, b in _round_robin(self.ids, self.seed, self.tick):
                enter = attempted[a] and attempted[b] and (
                    self.balances[a] >= STAKE and self.balances[b] >= STAKE
                )
                winner = None
                if enter:
                    move(a, ESCROW, STAKE, "stake")
                    move(b, ESCROW, STAKE, "stake")
                    if scores[a] != scores[b]:
                        winner = a if scores[a] > scores[b] else b
                        move(ESCROW, winner, 2 * STAKE, "win")
                    else:
                        move(ESCROW, a, STAKE, "refund")
                        move(ESCROW, b, STAKE, "refund")
                pairs.append({"participants": [a, b], "entered": enter,
                              "winner": winner})
        if (sum(self.balances.values()) != 0 or
                any(self.balances[a] < 0 for a in (*self.ids, ESCROW)) or
                self.balances[ESCROW] != 0):
            raise AssertionError("population ledger conservation failure")
        row = {
            "tick": self.tick, "weather": weather, "task": task.as_dict(),
            "optimal_score": optimum, "actions": {
                a: actions[a].mask for a in self.ids
            }, "consultations": {a: calls.get(a, 0) for a in self.ids},
            "attempted": attempted, "scores": scores, "rewards": rewards,
            "alive": {a: self.balances[a] > 0 for a in self.ids},
            "pairs": pairs, "before": before,
            "after": dict(self.balances), "transfers": transfers,
        }
        self.tick += 1
        return row


def make_arena(name: str, seed: int,
               ids: tuple[str, ...]) -> ArenaAdapter:
    """Explicit vetted factory: arbitrary import strings are NOT a plugin API."""
    if name == "task-duel":
        return NativeTaskArena(seed, ids, duel=True)
    if name == "task-work":
        return NativeTaskArena(seed, ids, duel=False)
    if name == "legacy-m0":
        return LegacyM0Adapter(seed, ids)
    if name == "legacy-m20":
        return LegacyM20Adapter(seed, ids)
    raise ValueError("unknown arena adapter")


class PopulationSession:
    """Step-by-step coordinator; can be paused by simply not calling step().

    No sleeps, async provider calls, user-generated code, or browser coupling.
    New trusted adapters can be injected for research, but only built-ins have
    a self-contained historical offline verifier at present.
    """

    def __init__(self, *, seed: int, arena_name: str,
                 organisms: tuple[OrganismSpec, ...]):
        if type(seed) is not int or seed < 0 or not organisms or (
            not isinstance(organisms, tuple)) or not all(
                isinstance(o, OrganismSpec) for o in organisms):
            raise ValueError("invalid session configuration")
        self.organisms = organisms
        self.ids = tuple(o.id for o in organisms)
        self.arena = make_arena(arena_name, seed, self.ids)
        if any(o.contract != self.arena.contract for o in organisms):
            raise ValueError("organism action contract incompatible with arena")
        self.brains = {o.id: BuiltinOrganism(o) for o in organisms}
        self.seed = seed
        self.arena_name = arena_name
        self.events: list[dict] = []
        self.previous_hash = sha(self.manifest)

    @property
    def manifest(self) -> dict:
        return {
            "protocol": VERSION, "seed": self.seed,
            "arena": self.arena_name, "arena_rules": (
                "m0-v2" if self.arena_name == "legacy-m0" else
                "m20-v1" if self.arena_name == "legacy-m20" else
                "population-task-v1"
            ),
            "organisms": [
                {"id": spec.id, "brain": spec.brain,
                 "contract": spec.contract, "genome_hash": spec.genome_hash}
                for spec in self.organisms
            ],
            "provider": "none",
            "real_requests": 0,
        }

    def step(self) -> dict:
        if (self.arena.tick >= MAX_TICKS or
                (self.arena.tick + 1) * len(self.ids) > MAX_WORK):
            raise ValueError("population tick/work cap reached")
        observations = self.arena.observations()
        if set(observations) != set(self.ids):
            raise AssertionError("arena did not give each organism an observation")
        actions: dict[str, object] = {}
        for spec in self.organisms:
            # Separate stable random streams per organism: no scheduling leak.
            key = int(hashlib.sha256(
                f"{self.seed}:{spec.id}:{self.arena.tick}".encode("ascii")
            ).hexdigest()[:16], 16)
            actions[spec.id] = self.brains[spec.id].decide(
                observations[spec.id], Random(key))
        raw = self.arena.step(actions)
        if raw["tick"] != len(self.events):
            raise AssertionError("arena diverged from event cursor")
        for spec in self.organisms:
            own_score = raw.get("scores", {}).get(spec.id)
            own_reward = raw.get("rewards", {}).get(spec.id)
            own_energy = self.arena.balances[spec.id]
            self.brains[spec.id].feedback({
                "tick": self.arena.tick - 1, "score": own_score,
                "reward": own_reward, "energy_after": own_energy,
            })
        payload = {
            "tick": raw["tick"], "arena": self.arena_name,
            "referee": raw,
            "genomes": {o.id: o.genome_hash for o in self.organisms},
            "energy": {a: self.arena.balances[a] for a in self.ids},
        }
        event_hash = hashlib.sha256(
            (self.previous_hash + "\n" + canonical(payload)).encode("ascii")
        ).hexdigest()
        event = {**payload, "previous_hash": self.previous_hash,
                 "event_hash": event_hash}
        self.previous_hash = event_hash
        self.events.append(event)
        return event

    def run(self, ticks: int) -> dict:
        if (type(ticks) is not int or not 1 <= ticks <= MAX_TICKS or
                ticks * len(self.ids) > MAX_WORK):
            raise ValueError("invalid tick count or excessive event volume")
        for _ in range(ticks):
            self.step()
        return self.report()

    def report(self) -> dict:
        energy = {a: self.arena.balances[a] for a in self.ids}
        summary = {
            "population": len(self.ids),
            "ticks": len(self.events),
            "survivors": sum(v > 0 for v in energy.values()),
            "final_energy": energy,
            "highest_energy": (
                max(self.ids, key=lambda a: (energy[a], -self.ids.index(a)))
            ),
            "actual_provider_calls": 0,
            "actual_provider_tokens": 0,
            "purpose": "Offline adapter/protocol proof; no evolving prompts or code",
        }
        report = {
            "manifest": self.manifest,
            "events": list(self.events),
            "summary": summary,
            "head": self.previous_hash,
        }
        return report


def build_report(seed: int, ticks: int, arena: str,
                 brains: tuple[str, ...]) -> dict:
    return PopulationSession(
        seed=seed, arena_name=arena, organisms=make_specs(brains)
    ).run(ticks)


def verify_report(report: object) -> dict:
    if (not isinstance(report, dict) or
            set(report) != {"manifest", "events", "summary", "head"} or
            not isinstance(report["manifest"], dict)):
        raise ValueError("invalid population report structure")
    m = report["manifest"]
    if set(m) != {"protocol", "seed", "arena", "arena_rules", "organisms",
                  "provider", "real_requests"} or m["protocol"] != VERSION:
        raise ValueError("invalid population manifest")
    specs = m["organisms"]
    if (not isinstance(specs, list) or not 2 <= len(specs) <= MAX_AGENTS
            or any(not isinstance(s, dict) or set(s) != {
                "id", "brain", "contract", "genome_hash"
            } for s in specs)):
        raise ValueError("invalid organism registry in report")
    if not isinstance(report["events"], list):
        raise ValueError("invalid event log")
    if not 1 <= len(report["events"]) <= MAX_TICKS or (
        len(report["events"]) * len(specs) > MAX_WORK
    ):
        raise ValueError("invalid replay length")
    brains = tuple(s["brain"] for s in specs)
    rebuilt = build_report(m["seed"], len(report["events"]), m["arena"], brains)
    if canonical(report) != canonical(rebuilt):
        raise ValueError("population report, action, genome or ledger mismatch")
    return {
        "verified": True, "head": rebuilt["head"], "summary": rebuilt["summary"]
    }


def verify_file(path: str) -> dict:
    source = Path(path)
    if not source.is_file() or source.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("missing or oversized population report")
    try:
        report = json.loads(source.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid population JSON") from exc
    return verify_report(report)


def run_population(args) -> dict:
    if args.provider != "fake":
        raise ValueError("population-v1 is offline only; select --provider fake")
    if not args.benchmark_out:
        raise ValueError("--population requires --benchmark-out NEW_FILE")
    target = Path(args.benchmark_out)
    if target.exists():
        raise ValueError("refusing to overwrite existing population report")
    if (type(args.population) is not int or
            not 2 <= args.population <= MAX_AGENTS):
        raise ValueError("--population must be 2..128")
    names = tuple(x.strip() for x in args.population_brains.split(","))
    if not names or any(not x for x in names):
        raise ValueError("empty organism policy")
    # Input is small explicit configuration; cycle policies, never dynamically
    # import arbitrary modules or evaluate model output.
    if len(names) > args.population:
        raise ValueError("more distinct policy entries than organisms")
    chosen = tuple(names[i % len(names)] for i in range(args.population))
    report = build_report(args.seed, args.ticks, args.population_arena, chosen)
    verify_report(report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return {"verified": True, "path": str(target), "head": report["head"],
            "summary": report["summary"]}
