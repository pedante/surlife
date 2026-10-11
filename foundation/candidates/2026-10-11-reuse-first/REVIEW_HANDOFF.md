# R1 source audit, review handoff and unresolved conflicts

**Candidate:** [PROPOSAL.md](PROPOSAL.md) · [TRADEOFFS.md](TRADEOFFS.md).  
**Date:** 2026-10-11. **Author role:** synthesizing author of a NEW candidate, **not** an independent reviewer of frozen 0001. It would be methodologically false to count this document as a reviewer submission.  
**Source baseline:** `pedante/surlife` main plus unmerged PRs #1/#2/#3 accessed through GitHub. The original project has no runnable Surlife implementation.

## 1. Audited canonical files and what survives

| Source | Core idea/evidence | R1 handling |
|---|---|---|
| [root AGENTS.md](../../../AGENTS.md) | immutable referee, no unsafe organism authority, critical review discipline | Keep all invariants; no runtime code |
| [root README.md](../../../README.md) | hybrid evolving prompts/code, survival, weather, public competitors, eventual heredity | Preserve as long-term north star; do not claim working ecosystem |
| [foundation/README.md](../../README.md) | iterative design, one living plan, immutable review snapshots | R1 lives **outside** PLAN and iterations pending human decision |
| [foundation/AGENTS.md](../../AGENTS.md) | reviewers may only edit reviews, revisers need acceptance | R1 is a design candidate, not a reviewer artifact nor accepted revision |
| [foundation/CONTEXT.md](../../CONTEXT.md) | organism vs referee boundaries, social/ecological future | Explicit future extension seams |
| [foundation/PLAN.md](../../PLAN.md) | M0 deterministic world → M1 prompt agents → M2 one mutable module, controls | Preserve milestone gates and refine architecture/interface/economy |
| [foundation/REVIEW_PROTOCOL.md](../../REVIEW_PROTOCOL.md) | independent critique and human synthesis before plan changes | No auto-approval or reviewer consensus claim |
| [foundation/RUBRIC.md](../../RUBRIC.md) | 7 design dimensions, security blockers trump scores | Retain official rubric; trade-off score is separate user-priority metric |
| [foundation/STATUS.json](../../STATUS.json) | iteration 0001, zero completed reviews, implementation not started | Do NOT update to imply R1 accepted |
| [0001 frozen PROPOSAL](../../iterations/0001/PROPOSAL.md) | original falsifiable minimum experiment | Remains unchanged; R1 is proposed future replacement |
| [0001 SYNTHESIS](../../iterations/0001/SYNTHESIS.md) | synthesis pending | Do not manufacture evidence |
| [0001 reviews folder](../../iterations/0001/reviews/README.md) | no completed independent reviews yet | Commission separate reviewers before promoting R1 |
| [foundation/ideas/README.md](../../ideas/README.md) | ideas are hypotheses, not architecture requirements | R1 adopts only testable interface seams |
| [foundation/ideas/0001](../../ideas/0001-future-ecosystem-mechanics.md) | aging, skills, mixing, assimilation, social learning, niche construction | Preserve in later M3–M6, requiring independent gates |
| [foundation/decisions/README.md](../../decisions/README.md) | ADRs require maintainer decision | Proposed choices C-R1..C-R6 not yet ADRs |
| [docs/01-origins-ideas-problems.md](../../../docs/01-origins-ideas-problems.md) | shift from arbitrary self-editing to bounded hybrid prompt/code | Reject source corruption and whole-world self-modification |
| [docs/02-hybrid-organism.md](../../../docs/02-hybrid-organism.md) | immutable laws / trusted core / mutable genome / environmental alteration | Maintain ownership split; add versioned skill contracts |
| [docs/03-agent-frameworks.md](../../../docs/03-agent-frameworks.md) | mini-SWE, nanobot, Igor, Letta, DGM, OpenEvolve | Narrow mini-SWE pilot, borrow patterns, reject giant unified runtime |
| [docs/04-what-is-life.md](../../../docs/04-what-is-life.md) | identity, resource metabolism, learning, heredity, death, open-endedness | Distinguish learning, evolution and open-endedness |
| [docs/05-related-research.md](../../../docs/05-related-research.md) | Avida, Voyager, Promptbreeder, OpenLife etc | Methodological background, not performance guarantees |
| [docs/06-lifecycle-and-arena.md](../../../docs/06-lifecycle-and-arena.md) | tick phases, ledger, weather, interventions, illness, reproduction | Version phases; defer illness and reproduction |
| [docs/07-technical-architecture.md](../../../docs/07-technical-architecture.md) | Python-first core, energy ledger, genome store, isolated code | Simplify to SQLite + strict external task/worker contracts |
| [docs/08-roadmap-and-experiments.md](../../../docs/08-roadmap-and-experiments.md) | static/prompt/code/hybrid controls, M0–M5 staged | Add P0 adapter check, explicit lifecycle cost, M6 ambition |
| [docs/09-decisions-and-open-questions.md](../../../docs/09-decisions-and-open-questions.md) | preferred ideas D-01..D-15, unresolved tasks | Carry preferences, not treat as enacted ADRs |
| [docs/REFERENCES.md](../../../docs/REFERENCES.md) | prior external research links | Keep provenance; pin exact versions before code reuse |
| [examples/organism.example.json](../../../examples/organism.example.json) | genome manifest draft | Preserve concept; amend schema only after acceptance |
| [examples/world.example.json](../../../examples/world.example.json) | cap, weather, funding, tentative upkeep prices | Values are illustrative only, no calibration |
| [examples/action.example.json](../../../examples/action.example.json) | action intent schema | Extend with idempotency and separated cognition; not existing validated spec |
| [foundation/prompts/REVIEWER.md](../../prompts/REVIEWER.md) | independent reviewer input contract | Use for independent R1 reviewers **after freezing an accepted candidate** |

