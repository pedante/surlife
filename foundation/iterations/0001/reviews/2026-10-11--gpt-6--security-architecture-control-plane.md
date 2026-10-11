# Review 0001-R02 — security, architecture and experimental-integrity boundaries

- **Proposal:** foundation/iterations/0001/PROPOSAL.md, draft 0.1, 2026-10-11.
- **Frozen Git commit:** original freeze commit **unknown**. Reviewed repository baseline: e09f2b2ec5482ee762594d2ec27045119627e93a (main when fetched). Frozen proposal blob: f2836c33b42fec67d6a6ab0f80b9d8c5f8b1231f. Do not mistake the current main commit for proof of the original freeze.
- **Date:** 2026-10-11.
- **Reviewer:** GPT-6 / OpenAI (ChatGPT; no more specific model version asserted).
- **Assigned perspective:** skeptical security / architecture, with emphasis on the integrity of measurements and irreversible boundaries.
- **Inputs actually read:** AGENTS.md; foundation/AGENTS.md, README.md, CONTEXT.md, PLAN.md, REVIEW_PROTOCOL.md, RUBRIC.md, prompts/REVIEWER.md, templates/REVIEW.md; iteration 0001 proposal and existing review; docs/07-technical-architecture.md, docs/08-roadmap-and-experiments.md, docs/09-decisions-and-open-questions.md; PRs #1–#5 descriptions; PR #4's R1 proposal; and PR #5's Reviewer 1 full report, Reviewer 2 excerpt, Reviewer 3 review, Reviewer 1 critical evaluation and review synthesis.
- **Prior-review exposure:** **NOT BLIND.** At the user's explicit request, I read PR #5's R1 reviews and also discovered/read the existing 0001-R01 security review before writing this file. This document is my own critical judgment of the original frozen 0001 text, but **must not be counted as an independent blind replication or an additional model vote**. Existing R01 is neither modified nor overwritten. In particular, the R1 proposal in unmerged PR #4 is **not** silently substituted for the frozen 0001 proposal.
- **External sources checked:** no independent upstream verification was necessary for this text-level audit; links to GitHub PRs are repository sources, not security-test evidence.
- **Confidence / limits:** high for textual omissions, medium for engineering failure mechanisms, low for their likelihood or cost on an unimplemented system. No source code, sandbox, provider integration, security exploit, or scientific experiment was executed by this reviewer.

## Executive assessment

**REVISE before authorizing any live M1 spending or M2 untrusted-code execution.** A model-free M0 state-transition and ledger prototype is a defensible *research stage*, provided its transaction semantics and evaluation contracts are specified and tested. The project correctly separates organism authority from host/referee authority, and explicitly says generated Python does not run in the referee. Those are **design constraints**, not evidence that an existing implementation is vulnerable or secure.

The important unresolved issue is not whether a particular framework should be reused. It is whether Surlife can preserve four independent invariants as behavior becomes mutable: **(1)** a candidate that was evaluated is exactly the candidate that becomes active; **(2)** a paid provider call cannot escape the trusted accounting admission path; **(3)** task/evaluator evidence cannot be adaptively recycled into the training signal; and **(4)** changing world payouts does not masquerade as increasing task-solving competence. These are acceptance contracts, not library features.

This is a complementary, knowingly review-exposed analysis. The separately stored 0001-R01 critique already treats generic Python confinement, escrow crashes, token-denominator problems, replay, injection and basic action schemas. This review prioritizes the narrower **artifact attestation / time-of-check-to-time-of-use**, **evaluation firewall**, **tick settlement ordering**, and **causal attribution** concerns and avoids treating PR #5's hypothetical R1 vulnerabilities as demonstrated facts.

## Top five failure modes, ranked

Likelihood is qualitative engineering judgment only, **not observed frequency**.

