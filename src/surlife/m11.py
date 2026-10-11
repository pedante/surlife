"""M1.1: post-outcome reflection, selective cognition and pending (not auto-accepted) souls.

The arena stays M0-v2; there is at most ONE charged model request per actor per
tick. A reflection uses the consultation slot and a cheap action that tick.
Proposals never change the active prompt until separate paired evaluation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from uuid import uuid4

from .core import AGENTS, POLICIES, RULES_VERSION, START_ENERGY, STAKE, Action, Arena
from .gateway import FakeGateway, GatewayError, OpenRouterGateway
from .model_registry import check_model
from .souls import Soul
from .storage import Journal

MAX_PENDING = 1
MAX_SEEN_TASKS = 4096


def task_fingerprint(task: dict) -> str:
    return hashlib.sha256(json.dumps(task, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass
class EvolutionSoul(Soul):
    pending: list[dict] = field(default_factory=list)
    evaluation_history: list[dict] = field(default_factory=list)
    seen_task_hashes: list[str] = field(default_factory=list)
    history_complete: bool = True

    @classmethod
    def restore(cls, actor: str, snapshot: str) -> "EvolutionSoul":
        base = Soul.restore(actor, snapshot)
        content = json.loads(Path(snapshot).read_text(encoding="utf-8"))
        pending = content.get("pending", [])
        seen = content.get("seen_task_hashes", [])
        complete = content.get("history_complete", False)
        if (not isinstance(seen, list) or len(seen) > MAX_SEEN_TASKS
                or any(not isinstance(x, str) or not re.fullmatch(r"[0-9a-f]{64}", x) for x in seen)
                or type(complete) is not bool):
            raise ValueError("invalid seen-task history")
        history = content.get("evaluation_history", [])
        if not isinstance(pending, list) or len(pending) > MAX_PENDING:
            raise ValueError("invalid pending revisions")
        for item in pending:
            if (not isinstance(item, dict) or not isinstance(item.get("note"), str)
                    or not 12 <= len(item["note"]) <= 120
                    or item.get("baseline_hash") != base.sha256
                    or type(item.get("tick")) is not int):
                raise ValueError("invalid pending revision")
        if (not isinstance(history, list) or len(history) > 30
                or any(not isinstance(item, dict) for item in history)):
            raise ValueError("invalid evaluation history")
        return cls(**base.__dict__, pending=pending, evaluation_history=history,
                   seen_task_hashes=seen, history_complete=complete)

    def save(self, run_dir: Path) -> None:
        """Atomically save complete lineage; inherited M1 snapshots remain compatible."""
        run_dir.mkdir(parents=True, exist_ok=True)
        final = run_dir / (self.actor + ".json")
        temp = run_dir / (self.actor + ".tmp")
        data = {
            "actor": self.actor, "base": self.base, "version": self.version,
            "notes": self.notes, "sha256": self.sha256,
            "memory": self.memory, "revisions": self.revisions,
            "pending": self.pending, "evaluation_history": self.evaluation_history,
            "seen_task_hashes": self.seen_task_hashes, "history_complete": self.history_complete,
        }
        with temp.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, sort_keys=True, indent=2)
            fp.write("\n")
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(temp, final)

    def observe_result(self, obs, mask: int | None, score: int | None,
                       optimum: int, reward: int, energy: int, source: str) -> None:
        self.observe(obs.tick, score, optimum, reward, energy)
        fingerprint = task_fingerprint(obs.task.as_dict())
        if fingerprint not in self.seen_task_hashes:
            self.seen_task_hashes.append(fingerprint)
            if len(self.seen_task_hashes) > MAX_SEEN_TASKS:
                self.history_complete = False
                self.seen_task_hashes.pop(0)
        cost = (sum(c for i, (c, _) in enumerate(obs.task.items) if mask & (1 << i))
                if type(mask) is int and 0 <= mask < (1 << len(obs.task.items)) else None)
        optimum_mask = max(range(1 << len(obs.task.items)),
                           key=lambda m: (obs.task.score(m), -m))
        self.memory[-1].update({
            "mask": mask, "selected_cost": cost, "capacity": obs.task.capacity,
            "legal": score is not None and score >= 0,
            "regret": optimum - score if score is not None and score >= 0 else None,
            "optimal_mask": optimum_mask, "items": [list(x) for x in obs.task.items],
            "decision_source": source,
        })

    def messages(self, obs) -> list[dict]:
        messages = super().messages(obs)
        # The action request cannot modify the active soul. Its output only
        # chooses a subset; reflection happens on a separate later turn.
        messages[0]["content"] = (
            "You are an organism competing to survive in a resource-allocation world. "
            "Return only the required JSON action: mask bit i selects item i, "
            "or null to wait. Compute the total selected cost and ENSURE it is "
            "not above capacity. Aim for the highest legal total reward. "
            "Do not propose soul notes in this action: set soul_update to empty. "
            "Your current strategy is:\n" + self.full_prompt
        )
        return messages

    def reflection_messages(self) -> list[dict]:
        previous = self.memory[-1]
        return [
            {"role": "system", "content": (
                "This is a SEPARATE reflection after a completed arena action. "
                "The referee already scored the decision. Propose at most one "
                "GENERAL, reusable strategy rule (<=120 characters), not a "
                "puzzle-specific calculation. Never include item indices, bit "
                "numbers, particular item costs, capacities or example values. "
                'Output JSON only: {"soul_update":"general reusable rule"} '
                'or {"soul_update":""} if no defensible improvement. '
                "The note is merely a hypothesis for separate evaluation."
            )},
            {"role": "user", "content": json.dumps(
                {"past_result": previous, "current_strategy": self.full_prompt},
                sort_keys=True,
            )},
        ]

    def stage(self, note: str, tick: int) -> bool:
        """Queue a general hypothesis. Never auto-activate an untested note."""
        note = " ".join(note.split()).strip()
        if (not 12 <= len(note) <= 120 or self.pending
                or self.version >= 3 or note in self.notes
                or len(self.full_prompt) + len(note) > 2000
                or re.search(r"\d|\bbit\b|\bitem\s+[a-z0-9]+", note, re.I)):
            return False
        if not self.memory:
            return False
        previous = self.memory[-1]
        if previous.get("decision_source") != "llm_action":
            return False
        if previous.get("score") == previous.get("optimum"):
            return False
        self.pending.append({"note": note, "tick": tick, "baseline_hash": self.sha256})
        return True

    def accept_pending(self, evaluation: dict) -> bool:
        if not self.pending:
            raise ValueError("no pending revision")
        current = self.pending.pop(0)
        approved = bool(evaluation["accepted"])
        if approved:
            self.notes.append(current["note"])
            self.version += 1
            self.revisions.append({
                "tick": current["tick"], "version": self.version,
                "sha256": self.sha256, "note": current["note"],
                "evaluation_seed": evaluation["seed"],
            })
        self.evaluation_history.append({
            **evaluation, "proposed_tick": current["tick"],
            "candidate_hash": hashlib.sha256(
                (self.full_prompt + current["note"]).encode("utf-8")
            ).hexdigest() if not approved else self.sha256,
        })
        self.evaluation_history[:] = self.evaluation_history[-30:]
        return approved


def can_spend(arena: Arena, actor: str, weather: str, min_energy: int = 1) -> bool:
    energy = arena.balances[actor]
    if energy <= 0:
        return False
    mint = 1 if arena.tick % 4 == 0 else 0
    upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
    return max(0, energy + mint - upkeep) >= max(1, min_energy)


def choose_mode(soul: EvolutionSoul, arena: Arena, actor: str,
                weather: str, cognition: str, gateway_remaining: int) -> str:
    """Host-owned deterministic *proxy* for selective cognition, not a learned policy."""
    if not gateway_remaining or not can_spend(arena, actor, weather):
        return "cheap"
    if cognition == "never":
        return "cheap"
    # Reflection is a separate call one tick AFTER a failed model action.
    # Greedy acts on the reflection tick, so at most one charged call/tick.
    if (not soul.pending and soul.version < 3 and soul.memory
            and soul.memory[-1].get("decision_source") == "llm_action"
            and soul.memory[-1]["score"] != soul.memory[-1]["optimum"]
            and can_spend(arena, actor, weather, min_energy=6)):
        return "reflection"
    if cognition == "always":
        return "action"
    if cognition == "selective" and arena.tick % 3 == 0 and can_spend(
        arena, actor, weather, min_energy=9
    ):
        return "action"
    return "cheap"


def run_m11(args, db_path: Path) -> dict:
    if args.a != "llm" or args.b not in POLICIES:
        raise ValueError("M1.1 currently supports --a llm against one scripted --b policy")
    if args.cognition not in ("always", "selective", "never"):
        raise ValueError("invalid cognition mode")
    if args.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required for --provider openrouter")
        check_model(args.model)
    gateway = (OpenRouterGateway(model=args.model, max_requests=args.max_requests,
                                 max_output_tokens=args.max_output_tokens,
                                 reasoning=args.reasoning)
               if args.provider == "openrouter" else FakeGateway(max_requests=args.max_requests))
    run_id = args.run_id or uuid4().hex[:12]
    root = Path(args.souls_dir) / run_id
    if root.exists():
        raise ValueError("souls directory exists; choose another run ID")
    source = getattr(args, "inherit_soul_a", None)
    custom = getattr(args, "soul_a", None)
    if source and custom:
        raise ValueError("choose only --soul-a or --inherit-soul-a")
    if source:
        soul = EvolutionSoul.restore("a", source)
    else:
        base = Soul.new("a", custom)
        soul = EvolutionSoul(**base.__dict__)

    arena = Arena(args.seed)
    manifest = {
        "rules": RULES_VERSION, "kind": "m12-observable-evolution" if getattr(args, "m12", False) else "m11-staged-evolution",
        "seed": args.seed, "start_energy": START_ENERGY, "stake": STAKE,
        "policies": {"a": "llm", "b": args.b},
        "cognition": args.cognition,
        "provider": args.provider, "requested_model": (
            args.model if args.provider == "openrouter" else "surlife/fake-model"
        ),
        "max_requests": args.max_requests, "max_output_tokens": args.max_output_tokens,
        "reasoning": args.reasoning if args.provider == "openrouter" else "fake",
        "initial_soul_hashes": {"a": soul.sha256},
    }
    stage_count = 0
    mode_counts = {"action": 0, "reflection": 0, "cheap": 0}
    with Journal(db_path) as journal:
        journal.create_run(run_id, manifest)
        soul.save(root)
        for _ in range(args.ticks):
            observations = arena.observations()
            a_obs, b_obs = observations["a"], observations["b"]
            b_action = (POLICIES[args.b](b_obs, Random(
                arena.seed * 1_000_003 + arena.tick * 9_176 + 2
            )) if b_obs.own_energy else Action(None))
            costs: dict[str, int] = {}
            stage_note = ""
            metadata: dict[str, dict] = {}
            if not a_obs.own_energy:
                a_action, mode = Action(None), "dead"
            else:
                mode = choose_mode(
                    soul, arena, "a", a_obs.weather, args.cognition, gateway.remaining
                )
                a_action = POLICIES["greedy"](a_obs, Random(0))
                if mode in ("action", "reflection"):
                    before = gateway.calls
                    try:
                        messages = (soul.messages(a_obs) if mode == "action"
                                    else soul.reflection_messages())
                        reply = gateway.ask(messages, mode=mode if mode == "reflection" else "action")
                        if mode == "action":
                            a_action = Action(reply.mask)
                        else:
                            stage_note = reply.soul_update
                        metadata["a"] = {
                            "status": "ok", "consulted": True, "mode": mode,
                            "model": reply.model, "usage": reply.usage,
                            "soul_version": soul.version, "soul_hash": soul.sha256,
                        }
                    except GatewayError as exc:
                        metadata["a"] = {
                            "status": "provider_or_parse_failure", "consulted": gateway.calls > before,
                            "mode": mode, "failure_reason": exc.reason,
                            "model": exc.model or gateway.model, "usage": exc.usage,
                            "soul_version": soul.version, "soul_hash": soul.sha256,
                        }
                        mode = "cheap"
                    if gateway.calls > before:
                        costs["a"] = 1
                else:
                    metadata["a"] = {"status": "cheap_fallback", "consulted": False,
                                     "mode": "cheap"}
            if mode in mode_counts:
                mode_counts[mode] += 1
            source = "llm_action" if mode == "action" and metadata.get("a", {}).get("status") == "ok" else (
                "greedy_during_reflection" if mode == "reflection" else "greedy_fallback"
            )
            record = arena.step({"a": a_action, "b": b_action}, costs)
            if a_obs.own_energy:
                soul.observe_result(
                    a_obs, a_action.mask, record["scores"]["a"],
                    record["optimal_score"], record["rewards"]["a"],
                    record["after"]["a"], source,
                )
                if stage_note and mode == "reflection":
                    # Reflection was conditioned on *previous* actual feedback;
                    # the current Greedy action is never used as proposal evidence.
                    previous = soul.memory[-2] if len(soul.memory) >= 2 else None
                    if previous:
                        # Stage against the failed LLM outcome, not today's Greedy outcome.
                        latest = soul.memory.pop()
                        accepted_for_evaluation = soul.stage(stage_note, arena.tick - 2)
                        soul.memory.append(latest)
                        if accepted_for_evaluation:
                            stage_count += 1
                    else:
                        accepted_for_evaluation = False
                    metadata["a"]["revision_pending"] = accepted_for_evaluation
            for actor, obs, action in (("a", a_obs, a_action), ("b", b_obs, b_action)):
                score = record["scores"][actor]
                selected_cost = (sum(c for i, (c, _) in enumerate(obs.task.items)
                                     if action.mask & (1 << i))
                                 if type(action.mask) is int and 0 <= action.mask < 32 else None)
                metadata.setdefault(actor, {}).update({
                    "action_source": source if actor == "a" else args.b,
                    "legal": score is not None and score >= 0,
                    "selected_cost": selected_cost,
                    "score_ratio": (round(score / record["optimal_score"], 6)
                                    if score is not None and score >= 0 else None),
                })
            if getattr(args, "m12", False):
                # Shadow baseline is observation-only: it NEVER replaces the
                # proposed model action or changes settlement, and is scored
                # against the exact same task for causal diagnostics.
                greedy_mask = POLICIES["greedy"](a_obs, Random(0)).mask
                greedy_score = a_obs.task.score(greedy_mask)
                model_score = record["scores"]["a"]
                metadata.setdefault("a", {}).update({
                    "shadow_greedy_mask": greedy_mask,
                    "shadow_greedy_score": greedy_score,
                    "delta_vs_greedy": (model_score - greedy_score
                                        if model_score is not None else None),
                    "decision_cost": record["consultations"]["a"],
                })
            record["model_calls"] = metadata
            journal.append(run_id, record)
            soul.save(root)
        report = journal.replay(run_id)
    report.update({
        "kind": manifest["kind"], "provider": args.provider,
        "model_requests": gateway.calls, "max_requests": gateway.limit,
        "requested_model": manifest["requested_model"], "cognition": args.cognition,
        "consultation_modes": mode_counts, "pending_revisions": len(soul.pending),
        "staged_revisions": stage_count, "soul_versions": {"a": soul.version},
        "soul_dir": str(root),
        "note": "Candidates are NOT activated until a separate paired held-out evaluation accepts them.",
    })
    return report
