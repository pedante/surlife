# Evolution-first implementation track (after M2.0)

**State:** Scoped proposal, NOT implemented. **Date:** 2026-10-12.  
**Direction:** [ADR-0002](decisions/ADR-0002-evolution-first.md).  
**Do not relabel previous milestone implementations or rewrite their protocols.**

## Goal

Demonstrate a software organism that **uses scarce, metered LLM consultations to choose a reusable change to its own strategy**, tests the change, pays for the attempts, and retains or rolls it back in a persistent competition. The arena exists to make that capability useful; enriching soil, movement or scenery is not an acceptance criterion.

### Already available — reuse before rewriting

| Component | Verified implementation area | Limitation |
|---|---|---|
| Versioned soul prompt, data-only notes, bounded memory | `src/surlife/souls.py` | M1-era tasks; no code modification |
| Model reflection, pending candidate, prompt hashes | `src/surlife/m11.py` | Host schedules cognition, reflection; mutation is not yet an independently budgeted organism policy |
| Conservative multi-cohort candidate evaluation | `src/surlife/evaluation_v2.py` | Separately operator-triggered; evaluation has no in-arena energy charge |
| Adaptive request policy, inheritance/tournaments | `src/surlife/m16.py`–`m18.py`, `m111.py` | Numeric cognition policy is not an editable soul/code genome |
| Objective non-additive challenges | `src/surlife/m19.py`, `m110.py` | Cheap marginal/beam/Oracle comparisons remain essential |
| Shared consequences / simultaneous actions / deterministic replay | `src/surlife/m20.py` | Optional ecology fixture; hard-coded policies, no learning |
| Referee, virtual ledger, bounded model gateway | `src/surlife/core.py`, `storage.py`, `gateway.py` | Never give these editable authority to organisms |

## M2.1 — First persistent *autonomous prompt-mutating organism*

**Research question:** Can giving an organism control of *when to consult, whether to propose a prompt mutation, and whether to spend on testing* improve net held-out survival/work relative to a frozen-prompt peer with the same **total** provider budget?

1. **One bounded action contract.** Organism may `work` with its current strategy, `consult`, `propose_prompt`, `trial_pending`, `activate_pending` or `discard_pending`. The referee/gateway validate schema, turn legality, ownership, remaining budget and activation evidence. Not every turn requires an LLM.
2. **Separate the mutation from the work.** A reflection/proposal is a model-produced *candidate*, not immediate authority to change the active prompt. Candidate has immutable parent hash, candidate hash, proposer request provenance, generation, and an explicit version. A pending candidate never affects ordinary work until an accepted activation boundary.
3. **No privileged agent tools.** The model never receives actual API keys, another organism's private state, referee source-edit permissions, shell, networking or a path it can use to overwrite live code. Provider-facing prompt text is always lower-trust than host rules.
4. **Charge the full lifecycle.** Charge virtual energy for consultation, proposal, candidate evaluation/trials and upkeep under documented rules; separately meter real input/output tokens, real request counts and external cost estimates. Hard host-owned call/monetary ceilings are checked before requests. The organism can earn more *virtual* energy and, if enabled, a predetermined bounded allowance over time; earning energy never bypasses the real gateway cap.
5. **Promotions must be earned.** A host-verified comparison on disjoint held-out tasks, matched with the baseline and no increased invalidity, is required before activation. A rejected, failed or budget-exhausted candidate remains inactive. Track all trials, not only winners. The organism chooses whether to submit and activate; the host checks admissibility/evidence, not the organism's self-reported score.
6. **Persistent competition.** Keep agent identity, genome hash, energy, past actions and memory across multiple ticks. Use objective puzzle/TaskPack challenge sequences with changes in conditions and optionally adversarial opponents. Start with only two agents, no spatial movement or agriculture. Matched challenge seeds and public information must be documented.
7. **Dual control groups.** Compare a frozen-prompt organism, a prompt-mutating organism and a strong no-LLM deterministic baseline on identical held-out streams. Distinguish survival/wins from general usefulness and from outspending the opponent. Treat oracle/DP as unpriced diagnostic baselines, not evidence that an LLM is competitive.
8. **Replay.** Save versioned report with every action, soul version/hash, proposed hypothesis, test outcome, resource transfer, provider usage and failure reason. Verify offline from trusted rules and stored decisions. Replay should not make new model calls. Hashes establish consistency, not authorship/authenticity.