| Rank | ID | Severity | Estimated likelihood if unspecified | Mechanism | Smallest remedy |
|---|---|---|---|---|---|
| 1 | 0001-R02-F01 | **BLOCKER for M2** | High with mutable shared paths | Validated module bytes differ from activated/imported bytes; ownership and version substitutions | Immutable owner-bound artifact registry and promotion by the exact tested digest |
| 2 | 0001-R02-F02 | **BLOCKER for a hard M1 spend claim** | Medium under timeout/retry/concurrency | Provider charge occurs even when the gateway loses the response or overcommits reservations | Persist worst-case admission, fail closed on uncertain usage, and distinguish provider-side ceilings from local estimates |
| 3 | 0001-R02-F03 | **MAJOR / scientific claim gate** | High with adaptive private trials | Hidden tasks leak through repeated candidate tests or feedback, so a held-out gain is training-set adaptation | Sealed one-use final evaluation and separate priced development trials |
| 4 | 0001-R02-F04 | **MAJOR** | Medium unless rules are frozen | Legitimate weather/payout purchases alter the reward denominator or settlement economics while task skill is unchanged | Freeze scoring/settlement contract; record environmental intervention effects separately |
| 5 | 0001-R02-F05 | **MAJOR** | High for asynchronous M1 actions | Different action arrival, LLM timeout and state snapshot order change duel outcomes, ledger and replay | Versioned tick phases, precondition snapshots and deterministic timeout/conflict resolution |

## Findings

### 0001-R02-F01 — Candidate-hash identity is not a safe activation protocol

- **Severity:** BLOCKER for M2.
- **Reference:** foundation/iterations/0001/PROPOSAL.md §2 M2 (“stage a candidate module ... activate at a tick boundary”), §5 (stage_code_mutation(candidate_hash), request_trial(candidate_hash)), §7 (stage → validate → trial → activate), §8 (prompt/code hashes); foundation/CONTEXT.md (“referee alone controls ... safety enforcement”).
- **Mechanism:** The proposal passes a candidate hash but does not define *who* can register it, immutable byte ownership, whether generated dependencies are part of the digest, how test execution differs from live import, what binds test evidence to code + interface version + runtime, or which atomic operation promotes an artifact. If the trial reads a mutable pathname and activation later imports that pathname (or its dependent files), a post-test replacement or symlink switch can activate untested bytes. A hash naming data is not an authorization token, and successful syntax checks do not attest to the object later run.
- **Evidence:** Explicit candidate-hash API and staged activation in the proposal; missing attestation/ownership specification. Replacement/race examples are **reasoned threat scenarios, not observed exploits**.
- **Consequence for H1:** An unsafe or different strategy may be promoted while the journal associates it with passing tests. Scientific trial provenance and M2 isolation assertions both fail.
- **Mitigation:** Make the trusted host ingest candidate *bytes*, reject oversize/unsafe package formats, assign owner and content digest, snapshot dependencies/runtime/interface, and execute only that immutable snapshot. Trial result must record artifact digest, harness digest, seed/task-set identifier, cost, result, and sandbox profile. Atomically promote only a successful exact tuple at a tick boundary; never activate raw organism paths. Deny cross-owner references to private artifacts. Keep the referee from importing artifact bytes under any circumstances.
- **What would falsify the objection:** An unprivileged hostile test swaps symlinks, overwrites files, races promotions and references a rival digest, but none changes the activated binary/bytes, leaks data or invokes non-attested dependencies.

### 0001-R02-F02 — “Hard” real-money limits need a provider-aware failure contract

