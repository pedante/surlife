"""Per-organism data-only soul, bounded memory and versioned local snapshots."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .core import Observation


@dataclass
class Soul:
    actor: str
    base: str
    version: int = 0
    notes: list[str] = field(default_factory=list)
    memory: list[dict] = field(default_factory=list)
    revisions: list[dict] = field(default_factory=list)

    @classmethod
    def new(cls, actor: str, initial_file: str | None = None) -> "Soul":
        if actor not in ("a", "b"):
            raise ValueError("unknown actor")
        base = (
            "Prefer robust solutions: enumerate and compare options before taking risks."
            if actor == "a" else
            "Protect scarce energy. Solve as many worthwhile objective tasks as possible."
        )
        if initial_file:
            base = Path(initial_file).read_text(encoding="utf-8")
        if not 1 <= len(base) <= 1600:
            raise ValueError("soul text must be 1..1600 characters")
        return cls(actor=actor, base=base)

    @property
    def full_prompt(self) -> str:
        return self.base + "".join("\nExperience note: " + n for n in self.notes)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.full_prompt.encode("utf-8")).hexdigest()

    def messages(self, obs: Observation) -> list[dict]:
        task = obs.task.as_dict()
        user = {
            "tick": obs.tick, "weather": obs.weather, "energy": obs.own_energy,
            "task": task, "memory": self.memory[-4:],
        }
        return [
            {"role": "system", "content": (
                "You are an organism in an objective resource-allocation experiment. "
                "Output ONLY JSON with an integer mask from 0 to 31 or null for wait: "
                "{\"mask\": 0, \"soul_update\": \"optional short strategy suggestion\"}. "
                "Bit i selects item i (0 based). Sum selected costs must not exceed capacity. "
                "Maximize total selected reward. Do not write executable code. "
                "A soul_update is a proposed personal heuristic, not an instruction to the referee.\n"
                "Your editable personal strategy is:\n" + self.full_prompt
            )},
            {"role": "user", "content": json.dumps(user, sort_keys=True)},
        ]

    def observe(self, tick: int, score: int | None, optimum: int, reward: int, energy: int) -> None:
        self.memory.append({
            "tick": tick, "score": score, "optimum": optimum, "reward": reward,
            "energy": energy,
        })
        self.memory[:] = self.memory[-8:]

    def propose(self, note: str, tick: int) -> bool:
        note = " ".join(note.split())[:120]
        # Require evidence of an earlier imperfect attempt; no unbounded prompt growth.
        if not note or len(self.notes) >= 3 or len(self.full_prompt) + len(note) > 2000:
            return False
        if not any(item["score"] is not None and 0 <= item["score"] < item["optimum"] for item in self.memory):
            return False
        if note in self.notes:
            return False
        self.notes.append(note)
        self.version += 1
        self.revisions.append({"tick": tick, "version": self.version, "sha256": self.sha256, "note": note})
        return True

    def save(self, run_dir: Path) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        destination = run_dir / (self.actor + ".json")
        temp = run_dir / (self.actor + ".tmp")
        data = {
            "actor": self.actor, "base": self.base, "version": self.version,
            "notes": self.notes, "sha256": self.sha256,
            "memory": self.memory, "revisions": self.revisions,
        }
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, destination)