## 2. Three open PRs were read; do not mistake them for accepted decisions

| PR | State at audit | Actual content | R1 treatment |
|---|---|---|---|
| [#1 — reusable life agents/arenas](https://github.com/pedante/surlife/pull/1) | **Open**, 5 files, 29 untested candidates; no comments or review submissions | `foundation/research/REUSE_CANDIDATES.md`, `CANDIDATES.json`, `EVALUATION_PROTOCOL.md`, README/navigation | Use inventory, initial licenses, hard reuse tests, no made-up measurements. [Direct research branch](https://github.com/pedante/surlife/tree/research/life-agents-arenas-catalog-20261011/foundation/research). |
| [#2 — arena frameworks](https://github.com/pedante/surlife/pull/2) | **Open draft**, 2 files; no comments or reviews | Custom authoritative Python referee; optional PettingZoo adapter; OpenSpiel task benchmark | **Tentative architectural selection** subject to integration spike. [Specific note](https://github.com/pedante/surlife/blob/research/arena-framework-architecture-20261011/foundation/ideas/0002-arena-framework-comparison.md). |
| [#3 — brain comparison](https://github.com/pedante/surlife/pull/3) | **Open**, 2 files; no comments or reviews | Mini-SWE-style restricted loop vs nanobot; M2 isolated coding worker, pinned upstream repo examples | **Tentative reasoning selection**, preserve custom-loop fallback. [Specific note](https://github.com/pedante/surlife/blob/research/nanobot-vs-mini-swe-core-20261011/foundation/ideas/0002-reasoning-core-nanobot-vs-mini-swe.md). |

**Merge caveat:** PR #2 and #3 both edit `foundation/ideas/README.md` from the same base. A maintainer should reconcile the index after choosing which to merge, rather than assume both PRs apply without conflict. PR #1 edits `foundation/README.md` and introduces the research directory. R1 introduces its own folder, avoiding overlapping edits and dependency on unmerged branch contents.

### Actual source-code observations, not hypotheses

1. PR #3 inspected [mini-SWE `DefaultAgent` at 04d809ce](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py) — model query, trajectory and action execution are coupled around an environment interface. Its [local environment](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py) uses `shell=True` and host environment variables: never expose to an organism referee boundary. A Docker environment also executes commands and needs separate security review. MIT license identified.
2. [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) defines AEC and Parallel multiagent APIs; it does **not** implement Surlife's protected energy ledger. An adapter is a portability mechanism, not a referee.
3. [OpenSpiel](https://github.com/google-deepmind/open_spiel) offers existing objective games and game-analysis tools, but requires its own C++/Python dependency considerations.
4. [DGM](https://github.com/kew-lab/darwin-godel-machine) publicly warns that model-generated code can be destructive; its runnable evaluator is **not** Surlife's sandbox solution. [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) supports population archive and evaluators; neither has been benchmarked here.
5. [Descartes](https://github.com/Lightless-Labs/descartes) documents layered cheap reflexes, evidence, LLM escalation and learning. Its `package.json` currently says `UNLICENSED`; do not copy it. [Foundry](https://github.com/Lightless-Labs/foundry) supplies independent red/green methodology; full execution engine is not in that public plugin repo.
6. Earlier discussion and `docs/03` already warned that Igor's host-administration Bash loader is not suitable for hostile organisms.

## 3. Open contradictions or underspecified choices that reviewers should attack

| ID | Issue | Why it matters | R1 disposition |
|---|---|---|---|
| R1-Q01 | `docs/06` describes complex lifecycle every tick; frozen 0001 deliberately excludes reproduction/illness | Too many simultaneous mechanisms prevent causal interpretation | Reserve extension phases only |
| R1-Q02 | Frozen 0001 mixes `reflect`, `stage_code_mutation` and `compete` in one action vocabulary | Thought, write and game transitions have different authority and time/cost semantics | Separate cognitive and world actions, define budgets and tick phases |
| R1-Q03 | PR #3 recommends a mini-SWE-**style** loop, while the user prefers actual mini-SWE reuse | Whole package may be larger and less safe than expected; pattern-only may underdeliver reuse | P0 directly compares adapted upstream code to native loop, chooses after evidence |
| R1-Q04 | SQLite append/commit vs raw append-only JSONL | JSONL by itself does not make ledger/state atomic across crash | SQLite transaction is source of truth; JSONL an export |
| R1-Q05 | Task-duel not yet specified enough to reward learning | Greedy/reference policy may dominate all tasks; code skill may be overinvestment | Discriminating seeded puzzle family and optional existing benchmark |
| R1-Q06 | Severe scarcity may create random winner-take-all elimination | Confounds competence and beginning wealth | Matched starting balance, independent blind benchmark, calibrated mint/upkeep |
| R1-Q07 | Big vision includes evolvable 'metabolism' but immutable real resource limits | Risk of allowing organism control of supervisor billing | Metabolism is organism strategy under externally frozen price rules |
| R1-Q08 | Hidden test descriptions can leak through evaluation messages | Produces overfitting and tainted lineage selection | Opaque trial feedback, held-out research test physically separated |
| R1-Q09 | Provider's usage/billing may lag/omit data | In-world energy is not a provider financial lock | Conservative pre-reservations and provider-side cap when available, fail-closed |
| R1-Q10 | Stateful LLM text is nondeterministic | Fresh rerun cannot guarantee byte replay | Archive original outputs; replay reducer with recorded decisions |
| R1-Q11 | Container boundaries are often overstated | Host compromise invalidates research | No generated code until independently reviewed confinement passes |
| R1-Q12 | "Open-ended" term invites unjustified claim | One task pack tests narrow improvement only | Later cross-domain niches and falsifiable novelty metrics |

## 4. Independent review assignment (do not simulate independence)

This candidate is **not a completed independent review of iteration 0001**. Before any promotion:

1. Collect one unexposed independent **security, licensing and implementation-ease** review of frozen 0001 under `foundation/iterations/0001/reviews/` using canonical protocol.
2. Collect an independent **experimental validity, economy and open-endedness** review, without revealing review 1 to reviewer 2.
3. Synthesize *0001* reviews and make an explicit maintainer decision. Record the dispositions and accepted modifications.
4. Use R1 as one proposed synthesis input / revised candidate, not as the source of the reviews' alleged independent agreement. If selected, update `PLAN.md`, status and a **new frozen numbered iteration** in a separate, explicitly approved revision PR; never overwrite 0001.
5. Run independent reviews against that new frozen iteration before approving implementation. Use the official [rubric](../../RUBRIC.md), not R1's separate user-priority architecture weights.

**Reviewer challenge A (architecture/security)**: Show the smallest viable interfaces. Find one way mini-SWE default behavior could cross authority, one crash/retry double-settlement, one memory leak, one unaccounted real-billing path, and one cheaper architecture.

**Reviewer challenge B (science/economics)**: Construct a fixed/deterministic agent that appears to improve on the benchmark without learning; show a scenario where hybrid skill development loses on total tokens and/or CPU; propose matched-budget evaluation under new weather and novel task families.

**Reviewer challenge C (reuse and future scope, optional)**: Identify 2 upstream libraries whose adoption would *measurably* reduce maintenance; identify where custom contracts become lock-in or restrict inheritance and emergent cognition; propose precise adapter migration tests.

## 5. Immediate bounded empirical evidence to seek (if a maintainer approves)

**P0-P1 (offline):** pinned mini-SWE local action interface vs safe structured-action adapter vs tiny native Python runner. No provider calls. Count dependencies, privileged lines, error surfaces, trajectory fidelity, ability to plug in fake models and context stores. Reject adapters that allow shell or host reads.

**P0-P2 (offline):** simple task scorer and OpenSpiel existing task option. Prove differences between two deterministic policies in several regimes; choose smallest discriminating benchmark. This is allowed as a controlled comparator without making OpenSpiel the referee.

**P0-P3 (offline):** design SQLite schema, idempotent event reducer, seeded replay and leakage/privacy tests using generated examples, no paid models.

**No real code mutation experiments** before documented isolation threat model, independent adversarial tests, explicit cost cap and maintainer authorization.

## 6. Evidence status labels

- **Verified:** repository documents/README, direct upstream source snippets, PR metadata, license declaration text cited above.
- **Plausible design hypothesis:** small Python referee + mini-SWE adapter, TaskPack interchange, selective cognitive escalation and future inheritance.
- **Untested engineering estimate:** scores in TRADEOFFS, relative complexity, model cost and migration difficulty.
- **Experimental finding:** **none** from Surlife itself. No tests, provider spending, integration benchmarks or simulations have been performed as part of this proposal.

**Review unit:** R1 should remain in its own candidate folder unless the maintainer intentionally freezes a new iteration later.
