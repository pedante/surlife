# Multi-model recursive design review protocol

This is **iterative design criticism**, not an autonomous unbounded self-improvement system. All stages are saved in Git and remain auditable.

## Roles
- **Author:** drafts a bounded proposal with hypothesis, alternatives, interfaces, acceptance tests and risks.
- **Reviewer:** independently criticizes a *frozen* proposal; does not edit it.
- **Synthesizer:** groups reviews, distinguishes facts vs speculative claims, and recommends dispositions.
- **Maintainer:** decides which changes to accept and when to stop iterating. LLM consensus is insufficient.
- **Implementer / evaluator (later):** executes only approved experiments, returns logs and measured results for the next review.

## One round — exact process
0. Confirm baseline: read README/CONTEXT/PLAN/RUBRIC; check git status. Do not rewrite unrelated source.
1. **Freeze** proposal from PLAN.md to iterations/NNNN/PROPOSAL.md in Git; label state 'awaiting reviews'. Record baseline commit SHA, model versions when available, and chosen review perspectives.
2. **Independent reviews.** Prefer two models or separately isolated sessions. Reviewers see the *same frozen proposal* and background context, not each other's reviews. A reviewer chooses a distinct perspective: (a) engineering/sandbox/architecture, (b) economics/scientific validity, optionally (c) simplification/product feasibility. Use prompts/REVIEWER.md and templates/REVIEW.md.
3. Store raw critiques in iterations/NNNN/reviews/YYYY-MM-DD--model--perspective.md, with model/provider/date, context hash or Git commit, evidence links and limitations. Do not modify earlier reviews.
4. **Synthesize** only after independent reviews exist: list objections by ID, root causes, conflicting claims, severity and supporting evidence; propose accept/reject/defer/experiment for each; acknowledge reviewer blindness and invented claims.
5. Human/maintainer **decides**: append accepted decisions to decisions/, preserve original proposal, update PLAN.md and create iterations/NNNN+1/PROPOSAL.md as the next frozen snapshot; trace revisions to review IDs. Declined ideas stay visible.
6. Stop iterating on prose when (a) a clear falsifiable minimal experiment exists, (b) remaining objections can only be answered empirically, (c) improvement is marginal, or (d) cost/time budget is reached. Then request explicit authorization to implement.
7. After implementation, replace hypothetical debate with tests: actual failures and data become inputs to a new review round. Do not let LLMs grade themselves by rewriting the scoring criteria.

## Scoring and evidence
Use [RUBRIC.md](RUBRIC.md). Scores help comparison but cannot overrule a single critical safety flaw. Every review item must be grounded in a proposal passage, a verified external source or clearly labeled reasoning. Request tests for speculative disagreements.

## Revision discipline
- A proposal has immutable snapshots and one working PLAN.md. Iterations are numbered four digits.
- Never delete or overwrite a prior submitted review; if a critique contains errors, add a correction with citation to it.
- Protect the comparison: after seeing reviewer A, reviewer B is **not** independent. Record such exposure explicitly.
- Beware shared failure modes: multiple LLMs may repeat the same mistake. Distinct models, adversarial instructions and independent tests are preferable to more rounds of agreement.
- Do not present hypothetical estimates as measured probabilities or fabricated benchmarks.
- Do not disclose credentials, private organism memories or sensitive host information in review context.
- The repo is private, but treat any model context as shared with that provider under its configured data practices; minimize unnecessary personal data.

## What to send a new LLM
**Minimal portable review package:** CONTEXT.md + frozen PROPOSAL.md + RUBRIC.md + prompts/REVIEWER.md. Supply selected docs/ only when the reviewer needs evidence. Include the repo name and frozen Git commit. For models without repo access, paste or attach these exact files. Do not dump all histories, previous reviews or entire source trees into a first-pass critique.

## Suggested prompts
- 'Review this as a skeptical security/architecture engineer. Do not edit the plan.'
- 'Review this as an experimental scientist and game-economy designer. Do not edit the plan.'
- 'Synthesize critiques, identify contradictions and recommend the smallest next revision. Do not alter the original snapshot.'
- 'Revise the canonical plan based only on approved decisions, preserving testability and scope.'

## Status definitions
DRAFT → FROZEN → REVIEWING → SYNTHESIS_PENDING → DECISION_PENDING → REVISED or READY_FOR_IMPLEMENTATION.
A model cannot honestly mark its own proposal 'validated' from argument alone.

## When automation is added
A future script could create review files and GitHub PRs, but must have max calls, max money, max iterations, explicit human merge gate and zero permission to touch referee secrets or billing. This is not implemented yet.
