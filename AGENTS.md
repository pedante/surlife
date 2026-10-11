# Surlife — instructions for coding and research agents

Surlife is an **unimplemented artificial-life research proposal**. Do not confuse design documents or examples with validated software.

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
