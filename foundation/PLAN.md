# Proposal 0001 — Surlife minimal evolutionary arena

> **Implementation-priority clarification, approved 2026-10-12:** This original design already treats mutable prompts and Python modules as the research target. The implementation has meanwhile produced M0–M2.0 prototypes, but the M2.0 number was used for an optional ecology experiment rather than the code-mutation stage envisioned below. Preserve the original review snapshot and protocol histories. **Next proposed implementation is M2.1 autonomous prompt mutation, then M2.2 isolated code mutation; detailed contracts and gates are in [EVOLUTION_FIRST.md](EVOLUTION_FIRST.md) and [ADR-0002](decisions/ADR-0002-evolution-first.md).** Do not interpret stock, soil or harvesting as required world features. This note is a human-direction decision, not evidence of experimentally validated learning.


**Revision:** draft 0.1 — **unreviewed / not approved for implementation**  
**Review unit:** this exact document, frozen as iterations/0001/PROPOSAL.md  
**Date:** 2026-10-11  
**Goal:** produce a *small, falsifiable, low-cost* test that we can critique and then implement.

## 1. Hypothesis and outcome we care about
**H1:** organisms allowed to revise their own soul prompts and later acquire tested reusable Python abilities can achieve more correct work per 1,000 actual LLM tokens than equivalent fixed-strategy and prompt-only organisms, under matched resource budgets.

**H0:** no measurable gain once token costs, task difficulty, environment variation and selection bias are controlled.

We value reproducibility above dramatic-looking agent behavior. A working game with no progress is a valid negative result.

## 2. Scope: three gated milestones
**M0 — world with no LLM.** Python deterministic arena, two reference agents, one objectively scored task duel, virtual energy transfer/maintenance, seeded normal/fog/drought weather, append-only ledger/event stream and exact replay tests.

**M1 — prompt organisms.** Two independent agents sharing a trusted core but having different editable souls, episode memory and LLM access via a metered gateway. Their action is bounded JSON: wait, observe, compete, reflect, propose_soul_revision, or buy permitted weather intervention. An optional cheap deterministic policy may skip the LLM.

**M2 — code mutation.** One small organism-owned Python decision module with a frozen input/output contract. An agent can consult an LLM, stage a candidate module, run limited validation and private trials, compare with baseline, activate at a tick boundary or roll back. Code never runs in the referee process.

Explicitly **out of scope for v0**: mating, assimilation, natural-language free-form world laws, arbitrary external web, direct opponent-code edits, multi-language inheritance, sophisticated illness/age, and population growth beyond two agents.

## 3. Components and authority
- **Referee/world (Python):** advances ticks; provides filtered observations; adjudicates deterministic contests; prices interventions; logs outcomes. Uneditable by organisms.
- **Ledger:** atomic balanced transfers between agents, escrow and world mint/burn accounts; no negative balances. True provider tokens/money are accounted separately.
- **Trusted life core:** composes fixed mission + editable soul + selected private memories + current observation; validates actions; brokers model calls; manages per-organism workspaces.
- **Organism genome:** unique soul.md, event-derived memory, learned runbooks and (M2) mutable strategy.py; versioned per individual.
- **Execution worker:** constrained subprocess or stronger isolated sandbox for generated code, no secrets/host network/other agent files. The worker is never privileged.
- **Evaluation harness:** fixed deterministic reference agents plus hidden seeded tasks; stores actual tokens, scores, agent/genealogy identifiers and code/prompt hashes.

World actions can adjust *parameterized* weather or payouts through an approved rule contract, not edit world source.

## 4. Minimal game proposal: task duel
On a turn, available agents may enter a duel with equal stated stake. Each receives a seeded, objectively checkable micro-task (e.g. choose the best action under a small resource-allocation puzzle) with a strict output schema and identical time/compute allowances. The deterministic scorer transfers escrowed virtual energy to the winner; ties have an explicit refund policy. Tasks have public practice instances and held-out evaluation instances. **Reviewer challenge:** is this too contrived, too LLM-dependent, or too easy to reward-hack? Suggest a better game of comparable complexity if so.

## 5. Proposed actions and observation
A filtered observation contains tick, self energy/health summary, weather, recent public match outcomes, public competitor profiles, visible offers and allowable actions. Private source and memory do not cross the boundary by default.

