# R1 — Reviewer 1 architecture/security notes (reconstructed from supplied material)

> **Provenance warning — NOT a verified original final review.** This file was assembled on 2026-10-11 from the user's supplied sequence of Reviewer 1 progress/analysis notes. The supplied material contains no final Markdown report, no actual upstream citation ledger, no exact model/provider identity, and no confirmation that the reviewer successfully read the private repository. **Do not count this reconstruction as a fully independent, source-verified critique or an implemented security design.** The notes themselves explicitly say GitHub could not be accessed and much of the analysis was inferred from the task description. This editorial reconstruction preserves the substance of the supplied positions, while marking unsupported claims and correcting unsafe overstatements.

| Field | Value |
|---|---|
| Proposal under discussion | Surlife candidate R1, PR [#4](https://github.com/pedante/surlife/pull/4), **not** the older `foundation/PLAN.md` |
| Source proposal SHA | `8b4a23d23db30adaa5b3008ad419089cf7697735` (identified by the repository owner/review integration; **not verified by Reviewer 1**) |
| Date of compilation | 2026-10-11 |
| Reviewer 1 provider/model | **Not stated in supplied notes; unknown.** Do not attribute the notes to any particular model. |
| Source form | User-provided narrative of review progress and proposed conclusions, **not an original completed review artifact** |
| Reviewer's repository access | **Reported unavailable**; the notes explicitly pivot to inference/simulation |
| Execution evidence | None; no security tests, integration tests or benchmarks supplied |
| Independence | Access to other reviews is not described; **cannot verify** |
| Integration/editorial handling | Positions transcribed/paraphrased faithfully, with technical qualifications added and labeled below |

## 1. Executive position recovered from the notes

**Provisional view expressed by Reviewer 1: strongly reconsider R1's dependency and runtime choices.** The notes favor a Python-controlled multi-agent environment via **PettingZoo**, possibly **Mesa**, a strictly limited agent state machine rather than a shell-centric mini-SWE runtime, a stronger generated-code isolation boundary, a LiteLLM proxy, and a larger-scale database strategy. A candidate replacement combines **PettingZoo + WebAssembly-based skill execution + PostgreSQL/snapshots**.

This is a position based primarily on inferred architecture. It is **not** evidence that PettingZoo, Wasm, LiteLLM or PostgreSQL was run, and should **not** supersede the primary R1 proposal or source-verified engineering evidence.

**Important cross-check against actual R1:** R1 already says an organism worker may not receive referee authority, a plain local subprocess/default Docker setup is insufficient isolation, model spending is independently controlled, and SQLite is serialized for a small v0. Several notes frame these as absent; those criticisms are inaccurate as descriptions of the proposal, even if they motivate more specific acceptance tests.

## 2. Architecture and security objections recovered

### R1-RV1-N01 — MAJOR: coding-agent reasoning core may be a poor fit

**Note-derived claim:** Adapting mini-SWE-agent's shell-oriented multi-step workflow to long-lived, one-intent organisms risks brittle integration. A small explicit state machine and structured JSON action envelope may be easier to understand.

**R1 reference:** `PROPOSAL.md` §§0, 3–4; `TRADEOFFS.md` §§1–3.

**Engineering qualification:** This is a serious hypothesis, not demonstrated. R1 already mandates a fake-model spike and a tiny loop fallback. Test the actual number of extension points, custom parser changes, dependencies, permissible action paths, restart behavior and paid token overhead. Do not discard mini-SWE's separate use as an M2 coding worker without a like-for-like evaluation.

**Evidence required:** Two scripted organisms with the same mocked model outputs produce byte-equivalent intents and replay records through native and mini-SWE adapters; no shell environment reachable.

### R1-RV1-N02 — MAJOR: claim that a bespoke referee reinvents all of PettingZoo is too broad

**Note-derived claim:** Adopt PettingZoo's multi-agent interface, with Mesa for spatial models and scheduling, rather than inventing all simulation plumbing.

**R1 reference:** `PROPOSAL.md` §§2–3, 5–6.

**Engineering qualification:** PettingZoo specifies multi-agent `reset/step` interfaces; it does **not** itself supply Surlife's secure escrow ledger, account settlement, genome authorization, model-money accounting or event replay. A `ParallelEnv` wrapper can be valuable **without replacing** a small authoritative reducer. Mesa may earn a role once spatial interactions and complex scheduling are actually required. Treat “referee = PettingZoo” as an **unverified integration hypothesis** rather than a supported fact.

**Evidence required:** PettingZoo conformance and fixed-seed parity against the same reference ledger/replay invariants; compare *total maintained code/dependencies*, not the existence of framework features.

### R1-RV1-N03 — BLOCKER if violated: hostile executable code cannot be trusted

**Note-derived claim:** Model-authored Python must not execute with host secrets, referee state or peer workspaces. The notes propose gVisor-backed containers or WebAssembly runtimes.

**R1 reference:** `PROPOSAL.md` §§2, 4, 7, 9.

**Engineering qualification:** R1 already recognizes this blocker. gVisor and Wasm may reduce exposure under a **specified threat model**, but neither is a “mathematically provable memory boundary” for an entire end-to-end host system. Wasm embedding, filesystem/network imports, fuel/memory limits, host function capabilities, generated-code translation and escape paths require independent testing. A Python `eval` ban is not a sandbox. Default Docker also does not magically make untrusted code safe.

**Evidence required:** disposable-worker profile with no network/secrets/peer mounts, CPU/memory/time quotas, resistant to file-read and capability escalation fixtures, and fail-closed host/worker protocol.

### R1-RV1-N04 — BLOCKER if violated: independently meter real API spending

**Note-derived claim:** Protect real provider credentials and enforce spending quotas through a local model proxy, possibly LiteLLM.

**R1 reference:** `PROPOSAL.md` §§2, 6.

**Engineering qualification:** LiteLLM supplies provider abstraction/routing, **not proof of a hard spending ceiling**. Surlife still needs a trusted pre-call worst-case reservation, output limits, retries and concurrency admission, uncertain-usage accounting and external account-side checks. Cost estimates after model invocation alone are insufficient.

**Evidence required:** concurrent reservation, provider timeout/retry, missing usage, streaming interruption and spending-stop fixtures with mock transport and no real calls.

### R1-RV1-N05 — QUESTION: SQLite growth/concurrency risk lacks a measured threshold

**Note-derived claim:** SQLite event sourcing and genome versioning might create substantial contention/size, so PostgreSQL/snapshots (DuckDB for analytics) might be better.

**R1 reference:** `PROPOSAL.md` §§2, 6, 9.

**Engineering qualification:** A serialized, two-organism initial world is a good match for SQLite transactional semantics. Neither “computationally prohibitive” state growth nor a need for distributed execution was demonstrated by the notes. Keep a migration seam and measure write volume, lock duration, replay and snapshot size before adding a database service.

**Evidence required:** crash/recovery and restart invariants at target agent/tick counts; a predeclared threshold at which PostgreSQL's concurrency benefits justify its deployment cost.

### R1-RV1-N06 — MAJOR: memory growth and independent organism fault isolation

**Note-derived claim:** Unbounded history, context and live workers may harm long-running organisms. Memory compression, retrieval and isolation should be explicit.

**R1 reference:** `PROPOSAL.md` §§2–3, 6, 9.

**Engineering qualification:** An optional memory retrieval/index policy is valuable, but a vector database or complicated hierarchical memory system is not automatically needed for two organisms. Define bounded context, private data access, durable append events vs mutable summaries, worker restarts and explicit corruption recovery. Avoid a single shared mutable worker context.

**Evidence required:** offline restart with two different souls/memories; forced worker crash does not expose, delete or modify another organism's state or damage the ledger.

### R1-RV1-N07 — QUESTION: multi-generation evolution and distributed execution

**Note-derived claim:** A fixed single-host serialized model may limit large-scale populations.

**Engineering qualification:** This is a plausible future scaling issue, **not** a blocker for R1's 2-organism experiment. Versioned wire protocols, append-only lineage hashes and isolated worker placement offer migration without prebuilding a distributed scheduler. Postpone remote execution until a measured workload demands it.

## 3. Reuse alternatives named in the notes

| Candidate | Role proposed in notes | Editorial assessment of reuse |
|---|---|---|
| PettingZoo | Main multi-agent environment interface | Good adapter candidate; not replacement for economic/referee laws |
| Mesa | Spatial grid and scheduling | Test when richer ecology arrives, not necessarily M0 |
| mini-SWE-agent | Replace with a structured decision loop | Strong hypothesis for M1; preserve optional M2 coding-worker evaluation |
| LiteLLM proxy | Model credential and quota facade | Provider abstraction useful if needed; spending authority must remain Surlife-owned |
| Wasmtime/Wasm or gVisor | Code isolation | Threat-model-dependent candidates requiring specific host/API tests |
| PostgreSQL | World and genome persistence | Good for later concurrency; premature before SQLite bottleneck evidence |
| DuckDB | Offline analytics | Potentially useful independently from live transactions |
| LangGraph | State-machine tooling alternative | Could be overkill for one intent per tick; test minimal protocol first |
| OpenSpiel | Notes would reject turn-based games | Overbroad rejection: existing objective games may reduce bespoke benchmarking even if not live world |
| PettingZoo + Mesa + proxy + Wasm + PostgreSQL | Entire alternative stack | High reuse on paper, also significant integration/operation complexity |

## 4. Alternative scores quoted in the supplied notes

The notes report **30.5/100 for “initial architecture”; 78.5/100 for PettingZoo/Wasm/PostgreSQL; 67/100 and 66.5/100 for two other unnamed alternatives**. **These cannot be validated**: no criterion-level ratings, code, reproducible score calculation, objective evidence, or precise alternative names are present in the source material. Preserve them as *the reviewer's asserted scores*, **not this file's measured ranking**.

Under the user's weighting (reuse 30%, integration 25%, evolutionary freedom 20%, security 15%, reproducibility 10%), the central tension is that replacing a small reducer with three new services may **reduce** integration simplicity even while reusing more lines of third-party code.

## 5. Proposed incremental integration sequence attributed to Reviewer 1

The supplied notes propose: (1) first establish provider proxy/spend protection; (2) choose and test a Wasm or gVisor isolation strategy; (3) integrate PettingZoo and optional Mesa; (4) use structured LLM or state-machine agents; (5) test context longevity, generated Wasm compilation and SQLite contention before scaling.

**Editorial alternative, consistent with R1's no-paid-call gates:** Begin with zero-provider-cost referee/replay/ledger fixtures; add mock provider budget reservations and a no-shell action runner; only develop isolated generated-code execution and optional PettingZoo interoperability after the minimum experiment proves interesting. Whether the extra components truly save maintenance remains unverified.

## 6. Counterexamples, stop conditions and required evidence

1. **PettingZoo-only economy exploit:** a legal multi-agent reward is incorrectly credited as ledger currency twice on duplicate `step` calls. An independently idempotent SQLite settlement must prevent it.
2. **Proxy quota exploit:** a retry or simultaneous request bypasses a post-call token counter. Reject unless pre-call reservation and serializable reconciliation survive injected failures.
3. **Wasm false safety:** host functions permit reading a mounted secret or calling an unrestricted service despite bytecode memory isolation. Deny such capabilities by construction and demonstrate the rejection.
4. **SQLite scale assumption:** real two-organism replay remains fast and correct under target loads; a database service then adds cost without benefit.
5. **Scientific confound:** a more complex optimized stack produces different task outcomes because of extra cognition calls, not improved evolution; compare identical opportunities and true lifecycle resources.

## 7. What this document can and cannot establish

**Supported:** the reviewer notes express skepticism about mini-SWE for routine decisions, seek greater reuse of simulation contracts, and prioritize confinement and model-cost authority.

**Unsupported:** that Reviewer 1 read PR #4; that the private repository was nonexistent; that PettingZoo fully replaces the referee; that WebAssembly delivers an end-to-end mathematical security proof; that SQLite cannot scale; that the stated architecture scores are evidence-based; that security fixes were *implemented*. The phrase “implementing security fixes” in the supplied notes describes a drafting intention, **not code changes**.

**Disposition:** treat as **preliminary, provenance-limited reviewer input** for later synthesis. Obtain the original complete report or a new verified independent review before counting it as a formal R1 reviewer submission.

## Source links used to contextualize, not to retroactively validate Reviewer 1

- [R1 proposal](https://github.com/pedante/surlife/blob/8b4a23d23db30adaa5b3008ad419089cf7697735/foundation/candidates/2026-10-11-reuse-first/PROPOSAL.md)
- [R1 tradeoffs](https://github.com/pedante/surlife/blob/8b4a23d23db30adaa5b3008ad419089cf7697735/foundation/candidates/2026-10-11-reuse-first/TRADEOFFS.md)
- [PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/)
- [mini-SWE DefaultAgent](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/agents/default.py)
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html)

**Integrity statement:** This editorial reconstruction does not modify the original R1 proposal and is not a substitute for the missing original Reviewer 1 report.
