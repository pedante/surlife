"""SQLite transaction journal for one local world; verifiable, not tamper-proof.

Transactions atomically save each tick and its virtual balance transfers.
Replay uses stored policy *actions*, not regenerated policies or model outputs.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .core import Action, AGENTS, Arena, RULES_VERSION


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(prev: str, payload: str) -> str:
    return hashlib.sha256((prev + "\n" + payload).encode("utf-8")).hexdigest()


class Journal:
    def __init__(self, db: str | Path):
        self.db = sqlite3.connect(str(db), timeout=5, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, manifest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rounds (
                run_id TEXT NOT NULL, tick INTEGER NOT NULL, payload TEXT NOT NULL,
                previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
                PRIMARY KEY (run_id, tick),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );
            CREATE TABLE IF NOT EXISTS transfers (
                run_id TEXT NOT NULL, tick INTEGER NOT NULL, seq INTEGER NOT NULL,
                source TEXT NOT NULL, destination TEXT NOT NULL, amount INTEGER NOT NULL, kind TEXT NOT NULL,
                PRIMARY KEY(run_id, tick, seq)
            );
        """)
        self.db.execute("PRAGMA foreign_keys=ON")

    def __enter__(self) -> "Journal":
        return self

    def __exit__(self, *_: object) -> None:
        self.db.close()

    def create_run(self, run_id: str, manifest: dict) -> None:
        if not run_id or len(run_id) > 128 or manifest.get("rules") != RULES_VERSION:
            raise ValueError("invalid run metadata")
        content = canonical(manifest)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT manifest FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if old is None:
                self.db.execute("INSERT INTO runs VALUES (?,?)", (run_id, content))
            elif old[0] != content:
                raise ValueError("run ID already used for different manifest")
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def append(self, run_id: str, record: dict) -> str:
        payload = canonical(record)
        tick = record["tick"]
        if type(tick) is not int or tick < 0:
            raise ValueError("invalid tick")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute("SELECT tick, event_hash FROM rounds WHERE run_id=? ORDER BY tick DESC LIMIT 1", (run_id,)).fetchone()
            existing = self.db.execute("SELECT payload, event_hash FROM rounds WHERE run_id=? AND tick=?", (run_id, tick)).fetchone()
            if existing:
                if existing[0] != payload:
                    raise ValueError("conflicting repeat of settled tick")
                self.db.execute("COMMIT")
                return existing[1]
            if not self.db.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
                raise ValueError("unknown run ID")
            if tick != (prior[0] + 1 if prior else 0):
                raise ValueError("tick gap or out-of-order settlement")
            previous_hash = prior[1] if prior else "GENESIS"
            event_hash = digest(previous_hash, payload)
            self.db.execute("INSERT INTO rounds VALUES (?,?,?,?,?)", (run_id, tick, payload, previous_hash, event_hash))
            for i, t in enumerate(record["transfers"]):
                self.db.execute("INSERT INTO transfers VALUES (?,?,?,?,?,?,?)",
                                (run_id, tick, i, t["from"], t["to"], t["amount"], t["kind"]))
            self.db.execute("COMMIT")
            return event_hash
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def replay(self, run_id: str) -> dict:
        row = self.db.execute("SELECT manifest FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("unknown run")
        manifest = json.loads(row[0])
        if manifest["rules"] != RULES_VERSION:
            raise ValueError("unsupported rules version")
        arena = Arena(manifest["seed"], manifest["start_energy"], manifest["stake"])
        prev = "GENESIS"
        wins = {"a": 0, "b": 0}
        correct = {"a": 0, "b": 0}
        entered = 0
        attempts = {"a": 0, "b": 0}
        legal_attempts = {"a": 0, "b": 0}
        invalid_attempts = {"a": 0, "b": 0}
        score_ratio_sums = {"a": 0.0, "b": 0.0}
        total_regret = {"a": 0, "b": 0}
        consultation_modes: dict[str, int] = {}
        by_action_source: dict[str, dict] = {}
        shadow_llm = {"compared": 0, "better": 0, "same": 0, "worse": 0,
                      "total_score_delta": 0}
        earned = {"a": 0, "b": 0}
        consultations = {"a": 0, "b": 0}
        n = 0
        provider_requests = 0
        usage_missing = 0
        usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        routed_models = {}
        failure_reasons: dict[str, int] = {}
        for tick, payload, previous_hash, event_hash in self.db.execute(
            "SELECT tick, payload, previous_hash, event_hash FROM rounds WHERE run_id=? ORDER BY tick", (run_id,)
        ):
            if tick != n or previous_hash != prev or digest(prev, payload) != event_hash:
                raise ValueError("journal order/hash mismatch")
            data = json.loads(payload)
            actions = {a: Action(data["actions"][a]) for a in AGENTS}
            expected = arena.step(actions, data.get("consultations"))
            replay_data = dict(data)
            replay_data.pop("model_calls", None)  # provider logs are observations, not referee authority
            if canonical(expected) != canonical(replay_data):
                raise ValueError("recorded transition violates referee replay")
            saved_transfers = [dict(zip(("from", "to", "amount", "kind"), t)) for t in self.db.execute(
                "SELECT source, destination, amount, kind FROM transfers WHERE run_id=? AND tick=? ORDER BY seq", (run_id, tick))]
            if saved_transfers != expected["transfers"]:
                raise ValueError("transaction ledger disagrees with recorded world")
            for meta in data.get("model_calls", {}).values():
                if meta.get("status") == "provider_or_parse_failure":
                    reason = str(meta.get("failure_reason", "unspecified"))
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                if not meta.get("consulted"):
                    continue
                mode = str(meta.get("mode", "action"))
                consultation_modes[mode] = consultation_modes.get(mode, 0) + 1
                provider_requests += 1
                model = str(meta.get("model", "unknown"))
                routed_models[model] = routed_models.get(model, 0) + 1
                usage = meta.get("usage")
                if not isinstance(usage, dict) or any(type(usage.get(k)) is not int for k in usage_totals):
                    usage_missing += 1
                else:
                    for k in usage_totals:
                        usage_totals[k] += usage[k]
            for actor in AGENTS:
                info = data.get("model_calls", {}).get(actor, {})
                source = str(info.get("action_source", manifest.get("policies", {}).get(actor, "scripted")))
                row = by_action_source.setdefault(source, {
                    "attempts": 0, "legal": 0, "invalid": 0, "optimal": 0,
                    "score_sum": 0, "optimum_sum": 0,
                })
                if expected["attempted"][actor]:
                    row["attempts"] += 1
                    score = expected["scores"][actor]
                    row["optimum_sum"] += expected["optimal_score"]
                    if score is not None and score >= 0:
                        row["legal"] += 1
                        row["score_sum"] += score
                    else:
                        row["invalid"] += 1
                    if score == expected["optimal_score"]:
                        row["optimal"] += 1
                if (actor == "a" and source == "llm_action"
                        and type(info.get("delta_vs_greedy")) is int):
                    delta = info["delta_vs_greedy"]
                    shadow_llm["compared"] += 1
                    shadow_llm["total_score_delta"] += delta
                    shadow_llm["better" if delta > 0 else "worse" if delta < 0 else "same"] += 1
            if expected["entered"]:
                entered += 1
            for a in AGENTS:
                attempts[a] += int(expected["attempted"][a])
                if expected["attempted"][a]:
                    score = expected["scores"][a]
                    if score is not None and score >= 0:
                        legal_attempts[a] += 1
                        score_ratio_sums[a] += score / expected["optimal_score"]
                        total_regret[a] += expected["optimal_score"] - score
                    else:
                        invalid_attempts[a] += 1
                correct[a] += int(expected["attempted"][a] and expected["scores"][a] == expected["optimal_score"])
                earned[a] += expected["rewards"][a]
                consultations[a] += expected["consultations"][a]
            if expected["winner"]:
                wins[expected["winner"]] += 1
            n += 1
            prev = event_hash
        return {"run_id": run_id, "rounds": n, "head": prev, "balances": arena.balances,
                "wins": wins, "correct": correct, "attempts": attempts,
                "earned": earned, "consultations": consultations,
                "alive": {a: arena.balances[a] > 0 for a in AGENTS},
                "entered": entered, "verified": True,
                "provider_requests": provider_requests, "reported_tokens": usage_totals,
                "unknown_usage_requests": usage_missing, "routed_models": routed_models,
                "failure_reasons": failure_reasons,
                "legal_attempts": legal_attempts, "invalid_attempts": invalid_attempts,
                "mean_score_ratio": {a: round(score_ratio_sums[a] / attempts[a], 4)
                                     if attempts[a] else None for a in AGENTS},
                "total_legal_regret": total_regret,
                "consultation_modes": consultation_modes,
                "by_action_source": by_action_source, "llm_vs_shadow_greedy": shadow_llm}
