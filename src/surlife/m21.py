"""M2.1 experimental organism-owned prompt mutation, OFFLINE fake model only.

This tests *control flow*, not LLM intelligence. A scripted fake consultation
responds to versioned prompt text. The trusted M0-v2 referee remains unchanged.
No external provider, generated source execution, or world ecology is involved.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .core import AGENTS, Action, Arena, greedy, optimal
from .souls import Soul
from .storage import canonical

VERSION = "m21-v1"
MAX_TICKS = 64
MAX_REQUESTS = 24
MAX_REPORT_BYTES = 3_000_000
TRIALS_REQUIRED = 3
MODES = ("evolving", "frozen")
# The following text/behavior is an explicitly SCRIPTED fake-provider fixture.
SUGGESTION = "Enumerate legal subsets and compare total reward before selecting a mask."
STRATEGY_MARKER = "Enumerate legal subsets"


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def task_key(task) -> str:
    return digest(task.as_dict())


class ScriptedModel:
    """Deterministic test double. Not a trained agent, prompt optimizer or API."""

    def __init__(self, limit: int):
        self.limit = limit
        self.calls = 0

    @property
    def remaining(self) -> int:
        return self.limit - self.calls

    def ask(self, actor: str, tick: int, kind: str, prompt: str, task=None) -> tuple[Any, dict]:
        if self.remaining <= 0:
            raise ValueError("fake model request limit exhausted")
        if kind not in ("reflection", "trial", "work"):
            raise ValueError("invalid consultation")
        self.calls += 1
        answer = SUGGESTION if kind == "reflection" else (
            optimal(task, None).mask if STRATEGY_MARKER in prompt
            else greedy(task, None).mask
        )
        record = {
            "request": self.calls, "actor": actor, "tick": tick, "kind": kind,
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "task_hash": task_key(task.task) if task is not None else None,
            "response_hash": digest(answer),
            "provider": "scripted-fake", "model": "m21/fake-prompt-fixture",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return answer, record


@dataclass
class Individual:
    actor: str
    mode: str
    soul: Soul
    pending: dict | None = None
    trials: list[dict] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    imperfect: bool = False
    attempted_revision: bool = False
    events: list[dict] = field(default_factory=list)

    def decide(self, tick: int, can_call: bool) -> str:
        """Initial organism-owned metapolicy; deterministic trusted fixture."""
        if self.mode == "frozen":
            return "work"
        if self.pending is not None:
            if len(self.trials) >= TRIALS_REQUIRED:
                return "decide_revision"
            return "trial_pending" if can_call else "work"
        if self.imperfect and not self.attempted_revision and can_call:
            return "propose_prompt"
        if self.soul.version and can_call and tick % 3 == 1:
            return "consult_work"
        return "work"


def _holdout(seed: int, actor: str, index: int, excluded: set[str]):
    """Fixed separate seed namespace; no repeated/exposed live puzzle allowed."""
    for attempt in range(512):
        candidate = Arena(seed + 900_001 + index * 37_117
                          + (0 if actor == "a" else 4_000_019)
                          + attempt * 107).observations()[actor]
        if task_key(candidate.task) not in excluded:
            return candidate
    raise ValueError("unable to sample disjoint trial puzzle")


def _can_call(arena: Arena, actor: str, remaining: int, weather: str) -> bool:
    energy = arena.balances[actor]
    mint = int(arena.tick % 4 == 0 and energy > 0)
    upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
    return remaining > 0 and energy > 0 and max(0, energy + mint - upkeep) >= 1


def _start_candidate(individual: Individual, note: str, tick: int) -> dict:
    note = " ".join(note.split())
    if (not 12 <= len(note) <= 120 or re.search(r"[\x00-\x1f]", note)
            or note in individual.soul.notes or individual.soul.version >= 3
            or len(individual.soul.full_prompt) + len(note) + 18 > 2000):
        return {"decision": "invalid_proposal"}
    if not individual.imperfect:
        return {"decision": "no_failed_experience"}
    parent = individual.soul.sha256
    candidate_prompt = individual.soul.full_prompt + "\nExperience note: " + note
    individual.pending = {
        "note": note, "parent_hash": parent,
        "candidate_hash": hashlib.sha256(candidate_prompt.encode("utf-8")).hexdigest(),
        "proposed_tick": tick,
    }
    return {"decision": "staged", **individual.pending}


def _finish_candidate(individual: Individual, tick: int) -> dict:
    pending = individual.pending
    if pending is None or len(individual.trials) != TRIALS_REQUIRED:
        raise ValueError("incomplete candidate evaluation")
    if individual.soul.sha256 != pending["parent_hash"]:
        raise ValueError("candidate parent does not match active soul")
    gains = [t["candidate_score"] - t["baseline_score"] for t in individual.trials]
    accepted = all(g >= 0 for g in gains) and sum(gains) >= 1 and all(
        t["candidate_score"] >= 0 for t in individual.trials
    )
    result = {
        "decision": "activated" if accepted else "rejected",
        "parent_hash": pending["parent_hash"],
        "candidate_hash": pending["candidate_hash"],
        "trial_gain": sum(gains), "trial_count": len(gains),
        "paid_trial_requests": len(gains),
    }
    if accepted:
        individual.soul.notes.append(pending["note"])
        individual.soul.version += 1
        individual.soul.revisions.append({
            "tick": tick, "version": individual.soul.version,
            "sha256": individual.soul.sha256, "note": pending["note"],
            "parent_sha256": pending["parent_hash"],
            "candidate_sha256": pending["candidate_hash"],
        })
        if individual.soul.sha256 != pending["candidate_hash"]:
            raise AssertionError("activated prompt hash differs from trialed bytes")
    individual.pending = None
    individual.trials = []
    return result


def _episode(seed: int, ticks: int, modes: dict[str, str],
             max_requests: int) -> dict:
    arena = Arena(seed)
    model = ScriptedModel(max_requests)
    players = {actor: Individual(actor, modes[actor], Soul.new(actor))
               for actor in AGENTS}
    rows: list[dict] = []
    consultations: list[dict] = []
    history: list[dict] = []
    for tick in range(ticks):
        observations = arena.observations()
        actions: dict[str, Action] = {}
        charged: dict[str, int] = {}
        intents: dict[str, str] = {}
        mutations: list[dict] = []
        before = {a: players[a].soul.sha256 for a in AGENTS}
        for actor in AGENTS:
            player = players[actor]
            obs = observations[actor]
            # A dead organism cannot consult, mutate or be resurrected.
            if obs.own_energy <= 0:
                intents[actor] = "dead"
                actions[actor] = Action(None)
                continue
            can_call = _can_call(arena, actor, model.remaining, obs.weather)
            intent = player.decide(tick, can_call)
            intents[actor] = intent
            actions[actor] = greedy(obs, None)
            if intent == "propose_prompt":
                note, request = model.ask(actor, tick, "reflection", player.soul.full_prompt)
                consultations.append(request)
                charged[actor] = 1
                player.attempted_revision = True
                event = _start_candidate(player, note, tick)
                mutations.append({"actor": actor, **event})
                player.events.append({"tick": tick, **event})
            elif intent == "trial_pending":
                if player.pending is None:
                    raise AssertionError("trial without candidate")
                excluded = set(player.seen)
                excluded.update(task_key(row.task) for row in observations.values())
                excluded.update(trial["task_hash"] for trial in player.trials)
                trial_obs = _holdout(seed, actor, len(player.trials), excluded)
                candidate_prompt = (player.soul.full_prompt + "\nExperience note: "
                                    + player.pending["note"])
                answer, request = model.ask(
                    actor, tick, "trial", candidate_prompt, trial_obs
                )
                consultations.append(request)
                charged[actor] = 1
                baseline = greedy(trial_obs, None).mask
                record = {
                    "task_hash": task_key(trial_obs.task),
                    "baseline_score": trial_obs.task.score(baseline),
                    "candidate_score": trial_obs.task.score(answer),
                    "candidate_mask": answer, "baseline_mask": baseline,
                }
                player.trials.append(record)
                mutations.append({"actor": actor, "decision": "trial",
                                  "candidate_hash": player.pending["candidate_hash"],
                                  **record})
            elif intent == "decide_revision":
                event = _finish_candidate(player, tick)
                mutations.append({"actor": actor, **event})
                player.events.append({"tick": tick, **event})
            elif intent == "consult_work":
                answer, request = model.ask(actor, tick, "work",
                                            player.soul.full_prompt, obs)
                consultations.append(request)
                charged[actor] = 1
                # Do not repair invalid model output; the referee scores it.
                actions[actor] = Action(answer)
        row = arena.step(actions, consultations=charged)
        for actor in AGENTS:
            p = players[actor]
            p.seen.add(task_key(observations[actor].task))
            score = row["scores"][actor]
            if score is not None and score >= 0 and score < row["optimal_score"]:
                p.imperfect = True
            if score is not None:
                p.soul.observe(tick, score, row["optimal_score"],
                               row["rewards"][actor], row["after"][actor])
        row["intents"] = intents
        row["mutations"] = mutations
        row["genomes_before"] = before
        row["genomes_after"] = {a: players[a].soul.sha256 for a in AGENTS}
        rows.append(row)
    summaries = {
        actor: {
            "mode": modes[actor], "final_energy": arena.balances[actor],
            "alive": arena.balances[actor] > 0,
            "soul_version": players[actor].soul.version,
            "soul_hash": players[actor].soul.sha256,
            "active_prompt": players[actor].soul.full_prompt,
            "pending": players[actor].pending,
            "trial_results": players[actor].trials,
            "revision_events": players[actor].events,
            "consultations": sum(c["actor"] == actor for c in consultations),
        } for actor in AGENTS
    }
    return {"ticks": rows, "consultations": consultations,
            "organisms": summaries,
            "final_balances": arena.balances,
            "fake_requests": model.calls}


def build_report(seed: int, ticks: int, a: str = "evolving",
                 b: str = "frozen", max_requests: int = 8) -> dict:
    if type(seed) is not int or seed < 0:
        raise ValueError("M2.1 requires a nonnegative seed")
    if type(ticks) is not int or not 2 <= ticks <= MAX_TICKS:
        raise ValueError("M2.1 requires 2..64 ticks")
    if a not in MODES or b not in MODES:
        raise ValueError("invalid organism mode")
    if type(max_requests) is not int or not 1 <= max_requests <= MAX_REQUESTS:
        raise ValueError("M2.1 request budget must be 1..24")
    manifest = {
        "experiment": VERSION, "seed": seed, "ticks": ticks,
        "a": a, "b": b, "provider": "scripted-fake",
        "max_requests": max_requests, "referee": "m0-v2",
        "trial_count": TRIALS_REQUIRED,
    }
    episodes = {
        "primary": _episode(seed, ticks, {"a": a, "b": b}, max_requests),
        "frozen_control": _episode(
            seed, ticks, {"a": "frozen", "b": "frozen"}, max_requests
        ),
    }
    summary = {
        "a_energy_difference_vs_frozen":
            episodes["primary"]["organisms"]["a"]["final_energy"]
            - episodes["frozen_control"]["organisms"]["a"]["final_energy"],
        "primary_fake_requests": episodes["primary"]["fake_requests"],
        "control_fake_requests": episodes["frozen_control"]["fake_requests"],
        "actual_provider_requests": 0, "actual_provider_tokens": 0,
        "claims": "Scripted provider tests mutation plumbing only, NOT autonomous LLM learning.",
        "unpriced_optimal_reference": True,
    }
    report = {"manifest": manifest, "episodes": episodes, "summary": summary}
    report["head"] = digest(report)
    return report


def verify_report(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
        raise ValueError("invalid M2.1 report")
    m = report["manifest"]
    if set(m) != {"experiment", "seed", "ticks", "a", "b", "provider",
                  "max_requests", "referee", "trial_count"}:
        raise ValueError("invalid M2.1 manifest keys")
    if (m["experiment"] != VERSION or m["provider"] != "scripted-fake"
            or m["referee"] != "m0-v2" or m["trial_count"] != TRIALS_REQUIRED):
        raise ValueError("unsupported M2.1 manifest")
    expected = build_report(m["seed"], m["ticks"], m["a"], m["b"],
                            m["max_requests"])
    if canonical(report) != canonical(expected):
        raise ValueError("M2.1 action, mutation, accounting or digest mismatch")
    return {"verified": True, "head": expected["head"],
            "summary": expected["summary"]}


def verify_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("missing/oversized M2.1 report")
    try:
        report = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid M2.1 report JSON") from exc
    return verify_report(report)


def run_m21(args) -> dict:
    if args.provider != "fake":
        raise ValueError("M2.1 prototype is OFFLINE ONLY; choose --provider fake")
    if not args.benchmark_out:
        raise ValueError("M2.1 requires --benchmark-out FILE")
    target = Path(args.benchmark_out)
    if target.exists():
        raise ValueError("M2.1 will not overwrite an existing report")
    report = build_report(args.seed, args.ticks, args.m21_a,
                          args.m21_b, args.max_requests)
    verify_report(report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return {"verified": True, "report_path": str(target),
            "head": report["head"], "summary": report["summary"]}