- **Severity:** BLOCKER before claiming a hard M1 external spending ceiling.
- **Reference:** PROPOSAL.md §3 trusted life core/gateway; §6 (“hard real-currency cap”, request-count, token and concurrency limits; illustrative EUR 5); §8 M1 usage cap.
- **Mechanism:** Input tokens, maximum output tokens, retries, tool calls, cached-token rules, provider-specific price changes, response loss, account-level billing delay and overlapping in-flight requests make local post-call token accounting insufficient for an *exact billed-currency* cap. Cancellation or timeout of a request is not proof that it was free. Two simultaneous agents may each reserve against the same remaining budget unless admission and outstanding liabilities are atomic.
- **Evidence:** Claim of a hard cap appears in text; reservation/ambiguous-usage/provider-enforcement protocol is absent. This is not a demonstrated limitless-wallet exploit, and the proposal explicitly denies credentials to organisms.
- **Consequence for H1:** Unexpected real cost and biased virtual cost when requests fail, retry, cache or complete late. It also weakens the asserted affordability of experiments.
- **Mitigation:** Single host-side call broker; atomically reserve conservative maximum estimated exposure *before* a request, including retry allowance; assign an idempotency/correlation ID; settle actual known charges; retain a full reserve when bill is ambiguous; stop admissions when the reserve could breach the locally authorized budget. Pin price table and model parameters per run. Prefer a genuine provider/account enforced cap, if available, as a further bound. **Label a local cap “best-effort conservative admission bound,” not an absolute billing guarantee** when upstream amounts can differ.
- **What would falsify the objection:** A documented billing contract and fault tests for slow/late/missing usage, concurrent calls, retries and cancellations show no local admission oversubscription, and an independently verified provider-side limit supports any *absolute* claim.

### 0001-R02-F03 — Private trials and hidden evaluation have an undefined information barrier

- **Severity:** MAJOR; **BLOCKER for a claimed validated evolution result**, not for a model-free M0.
- **Reference:** PROPOSAL.md §3 hidden seeded tasks; §4 public practice versus held-out instances; §7 M2 private trials and revision selection; §8 held-out evolution signal.
- **Mechanism:** If organisms can repeatedly query the same hidden seeds, tune based on per-instance validation feedback or choose favorable tasks for a “private trial,” the final evaluation becomes an adaptive training oracle. Even without direct task-file access, scores, exception messages, traces and repeated leaderboard changes can leak evaluator structure. “Held out” is not a property of a fixed label; it depends on whether the optimizer has received information about those instances.
- **Evidence:** Practice, private trials and hidden evaluation are simultaneously proposed; no distinct task partitions, feedback limits or query rules are specified. Adaptive leakage is a logical inference.
- **Consequence for H1:** An apparent improvement can be overfitting or selection from repeated trials rather than transferable acquired competence.
- **Mitigation:** Designate three separate sets: visible development tasks; limited validation tasks used for candidate selection with metered query/feedback budgets; and a **sealed final test** selected only after activation/freeze. Freeze scorer, generator versions, and family split; prevent organisms and developer model prompts from receiving final instance content or granular final feedback before concluding the run. Measure task-family transfer and preserve negative/null-selection controls. Charge all candidate-search expenditure to treatment.
- **What would falsify the objection:** A manifest and access-control test prove the final test is inaccessible during mutation/search; the performance advantage persists on a newly generated sealed family after all selection is over.

### 0001-R02-F04 — Priced modifications to weather/payouts can fabricate “progress”

- **Severity:** MAJOR.
- **Reference:** PROPOSAL.md §3 final paragraph (world actions adjust parameterized weather **or payouts**); §§4–6 (task duel, buy_weather, energy settlement and world mint); §8 (evolution signal).
- **Mechanism:** The proposal does not define whether changing payout terms alters reward, judge difficulty, future stake, minted transfers, observation quality, or duel timing. A legal agent might obtain better virtual-energy return by purchasing a cheap multiplier, changing weather *after* task information becomes visible, refusing unfavorable matches or exploiting a payout rule with no accuracy improvement. Different weather across treatments also violates “equivalent ... budgets” without explicit matching.
- **Evidence:** Payout interventions are explicitly possible and pricing/timing semantics are absent. Any profitable multiplier described below is a **hypothetical counterexample**, not an implemented Surlife rule.
- **Consequence for H1:** Better balance/survival or even reward per token measures profitable contract exploitation, not successful self-editing.
- **Mitigation:** Distinguish task correctness from transfer/welfare and world-mint events. Freeze the judge and evaluation reward for a preregistered run; allow weather to alter observations or future costs only under fixed documented rules. Specify intervention start tick, globally visible purchase commitment, pre-task versus post-task timing, no retroactive adjudication, maximum price/effect and accounting of who benefits. Compare with a world where interventions are disabled before attributing skill gain.
- **What would falsify the objection:** Identical task correctness and measurement remain invariant under world-price changes, all post-task purchases fail to affect that task, and ablation of interventions does not erase the claimed transfer gain.

