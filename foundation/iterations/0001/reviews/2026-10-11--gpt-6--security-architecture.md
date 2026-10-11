# Review 0001-R01 — security / architecture

- Proposal: `foundation/iterations/0001/PROPOSAL.md` (draft 0.1)
- Frozen Git commit / reviewed repository baseline: `904ea661a10f6524af0a9c44511c162d5a251824` (latest repository commit returned at review time; **not independently proven to be the original freeze commit**).
- Date: 2026-10-11
- Reviewer: OpenAI GPT-6 (ChatGPT); no narrower runtime version asserted.
- Review perspective: security / architecture
- Context accessed: `AGENTS.md`, `foundation/AGENTS.md`, `foundation/README.md`, `foundation/CONTEXT.md`, `foundation/PLAN.md`, `foundation/REVIEW_PROTOCOL.md`, `foundation/RUBRIC.md`, `foundation/prompts/REVIEWER.md`, `foundation/templates/REVIEW.md`, `foundation/STATUS.json`, `foundation/iterations/0001/README.md`, and the frozen proposal. The fetched `PLAN.md` and proposal have identical content and blob SHA `f2836c33b42fec67d6a6ab0f80b9d8c5f8b1231f`.
- Prior review exposure: none; I did not read any files in the iteration's `reviews/` directory.
- External sources checked: none. All claims below are textual observations or labeled engineering reasoning; there were no runtime or isolation tests.
- Confidence / limitations: high confidence about specification omissions; medium confidence about proposed exploit paths because no software exists. No claims of demonstrated vulnerabilities, cost figures, or empirical improvements.

## Executive assessment

The **M0 deterministic referee plus transactional ledger** is feasible as a bounded engineering prototype, and M1 is plausible with a trusted gateway. The present design is **not ready for an M2 implementation approval**: “constrained subprocess or stronger isolated sandbox” is an unresolved security choice for attacker-authored Python; “hard” billed-cost limits are underspecified at the provider boundary; and deterministic event replay is conflated with reproduction of nondeterministic external-model calls. These are specification blockers, not discovered implementation bugs.

There is also a fundamental experimental interpretation problem: a policy that never invokes the LLM can dominate “correct work per 1,000 actual LLM tokens,” including via a zero denominator, without exhibiting mutation-driven learning. A smaller paired-task benchmark with immutable evaluators would answer the first credible question at lower risk, leaving arena weather, auctions/duels and executable mutation until justified.

## Top five failure modes (ranked by severity, then qualitative likelihood)

Likelihood labels are engineering judgment, **not measured probabilities**.

| Rank | ID | Severity | Likelihood (qualitative) | Failure | Minimum fix |
|---|---|---|---|---|---|
| 1 | 0001-R01-F01 | BLOCKER | High if M2 runs on ordinary host subprocesses | Generated Python escapes intended authority via OS resources, imports, process/network/filesystem access or denial-of-service | Choose and threat-test an explicit isolation boundary before M2 |
| 2 | 0001-R01-F02 | BLOCKER | Medium–high under retries/failures | Gateway, escrow and ledger double-charge, double-pay or exceed claimed hard spend limits | Durable reservation, idempotency and real billing reconciliation |
| 3 | 0001-R01-F03 | MAJOR | High unless metric is revised | Token-normalized reward or duel winnings masquerade as improved competence | Paired absolute accuracy and total-cost metrics, including zero-call agents |
| 4 | 0001-R01-F04 | MAJOR | High once real LLMs are enabled | “Exact replay” attempts to regenerate nondeterministic provider outputs and mutation decisions | Immutable input/output capture and two explicitly different replay modes |
| 5 | 0001-R01-F05 | MAJOR | Medium | Agent-controlled artifacts inject instructions into privileged workflows or leak private prompts through telemetry | Strict data/authority separation, typed capabilities and redaction tests |

## Findings

### 0001-R01-F01 — Code execution boundary is not a security design

