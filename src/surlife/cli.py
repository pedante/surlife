"""Run the offline Surlife M0 duel: python -m surlife.cli --seed 7 --ticks 12."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from .core import AGENTS, POLICIES, RULES_VERSION, START_ENERGY, STAKE, Arena, choose_actions
from .storage import Journal


def main() -> None:
    parser = argparse.ArgumentParser(description="Surlife M0: deterministic two-organism duel (no LLM calls)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--ticks", type=int, default=12)
    parser.add_argument("--a", choices=sorted(POLICIES), default="greedy")
    parser.add_argument("--b", choices=sorted(POLICIES), default="optimal")
    parser.add_argument("--db", default="out/surlife.sqlite")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--replay", metavar="RUN_ID", help="verify saved events without running new turns")
    args = parser.parse_args()
    if args.seed < 0 or args.ticks < 0:
        parser.error("--seed and --ticks must be nonnegative")
    path = Path(args.db)
    path.parent.mkdir(parents=True, exist_ok=True)
    with Journal(path) as journal:
        if args.replay:
            print(json.dumps(journal.replay(args.replay), indent=2, sort_keys=True))
            return
        run_id = args.run_id or uuid4().hex[:12]
        manifest = {"rules": RULES_VERSION, "seed": args.seed, "start_energy": START_ENERGY,
                    "stake": STAKE, "policies": {"a": args.a, "b": args.b},
                    "kind": "m0-scripted-reference-policies"}
        journal.create_run(run_id, manifest)
        arena = Arena(args.seed)
        for _ in range(args.ticks):
            journal.append(run_id, arena.step(choose_actions(arena, {a: manifest["policies"][a] for a in AGENTS})))
        report = journal.replay(run_id)
    report["policies"] = manifest["policies"]
    report["note"] = "Only scripted reference policies were run; no learning, LLM or untrusted code."
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