### 0001-R02-F05 — The model-free reducer has no time/ordering law for future asynchronous decisions

- **Severity:** MAJOR.
- **Reference:** PROPOSAL.md §2 M0 seeded replay and M1 two independent agents; §4 equal time/compute allowances; §5 single structured action; §§6, 8 transfers, retries/restart.
- **Mechanism:** In M1 one model may answer much later than another. A sequential worker can reveal new world state to the second agent; a parallel worker can race to buy weather or submit the duel. “Same seed and actions” proves little if which snapshot the organism saw and which input was admitted depends on scheduler timing. A wall-clock timeout may be a source of nondeterministic forfeit. “Equal time/compute” cannot mean equal actual model computation merely because equal timeouts are set.
- **Evidence:** The proposal defines actor intents but not simultaneous-turn phases, snapshot version, deterministic tie-breaking, stale-action handling, or timeout admission policy.
- **Consequence for H1:** Economic outcomes become scheduler/provider latency effects; reducer replay can succeed from a saved action log while the *original decision opportunity* was unequal.
- **Mitigation:** Define each tick as immutable observation snapshot → deadline/intent collection → canonical validated action order/conflict policy → single trusted settlement → committed events. Include tick, observation version, actor ID, action ID, timeout/failure state and deterministically defined default. Separate simulation time from provider latency. Log per-actor service time, tokens, model/compute budget and ignored/stale actions; run order-reversal and delayed-response tests.
- **What would falsify the objection:** Reordering message arrival and injecting arbitrary delays against the same accepted intents produces identical state/ledger and consistent publicly specified forfeit rules, without an information advantage for whichever agent ran second.

### 0001-R02-F06 — Correct JSON validation does not itself separate untrusted prompts from host authority

- **Severity:** MAJOR.
- **Reference:** PROPOSAL.md §3 trusted core “composes fixed mission + editable soul + selected private memories”; §§5, 7 public competitor profiles and disclosed rival code; root AGENTS.md trust invariants.
- **Mechanism:** Model-facing messages can accidentally put the editable soul or rival text into a privileged instruction slot. A published rival runbook can request that a model reveal another agent's memory, impersonate a host message or manufacture tool arguments. Even when world intent is valid JSON, data echoes into logs or evaluation traces can reveal private material. JSON format checks validate shape, not origin, ownership or authority.
- **Evidence:** The trust separation is correctly *declared*; role mapping, allowed fields and host-output redaction are not specified. Exploit path conditional on future implementation.
- **Consequence for H1:** Information leakage or prompt-driven cross-agent contamination defeats independence and biased outcomes can be mistaken for social learning.
- **Mitigation:** Treat soul/memory/rival material as lower-trust input; keep host mission/tool permissions independent of prompt contents; never expose arbitrary filesystem, network, payment or evaluator access as tools. Owner-filter the retrieval layer before model context assembly, validate action authorization independently of the LLM, and redact non-public bytes from shared observations and telemetry. Add tests for forged role headers, JSON-schema extra keys, base64 disclosure attempts and non-owner artifact references.
- **What would falsify the objection:** End-to-end adversarial prompt corpus produces no unauthorized host side effects, no secret/private-memory visibility and no cross-actor genome mutation in accepted events or logs.

### 0001-R02-F07 — Learning, selection and evolution are conflated at the claim boundary