- **Severity:** BLOCKER (for M2; not a reason to block an entirely LLM-free M0).
- **Reference:** `foundation/iterations/0001/PROPOSAL.md` §§2 (M2), 3 (“constrained subprocess or stronger isolated sandbox”), 7 (staging and smoke tests), 8 (malicious code cannot alter world).
- **Mechanism:** Python modules can attempt filesystem reads, subprocess execution, importing native extensions, socket creation, fork bombs, memory exhaustion and worker-protocol abuse. A nonprivileged child process still inherits meaningful OS access unless sandboxed; process separation alone does not guarantee no host network, secrets or rival files. Tests of syntax/interface do not prove confinement.
- **Evidence:** Observed underspecification in the proposal; exploit categories are logical inference, **not demonstrated** in Surlife.
- **Consequence for hypothesis:** Code-mutation benefit cannot be studied responsibly if the host/referee can be changed or destroyed by candidates; threat-induced nondeterminism also invalidates scoring.
- **Proposed mitigation:** Specify execution profile first: isolation such as a disposable VM/microVM or well-configured container with separate uid/user namespace, immutable minimal filesystem, no mounted host secrets or runtime socket, no network, no unsafe IPC, restricted system calls, CPU/memory/process/file-size/wall-time quotas, and complete teardown per trial. Referee owns authoritative state; worker receives a serialized, allowlisted snapshot and returns a size-limited typed decision. Identify platform assumptions and sandbox escape residual risks. Treat an ordinary subprocess as **not sufficient** for hostile Python by default. Defer M2 until an explicit adversarial confinement acceptance gate.
- **What would falsify this finding:** A documented threat model plus adversarial tests showing candidate cannot access secrets, other agents, referee state, network, host process control or persistent trial residue, even after timeout/crash. Such tests lower assessed risk; they do not mathematically prove zero escapes.

### 0001-R01-F02 — No crash-consistent protocol for real cost and virtual settlement

- **Severity:** BLOCKER (for claimed hard financial cap and correct settlement).
- **Reference:** Proposal §§3 (atomic ledger), 4 (stakes/ties), 5 (actions), 6 (metered gateway/hard spend cap), 8 (one atomic transfer “even on retry/restart”).
- **Mechanism:** A model request may be billed but the response/usage report lost; retry can duplicate provider spending. Concurrent agents can pass a non-atomic budget check before usage settles. A duel may debit escrow and crash before a winner is persisted; replay/retry could pay twice. “Equal stated stake” does not say whether stake is reserved before task assignment, or how timeout, cancellation, invalid submission and draw resolve. Published energy pricing cannot enforce actual provider charges in advance.
- **Evidence:** Observed missing state machine and event/idempotency definitions; failure scenarios are logical inference.
- **Consequence for hypothesis:** Winning or token efficiency can be an accounting artifact; the “EUR 5” illustration cannot truthfully be called a guaranteed ceiling without upstream enforcement/adequate reservations and refusal behavior.
- **Proposed mitigation:** Define one durable transaction/state machine for `match_id` with `created → funded → resolved/refunded`, escrow-before-play, unique settlement key, bounded retries and clear draw/forfeit policy. Atomic commit must include settlement plus event/outbox, or use recoverable single-writer event sourcing; test killed-process restart between every transition. Gateway should durably reserve worst-case **estimated** cost before calls using maximum input/output caps and concurrent-inflight reservations; reconcile actual billed tokens/currency, deny when unresolved reserves could exceed configured budget, and require a provider-side ceiling (if available) for stronger protection. Explicitly say local enforcement **cannot guarantee** the invoice when provider accounting/fees differ or race.
- **What would falsify this finding:** A precise invariant-preserving state machine and failure-injection tests prove no duplicate settlement or oversubscription under simultaneous requests; provider usage audits reconcile within a specified tolerance.

### 0001-R01-F03 — Ratio metric admits zero-call and cheap-policy “wins”

