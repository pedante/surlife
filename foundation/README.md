# Surlife foundation — living research and iterative design

**Purpose:** turn the Surlife/Igor Life vision into a testable engineering proposal through independent LLM critique and explicit decisions. This folder is **not** the runtime of the arena.

## Start here (human or AI)
1. [CONTEXT.md](CONTEXT.md) — compact brief, vision, constraints, and source-of-truth map.
2. [PLAN.md](PLAN.md) — **the single current proposal** we are iterating on.
3. [REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md) — how to perform independent reviews, synthesis and revisions.
4. [RUBRIC.md](RUBRIC.md) — how to evaluate an iteration against explicit criteria.
5. [STATUS.json](STATUS.json) — machine-readable current iteration and evidence status.
6. [iterations/0001/](iterations/0001/) — **frozen** starting proposal, review location and synthesis state.

For Codex, use root [AGENTS.md](../AGENTS.md) and this directory's [AGENTS.md](AGENTS.md). For other LLMs copy [prompts/REVIEWER.md](prompts/REVIEWER.md).

## What actually evolves in this research process?

| Artifact | Can change? | Meaning |
|---|---|---|
| PLAN.md | **Yes**, after synthesis/decision | Current design hypothesis; initial object of recursive improvement |
| iterations/NNNN/PROPOSAL.md | **No**, once review starts | Frozen candidate supplied identically to each reviewer |
| iterations/NNNN/reviews/*.md | Append new independent reviews | Model-identified weaknesses, alternatives and evidence |
| iterations/NNNN/SYNTHESIS.md | Updated by synthesizer; frozen when accepted | Accepted/rejected/deferred critiques and next experiment |
| decisions/README.md | Append decision records | Explicit human-approved or proposed tradeoffs, never silent drift |
| ideas/*.md | Yes | Brainstorming; not automatically project requirements |
| docs/*.md | Background references | Earlier discussions and research, not the current plan |
| Code and tests (future) | Only against approved milestone | Actual implementations; never equated with design acceptance |

## Existing software reuse research

Before building the arena or agent core, consult [research/README.md](research/README.md) for the curated 29-candidate inventory, machine-readable evaluation queue and falsifiable reuse-versus-build protocol. This research is background, not approval to modify the frozen proposal or import any dependency.

## Recommended iteration loop
1. **Draft:** write a bounded problem, proposal, alternatives, metrics, failure criteria and unanswered questions into PLAN.md.
2. **Freeze:** copy PLAN.md into a new numbered iterations/NNNN/PROPOSAL.md; note exact Git commit in each reviewer submission.
3. **Critique independently:** solicit at least two reviewers with distinct perspectives (e.g. architecture/security vs scientific validity/economy). Do not reveal others' critiques before each reviewer submits.
4. **Synthesize:** create an issue-by-issue decision table including contradictory opinions and evidence quality. Not all criticism deserves acceptance.
5. **Decide:** a human or explicitly appointed maintainer accepts changes and records the reasons. Create the next revised PLAN.md and new frozen iteration.
6. **Stop or build:** when acceptance criteria are met or no further useful changes emerge, implement the smallest experimental slice; critique its measured results instead of endlessly polishing prose.

### Suggested first review
Use the [reviewer prompt](prompts/REVIEWER.md) with foundation/iterations/0001/PROPOSAL.md. Ask one model to stress-test feasibility and security; ask a different model to stress-test evaluation, economics and scientific claims. Both should cite file paths and avoid imaginary test results.

### Status and trust
No reviewers have been run yet. No plan is accepted as scientifically validated. The initial proposal is a starting hypothesis, not a completed spec.

**Do not** claim a model agrees because it failed to comment, count model votes as evidence, or use recursive review to bypass hard resource limits.

## Relation to existing documents
The original [docs/](../docs/) retains the broad brainstorming, alternative agent frameworks, artificial-life concepts and related research. Foundation narrows this into a **traceable, revisable decision process**. Avoid copying whole background documents into every prompt: send the context pack, frozen proposal, rubric and selected relevant references.
