"""One locally controlled M1 experiment with LLM souls and replayable referee state."""
from __future__ import annotations

import json
import os
from pathlib import Path
from random import Random
from uuid import uuid4

from .core import (
    AGENTS, COGNITION_COST, POLICIES, RULES_VERSION, START_ENERGY, STAKE,
    Action, Arena,
)
from .gateway import FakeGateway, GatewayError, OpenRouterGateway
from .souls import Soul
from .storage import Journal


def can_consult(arena: Arena, actor: str, weather: str) -> bool:
    """Do not place a call that the organism cannot pay for after known upkeep."""
    bal = arena.balances[actor]
    if bal <= 0:
        return False
    mint = 1 if arena.tick % 4 == 0 else 0
    upkeep = {"normal": 1, "fog": 2, "drought": 3}[weather]
    return max(0, bal + mint - upkeep) >= COGNITION_COST


def run_m1(args, db_path: Path) -> dict:
    if args.provider == "openrouter" and any(p == "llm" for p in (args.a, args.b)):
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required for --provider openrouter")
    gateway = (OpenRouterGateway(model=args.model, max_requests=args.max_requests,
                                 max_output_tokens=args.max_output_tokens)
               if args.provider == "openrouter" else FakeGateway(max_requests=args.max_requests))
    policies = {"a": args.a, "b": args.b}
    run_id = args.run_id or uuid4().hex[:12]
    root = Path(args.souls_dir) / run_id
    if root.exists():
        raise ValueError("souls directory exists; choose another run_id (M1 resume not yet implemented)")
    souls = {
        a: Soul.new(a, getattr(args, "soul_" + a)) for a in AGENTS if policies[a] == "llm"
    }
    arena = Arena(args.seed)
    manifest = {
        "rules": RULES_VERSION, "kind": "m1-prompt-souls",
        "seed": args.seed, "start_energy": START_ENERGY, "stake": STAKE,
        "policies": policies, "provider": args.provider,
        "requested_model": args.model if args.provider == "openrouter" else "surlife/fake-model",
        "max_requests": args.max_requests, "max_output_tokens": args.max_output_tokens,
        "initial_soul_hashes": {a: s.sha256 for a, s in souls.items()},
    }
    with Journal(db_path) as journal:
        journal.create_run(run_id, manifest)
        for soul in souls.values():
            soul.save(root)
        for _ in range(args.ticks):
            observations = arena.observations()
            actions: dict[str, Action] = {}
            consultations: dict[str, int] = {}
            metadata: dict[str, dict] = {}
            proposed: dict[str, str] = {}
            for a in AGENTS:
                obs = observations[a]
                if obs.own_energy <= 0:
                    actions[a] = Action(None)
                    continue
                if policies[a] in POLICIES:
                    actions[a] = POLICIES[policies[a]](
                        obs, Random(arena.seed * 1_000_003 + arena.tick * 9_176 + (1 if a == "a" else 2))
                    )
                    continue
                if not gateway.remaining or not can_consult(arena, a, obs.weather):
                    actions[a] = POLICIES["greedy"](obs, Random(0))
                    metadata[a] = {"status": "cheap_fallback", "consulted": False}
                    continue
                prior = gateway.calls
                soul = souls[a]
                try:
                    reply = gateway.ask(soul.messages(obs))
                    actions[a] = Action(reply.mask)
                    proposed[a] = reply.soul_update
                    metadata[a] = {
                        "status": "ok", "consulted": True, "model": reply.model,
                        "usage": reply.usage, "soul_version": soul.version,
                        "soul_hash": soul.sha256,
                    }
                except GatewayError:
                    actions[a] = POLICIES["greedy"](obs, Random(0))
                    metadata[a] = {"status": "provider_or_parse_failure", "consulted": gateway.calls > prior,
                                   "model": gateway.model, "usage": None,
                                   "soul_version": soul.version, "soul_hash": soul.sha256}
                if gateway.calls > prior:
                    consultations[a] = 1  # charged even for failed/unknown-usage calls

            record = arena.step(actions, consultations)
            for a, soul in souls.items():
                soul.observe(arena.tick - 1, record["scores"][a], record["optimal_score"],
                             record["rewards"][a], record["after"][a])
                changed = soul.propose(proposed.get(a, ""), arena.tick - 1)
                if a in metadata:
                    metadata[a]["revision_accepted"] = changed
                    metadata[a]["soul_version_after"] = soul.version
            record["model_calls"] = metadata
            journal.append(run_id, record)
            for soul in souls.values():
                soul.save(root)
        report = journal.replay(run_id)

    report.update({
        "provider": args.provider, "requested_model": manifest["requested_model"],
        "model_requests": gateway.calls, "max_requests": gateway.limit,
        "soul_versions": {a: s.version for a, s in souls.items()},
        "soul_dir": str(root),
        "note": "M1 prompts are editable, but automatic changes are unvalidated hypotheses; no code mutation.",
    })
    return report
