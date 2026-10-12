"""M2.1-C: opt-in response-bank prompt evolution, with strictly gated free provider.

Independent version m21c-v1. M2.1-v1 and all earlier referee reports stay intact.
All model-dependent outcomes can be rebuilt from recorded bounded responses;
the verifier never calls a model. Code authored by organisms is never executed.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .core import AGENTS, Action, Arena, Observation, Task, greedy, optimal
from .gateway import GatewayError, OpenRouterGateway, Reply, normalized_usage
from .m21 import Individual, _can_call, _holdout, _start_candidate, digest, task_key
from .souls import Soul
from .storage import canonical

VERSION = "m21c-v1"
PROMPT_VERSION = "m21c-paired-prompt-v1"
MAX_TICKS = 64
MAX_REQUESTS = 12
MAX_LIVE_REQUESTS = 8
MAX_REPORT_BYTES = 4_000_000
PAIRS_REQUIRED = 2
FIXTURE_MODEL = "m21c/fixture"
NOTE = "Enumerate legal subsets and compare total reward before selecting a mask."
MARKER = "Enumerate legal subsets"
MODES = ("evolving", "frozen")
FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _messages(kind: str, prompt: str, obs: Observation | None,
              last: dict | None) -> list[dict]:
    if kind == "reflection":
        if obs is not None:
            raise ValueError("reflection cannot see an unreleased trial")
        return [
            {"role": "system", "content": (
                "You are proposing ONE short, GENERAL strategy refinement for "
                "your own organism. Do not edit referee rules or another organism. "
                "Do not request tools or runnable code. Output JSON only with "
                "soul_update as a strategy note, or empty if no useful proposal. "
                "Your existing editable strategy: " + prompt
            )},
            {"role": "user", "content": json.dumps(
                {"feedback": last or {}, "question":
                 "What reusable decision rule might reduce future errors?"},
                sort_keys=True,
            )},
        ]
    if kind not in ("baseline", "candidate", "work") or obs is None:
        raise ValueError("invalid model question")
    return [
        {"role": "system", "content": (
            "You are competing in an objective resource-allocation task. "
            "Choose a subset of five items, bit i selects item i. Total cost "
            "must not exceed capacity. Maximize reward. Return JSON with integer "
            "mask or null to abstain and an empty soul_update. No executable "
            "tools or mutations in this action. Your editable strategy: " + prompt
        )},
        {"role": "user", "content": json.dumps({
            "tick": obs.tick, "weather": obs.weather,
            "energy": obs.own_energy, "task": obs.task.as_dict()
        }, sort_keys=True)},
    ]


class FixtureGateway:
    """Offline MODEL STUB. Prompt-sensitive answers are programmed, not learned."""

    model = FIXTURE_MODEL

    def ask(self, messages: list[dict], *, mode: str) -> Reply:
        if mode == "reflection":
            return Reply(None, NOTE, self.model, {key: 0 for key in FIELDS})
        data = json.loads(messages[-1]["content"])
        raw = data["task"]
        task = Task(tuple(tuple(item) for item in raw["items"]), raw["capacity"])
        obs = Observation(data["tick"], data["weather"], task, data["energy"])
        mask = (optimal if MARKER in messages[0]["content"] else greedy)(obs, None).mask
        return Reply(mask, "", self.model, {key: 0 for key in FIELDS})


@dataclass
class MutationState:
    paired: list[dict] = field(default_factory=list)
    unfinished: dict | None = None
    rejected_reason: str | None = None


class ResponseDriver:
    """Every admitted request gets exactly one immutable, replayable bank entry."""

    def __init__(self, *, limit: int, provider: str, model: str,
                 gateway=None, bank: list[dict] | None = None):
        self.limit = limit
        self.provider = provider
        self.model = model
        self.gateway = gateway
        self.replay_bank = bank
        self.entries: list[dict] = []
        self.blocked = False
        self.aborted_reason: str | None = None
        self.index = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - len(self.entries)) if not self.blocked else 0

    def ask(self, actor: str, tick: int, kind: str, prompt: str,
            obs: Observation | None, feedback: dict | None) -> tuple[Any, dict]:
        if self.remaining == 0:
            raise ValueError("admission cap exhausted")
        messages = _messages(kind, prompt, obs, feedback)
        request = {
            "request": len(self.entries) + 1,
            "actor": actor, "tick": tick, "kind": kind,
            "prompt_hash": _hash_prompt(prompt),
            "task_hash": task_key(obs.task) if obs is not None else None,
            "messages_hash": digest(messages),
        }
        if self.replay_bank is not None:
            if self.index >= len(self.replay_bank):
                raise ValueError("response bank exhausted")
            stored = self.replay_bank[self.index]
            self.index += 1
            if not isinstance(stored, dict) or not all(
                stored.get(key) == val for key, val in request.items()
            ):
                raise ValueError("bank context or request mismatch")
            response = stored.get("response")
            if not isinstance(response, dict):
                raise ValueError("malformed bank response")
            record = stored
        else:
            response = self._collect(messages, kind)
            record = {**request, "response": response}
        self.entries.append(record)
        # These checks apply to BOTH captured provider replies and replay files.
        status = response.get("status")
        usage = response.get("usage")
        if status not in ("ok", "error") or not isinstance(usage, dict):
            raise ValueError("malformed response-bank status or usage")
        if set(usage) != set(FIELDS) or any(
            v is not None and (type(v) is not int or v < 0)
            for v in usage.values()
        ):
            raise ValueError("invalid provider usage accounting")
        if (any(usage[key] is None for key in FIELDS)
                or status == "error"):
            self.blocked = True
            self.aborted_reason = ("unknown_usage" if any(
                usage[key] is None for key in FIELDS
            ) else response.get("reason", "provider_error"))
        if status == "ok":
            if response.get("model") != self.model:
                self.blocked = True
                self.aborted_reason = "routed_model_mismatch"
            elif kind == "reflection":
                note = response.get("note")
                if not isinstance(note, str) or len(note) > 120:
                    self.blocked = True
                    self.aborted_reason = "invalid_reflection"
            else:
                mask = response.get("mask")
                if mask is not None and (type(mask) is not int or
                                          mask < 0 or mask >= 32):
                    self.blocked = True
                    self.aborted_reason = "invalid_mask"
                elif response.get("note") is not None:
                    self.blocked = True
                    self.aborted_reason = "action_contained_mutation"
        if self.blocked:
            return None, record
        return (response["note"] if kind == "reflection" else response["mask"]), record

    def _collect(self, messages: list[dict], kind: str) -> dict:
        try:
            result: Reply = self.gateway.ask(
                messages, mode="reflection" if kind == "reflection" else "action")
            usage = normalized_usage(result.usage) or dict.fromkeys(FIELDS)
            # Even a successful response with missing usage fails closed.
            return {
                "status": "ok", "model": result.model, "usage": usage,
                "note": result.soul_update if kind == "reflection" else None,
                "mask": result.mask if kind != "reflection" else None,
            }
        except GatewayError as exc:
            return {
                "status": "error", "model": (exc.model or self.model)[:160],
                "usage": normalized_usage(exc.usage) or dict.fromkeys(FIELDS),
                "reason": exc.reason if isinstance(exc.reason, str) and
                          len(exc.reason) < 120 else "provider_error",
            }

    def finish(self) -> None:
        if self.replay_bank is not None and self.index != len(self.replay_bank):
            raise ValueError("unused/unrequested bank entries")


def _preflight(seed: int, ticks: int, a: str, b: str,
               max_requests: int, provider: str, model: str) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("invalid seed")
    if type(ticks) is not int or not 2 <= ticks <= MAX_TICKS:
        raise ValueError("ticks must be 2..64")
    if a not in MODES or b not in MODES:
        raise ValueError("invalid organism modes")
    if type(max_requests) is not int or not 1 <= max_requests <= MAX_REQUESTS:
        raise ValueError("requests must be 1..12")
    if provider not in ("fixture", "openrouter-free"):
        raise ValueError("unsupported provider")
    if type(model) is not str or not model or len(model) > 140:
        raise ValueError("invalid model")
    if provider == "fixture" and model != FIXTURE_MODEL:
        raise ValueError("fixture requires pinned fixture model")
    if provider == "openrouter-free" and (
        max_requests > MAX_LIVE_REQUESTS or not model.endswith(":free")
        or model == "openrouter/free"):
        raise ValueError("live requests limited to 8 and one pinned free model")


def _episode(seed: int, ticks: int, modes: dict, driver: ResponseDriver) -> dict:
    arena = Arena(seed)
    players = {a: Individual(a, modes[a], Soul.new(a)) for a in AGENTS}
    state = {a: MutationState() for a in AGENTS}
    rows: list[dict] = []
    # All competition tasks are excluded from holdout trials; trial tasks
    # never enter any organism's feedback until their paired results resolve.
    future = Arena(seed)
    live_hashes: set[str] = set()
    for i in range(ticks):
        future.tick = i
        live_hashes.add(task_key(future.observations()["a"].task))
    used_holdouts: set[str] = set()
    for tick in range(ticks):
        observations = arena.observations()
        actions: dict[str, Action] = {}
        charged: dict[str, int] = {}
        intents: dict[str, str] = {}
        mutations: list[dict] = []
        previous_genomes = {a: players[a].soul.sha256 for a in AGENTS}
        for actor in AGENTS:
            p = players[actor]
            m = state[actor]
            obs = observations[actor]
            actions[actor] = greedy(obs, None) if obs.own_energy else Action(None)
            if obs.own_energy <= 0:
                intents[actor] = "dead"
                continue
            can_call = _can_call(arena, actor, driver.remaining, obs.weather)
            if p.mode == "frozen" or driver.blocked:
                kind = "cheap"
            elif p.pending is not None:
                if m.unfinished is not None:
                    kind = "candidate" if can_call else "cheap"
                elif len(m.paired) >= PAIRS_REQUIRED:
                    kind = "decide_revision"
                else:
                    kind = "baseline" if can_call else "cheap"
            elif p.imperfect and not p.attempted_revision and can_call:
                kind = "reflection"
            elif p.soul.version and can_call and tick % 3 == 1:
                kind = "work"
            else:
                kind = "cheap"
            intents[actor] = kind
            if kind == "decide_revision":
                if p.pending is None or len(m.paired) != PAIRS_REQUIRED:
                    raise AssertionError("missing completed comparison")
                gains = [x["candidate_score"] - x["baseline_score"]
                         for x in m.paired]
                accepted = (all(x["baseline_score"] >= 0 and
                                x["candidate_score"] >= 0 for x in m.paired)
                            and all(g >= 0 for g in gains)
                            and sum(gains) > 0)
                event = {
                    "actor": actor, "decision": "activated" if accepted else "rejected",
                    "parent_hash": p.pending["parent_hash"],
                    "candidate_hash": p.pending["candidate_hash"],
                    "total_gain": sum(gains),
                    "pairs": len(m.paired), "paid_trial_requests": 2 * len(m.paired),
                }
                if accepted:
                    p.soul.notes.append(p.pending["note"])
                    p.soul.version += 1
                    p.soul.revisions.append({
                        "tick": tick, "version": p.soul.version,
                        "parent_sha256": p.pending["parent_hash"],
                        "sha256": p.soul.sha256, "note": p.pending["note"],
                    })
                    if p.soul.sha256 != p.pending["candidate_hash"]:
                        raise AssertionError("activated wrong source bytes")
                p.pending = None
                p.events.append(event)
                mutations.append(event)
                continue
            if kind not in ("reflection", "baseline", "candidate", "work"):
                continue
            if not can_call:
                raise AssertionError("consultation admitted without funds")
            if kind == "reflection":
                active_prompt = p.soul.full_prompt
                trial_obs = None
            elif kind == "work":
                active_prompt = p.soul.full_prompt
                trial_obs = obs
            elif kind == "baseline":
                excluded = live_hashes | used_holdouts
                trial_obs = _holdout(seed, actor, len(m.paired), excluded)
                # Reserve this task before provider calls to avoid reuse.
                used_holdouts.add(task_key(trial_obs.task))
                m.unfinished = {
                    "task": trial_obs.task.as_dict(), "task_hash": task_key(trial_obs.task),
                    "seed_tick": trial_obs.tick, "weather": trial_obs.weather,
                    "energy": trial_obs.own_energy,
                }
                active_prompt = p.soul.full_prompt
            else:
                if m.unfinished is None or p.pending is None:
                    raise AssertionError("candidate without pinned baseline trial")
                t = m.unfinished
                trial_obs = Observation(t["seed_tick"], t["weather"],
                                        Task(tuple(tuple(x) for x in t["task"]["items"]),
                                             t["task"]["capacity"]), t["energy"])
                active_prompt = (p.soul.full_prompt + "\nExperience note: " +
                                 p.pending["note"])
                if _hash_prompt(active_prompt) != p.pending["candidate_hash"]:
                    raise AssertionError("candidate bytes drift")
            feedback = (p.soul.memory[-1] if p.soul.memory else None)
            answer, request = driver.ask(actor, tick, kind, active_prompt,
                                         trial_obs, feedback)
            charged[actor] = 1
            if driver.blocked:
                p.pending = None
                m.unfinished = None
                mutations.append({"actor": actor, "decision": "aborted",
                                  "reason": driver.aborted_reason})
                p.events.append(mutations[-1])
                continue
            if kind == "reflection":
                p.attempted_revision = True
                event = _start_candidate(p, answer, tick)
                mutations.append({"actor": actor, **event})
                p.events.append(mutations[-1])
            elif kind == "baseline":
                m.unfinished["baseline_mask"] = answer
                m.unfinished["baseline_score"] = (
                    trial_obs.task.score(answer) if answer is not None else -1
                )
            elif kind == "candidate":
                t = m.unfinished
                result = {
                    "task_hash": t["task_hash"],
                    "baseline_mask": t["baseline_mask"],
                    "candidate_mask": answer,
                    "baseline_score": t["baseline_score"],
                    "candidate_score": trial_obs.task.score(answer) if
                                       answer is not None else -1,
                }
                m.paired.append(result)
                mutations.append({"actor": actor, "decision": "paired_trial", **result})
                m.unfinished = None
            else:
                actions[actor] = Action(answer)
        row = arena.step(actions, charged)
        for actor in AGENTS:
            p = players[actor]
            score = row["scores"][actor]
            if score is not None and 0 <= score < row["optimal_score"]:
                p.imperfect = True
            if score is not None:
                p.soul.observe(tick, score, row["optimal_score"],
                               row["rewards"][actor], row["after"][actor])
                # Reflection sees the organism's actual prior work and its
                # referee feedback, never the holdout answer or rival memory.
                p.soul.memory[-1].update({
                    "task": row["task"], "submitted_mask": row["actions"][actor],
                    "weather": row["weather"], "energy_after": row["after"][actor],
                })
        row["intents"] = intents
        row["mutations"] = mutations
        row["genomes_before"] = previous_genomes
        row["genomes_after"] = {a: players[a].soul.sha256 for a in AGENTS}
        rows.append(row)
    organisms = {
        a: {
            "mode": players[a].mode,
            "final_energy": arena.balances[a],
            "soul_version": players[a].soul.version,
            "soul_hash": players[a].soul.sha256,
            "active_prompt": players[a].soul.full_prompt,
            "pending": players[a].pending,
            "uncompleted_pair": state[a].unfinished,
            "paired_results": state[a].paired,
            "revision_events": players[a].events,
            "alive": arena.balances[a] > 0,
        } for a in AGENTS
    }
    return {"ticks": rows, "organisms": organisms, "final_balances": dict(arena.balances)}


def _run(manifest: dict, *, gateway=None, bank: list[dict] | None = None) -> dict:
    _preflight(manifest["seed"], manifest["ticks"],
               manifest["a"], manifest["b"], manifest["max_requests"],
               manifest["provider"], manifest["model"])
    if (bank is None) == (gateway is None):
        raise ValueError("provide gateway OR replay bank")
    driver = ResponseDriver(
        limit=manifest["max_requests"], provider=manifest["provider"],
        model=manifest["model"], gateway=gateway, bank=bank)
    primary = _episode(manifest["seed"], manifest["ticks"],
                       {"a": manifest["a"], "b": manifest["b"]}, driver)
    driver.finish()
    control = _episode(manifest["seed"], manifest["ticks"],
                       {"a": "frozen", "b": "frozen"},
                       ResponseDriver(limit=manifest["max_requests"],
                                      provider="fixture", model=FIXTURE_MODEL,
                                      gateway=FixtureGateway()))
    bank_entries = driver.entries
    known = {key: 0 for key in FIELDS}
    usage_unknown = 0
    for entry in bank_entries:
        usage = entry["response"]["usage"]
        if any(usage[key] is None for key in FIELDS):
            usage_unknown += 1
        else:
            for key in FIELDS:
                known[key] += usage[key]
    summary = {
        "primary_requests": len(bank_entries),
        "external_request_attempts": len(bank_entries) if
            manifest["provider"] == "openrouter-free" else 0,
        "reported_tokens": known,
        "unknown_usage_requests": usage_unknown,
        "failed_or_aborted": bool(driver.aborted_reason),
        "failure_reason": driver.aborted_reason,
        "net_a_energy_advantage": (
            primary["organisms"]["a"]["final_energy"] -
            control["organisms"]["a"]["final_energy"]),
        "promotion_is_economic_proof": False,
    }
    report = {"manifest": manifest, "bank": bank_entries,
              "episodes": {"primary": primary, "frozen_control": control},
              "summary": summary}
    report["head"] = digest(report)
    return report


def build_report(seed: int, ticks: int, a: str = "evolving",
                 b: str = "frozen", max_requests: int = 8,
                 provider: str = "fixture", model: str = FIXTURE_MODEL,
                 gateway=None) -> dict:
    _preflight(seed, ticks, a, b, max_requests, provider, model)
    manifest = {
        "experiment": VERSION, "prompt_version": PROMPT_VERSION,
        "seed": seed, "ticks": ticks, "a": a, "b": b,
        "provider": provider, "model": model,
        "max_requests": max_requests, "referee": "m0-v2",
        "paired_trials": PAIRS_REQUIRED,
    }
    if gateway is None:
        if provider != "fixture":
            raise ValueError("real-provider calls require an explicitly supplied gateway")
        gateway = FixtureGateway()
    return _run(manifest, gateway=gateway)


def verify_report(report: dict) -> dict:
    if not isinstance(report, dict) or set(report) != {
        "manifest", "bank", "episodes", "summary", "head"
    } or not isinstance(report["manifest"], dict):
        raise ValueError("invalid M2.1-C report")
    m = report["manifest"]
    if set(m) != {"experiment", "prompt_version", "seed", "ticks", "a",
                  "b", "provider", "model", "max_requests", "referee",
                  "paired_trials"}:
        raise ValueError("unexpected manifest fields")
    if (m["experiment"] != VERSION or m["prompt_version"] != PROMPT_VERSION or
            m["referee"] != "m0-v2" or m["paired_trials"] != PAIRS_REQUIRED):
        raise ValueError("unsupported M2.1-C manifest")
    if not isinstance(report["bank"], list) or len(report["bank"]) > MAX_REQUESTS:
        raise ValueError("invalid response bank length")
    rebuilt = _run(m, bank=report["bank"])
    if canonical(rebuilt) != canonical(report):
        raise ValueError("M2.1-C bank, referee, mutation or accounting mismatch")
    return {"verified": True, "head": rebuilt["head"], "summary": rebuilt["summary"]}


def verify_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("missing or oversized M2.1-C report")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid M2.1-C JSON") from exc
    return verify_report(data)


def run_m21c(args) -> dict:
    if not args.benchmark_out:
        raise ValueError("M2.1-C requires --benchmark-out NEW_FILE")
    path = Path(args.benchmark_out)
    if path.exists():
        raise ValueError("refusing to overwrite existing M2.1-C report")
    if args.provider == "fake":
        provider, model, gateway = "fixture", FIXTURE_MODEL, FixtureGateway()
    elif args.provider == "openrouter":
        provider, model = "openrouter-free", args.model
        if not getattr(args, "m21c_confirm_live", False) or (
            os.environ.get("SURLIFE_M21C_APPROVE_LIVE") != "YES"):
            raise ValueError(
                "real provider disabled: require --m21c-confirm-live and "
                "SURLIFE_M21C_APPROVE_LIVE=YES"
            )
        if args.max_requests > MAX_LIVE_REQUESTS:
            raise ValueError("real-provider run caps requests at 8")
        if type(args.max_output_tokens) is not int or args.max_output_tokens > 512:
            raise ValueError("real-provider output limit must be at most 512")
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise ValueError("OPENROUTER_API_KEY required")
        # Live catalog must establish a pinned, zero-priced model supporting
        # structured output BEFORE any model request. Not an account billing cap.
        from .model_registry import check_model
        check_model(model)
        gateway = OpenRouterGateway(
            model=model, max_requests=args.max_requests,
            max_output_tokens=args.max_output_tokens, reasoning=args.reasoning,
        )
    else:
        raise ValueError("M2.1-C supports only offline fake or pinned free OpenRouter")
    report = build_report(args.seed, args.ticks, args.m21_a, args.m21_b,
                          args.max_requests, provider, model, gateway)
    # The bank verification is always offline even after a real provider run.
    verify_report(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    return {"verified": True, "report_path": str(path),
            "head": report["head"], "summary": report["summary"]}