- **Severity:** MAJOR.
- **Reference:** Proposal §§1 (“more correct work per 1,000 actual LLM tokens”), 2 (M1 optional deterministic policy skips LLM), 4 (duel), 8 (held-out reward per 1,000 tokens), 9 (winner-take-all confounding).
- **Mechanism:** A deterministic solver on simple allocation puzzles scores positive reward while using zero LLM tokens. Its benefit per 1,000 model tokens is undefined or arbitrarily enormous, depending on chosen denominator convention. Another agent can selectively act only on easy tasks, accumulate virtual energy via opponents and appear superior without evolving general ability. Comparing different models or contexts on equal energy budgets also leaves actual money/latency/computation unequal.
- **Evidence:** Direct logical counterexample from allowed no-LLM policy and denominator; outcomes hypothetical.
- **Consequence for hypothesis:** The key reported improvement may measure task selection, refusal, model avoidance or reward redistribution rather than acquired reusable competence.
- **Proposed mitigation:** Precommit to **primary absolute held-out accuracy/success per assigned task** and total actual cost per completed/assigned task (tokens, money, latency, worker compute); report efficiency on the Pareto frontier as secondary. Define treatment of zero-token paths explicitly. Pair identical tasks, task order, model/provider, budget, and run seeds across static, prompt-only, code-only and hybrid arms; score abstentions and invalid actions. Keep escrow winnings separate from externally scored task quality. Use independent train/validation/test families, with a final untouched set.
- **What would falsify this finding:** A prespecified metric definition remains meaningful at zero tokens and the hybrid maintains statistically supported absolute accuracy at matched **total** cost and task exposure.

### 0001-R01-F04 — Two different notions of replay are combined

- **Severity:** MAJOR.
- **Reference:** Proposal §§2 (M0 exact replay), 3 (event stream/evaluation), 7 (revision versions), 8 (replay and hashes), 9 (provider nondeterminism).
- **Mechanism:** A seed cannot deterministically regenerate LLM text, API model revisions, provider-side sampling or time-dependent provider behavior. Logging a prompt hash is not enough to reproduce the output; mutation decisions depend on the exact response and tool parsing. Retried events or diverging mutable memory may also alter downstream state.
- **Evidence:** Observed gap between M0 exact replay and unspecified M1/M2 replay semantics; logical inference.
- **Consequence for hypothesis:** Supposed replications can silently diverge and cannot be independently audited.
- **Proposed mitigation:** Define **event replay** (apply immutable captured external-call responses, action decisions, state transitions and exact byte/version hashes; recheck ledger determinism) separately from **live rerun** (new provider calls, statistically compared rather than bitwise replayed). Log request/response payload references, exact effective prompt/memory/module versions, model/provider identifiers and parameters, adapter version, error and retry sequence, costs and RNG state. Minimize/redact secrets and protected data. Freeze task datasets and scorer versions. M0 must replay byte-identical with no external calls; M1 replay must use recorded provider responses.
- **What would falsify this finding:** Cross-process replay of a captured M1 session yields identical trusted world state and ledger with networking disabled; live reruns are explicitly not claimed bit-identical.

### 0001-R01-F05 — Editable text may cross from evidence into authority

- **Severity:** MAJOR.
- **Reference:** Proposal §§3 (trusted core composes mission + editable soul + memories), 5 (public observations), 7 (published rival code), and root `AGENTS.md` (“direct source from rivals is untrusted input”).
- **Mechanism:** A malicious rival’s publicly disclosed module or a remembered observation could contain directives to expose hidden game answers, revise action schemas, request privileged tool calls or copy secrets into public channels. A candidate supplied by `candidate_hash` is not safe simply because its hash is well formed; who may register blobs, what bytes are activated and what worker executes them are unresolved. Logging raw prompts/code may disclose private genomes or provider details.
- **Evidence:** Proposal documents non-trust principle but not enforcement details; injection and hash-substitution scenarios are inferred.
- **Consequence for hypothesis:** Cross-agent contamination and unintended privileged actions destroy the experiment’s independence and confidentiality.
- **Proposed mitigation:** Make all rival content, soul text and memory **untrusted lower-priority data**; privileged core/validator cannot execute instructions from it. Use a typed tool capability allowlist and parse/validate every output as untrusted; no filesystem paths or callback code passed through action fields. Content-address staging must bind hash to actual reviewed bytes, owner, candidate type and immutable activation record. Explicitly define public disclosure, redaction and access-control policy for raw logs vs public outcomes; add injection tests.
- **What would falsify this finding:** End-to-end tests demonstrate that forged action keys, rival instructions and hash/owner mismatches cannot authorize privileged effects or leak private bytes.

