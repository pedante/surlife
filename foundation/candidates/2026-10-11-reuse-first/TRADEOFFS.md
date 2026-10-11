# Trade-offs and tentative scoring — candidate R1

**Date:** 2026-10-11. **State:** qualitative design judgments, *not measured benchmark scores*. No candidate here has passed Surlife tests. Hard security/legal/reproducibility gates override numeric scores. See [PROPOSAL.md](PROPOSAL.md) for the proposed system and [REVIEW_HANDOFF.md](REVIEW_HANDOFF.md) for evidence and review status.

## 1. Weighted architecture decision matrix

User priorities are explicit: **reuse/adaptability**, **easy integration**, and **ability to grow into ambitious digital life**. We score design hypotheses with:
- **R — useful reuse/adaptability, 30%:** scope of already-built compatible components and freedom from supplier lock-in.
- **I — integration/maintenance ease, 25%:** minimal trust surface, new dependencies, cross-language services, moving parts and upgrade friction.
- **F — future evolution room, 20%:** ability to add genome changes, new tasks/ecologies, reproduction, social exchange without replacing the architecture.
- **S — boundary clarity/safety, 15%:** separable referee, secrets, model gateway and untrusted code. A failing actual safety gate disqualifies regardless of score.
- **E — experimental clarity, 10%:** replayable, objective measurement and comparable baselines.

Each scored 0–5; total = `6R + 5I + 4F + 3S + 2E`, out of 100. This favors project goals rather than benchmark speed. **Confidence: low to moderate**, because engineering hours, code sizes, tests and package security were not measured.

| Option | R | I | F | S | E | /100 | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| **A — Custom referee + isolated mini-SWE-compatible runner + versioned skill/TaskPack contracts (proposed)** | 4 | 4 | 5 | 4 | 5 | **86** | Narrow reusable adapters, small authoritative core, explicit future extension seams. Actual mini-SWE code reuse remains conditional. |
| **F — Existing objective-task benchmark first, minimal life economy later** | 4 | 5 | 2 | 5 | 5 | **82** | Scientifically fast and low-risk but defers the survival/ecology research question. Strong falsification baseline. |
| **B — Fully original tiny agent loop + custom referee + small future-facing contracts** | 2 | 5 | 4 | 4 | 5 | **75** | Integration likely easiest, but reimplements trajectories/model behavior and may miss reusable components. Fallback if A's adapter fails. |
| **E — Custom referee + full mini-SWE + integrated DGM evolutionary machinery** | 5 | 2 | 4 | 2 | 4 | **70** | Substantial code reuse but dynamic code execution and optimizer integration make trust harder. |
| **G — Mesa world + mini-SWE organism + additional custom economy** | 4 | 3 | 4 | 3 | 3 | **70** | Worth a future ecology spike; no clear benefit for 2-organism M0 and adds scheduling abstractions. |
| **C — PettingZoo/OpenSpiel as primary life-world + unmodified mini-SWE** | 5 | 2 | 3 | 2 | 3 | **64** | PettingZoo/OpenSpiel do not supply persistent cost/ledger/lineage. Default mini-SWE shell makes it a security non-starter. |
| **D — Custom world + full nanobot runtime + full OpenEvolve framework** | 4 | 2 | 4 | 2 | 4 | **64** | Flexible, but assistant framework and optimizer both add major privilege/dependency surfaces. |
| **H — Directly transplant Descartes/Agent Zero as the entire organism runtime** | 4 | 1 | 3 | 1 | 2 | **48** | User-machine administration is not safe organism execution; Descartes source is marked UNLICENSED. |

**Sensitivity:** A's leading score depends on its *adapter* staying thin. If the mini-SWE adapter cannot be made safe or maintainable without importing significant shell/task/session assumptions, A becomes B (tiny native loop) with mini-SWE reserved for M2 isolated code generation. The first spike resolves that, not a vote. F is a useful scientific simplification and can run alongside A without replacing the life-world.

## 2. Component reuse decisions by milestone

