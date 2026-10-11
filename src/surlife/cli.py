"""Run Surlife M0 scripted and M1 bounded prompt-soul experiments."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from .core import AGENTS, POLICIES, RULES_VERSION, START_ENERGY, STAKE, Arena, choose_actions
from .storage import Journal


def main() -> None:
    parser = argparse.ArgumentParser(description="Surlife: offline M0 or bounded M1 with OpenRouter free models")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--ticks", type=int, default=12)
    parser.add_argument("--a", choices=sorted([*POLICIES, "llm"]), default="greedy")
    parser.add_argument("--b", choices=sorted(POLICIES), default="optimal")
    parser.add_argument("--db", default="out/surlife.sqlite")
    parser.add_argument("--provider", choices=("fake", "openrouter"), default="fake")
    parser.add_argument("--model", default="openrouter/free", help="openrouter/free or a pinned :free model")
    parser.add_argument("--max-requests", type=int, default=6, help="total LLM calls per run, hard admission cap")
    parser.add_argument("--max-output-tokens", type=int, default=512)
    parser.add_argument("--reasoning", choices=("off", "low", "auto"), default="off",
                        help="OpenRouter reasoning: off (default), low effort, or auto")
    parser.add_argument("--souls-dir", default="out/souls")
    parser.add_argument("--soul-a", help="optional custom initial soul text (LLM A)")
    parser.add_argument("--soul-b", help="optional custom initial soul text (LLM B)")
    parser.add_argument("--inherit-soul-a", help="prior a.json snapshot; restores soul and memory")
    parser.add_argument("--inherit-soul-b", help="prior b.json snapshot; restores soul and memory")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--replay", metavar="RUN_ID", help="verify saved events without running new turns")
    args = parser.parse_args()
    if args.seed < 0 or args.ticks < 0:
        parser.error("--seed and --ticks must be nonnegative")
    path = Path(args.db)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Replay is always offline and takes precedence over --provider / --a llm.
    if args.replay:
        with Journal(path) as journal:
            print(json.dumps(journal.replay(args.replay), indent=2, sort_keys=True))
        return
    if args.a == "llm" or args.b == "llm":
        from .runner import run_m1
        try:
            report = run_m1(args, path)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    with Journal(path) as journal:
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