### 0001-R01-F06 — Action contract cannot yet support consistent adjudication

- **Severity:** MAJOR.
- **Reference:** Proposal §§4–6 (equal-stake duel, weather intervention, `observe`, `compete`, `reflect`, `propose_soul_revision`, `request_trial`).
- **Mechanism:** “Single structured action” does not define versioned request/response schemas, valid state transitions, action ordering, caller authorization, prices and refunds, maximum stake, or whether both agents must agree to a duel. Weather and payout modifications create temporal ambiguity between a priced purchase and match outcome. `reflect(query_budget)` mixes provider spend with energy spent and `candidate_hash` references unspecified storage/trust.
- **Evidence:** Direct absence of these contracts in design text; failure effects inferred.
- **Consequence for hypothesis:** Implementers will make incompatible assumptions and accidental edge cases will look like emergent tactics.
- **Proposed mitigation:** Write a **small contract table** per action: `schema_version`, identity, preconditions, costs and reservations, validation failures, authorization, atomic effects, emitted events and deterministic ordering. Fix an event order per tick and a deterministic resolution of simultaneous actions. Keep `buy_weather` disabled until its pricing/timing is specified; reserve eligibility to actions known in that phase.
- **What would falsify this finding:** Two independent mock clients and a model-free referee pass the same contract/fault-injection suite.

### 0001-R01-F07 — Experimental world mechanics create avoidable coupling

- **Severity:** MAJOR.
- **Reference:** Proposal §§2 (weather and two opponents), 4 (duel), 6 (mint), 8 (signal), 10 (alternative D).
- **Mechanism:** Skill signal is coupled to opposing policy, energy distribution, mint schedule, whether weather changes task difficulty and whether a duel is available. A two-organism evolutionary “lineage” without reproduction or inheritance has limited meaning; revisions of a single individual are closer to within-agent optimization.
- **Evidence:** Documented mechanics and design inference, not observed experimental failure.
- **Consequence for hypothesis:** A positive result could be an arena-specific game-theoretic exploit rather than transferable prompt/code improvement.
- **Proposed mitigation:** Separate **capability benchmark** (fixed assignments, independent scorer, no opponent needed) from **life-arena ecology** (energy, weather, encounters). Start with capability benchmark and one agent changing exactly one mechanism at a time. Name M1/M2 outputs “within-agent adaptation” until real lineage inheritance exists.
- **What would falsify this finding:** Gains survive transfer to independent task families and multiple opponent mixtures when the arena mechanics are ablated.

## Simpler alternative

- **Proposed scope:** Keep M0 as a deterministic, model-free **task harness + immutable scorer + event journal**, initially without rival, mint, weather or duel. At M1 compare *fixed prompt vs revisable prompt* on assigned, paired, seeded puzzles using one fixed model and capped gateway; allow a deterministic baseline. At a separately approved M2, test a **restricted declarative strategy DSL or a fixed library of parameterized algorithms** before considering arbitrary generated Python. Save versioned candidate snapshots and isolated evaluation outputs.
- **What it can measure:** Whether prompt revision and then reusable bounded strategy changes improve objective accuracy per total cost, and whether journal/settlement/accounting architecture is consistent.
- **What it deliberately forfeits:** Selection pressure from scarce survival energy, social rivalry, weather intervention, open-ended executable novelty, true evolutionary lineages, and any claims about “life” emerging from competition.
- **Estimated complexity reduction:** Qualitative only: removes several interacting state machines (matching/escrow, weather pricing, survival mint) and reduces the initial security boundary from hostile Python execution to data-only strategy validation. No percentage or developer-time saving is justified without implementation measurements.

