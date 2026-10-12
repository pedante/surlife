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
    parser.add_argument("--provider", choices=("fake", "openrouter", "google"), default="fake")
    parser.add_argument("--model", default=None, help="provider-selected default; use --check-model before inference")
    parser.add_argument("--max-requests", type=int, default=6, help="total LLM calls per run, hard admission cap")
    parser.add_argument("--max-output-tokens", type=int, default=None,
                        help="output including thinking tokens: Google default 4096 (max 8192), other providers default 512")
    parser.add_argument("--google-timeout-seconds", type=int, default=90,
                        help="per-Gemini-request timeout (10..180 seconds, default 90); SDK retries disabled")
    parser.add_argument("--reasoning", choices=("off", "low", "auto"), default="off",
                        help="OpenRouter reasoning: off (default), low effort, or auto")
    parser.add_argument("--souls-dir", default="out/souls")
    parser.add_argument("--soul-a", help="optional custom initial soul text (LLM A)")
    parser.add_argument("--soul-b", help="optional custom initial soul text (LLM B)")
    parser.add_argument("--inherit-soul-a", help="prior a.json snapshot; restores soul and memory")
    parser.add_argument("--inherit-soul-b", help="prior b.json snapshot; restores soul and memory")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--replay", metavar="RUN_ID", help="verify saved events without running new turns")
    parser.add_argument("--m11", action="store_true", help="M1.1 staged, feedback-aware organism")
    parser.add_argument("--m12", action="store_true",
                        help="M1.2 observable organism; with --evaluate-soul use multi-cohort evaluation")
    parser.add_argument("--m13", action="store_true",
                        help="M1.3 action-contract experiment with legally admissible menu")
    parser.add_argument("--m14", action="store_true",
                        help="M1.4 deterministic headroom and survival benchmark")
    parser.add_argument("--m16", action="store_true",
                        help="M1.6 experience-adaptive consultation policy")
    parser.add_argument("--m17", action="store_true",
                        help="M1.7 inheritance and matched held-out policy comparison")
    parser.add_argument("--m18", action="store_true",
                        help="M1.8 single-response-bank multi-policy cognition tournament")
    parser.add_argument("--m19", action="store_true",
                        help="M1.9 fully offline coverage/synergy task-pack benchmark")
    parser.add_argument("--m110", action="store_true",
                        help="M1.10 shared-model-response cognition tournament in M1.9 worlds")
    parser.add_argument("--m111", action="store_true",
                        help="M1.11 offline TaskPack-specific inherited cognition and holdouts")
    parser.add_argument("--m21c", action="store_true",
                        help="M2.1-C paired prompt mutation with model-response audit (offline by default)")
    parser.add_argument("--m21c-confirm-live", action="store_true",
                        help="explicitly authorize zero-priced pinned OpenRouter provider pilot")
    parser.add_argument("--verify-m21c-file",
                        help="offline verify a recorded M2.1-C response-bank experiment")
    parser.add_argument("--m21", action="store_true",
                        help="M2.1 offline prompt-mutation tournament with scripted fake provider")
    parser.add_argument("--m21-a", choices=("evolving", "frozen"), default="evolving",
                        help="M2.1 organism A genome policy")
    parser.add_argument("--m21-b", choices=("evolving", "frozen"), default="frozen",
                        help="M2.1 organism B genome policy")
    parser.add_argument("--verify-m21-file",
                        help="M2.1 independent offline replay and prompt-mutation audit")
    parser.add_argument("--m20", action="store_true",
                        help="M2.0 persistent shared-resource ecology (offline only)")
    parser.add_argument("--m20-a", choices=("extractive", "steward", "opportunist", "rest"),
                        default="steward", help="M2.0 organism A trusted policy")
    parser.add_argument("--m20-b", choices=("extractive", "steward", "opportunist", "rest"),
                        default="extractive", help="M2.0 organism B trusted policy")
    parser.add_argument("--verify-m20-file",
                        help="M2.0 offline verify both mirrored ecology episodes and ledger")
    parser.add_argument("--m111-train-bank", action="append", default=[],
                        help="M1.11 verified M1.10 training response-bank report (repeat 1-4)")
    parser.add_argument("--m111-holdout-bank", action="append", default=[],
                        help="M1.11 disjoint verified held-out response-bank report (repeat 2-4)")
    parser.add_argument("--m111-virtual-cap", type=int, default=4,
                        help="M1.11 per-policy simulated consultation cap (1-48)")
    parser.add_argument("--m111-promote-policy-out",
                        help="M1.11 new data-only policy path, written only if dual-control gate passes")
    parser.add_argument("--verify-m111-file",
                        help="independently verify M1.11 learning, holdout outcomes and gate")
    parser.add_argument("--m110-pack", choices=("coverage", "synergy", "mixed"),
                        default="mixed", help="M1.10 task family")
    parser.add_argument("--m110-bank-in",
                        help="M1.10 previously verified bank; rerun policies without API calls")
    parser.add_argument("--m110-virtual-cap", type=int, default=4,
                        help="M1.10 per-policy virtual cognition cap")
    parser.add_argument("--verify-m110-file",
                        help="offline verify M1.10 taskpack scoring, bank and referee replay")
    parser.add_argument("--m19-pack", choices=("coverage", "synergy", "mixed"),
                        default="mixed", help="M1.9 non-additive task family")
    parser.add_argument("--verify-m19-file",
                        help="M1.9 independent scorer, referee and policy replay")
    parser.add_argument("--m18-bank-in",
                        help="M1.8 verified prior report; replay its bank with zero API calls")
    parser.add_argument("--m18-virtual-cap", type=int, default=4,
                        help="M1.8 simulated maximum consultations per arm (default 4)")
    parser.add_argument("--verify-m18-file",
                        help="offline verify M1.8 bank, arm decisions, learning and ledger")
    parser.add_argument("--train-report", action="append", default=[],
                        help="M1.7 verified M1.6 training report; repeat up to four times")
    parser.add_argument("--holdout-seeds", default="101,103",
                        help="M1.7 two to four nonnegative held-out seeds")
    parser.add_argument("--promote-policy-out",
                        help="M1.7 NEW policy snapshot path, only written when gate passes")
    parser.add_argument("--policy-in",
                        help="M1.6 only: inherit a data-only policy promoted by M1.7")
    parser.add_argument("--verify-adaptive-file",
                        help="offline verify M1.6 actions, accounting and policy updates")
    parser.add_argument("--verify-m17-file",
                        help="offline verify M1.7 cohort comparison and inheritance")
    parser.add_argument("--benchmark-cases", type=int, default=12)
    parser.add_argument("--benchmark-items", type=int, default=12)
    parser.add_argument("--benchmark-profile", choices=("mixed", "trap", "random"),
                        default="mixed")
    parser.add_argument("--benchmark-out",
                        help="optional NEW JSON report path for independent offline audit")
    parser.add_argument("--verify-benchmark-file",
                        help="offline replay and verify an existing M1.4 JSON report")
    parser.add_argument("--action-contract", choices=("menu", "raw"), default="menu",
                        help="M1.3 only: present cost-feasible menu or raw-mask control")
    parser.add_argument("--cognition", choices=("selective", "always", "never"),
                        default="selective", help="M1.1 host-owned cognition schedule")
    parser.add_argument("--evaluate-soul", metavar="FILE",
                        help="explicit paired holdout evaluation of one pending M1.1 soul")
    parser.add_argument("--evaluation-seed", type=int, default=1009)
    parser.add_argument("--evaluation-tasks", type=int, default=4)
    parser.add_argument("--evaluation-cohorts", type=int, default=2,
                        help="M1.2 paired cohorts (min 2, default 2)")
    parser.add_argument("--max-evaluation-requests", type=int, default=24,
                        help="M1.2 hard cap on real evaluation requests (max 24)")
    parser.add_argument("--eval-min-gain", type=int, default=2)
    parser.add_argument("--check-model", action="store_true",
                        help="check OpenRouter public model catalog without an LLM request or API key")
    args = parser.parse_args()
    if args.model is None:
        args.model = ("gemini-3.8-flash" if args.provider == "google"
                      else "dots-studio/dots-3-note-preview:free")
    if args.max_output_tokens is None:
        args.max_output_tokens = 4096 if args.provider == "google" else 512
    if args.provider == "google" and not (args.m14 or args.m16 or args.m17 or args.m18 or args.m110 or args.m111 or args.check_model or args.verify_benchmark_file or args.verify_adaptive_file or args.verify_m17_file or args.verify_m18_file or args.verify_m110_file or args.verify_m111_file):
        parser.error("--provider google is supported only in M1.4/M1.6/M1.7 benchmark experiments")
    if sum((args.m11, args.m12, args.m13, args.m14, args.m16, args.m17, args.m18, args.m19, args.m110, args.m111, args.m20, args.m21, args.m21c)) > 1:
        parser.error("choose only one experiment stage")
    if args.seed < 0 or args.ticks < 0:
        parser.error("--seed and --ticks must be nonnegative")
    if args.verify_m21c_file:
        from .m21c import verify_file as verify_m21c_file
        try:
            print(json.dumps(verify_m21c_file(args.verify_m21c_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m21_file:
        from .m21 import verify_file
        try:
            print(json.dumps(verify_file(args.verify_m21_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m20_file:
        from .m20 import verify_m20_file
        try:
            print(json.dumps(verify_m20_file(args.verify_m20_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m111_file:
        from .m111 import verify_m111_file
        try:
            print(json.dumps(verify_m111_file(args.verify_m111_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m110_file:
        from .m110 import verify_m110_file
        try:
            print(json.dumps(verify_m110_file(args.verify_m110_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m19_file:
        from .m19 import verify_m19_file
        try:
            print(json.dumps(verify_m19_file(args.verify_m19_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m18_file:
        from .m18 import verify_m18_file
        try:
            print(json.dumps(verify_m18_file(args.verify_m18_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_adaptive_file:
        from .m16 import verify_m16_file
        try:
            print(json.dumps(verify_m16_file(args.verify_adaptive_file), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_m17_file:
        from .m17 import verify_m17_file
        try:
            print(json.dumps(verify_m17_file(args.verify_m17_file), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.verify_benchmark_file:
        from .m14 import verify_report_file
        try:
            print(json.dumps(verify_report_file(args.verify_benchmark_file),
                             indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.check_model:
        if args.provider == "google":
            from .gemini_gateway import check_gemini_model as check_model
        else:
            from .model_registry import check_model
        try:
            print(json.dumps(check_model(args.model), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.evaluate_soul:
        if args.m12 or args.m13:
            from .evaluation_v2 import evaluate_snapshot_v2 as evaluate_snapshot
        else:
            from .evaluation import evaluate_snapshot
        try:
            print(json.dumps(evaluate_snapshot(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m21c:
        from .m21c import run_m21c
        try:
            print(json.dumps(run_m21c(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m21:
        from .m21 import run_m21
        try:
            print(json.dumps(run_m21(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m20:
        from .m20 import run_m20
        try:
            print(json.dumps(run_m20(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m111:
        from .m111 import run_m111
        try:
            print(json.dumps(run_m111(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m110:
        from .m110 import run_m110
        try:
            print(json.dumps(run_m110(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m19:
        from .m19 import run_m19
        try:
            print(json.dumps(run_m19(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m18:
        from .m18 import run_m18
        try:
            print(json.dumps(run_m18(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m16:
        from .m16 import run_m16
        try:
            print(json.dumps(run_m16(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m17:
        from .m17 import run_m17
        try:
            print(json.dumps(run_m17(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    if args.m14:
        from .m14 import run_m14
        try:
            print(json.dumps(run_m14(args), indent=2, sort_keys=True))
        except ValueError as exc:
            parser.error(str(exc))
        return
    path = Path(args.db)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Replay is always offline and takes precedence over --provider / --a llm.
    if args.replay:
        with Journal(path) as journal:
            print(json.dumps(journal.replay(args.replay), indent=2, sort_keys=True))
        return
    if args.m11 or args.m12 or args.m13:
        from .m11 import run_m11
        try:
            result = run_m11(args, path)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2, sort_keys=True))
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
