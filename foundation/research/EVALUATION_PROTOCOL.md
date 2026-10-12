# Evaluation protocol — reusable Surlife components

**Purpose:** turn [REUSE_CANDIDATES.md](REUSE_CANDIDATES.md) into small, falsifiable, independently reviewable experiments. The catalog is reconnaissance, not a dependency approval. Do not modify `foundation/PLAN.md` or any frozen `iterations/*/PROPOSAL.md` while evaluating candidates.

## Decision unit and baselines

Evaluate **the smallest component needed for one milestone**, not marketing claims of a whole framework. Compare:
- **B0:** ~smallest local stdlib Python solution satisfying the same API/invariant.
- **B1:** package used directly as library (if safe).
- **B2:** thin isolated adapter with only the tested submodule (if feasible).
- **B3:** borrow an idea/schema/test without importing its code.

Hold rules, seed list, hardware, runs, number of agents, permitted observations and reward calculation constant. Never charge virtual energy in lieu of measuring actual model tokens and currency.

## Hard gates (any FAIL blocks adoption)

| Gate | Required evidence |
|---|---|
| L — Rights/provenance | Recorded upstream URL, exact commit SHA, dependency list, file-level + asset/model licenses; redistribution obligations understood. Unknown/noncommercial source is **study only**, absent express legal clearance. |
| T — Trust boundary | World/referee has sole authority for scoring, ledger, credentials and actual spend. Only validated actions cross the edge. No agent prompt, code or vendor evaluator can mint energy, change rules, inspect rivals or call host shell directly. |
| S — Isolation | For generated code, use a hostile-code sandbox/VM with no credentials, no network, no supervisor or peer mounts and enforce CPU/memory/timeout limits. A subprocess alone is **not** a security boundary. Do not execute malicious probes on a personal host. |
| R — Reproducibility | Fixed seed + fixed scripted actions yield the same canonical event stream, state and account balances after restart/replay, including malformed/retried actions. |
| A — Accounting | Double-entry or balanced transfer invariant, no negative balances, idempotent duel settlement, explicit mint/burn, actual model requests and tokens metered outside genomes. |
| O — Observability | Fully reconstructible configurations; action, observation, score, actual tokens, energy, version hashes, timestamps and failures in machine-readable records. |

For purely inspirational (study-only) sources, mark irrelevant gates `N/A`; **never promote N/A to a passing runtime component**.

## Scored dimensions (0–5, after hard gates)

| Dimension | Weight | 0 versus 5 |
|---|---:|---|
| Minimal safe integration | 25% | Complex host/service/runtime changes vs few narrow interfaces |
| Reproducibility and objective scoring | 20% | Opaque/nondeterministic vs replayed seeded outcomes |
| Reuse value / saved maintenance | 20% | Duplicates tiny code vs replaces difficult tested capability |
| Cost/compute control | 15% | Unbounded external calls vs strict gateway and no-LLM tests |
| Scientific utility | 10% | Reward can be gamed vs held-out baseline measurements |
| Maintainability/licensing clarity | 10% | Fragile or unclear vs pinned dependencies, permissive proven license |

Weighted score = sum(weight × score / 5), 0–100. **Scores are hypotheses until a tested evaluation report is attached.** No high numerical score overrides a hard gate. Favor solutions with fewer dependencies and smaller privileged surfaces if scores are similar.

## Per-candidate reproducible procedure

1. **Static triage:** pin commit; inspect license, submodule and dependencies, security advisories, runtime/OS and code entrypoints. Record source URLs and facts, including maintenance uncertainty.
2. **Map authority:** diagram real API between `ArenaAdapter.reset(seed)`, `observe(agent_id)`, `step(validated_action)`, `get_events()`; identify who actually owns reward, state, model invocation, filesystem and clocks.
3. **Offline smoke:** inside disposable isolated environment, no credentials or network, instantiate one toy scenario with two scripted policies; show that outputs parse to Surlife's restricted action schema.
4. **Invariant suite:** identical seed+action replay; malformed action refusal; private memory separation; retry settlement once; ledger conservation including escrow, mint and burn. Failure means *no runtime adoption*.
5. **Resource/economy:** measure cold-start time, median step latency, memory footprint, Python/OS/JS/C++ transitive dependencies, new trusted lines of code and sandbox surface. Measurements need machine/config metadata, not guessed numbers.
6. **Head-to-head:** compare against minimal custom baseline under identical tasks/seeds; for M1/M2 run static, prompt-only, code-only and hybrid agents with matched actual token/currency and virtual energy budgets, report failures and uncertainty.
7. **Decision:** `adopt | adapt | study | defer | reject`; show what exact code/components remain, license obligations, blocker ownership and decision ID. Get human approval before changing `PLAN.md` or implementation scope.

## Initial experiments to commission

| Experiment | Candidates | Question | Simple pass/fail signal |
|---|---|---|---|
| E01 — arena protocol | W02, W03, minimal custom | Does a proven multi-agent API/game remove code without compromising referee authority? | All invariant checks pass; fewer total maintained moving parts |
| E02 — non-LLM ecology | W01, W04, W05, custom | Can seeded survival/task puzzles support two differently behaving baseline policies? | Repeatable held-out outcomes; outcome depends on strategy, not logs |
| E03 — scalable worlds (later) | W06, W07, W08 | Is a richer world worth dependencies and simulation cost? | Demonstrated extra measurable research value over E02 |
| E04 — strict brain | G01, G02, minimal custom | Which smallest agent loop safely accepts observation and emits one validated JSON action? | Zero shell/network/secret authority; per-agent independent memories and metered calls |
| E05 — mutation archive (M2) | G04, G05, minimal custom | Can candidate versioning + offline evaluation be borrowed without evaluator capture? | Parent hash, trial evidence, rollback and isolated execution verified |
| E06 — persistent social design (later) | W09, W10, W11, G07, G08 | Are memory/replay patterns cheaper to adapt than local SQLite/files? | Better cross-episode retrieval under equal actual token budgets and unchanged referee |

## Report format (one file per candidate / experiment)

Suggested: `foundation/research/evaluations/E01-W02-YYYYMMDD.md`.

```markdown
# E01-W02 — PettingZoo
Status: not_run | static_review | smoke_pass | test_fail | decision_recorded
Upstream repo and commit:
Local branch/adapter diff:
Licenses, assets and transitive dependencies:
Environment, interpreter and lock hash:
Target M0/M1/M2 contract:
Minimal integration and trusted boundary:
Hard gates L/T/S/R/A/O: PASS/FAIL/N/A with evidence (file/test/log):
Measurements: runs, seeds, outcomes, wall time, memory, code/dependency counts:
Actual LLM usage: requests, prompt/completion tokens, currency (if applicable):
Comparison against B0/B1/B2/B3:
Known negative/failed experiments:
Assessment, weighted dimensions and uncertainty:
Decision: adopt/adapt/study/defer/reject
Decision owner, review date, related decision ID:
```

**Stop condition:** a candidate that fails a legal or trust hard gate is study-only until resolved; stop testing a category after one clear fit is demonstrated and the next alternative cannot plausibly outperform its cost/security; otherwise cap evaluation work by a user-approved time and model-spend budget. Never automatically import source from multiple projects, initiate paid trials or promote a dependency without a human decision.