| Existing source | Proposed reuse | Timing | Direct source import? | Important test |
|---|---|---|---|---|
| [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) | Decision/trajectory/model loop; coding worker | M1, M2 | **Adapter candidate**, MIT; inspect pinned v2 API and remove shell authority | Same fixture succeeds as tiny native runner, with no host access |
| [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) | Standard `ParallelEnv` outer adapter for external agents | M2/M3 if research benefit | Optional MIT dependency, only if parity succeeds | Referee-native and adapted runs have same events/balances |
| [OpenSpiel](https://github.com/google-deepmind/open_spiel) | Pre-existing games, benchmark policies and analysis | M0 evaluation alternative, M2+ | Prefer **isolated task benchmark** to avoid C++ dependency in core | Two baselines discriminate, hidden seeds, score independent of stakes |
| [Mesa](https://github.com/mesa/mesa) | Scheduling/ecology patterns for larger worlds | M3+ | No for M0, potential arena implementation *only if* transition seam holds | Multiagent simulations beat bespoke scheduling complexity |
| [nanobot](https://github.com/HKUDS/nanobot) | Memory/context arrangement and tool ideas | M1 study | Not complete assistant runtime; MIT | Retrieval vs native SQLite improves held-out utility after cost |
| [Letta Code](https://github.com/letta-ai/letta-code) | Versioned identity and persistent memory | M1/M3 study | No TypeScript service in v0 | Memory benefit net of context spend |
| [Voyager](https://github.com/MineDojo/Voyager) | Reusable skill catalog and iterative repair patterns | M2 | Avoid Minecraft/Node dependencies | Working task skill invoked without LLM repeatedly |
| [Darwin Gödel Machine](https://github.com/kew-lab/darwin-godel-machine) | Trial/evaluation, ancestor graph, empirical fitness | M2 | No unrestricted DGM runtime; optional archive adapter | Safe independently tested parent/candidate comparisons |
| [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) | Population archive, diversity and evaluator conventions | M2/M4 | Try submodule only if licensing/dependency/trust audit passes | Archive beats minimal indexed candidate store |
| [Avida](https://github.com/devosoft/avida) | Methodology for inherited digital programs | M4 study | License not verified in PR #1 | Validly controlled inheritance measurements |
| [Neural MMO](https://github.com/NeuralMMO/environment) | Resource/survival mechanics and richer tasks | M3+ | Avoid full RL stack in M0 | Richer world adds non-trivial selection and maintains replay |
| [Concordia](https://github.com/google-deepmind/concordia) | Social scenarios, game-master design | M3+ | Outside referee, no LLM adjudication of energy | Strong social test with independent objective judge |
| [Igor](https://github.com/pedante/igor_core) | Runbooks, module validation and rollback lessons | M1/M2 | GPL questions; never use host shell module loader in referee | Smaller adapter than native implementation |
| [Descartes](https://github.com/Lightless-Labs/descartes) | Reflex/escalation, evidence completeness, staged learning | M1/M2 | **Design only**; package declares `UNLICENSED` | Evolved escalation saves tokens on unseen tasks |
| [Foundry](https://github.com/Lightless-Labs/foundry) | Independent red-team/hidden-test workflow | Before M2 | Pattern first; public plugin is not its private engine | Blind tests stay hidden from coder; exploit detected |
| [Third Thoughts](https://github.com/Lightless-Labs/third-thoughts) | Off-line transcript research: entropy, state changes, failure modes | M3+ | AGPL; method study, avoid runtime dependency | Stratified analysis robust across runs |
| [Willikins](https://github.com/Lightless-Labs/willikins) | Typed requests, approval semantics and drift guards | M0 design | AGPL; pattern only | Invalid actions rejected before effects |
| [Refinery](https://github.com/Lightless-Labs/refinery) | Independent review/critique workflows | Research design loop | MIT; **outside organisms** | Distinct critiques surface falsifiable objections |
| [Pessimal](https://github.com/Lightless-Labs/pessimal) | Host resource telemetry for many experiments | Much later | No v0 use; AGPL | Added overhead justified by experiment operations |

**License caution:** Per PR #1, OpenLife's official code is unverified, Avida's license unresolved, EMAS is PolyForm Noncommercial, and certain AgentSociety code is not covered by the same license. Do not casually import them into a permissively licensed project. Foundry's package describes MIT but no root LICENSE was found in a limited check; verify before copying. Each upstream dependency must be pinned to an exact commit/release and audited before actual import.

## 3. Attack the recommendation — key possible reversals

| Current assumption | Evidence that reverses the choice |
|---|---|
| Mini-SWE can expose one structured world intent cleanly | Its parser/runner needs custom hacks, costly context, unsafe shell coupling or a second process per simple choice → use tiny native decision loop, reserve mini-SWE for isolated mutation worker |
| Custom referee is cheaper than external world framework | Mesa/PettingZoo wrapper passes replay/economy/privacy invariants with fewer trusted lines and lower measured maintenance → adopt the small compatible piece |
| Code evolution yields net value | Generation + trial tokens exceed savings over observed reuse horizon; code-only/hybrid do not beat fixed/prompt controls → pause M2, refine task distribution |
| One puzzle family is enough to choose a mutation mechanism | Trivial optimal policy dominates all regimes, or hidden scores collapse → use several existing objective task packs / OpenSpiel before claiming progress |
| Reflexes aid autonomy | Fixed-reflex baseline beats evolved escalation and suppresses useful discovery → keep it optional and measure reward-cost Pareto front |
| A small Python ledger is safe | Crash/fault tests reveal inconsistent escrow or replay, even once → resolve invariant failure before any model calls |
| A container is sufficient for untrusted agents | Isolation review cannot confidently exclude host capabilities/secrets → no generated code on host, use reviewed disposable VM/remote sandbox or defer M2 |
| Existing repo review means acceptance | PRs #1–#3 lack independent reviews and remain open → document acceptance only after human decision under review protocol |

## 4. Explicitly rejected architectural shortcuts

- **Do not** merge nanobot, mini-SWE, Letta, DGM, OpenEvolve, and Descartes into one running organism.
- **Do not** use mini-SWE's default `LocalEnvironment` with `shell=True` for agents interacting with the real referee; its environment may expose process environment variables.
- **Do not** make the referee a God-model that judges natural-language performance, edits laws or approves its own changes.
- **Do not** treat a PettingZoo `reward` as permission to mint virtual energy. Objective task score, world E and real tokens are distinct.
- **Do not** call a source-code repository 'reusable open source' if effective license grants have not been verified.
- **Do not** present these scores as scientific evidence that the hybrid organism evolves.

## 5. Economic and integration budget discipline

Early M0/P0 tests must consume **zero provider calls**. M1 model runs require explicit spending authorization and a request/token/time cap. Compare implementations at the same task opportunities and **actual total lifecycle spend**; long prompts, failed requests and repeated tool calls count.

For each spike record at minimum: source SHA/license, Python/runtime version, install size/dependency graph, lines of new privileged adapter code, model calls/tokens and failures, median decision latency, seeded replay results, untrusted-data leakage attempts, cost of maintaining integration, and evidence-backed recommendation. No untested guessed 'weeks saved', '2x faster' or '94%-likely' claims.

## 6. Preferred merge/evaluation order

This is a **proposal merge sequence**, not authorization to implement:
1. Finish independent review of 0001, and decide which ideas from PR #1/2/3 to incorporate. Their proposals have useful but overlapping source context; avoid merging competing edits to `foundation/ideas/README.md` blindly.
2. Review candidate R1 as a *replacement candidate* for a future `PLAN.md` revision, with marked uncertain choices and explicit veto tests.
3. Pin upstream versions and run **P0 adapter+contract spike with fake models only** after approval.
4. Implement M0 once approved; no paid model calls until M0 gate.
5. Only then spend a separately approved capped budget comparing M1 runners and evolution controls.

No merge should remove original ideas, reviewer critiques or negative results.