### M2.1 suggested work slices

A. **Protocol/contracts** — versioned organism action/result/report schema, mutation state machine and exact budget rules. Prefer extending proven M1.1 parts rather than writing a second unrelated soul engine.  
B. **Deterministic offline vertical slice** — two persistent agents (mutating versus frozen) and fake-provider responses; run, replay and adversarial malformed candidate tests in CI.  
C. **Offline paired evaluation** — uncontaminated holdouts, full evaluation cost charged, candidate activation/rollback.  
D. **Limited real-model pilot** — opt-in only after correct hard metering/gateway preflight; disallow silent retries, report unknown model usage and abort promotion on provider failures.

**M2.1 pass/fail:** A fake-provider test demonstrates proposal → staged → tested → accepted/rejected → active or rolled back, with correct per-organism ownership and no active-prompt contamination; all fees and replay verify. A separate *live* evaluation is needed before claiming positive adaptive benefit. An M2.1 implementation that only lets a human edit `soul.md` is not complete.

## M2.2 — One genuinely evolvable Python module

**Research question:** Can an organism economically invest in code that generalizes and avoids later model consultations?

- Freeze an initial tiny interface, e.g. `decide(observation, memory) -> validated_action`. Keep source and mutable modules private to the organism.
- Mutation: model proposes data-only candidate source → stage → static/interface checks → confined worker smoke trials → held-out paired work trials → organism chooses activation/rejection/rollback. Archive old bytes, parent/candidate hashes, actual errors and charged testing costs.
- Before execution, choose and adversarially verify isolation: no referee secrets, network, host files, rival genomes or provider credentials; bounded CPU, memory, file writes, duration and stdout. **Do not use in-process `exec`, `eval`, ordinary unsandboxed imports, or a shell subprocess as a fake sandbox.** If confinement is unavailable, stage source data but do not execute it.
- Measure cold and later-generation work after *all* code-authoring, compilation/testing and model costs. Compare frozen, prompt-only, code-only, hybrid and strongest cheap-script baselines.

**M2.2 gate:** Demonstrated isolated candidate execution under hostile tests, then reproducible before/after work improvement with trial costs counted. Storing unexecuted module text alone is not success.

## M2.3 — Minimal competition and priced 'weather'

A **weather** event is a typed, referee-implemented modifier (e.g. cognition-energy surcharge, reduced public information, lower reward availability). It is not physical meteorology or a free-form prompt to the model. The purchaser pays; the modifier affects the buyer as well as adversaries where appropriate; duration, cost, applicability, maximum loss and cooldown are enforced. No intervention can alter the real-world model gateway limits or referee invariants.

**Tests:** Same source and seed without intervention; buyer loses energy immediately; effects expire; no unbounded griefing; multiple requests resolve deterministically; adapted organisms respond differently from frozen controls. Only expand interventions if they add a scientifically useful adaptation pressure.

## Later, not blockers to M2.1

- Clone/descendant lineage with inherited prompt, tested modules and selected memory, all versioned.
- More organisms and independent challenges, once two-agent dynamics support reliable inference.
- A read-only **Organism Evolution Viewer** backed by replay reports (prompt hashes, module revisions, consultations, wins/losses, ancestry). No physical map unless location is truly in the referee state.
- Import mini-SWE-agent or other agent framework **only after** a measured native-core-versus-adapter comparison on capability, isolation, overhead and cost.

## Explicit stop conditions

Pause the milestone and report evidence instead of improvising a new ecology if: (a) fake-provider safety/replay fails; (b) model calls cannot be reliably metered or capped; (c) a proposed mutation cannot be isolated from the host; (d) repeated real-model tests show worse net performance than simple no-LLM baselines; (e) holdout leaks into training. Negative results are valid scientific outcomes.

## Implementation brief for a coding agent

Read `AGENTS.md`, `foundation/CONTEXT.md`, ADR-0002, this file, `M11.md`, `M111.md`, `M20.md`, and the relevant source/tests. Propose the smallest **M2.1-A+B** opt-in PR: bounded organism-owned prompt candidate state machine, real energy/accounting hooks, deterministic fake-provider tests and offline verifier. Preserve M0–M2.0 behaviors and their tests. Do not expand stock/soil or execute generated code. Report tested vs untested behavior and request/currency caps. Never claim open-ended evolution from a scripted fake run.