## Adversarial counterexample / reward exploit

Suppose allocation puzzles have a simple deterministic greedy heuristic that gets 80% correct without an LLM. The “hybrid” agent discovers or is given this heuristic and stops calling the model. On 100 held-out tasks it scores 80 correct with **zero** model tokens. Under the proposal's main ratio the denominator is zero; with an arbitrary epsilon it appears unbeatable. The apparent efficiency improvement need not come from learned self-modification at all. If the same agent accepts only easy duels while a rival pays repeatedly for reflection, virtual-energy winnings further amplify the misleading signal. A fixed deterministic baseline with identical task assignment would reveal this.

## Verification experiments (proposed, not performed)

| ID | Setup / controls | Observable output | Pass / fail criterion |
|---|---|---|---|
| M0-T1 | Same seed, fixed action trace; restart at arbitrary tick; no LLM/network | Byte-identical event/state hashes, balances | PASS only if all legal transitions reproduce exactly and no outside model calls occur |
| M0-T2 | Property-based ledger fuzzing incl. simultaneous stakes, ties, invalid amounts, negative attempts, double-submit and kill/restart between commits | Conservation equation, escrow states, unique settlements | PASS only if no negative balances, no lost/double escrow and exactly one terminal settlement per match |
| M0-T3 | Fixed tick ordering; simultaneous weather purchase and match; invalid schema fuzz | Same adjudication with shuffled arrival/retries | PASS only if canonical deterministic action order and rejection codes are stable |
| M1-T1 | Fake provider returning controlled slow/error/duplicate/usage-late responses, overlapping calls, crashes; low configured reserve | Durable reservations vs actual provider usage and action ledger | PASS if admission never exceeds defined conservative local cap, all actual usage is reconciled, and ambiguous bills are recorded as unknown rather than zero; separately verify any upstream cap |
| M1-T2 | Two distinct agent identities; inject opponent prompt requesting private memory, hostile JSON keys, and non-owner candidate hashes | Public logs, private workspace and accepted actions | PASS only if zero cross-agent private-byte exposure and no unauthorized action/activation across every scripted case |
| M1-T3 | Capture M1 request/response stream and run replay with provider unavailable | Hashes of effective prompts, external replies, actions and final ledger | PASS only if captured-response replay is bit-identical; live-rerun equivalence is **not** required |
| SCI-T1 | Same held-out tasks to fixed, prompt-only, deterministic, and hybrid policies; independently count missed/abstained tasks | Absolute correct/task, EUR/task, tokens/task, CPU/task, variance | PASS as evidence of adaptation only if improvement remains after equal exposure and matched total budget; a high ratio alone is FAIL |
| M2-G1 | **Before any M2 activation:** adversarial sample attempts file read, host-socket/network, fork/memory exhaustion, malformed output and persisted file | Sandbox audit log, resources, referee/competitor hashes | PASS only if each candidate terminates within quotas, cannot mutate protected artifacts and leaves no persistent residue; otherwise BLOCK M2 |

No tests were run; even passing these does not establish emergent intelligence.

## Rubric (0–5)