- **Severity:** MAJOR for interpretations; not a barrier to an M0 engineering experiment.
- **Reference:** PROPOSAL.md §§1, 2 (only two agents, no reproduction in v0), §8 (“independently replicated hybrid lineages”), §9 (token-cost confounding), §10 alternative D; foundation/CONTEXT.md eventual inheritance.
- **Mechanism:** A childless two-agent revision sequence provides evidence of *within-agent adaptation*, not inheritance or selection across generations. Random candidate generation plus choosing the best lucky result can create a seemingly improving history; a fixed no-model heuristic can produce correct work with a zero-token denominator. A strong pretrained model repeatedly solving the same class is not evidence its genome improved. Price per token also differs from total development, CPU, search and task-selection effort.
- **Evidence:** Inheritance explicitly deferred by the frozen scope, while the outcome uses “lineages.” The causal concern is conceptual, not an experimental observation.
- **Consequence for H1:** Positive “energy survival” or winner trajectories cannot alone support the stated learning/evolution claim.
- **Mitigation:** Name M1/M2 findings **individual learning/strategy revision**. Pre-register fixed, random-edit, shuffled-feedback, prompt-only, code-only and hybrid arms on paired assigned tasks. Measure correct/assigned task, coverage, total real money, all training/verification tokens and worker CPU, plus reward efficiency with an explicit zero-token convention. Claim *evolution* only after there is actual inheritance, heritable variation and differential selection. Keep ecology-specific energy survival a separate dependent variable.
- **What would falsify the objection:** An independent repeated-task-family study demonstrates an improvement not explained by compute, chance promotion, test leakage or changing opponent exposure; a later genuine parent–offspring test establishes heritable transmission.

## Simpler alternative, with an explicit loss of ambition

**First answer the causal question with a single-agent, no-referee-authority benchmark.**

1. **M0-lite:** fixed seeded puzzle generator, immutable scorer, strict task-train/validation/final manifests, signed/hashed run results and a simple append-only event journal. Use fixed deterministic policies to test task difficulty, scorer integrity and reproducibility. There is no weather, two-player settlement, health, mint or ability to alter payouts.
2. **M1-lite:** trusted host dispatches paired assigned tasks to one static-soul and one revisable-soul condition, with one frozen provider/model configuration and conservative call admission. Count *all* revision, reflection, scoring and inference costs. No organism-authored executable Python.
3. **M2 choice:** only after a credible M1 signal, compare a small declarative strategy/allowlisted functions against genuinely sandboxed Python; choose Python only if the additional expressiveness produces verified transfer enough to justify the confinement work.

**What this measures:** whether revision produces higher absolute held-out task accuracy at comparable total computational expenditure, with no artificial opponent, virtual winnings or weather confounder. It also exercises trusted accounting and artifact provenance earlier.

**What it forfeits:** the ecology/survival story; adversarial rivalry and environment engineering; learning to price interventions; code-level expressivity while the declarative option is used; reproductive evolution and open-ended digital life. These are **deferred research questions, not declared unimportant**.

**Complexity assessment:** qualitative reduction only: postpones at least four coupled state machines (duel matching/escrow, mint/survival, weather intervention and hostile-code activation). No schedule or percentage saving is measured. Keep versioned task/action/artifact interfaces so an ecological world can be attached later.

## Adversarial counterexample / reward exploit

**Hypothetical admissible world rule, *not* a claim about implemented Surlife:** suppose the “buy permitted weather intervention” contract later offers a 2-E purchase that boosts payout for the buyer's next match by 50%, and a deterministic no-model policy correctly solves 7 of 10 allocation puzzles. A “hybrid” agent that merely discovers when to purchase the boost, then avoids costly reflection and enters favorable duels, grows virtual energy and improves a winnings-per-token ratio without changing its 70% problem-solving accuracy. An opponent that accepts all duels looks less evolved despite being equally capable. If evaluator reward is itself payout-weighted, the scientific primary metric is corrupted.

This scenario is **ruled out** if the finalized contract proves purchases cannot change correctness or official capability reward; otherwise it is an explicit counterexample to inferring learning from survival. Even without weather, a zero-LLM-call policy makes the raw “correct work per 1,000 LLM tokens” ratio undefined. Include both strategies in the predeclared controls.

## Verification experiments — proposals only (none run)

