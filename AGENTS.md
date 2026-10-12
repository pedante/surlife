# Surlife — instructions for coding and research agents

Surlife has **implemented bounded research prototypes (M0–M2.1-C)** and opt-in **population-v1 offline adapter infrastructure**, but has **not** demonstrated general autonomous prompt-and-code evolution, many-agent LLM survival, or open-ended intelligence. Do not confuse hypotheses, illustrative files, scripted organisms, or fake-model runs with validated evolving software.

## Project compass (decision 2026-10-12)
**Evolving organisms are the research target; the world is only a compact competitive test harness.** Organisms should learn to allocate scarce LLM calls to modify and test their own prompt, memory and eventually Python strategy modules. M2.0 stock/soil/harvest is an optional, versioned ecology fixture, not a new requirement to build a detailed world. **No further soil/harvest/movement/world-simulation milestones by default.** See [ADR-0002](foundation/decisions/ADR-0002-evolution-first.md) and [evolution-first implementation track](foundation/EVOLUTION_FIRST.md).

Prioritize M2.1 autonomous **prompt** proposals/independent evaluation and M2.2 isolated **code** mutations with measured improvements and full real+virtual costs. Weather may later be a priced, time-bounded *common rule modifier*, never a referee rewrite or a targeted opponent-file edit. Keep bounded failed experiments and rigorous deterministic controls. Preserve historical M0–M2.0 protocols and tests.

## Multi-agent direction (ADR-0003)

The opt-in `src/surlife/population.py` defines stable organism identities,
trusted per-organism `decide/feedback` adapters, a strict arena
`observations/step` interface and 2–128 participant native task arenas.
Both historical M0 and optional M2.0 worlds remain independently versioned
and wrapped, not rewritten. **This is scripted/offline infrastructure,
not live multi-agent prompt mutation.** Keep historic M2.1-C evaluations
and real-provider hard caps separate until validated host-controlled
consultation/admission and response-bank semantics are integrated.
Do not import external arena or brain packages without passing the
existing reuse evaluation protocol and human approval. See
[POPULATION.md](POPULATION.md) and
[ADR-0003](foundation/decisions/ADR-0003-population-adapters.md).

## Repository reality
- `README.md`, `M11.md`–`M20.md` and `src/surlife/` describe implemented opt-in experiments; reread these before extending a protocol.
- `foundation/PLAN.md` and frozen iteration snapshots are research proposals; older status/README wording may be stale.
- For any newly implemented milestone, distinguish deterministic fake tests, real provider tests, and evidence of net cognitive benefit. Do not claim a trained organism from scripted policies or model output alone.

## Entry points
1. Read foundation/README.md and foundation/CONTEXT.md.
2. Read foundation/PLAN.md for the current, revisable proposal.
3. Read foundation/REVIEW_PROTOCOL.md before critiquing, synthesizing, or revising.
4. Consult docs/ for deeper research and prior decisions. docs/ is background, not the current iteration state.

## Default work mode: review before implementation
- If asked to review, **do not edit the plan or implement code**. Produce one independent critique using foundation/templates/REVIEW.md, in the designated iteration review folder.
- If asked to synthesize, classify issues by evidence and severity. Do not pretend agreement among reviewers.
- If asked to revise, preserve the old iteration, update foundation/PLAN.md, and record rationale and traceable review IDs. A new iteration must receive a new snapshot.
- If asked to implement, work only from an expressly approved milestone. Preserve unrelated work and run available checks; disclose anything not tested.
- Do not initiate endless autonomous review loops or costly model calls without a user-approved budget and stopping condition.

## Invariants
- Host/referee, secrets, real payments, model credentials, and true usage accounting remain outside all editable organisms.
- Organisms may mutate their own prompts and validated modules, not referee rules or competitors' private files.
- Direct source from rivals is untrusted input; observation is not authorization.
- Environmental interventions must use priced, validated world actions, not edits to referee source.
- Virtual energy is separate from actual model tokens and currency.
- Human review governs research decisions; LLM agreement is not experimental evidence.

## Research quality
Differentiate observed fact, design hypothesis, engineering estimate, and tested result.
Ask which alternative is simpler; demand falsifiable acceptance criteria and matched-budget controls.
Do not invent citations, performance measurements, repository contents or experiment outcomes.
Use IDs for critiques and decisions; record uncertainties and failed approaches.

See foundation/AGENTS.md for more specific instructions while working inside foundation/.