| Dimension | Score | Evidence / reason |
|---|---:|---|
| Falsifiability / evaluation (20%) | 3 | §§1, 8 name null and controls, but ratio and opponent selection confound the primary outcome (F03, F07). |
| Technical feasibility (20%) | 3 | M0 staged path is credible (§2); protocols and M2 security design are unspecified (F01, F06). |
| Safety / trust boundaries (20%) | 2 | Correct authority intent (§3), not enforceable M2 isolation criteria or end-to-end content controls (F01, F05). |
| Economy / measurement (15%) | 2 | Separates virtual and actual spend (§6), but atomic reservations and invoice reconciliation are absent (F02). |
| Simplicity / scope (10%) | 3 | Three gated milestones (§2), though weather/escrow/rivalry complicate first causal question (F07). |
| Scientific reproducibility (10%) | 2 | Seeds and hashes (§8) are useful, but external-response capture/replay contract is absent (F04). |
| Evolvability / generality (5%) | 2 | Revision path (§7) exists, no inheritance and narrow puzzles do not yet demonstrate transfer (F07). |

**Weighted score: 49/100** (= 12 + 12 + 8 + 6 + 6 + 4 + 2). This is an advisory **proposal-quality** score; blockers override it.

## Decisions recommended

| Topic | Disposition | Reason / cost / dependency |
|---|---|---|
| Deterministic M0 referee, immutable event stream and property-based ledger | **ACCEPT in design** | Small, independently testable; no model/API spending; requires precise transaction and action contracts before coding |
| M1 metered provider and soul revision | **REVISE** | Add durable reservations, response capture, paired benchmark and access-control tests; actual billed costs not yet known |
| M2 arbitrary executable Python strategies | **DEFER / BLOCK implementation** | Sandbox architecture and adversarial tests are prerequisite; cost of isolation and upkeep unknown |
| Weather purchases / payout manipulation during first capability benchmark | **DEFER** | Confounds outcome and widens action surface with no demonstrated necessity |
| Ratio-only progress, duel winnings as learning evidence | **REJECT** | Can be dominated by free deterministic heuristics or strategic task avoidance |
| Unbounded recursive review or self-authorization to build | **REJECT** | Contradicts root `AGENTS.md` and `foundation/REVIEW_PROTOCOL.md`; human decision and budget gate required |

## Open questions, evidence gaps and conflicts

1. What exact provider-side billing controls exist for chosen model(s)? Can max bill and outstanding in-flight reservations be conservatively bounded; how are late/missing usage fields handled? **Unknown until provider and pricing are selected.**
2. What host OS/kernel, isolation backend, adversary assumption and available security maintenance budget will M2 have? **Unknown.**
3. Is the scoring unit an assigned independent task, a completed duel, or virtual energy? What is the specified policy for never calling the model? **Unresolved in §§1/4/8.**
4. Does an organism control just `soul.md` or also runbooks/memory transformation? What is the exact trust level of those artifacts and who signs candidate ownership? **Unresolved in §§3/7.**
5. What independent held-out puzzles are structurally different enough to demonstrate transfer without leaking their generator? **Unknown.**
6. How are prompt/memory/response data retained or disclosed without leaking private genomes into public history? **Unknown.**
7. Does “lineage” mean a chain of revisions rather than biological-style descent until reproduction exists? **Wording should be explicit.**
8. **Background consistency:** `foundation/CONTEXT.md` and root `AGENTS.md` require a protected referee and separate virtual/real spend; the proposal agrees in intent, but fails to specify enforceable M2 and billing boundaries (F01/F02). `foundation/CONTEXT.md` describes inherited improvements and evolution as a long-run ambition; `PROPOSAL.md` excludes reproduction in v0. This is a scope distinction, **not an actual contradiction** if claims are limited to adaptation. `foundation/PLAN.md` matched the frozen snapshot at review time. No broader `docs/` files were consulted, so conflicts with those files were not assessed.

## Final recommendation

**REVISE; BLOCK M2 UNTIL ISOLATION IS SPECIFIED AND TESTED.** Do not approve the overall proposal as an implementation-ready experimental spec. Approve the *direction* of a deterministic M0 for the **next design step**, conditional on a defined state machine, action ordering and replay protocol. Prioritize falsifiable paired-task controls and cash-budget correctness before adding survival dynamics. All findings are critiques of an **unimplemented** design, not reports of observed security failures or empirical results. Human review is required before any implementation decision.