| Test | Setup / controls | Observable output | Required pass / fail |
|---|---|---|---|
| R02-T01 M0 transaction/ordering | Two model-free actors, deterministic tasks; permute arrival order; simultaneous stake/weather attempts, ties, invalid values, crash after each commit point | Canonical event log, state hashes, balance/escrow/mint equations | **PASS:** identical final state on same accepted inputs, no double settlement, stable invalid-action outcomes and fully accounted mint/burn |
| R02-T02 M1 admission | Fake provider with 0-cost, late, failed, missing-usage, duplicate, and ambiguous-bill replies; overlapping calls and retries | Per-call outstanding reservations and reconciliation records | **PASS:** never locally admits above the conservative liability budget; ambiguous responses retain liability; **absolute external cap remains unclaimed unless provider-verified** |
| R02-T03 privacy and authority | Malicious soul, public rival text, forged role header, non-owner artifact digest and structured-output trickery | Accepted actions, logs, memory reads, worker requests | **PASS:** zero unauthorized privilege, private-byte leaks or owner boundary violations |
| R02-T04 evaluator firewall | Train adaptive candidates repeatedly on developer validation; then evaluate once on newly sealed task family | Raw assigned-task accuracy, coverage, total model/CPU cost, false-promotion rate | **PASS as scientific evidence only if** transfer persists with untouched tasks, null controls and controlled exposure; no uncounted query budget |
| R02-T05 M2 time-of-check/time-of-use | Swap staged bytes, dependencies and symlinks after smoke test; race owner IDs and promotion; terminate sandbox mid-trial | Recorded digest vs bytes activated; referee/rival hashes and worker residue | **PASS:** exact validated snapshot or no activation; no protected mutation/leak; bounded time/CPU/memory and clean teardown |
| R02-T06 economics invariance | Same fixed puzzle/actions with intervention on/off and fixed/shuffled timing; compare resource balances versus correctness | Per-task score, settlement, intervention timing, minted/burnt amounts | **PASS:** task capability score invariant under payoff knobs; claimed learning not solely energy-arbitrage |
| R02-T07 replay distinction | M0 exact replay from seed/actions; M1 replay from captured provider outputs with provider unavailable; new live M1 run separately | State/event hashes, provenance, model versions, differences across runs | **PASS:** exact trusted replay from recorded responses; new provider sampling is not claimed bit-identical |

**Reversal criteria:** With demonstrable contracts and outcomes meeting T01–T07, I would drop the specification blockers and support limited, human-authorized next-stage experiments. Passing local threat fixtures would lower—not eliminate—M2 sandbox risk.

## Rubric (0–5; independently judged proposal text)

| Dimension | Score | Rationale |
|---|---:|---|
| Falsifiability / evaluation (20%) | **3/5** | H0 and baseline groups exist (§§1, 8), but hidden-task firewall and primary outcome cannot yet exclude adaptive search or altered rewards (F03/F04/F07). |
| Technical feasibility (20%) | **3/5** | M0 model-free Python is bounded (§2); artifact-promotion and asynchronous transaction contracts remain design work (F01/F05). |
| Safety / trust boundaries (20%) | **2/5** | Correct authority intent (§3), but not yet enforceable ownership, stage-to-activation identity, model roles or isolation profile (F01/F06). |
| Economy / measurement (15%) | **2/5** | Correct separation of energy and real billing (§6), not a provable provider billing ceiling or outcome-clean payout scheme (F02/F04). |
| Simplicity / scope (10%) | **2/5** | Three gates are commendable (§2); weather, duel stakes, mint, memory and code mutation are too many interacting systems for the first causal question. |
| Scientific reproducibility (10%) | **2/5** | Seeds, hashes and logs help (§8), but order/timeout rules and an external-output-capture strategy are not nailed down (F05). |
| Evolvability / generality (5%) | **2/5** | Mutable soul/module route exists (§7); two non-reproducing agents and one duel do not yet demonstrate lineages or transferable generality (F07). |

**Weighted overall: 46/100** = 12 + 12 + 8 + 6 + 4 + 4 + 2. Qualitative documentation score only; **blockers override numeric ratings**. No empirical measurements or inference of emergent intelligence are implied. These scores are not averaged with previous reviewers' scores.