An agent returns a single structured action, for example:
- wait;
- observe(target_id, requested_public_field);
- compete(game_id, stake);
- reflect(query_budget);
- propose_soul_revision(candidate_hash);
- buy_weather(effect, duration, max_energy_price);
- at M2, stage_code_mutation(candidate_hash) or request_trial(candidate_hash).

All actions incur explicit costs; model calls and invalid actions have consistent accounting. World-owned action definitions cannot be changed by prompt injection.

## 6. Economy and limits
Virtual **energy** is not literal model tokens. Every LLM invocation is metered by actual input/output tokens and converted into energy using a documented pricing rule. The host gateway independently enforces a hard real-currency cap, token ceiling, request-count and concurrency limit; organisms never see credentials. A tiny configured world mint of renewable energy avoids mathematically inevitable exhaustion; its rate is fixed and logged. In-world winnings transfer (not mint) energy. All world-initiated burns/mints are explicit ledger events.

Research run: no external model calls during M0; configure a hard external spending limit before M1 (illustrative ceiling EUR 5). Never assume an internal ledger alone caps billed costs.

## 7. Learning, mutation and self-protection
M1 soul revisions require a stored parent version, candidate, stated hypothesis, estimated cost and activation event. Each organism may learn from own mistakes, public competition results and publicly disclosed rival code. Rival text is data, not trusted instruction.

M2 mutation flow: propose → stage → syntactic/interface checks → isolated smoke/benchmark trials → activate or reject → archive. Candidate tests are charged to its owner. Agent-created tests, backups and rollback procedures can evolve, while minimum host isolation and reference tests are always enforced by the world. A failed organism may lose in-world energy/health, but cannot damage the referee.

## 8. Evidence and success gates
**M0 acceptance:** same seed and actions reproduce identical balances and outcomes; all transactions balanced, replay succeeds, invalid actions cannot bypass rules; no model requests.

**M1 acceptance:** two distinct souls produce independently recorded actions; effective prompt and memory versions persist; model gateway records and caps actual usage; no shared private memory; game result produces one atomic transfer even on retry/restart.

**M2 acceptance:** an agent can stage a candidate, run it only in isolated context, keep/revert based on measured trials; malicious/broken code cannot alter the world or another organism; code/prompt hashes recorded.

**Evolution signal (not guaranteed):** independently replicated hybrid lineages improve held-out reward per 1,000 true LLM tokens and equal virtual-energy budgets versus prompt-only, static and code-only baselines; report variance/uncertainty, failures and total computational cost.

## 9. Known threats and uncertainties
- Is a two-agent game rich enough for meaningful learning, or only gaming of the reward?
- Does the LLM context cost overwhelm all benefits of prompt/code change?
- How should tasks be structured so a deterministic policy can gain measurable reusable skill?
- How will we prevent winner-take-all token accumulation from confounding skill?
- Can resource pricing be fair across models and over time?
- Can a small sandbox meaningfully contain agent-generated code, and what stronger isolation is needed?
- How do we reproduce LLM-dependent transitions when provider responses are nondeterministic?
- How much observation should be available without leaking private genomes?

These must receive explicit reviewer recommendations, not silently assumed answers.

## 10. Alternatives worth comparing
A. Prompt-only organisms first, no code at all.  
B. Minimal custom Python life core, borrowing only reusable ideas from Igor/nanobot/Letta/DGM.  
C. Embed an existing framework directly, accepting extra complexity.  
D. Instead of a duel, benchmark reusable algorithms on independently scored hidden puzzles.

The first decision is NOT 'which framework wins'; it is what minimal, observable mechanism demonstrates that mutation and learning make an economical difference.

## 11. What reviewers must deliver
1. Top 5 failure modes ranked by severity and likelihood, with concrete fixes.
2. At least one simpler alternative and what knowledge it sacrifices.
3. Specific interface and economy inconsistencies.
4. A falsifiable M0/M1 test design with pass/fail criteria.
5. Explicit accept/reject/defer recommendations, costs, and evidence gaps.
6. Separate **design feasibility** from claims about **emergent intelligence**.

This proposal is a candidate for criticism, **not** an instruction to begin implementation.
