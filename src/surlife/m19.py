"""M1.9: versioned, deterministic non-additive task packs; offline-only.

The trusted M0-v2 Arena controls payments, death, stakes and energy. Task
semantics are immutable input data with an independently recomputed oracle.
No hosted provider and no user/model-supplied executable task scripts.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from random import Random

from .core import Action, Arena, Observation, POLICIES, RULES_VERSION, Task
from .m16 import write_report
from .storage import canonical

VERSION = "m19-v1"
PACKS = ("coverage", "synergy", "mixed")
BASELINES = ("greedy", "marginal", "beam", "oracle")
MAX_CASES = 48
MAX_ITEMS = 14
MAX_REPORT_BYTES = 8_000_000
BEAM_WIDTH = 48


@dataclass(frozen=True)
class InteractionTask(Task):
    """Subset task whose rewards need not be the sum of item rewards.

    `items` is the public cost + singleton-value approximation used by the
    old ratio-Greedy heuristic. True scores may have overlaps or pair bonuses.
    All scoring-relevant data is exposed by as_dict(); no hidden task rule.
    """

    mode: str
    feature_masks: tuple[int, ...] = ()
    feature_weights: tuple[int, ...] = ()
    bonuses: tuple[tuple[int, int, int], ...] = ()

    def __post_init__(self) -> None:
        if (self.mode not in ("coverage", "synergy")
                or not 8 <= len(self.items) <= MAX_ITEMS
                or not 5 <= self.capacity <= 40
                or any(type(cost) is not int or not 1 <= cost <= 20
                       or type(value) is not int or not 0 <= value <= 100
                       for cost, value in self.items)):
            raise ValueError("invalid M1.9 task specification")
        if self.mode == "coverage":
            if (self.bonuses
                    or len(self.feature_masks) != len(self.items)
                    or not 1 <= len(self.feature_weights) <= 12
                    or any(type(w) is not int or not 1 <= w <= 30
                           for w in self.feature_weights)
                    or any(type(mask) is not int or not 1 <= mask < (1 << len(self.feature_weights))
                           for mask in self.feature_masks)):
                raise ValueError("invalid coverage task")
            for i, (_, reward) in enumerate(self.items):
                if reward != sum(w for j, w in enumerate(self.feature_weights)
                                 if self.feature_masks[i] & (1 << j)):
                    raise ValueError("singleton coverage reward mismatch")
        else:
            if self.feature_masks or self.feature_weights:
                raise ValueError("synergy pack may not include coverage features")
            unique = set()
            for i, j, bonus in self.bonuses:
                if (type(i) is not int or type(j) is not int or type(bonus) is not int
                        or not 0 <= i < j < len(self.items)
                        or not 1 <= bonus <= 100 or (i, j) in unique):
                    raise ValueError("invalid pairwise bonus")
                unique.add((i, j))
        object.__setattr__(self, "_m19_optimum", max(
            self.score(mask) for mask in range(1 << len(self.items))
        ))

    @property
    def optimum(self) -> int:
        return self._m19_optimum

    def score(self, mask: int) -> int:
        if type(mask) is not int or not 0 <= mask < (1 << len(self.items)):
            return -1
        selected = [i for i in range(len(self.items)) if mask & (1 << i)]
        if sum(self.items[i][0] for i in selected) > self.capacity:
            return -1
        if self.mode == "coverage":
            covered = 0
            for i in selected:
                covered |= self.feature_masks[i]
            return sum(w for j, w in enumerate(self.feature_weights)
                       if covered & (1 << j))
        result = sum(self.items[i][1] for i in selected)
        result += sum(bonus for i, j, bonus in self.bonuses
                      if mask & (1 << i) and mask & (1 << j))
        return result

    def as_dict(self) -> dict:
        details = {
            "pack": self.mode, "items": [list(x) for x in self.items],
            "capacity": self.capacity,
        }
        if self.mode == "coverage":
            details.update({
                "feature_masks": list(self.feature_masks),
                "feature_weights": list(self.feature_weights),
                "rule": "Sum unique covered feature weights; never count overlaps twice",
            })
        else:
            details.update({
                "pair_bonuses": [list(x) for x in self.bonuses],
                "rule": "Sum base item values and bonuses for selected pairs",
            })
        return details


def independent_score(task: InteractionTask, mask: int) -> int:
    """Intentionally separate scorer; not an alias to InteractionTask.score."""
    n = len(task.items)
    if type(mask) is not int or mask < 0 or mask >= (1 << n):
        return -1
    choice = tuple(i for i in range(n) if (mask >> i) & 1)
    if sum(task.items[i][0] for i in choice) > task.capacity:
        return -1
    if task.mode == "coverage":
        included = set()
        for i in choice:
            included.update(j for j in range(len(task.feature_weights))
                            if (task.feature_masks[i] >> j) & 1)
        return sum(task.feature_weights[j] for j in included)
    return (sum(task.items[i][1] for i in choice)
            + sum(bonus for i, j, bonus in task.bonuses
                  if i in choice and j in choice))


def marginal_mask(task: InteractionTask) -> int:
    """Ratio of ACTUAL marginal gains; never reads future puzzles or oracle."""
    mask, remaining = 0, task.capacity
    while True:
        base = task.score(mask)
        options = []
        for i, (cost, _) in enumerate(task.items):
            if mask & (1 << i) or cost > remaining:
                continue
            gain = task.score(mask | (1 << i)) - base
            if gain > 0:
                options.append((gain / cost, gain, -i, i, cost))
        if not options:
            break
        _, _, _, chosen, cost = max(options)
        mask |= 1 << chosen
        remaining -= cost
    return mask


def beam_mask(task: InteractionTask, width: int = BEAM_WIDTH) -> int:
    """Finite bounded prefix beam; useful but not guaranteed optimal."""
    if type(width) is not int or not 1 <= width <= 256:
        raise ValueError("invalid beam width")
    states = [(0, 0)]
    for i, (cost, _) in enumerate(task.items):
        proposals = list(states)
        for mask, spent in states:
            if spent + cost <= task.capacity:
                proposals.append((mask | (1 << i), spent + cost))
        # Favor high currently realized reward, breaking ties by low cost.
        proposals.sort(key=lambda state: (
            task.score(state[0]), -state[1], -state[0]), reverse=True)
        states = proposals[:width]
    return max((mask for mask, _ in states),
               key=lambda mask: (task.score(mask), -mask))


def make_pack_cases(seed: int, count: int, items: int, pack: str) -> list[dict]:
    if type(seed) is not int or seed < 0:
        raise ValueError("M1.9 seed must be nonnegative")
    if type(count) is not int or not 1 <= count <= MAX_CASES:
        raise ValueError("M1.9 cases must be between 1 and 48")
    if type(items) is not int or not 8 <= items <= MAX_ITEMS:
        raise ValueError("M1.9 items must be between 8 and 14")
    if pack not in PACKS:
        raise ValueError("M1.9 pack must be coverage, synergy or mixed")

    result = []
    for tick in range(count):
        family = pack if pack != "mixed" else ("coverage" if tick % 2 == 0 else "synergy")
        rng = Random(seed * 1_000_003 + tick * 9_176 + 7331)
        capacity = rng.randint(12, 20)
        if family == "coverage":
            weights = tuple(rng.randint(4, 12) for _ in range(8))
            masks = []
            for _ in range(items):
                feature_count = rng.randint(1, 3)
                chosen = rng.sample(range(len(weights)), feature_count)
                masks.append(sum(1 << bit for bit in chosen))
            costs = [rng.randint(1, 7) for _ in range(items)]
            pairs = tuple((costs[i], sum(weights[j] for j in range(len(weights))
                                          if masks[i] & (1 << j)))
                          for i in range(items))
            task = InteractionTask(pairs, capacity, family,
                                   tuple(masks), weights)
        else:
            pairs = tuple((rng.randint(2, 7), rng.randint(3, 19))
                          for _ in range(items))
            indices = rng.sample(range(items), 6)
            bonuses = tuple(sorted(
                (min(indices[k], indices[k + 1]),
                 max(indices[k], indices[k + 1]), rng.randint(17, 34))
                for k in range(0, 6, 2)))
            task = InteractionTask(pairs, capacity, family,
                                   bonuses=bonuses)
        oracle_mask = max(range(1 << items),
                          key=lambda m: (independent_score(task, m), -m))
        oracle_score = independent_score(task, oracle_mask)
        if task.optimum != oracle_score:
            raise AssertionError("task evaluator disagrees with separate exact oracle")
        neutral = Observation(tick, "normal", task, 30)
        greedy = POLICIES["greedy"](neutral, Random(0)).mask
        marginal = marginal_mask(task)
        beam = beam_mask(task)
        for mask in (greedy, marginal, beam):
            if independent_score(task, mask) != task.score(mask) or task.score(mask) < 0:
                raise AssertionError("trusted heuristic selected invalid task action")
        result.append({
            "task": task, "kind": family,
            "greedy_mask": greedy, "greedy_score": task.score(greedy),
            "marginal_mask": marginal, "marginal_score": task.score(marginal),
            "beam_mask": beam, "beam_score": task.score(beam),
            "oracle_mask": oracle_mask, "oracle_score": oracle_score,
            "gap": oracle_score - task.score(greedy),
        })
    return result


class TaskPackArena(Arena):
    """Inject only seeded tasks. The original trusted Arena.step settles all moves."""

    def __init__(self, seed: int, cases: list[dict]):
        super().__init__(seed)
        self.cases = cases

    def _puzzle(self):
        _, weather = super()._puzzle()
        return self.cases[self.tick]["task"], weather


def rollout(seed: int, cases: list[dict], arm: str) -> list[dict]:
    if arm not in BASELINES:
        raise ValueError("unknown M1.9 policy")
    arena = TaskPackArena(seed, cases)
    records = []
    for case in cases:
        obs = arena.observations()
        a = Action(case[f"{arm}_mask"]) if obs["a"].own_energy else Action(None)
        b = (POLICIES["greedy"](obs["b"], Random(0))
             if obs["b"].own_energy else Action(None))
        rec = arena.step({"a": a, "b": b})
        rec["benchmark"] = {
            "pack": case["kind"],
            "source": "trusted_" + arm,
            "greedy_mask": case["greedy_mask"],
            "greedy_score": case["greedy_score"],
            "marginal_mask": case["marginal_mask"],
            "marginal_score": case["marginal_score"],
            "beam_mask": case["beam_mask"],
            "beam_score": case["beam_score"],
            "oracle_mask": case["oracle_mask"],
            "oracle_score": case["oracle_score"],
            "gap": case["gap"],
        }
        records.append(rec)
    return records


def summarize(cases: list[dict], arms: dict[str, list[dict]]) -> dict:
    stats = {}
    for name, rows in arms.items():
        last = rows[-1]
        stats[name] = {
            "energy": last["after"]["a"],
            "alive": last["after"]["a"] > 0,
            "task_score_sum": sum(row["scores"]["a"] for row in rows
                                  if row["scores"]["a"] is not None),
            "optimal": sum(row["scores"]["a"] == row["optimal_score"]
                           for row in rows if row["attempted"]["a"]),
            "invalid": sum(row["scores"]["a"] == -1 for row in rows),
            "wins": sum(row["winner"] == "a" for row in rows),
            "consultations": sum(row["consultations"]["a"] for row in rows),
        }
    greedy_total = sum(c["greedy_score"] for c in cases)
    oracle_total = sum(c["oracle_score"] for c in cases)
    return {
        "headroom": {
            "cases": len(cases),
            "families": {family: sum(c["kind"] == family for c in cases)
                         for family in ("coverage", "synergy")},
            "greedy_total": greedy_total,
            "marginal_total": sum(c["marginal_score"] for c in cases),
            "beam_total": sum(c["beam_score"] for c in cases),
            "oracle_total": oracle_total,
            "greedy_gap": oracle_total - greedy_total,
            "positive_gap_cases": sum(c["gap"] > 0 for c in cases),
        },
        "arms": stats,
        "note": (
            "All policies are trusted, deterministic and UNPRICED. "
            "The oracle enumerates up to 2^14 masks. Marginal-greedy and "
            "finite-width beam are non-LLM baselines, not universally "
            "optimal. This benchmarks task difficulty, NOT model ability."
        ),
    }


def _head(manifest: dict, arms: dict, summary: dict) -> str:
    return hashlib.sha256(canonical({
        "manifest": manifest, "arms": arms, "summary": summary,
    }).encode("utf-8")).hexdigest()


def make_report(seed: int, count: int, items: int, pack: str) -> dict:
    cases = make_pack_cases(seed, count, items, pack)
    manifest = {
        "experiment": VERSION, "referee_rules": RULES_VERSION,
        "seed": seed, "cases": count, "items": items,
        "pack": pack, "beam_width": BEAM_WIDTH,
        "provider": "none", "cognition_requests": 0,
    }
    arms = {name: rollout(seed, cases, name) for name in BASELINES}
    summary = summarize(cases, arms)
    result = {"manifest": manifest, "arms": arms, "summary": summary}
    result["head"] = _head(manifest, arms, summary)
    return result


def verify_m19(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
        raise ValueError("invalid M1.9 report")
    m = report["manifest"]
    if (set(m) != {"experiment", "referee_rules", "seed", "cases",
                    "items", "pack", "beam_width", "provider",
                    "cognition_requests"}
            or m["experiment"] != VERSION or m["referee_rules"] != RULES_VERSION
            or m["beam_width"] != BEAM_WIDTH or m["provider"] != "none"
            or m["cognition_requests"] != 0):
        raise ValueError("unsupported M1.9 experiment manifest")
    expected = make_report(m["seed"], m["cases"], m["items"], m["pack"])
    if (canonical(expected["arms"]) != canonical(report.get("arms"))
            or canonical(expected["summary"]) != canonical(report.get("summary"))
            or expected["head"] != report.get("head")):
        raise ValueError("M1.9 independent arena/reward/strategy replay mismatch")
    return {"verified": True, "head": expected["head"],
            "summary": expected["summary"]}


def verify_m19_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("M1.9 report missing or exceeds size cap")
    try:
        report = json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid M1.9 JSON report") from exc
    return verify_m19(report)


def run_m19(args) -> dict:
    if args.a not in ("llm", "greedy") or args.b != "greedy":
        raise ValueError("M1.9 requires --a greedy/llm --b greedy for common CLI")
    if getattr(args, "provider", "fake") != "fake":
        raise ValueError("M1.9 is offline-only; use --provider fake")
    filename = getattr(args, "benchmark_out", None)
    if not filename:
        raise ValueError("M1.9 requires --benchmark-out")
    if Path(filename).exists():
        raise ValueError("M1.9 report exists; choose a NEW filename")
    report = make_report(args.seed, args.benchmark_cases, args.benchmark_items,
                         args.m19_pack)
    result = verify_m19(report)
    write_report(report, filename)
    return {"verified": result["verified"], "head": result["head"],
            "summary": result["summary"], "manifest": report["manifest"],
            "report_path": filename}