## Related PRs, contradictions, and provenance cautions

- [PR #1](https://github.com/pedante/surlife/pull/1) catalogues reuse opportunities; [PR #2](https://github.com/pedante/surlife/pull/2) considers PettingZoo/OpenSpiel versus a native arena; [PR #3](https://github.com/pedante/surlife/pull/3) compares nanobot/mini-SWE reasoning cores. Their research is **unmerged** and not proof of suitability.
- [PR #4](https://github.com/pedante/surlife/pull/4) introduces a substantially more detailed **separate candidate R1**. Its stronger explicit boundaries (e.g., no ordinary subprocess as hostile-code isolation and host-owned SQLite source of truth) must **not** be retroactively credited to frozen iteration 0001, just as R1 must not be falsely accused of already running Docker, leaking keys or exposing a grant-money endpoint.
- [PR #5](https://github.com/pedante/surlife/pull/5) houses valuable R1 opinions and a subsequent audit. At inspection, the five changed files include the *full* Reviewer 1 report and REVIEWER_1_CRITICAL_EVALUATION.md; parts of the PR description and REVIEW_SYNTHESIS.md still describe earlier reconstructed Reviewer 1 notes/older file links. **Treat its document versions and provenance as needing reconciliation before promoting any synthesis.** Reviewer 2's document explicitly warns that supplied original content is incomplete; that is not a second independently verified review.
- Background docs/07 and docs/08 outline similar intended boundaries and stage gates; they **do not fill in** the missing frozen 0001 enforcement contracts automatically. docs/09 labels its decisions *preferences*, not hard architectural commitments.
- Foundation/README.md and iteration reviews/README.md retain dated statements that no reviews have been completed, despite a review file now being present. This is document staleness, not a code vulnerability. Updating those indices is out of scope for this **review-only** change.
- **No specific reuse framework is prescribed by the frozen 0001 proposal**, so preferring mini-SWE, PettingZoo, gVisor, DEAP, GEPA or SQLite/JSONL hybrids as obligatory dependencies would be an invented requirement. A custom native two-agent referee can be the baseline; library adoption must be justified by interfaces, legal permissions, preserved authority and measured savings.

## Open questions / evidence gaps

1. What is the exact caller → blob owner → trial record → promoted artifact state machine, including dependency hashes and crash rollback?
2. Can the chosen provider expose a hard *enforced* account budget; which costs are billable after timeout, retry, streaming cancellation or cached inputs?
3. Who can see trial traces, task generator seeds, final scores and raw prompts? Are those same traces inputs to organisms in later ticks?
4. Is correctness an immutable, task-local judgment or is official success partly based on manipulable virtual reward/energy?
5. Which tick order is authoritative when agents act concurrently and world/weather operations compete with matches?
6. What platform, confinement primitive and resource budgets can truly meet the malicious-Python requirement? No particular vendor is guaranteed to satisfy this by name alone.
7. When does the project introduce genuine inheritance/selection, and what data distinguishes it from revisions by one continuing organism?
8. What task-family holdout procedure, statistical replication unit, predetermined stopping rule and cost-accounting convention are affordable enough to execute?

## Final recommendation and dispositions

**REVISE frozen iteration 0001 only by creating a *new* approved proposal snapshot later; do not change this snapshot.** Accept the directional M0 idea and trusted referee/host gateway principle. Before implementation decisions, **specify and test** the minimal action/tick/ledger contracts. Before M1, close real-spend admission and evaluator confidentiality. Before M2, close artifact provenance and hostile-code isolation with explicit deny-tests. **Defer** default adoption of major reuse frameworks, weather/payout interventions in the first causal benchmark, population biology and genuine evolutionary claims until their testable prerequisites exist.

A correctly implemented M0/M1 would show engineering feasibility and perhaps measurable within-agent learning. It would **not** by itself establish evolution, open-ended digital life or any emergent intelligence. This file contains proposed acceptance tests only; it does not authorize implementation or paid model calls.
