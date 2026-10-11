# R1 review synthesis — convergence, disagreements, and next plan

**Date:** 2026-10-11  
**Status:** Advisory synthesis for PR #5; **not an accepted architectural decision, revised proposal, implementation authorization, or scientific result.**  
**Reviewed design:** [R1 proposal](PROPOSAL.md) and [tradeoffs](TRADEOFFS.md), pinned at `8b4a23d23db30adaa5b3008ad419089cf7697735` in [PR #4](https://github.com/pedante/surlife/pull/4).  
**Collected reviews:** [Reviewer 1 — complete architecture/security review](reviews/2026-10-11--reviewer-1--architecture-security-full.md) · [Reviewer 2 — evolution/economy excerpt](reviews/2026-10-11--reviewer-2--evolution-economy-supplied-excerpt.md) · [Reviewer 3 — reuse/integration](reviews/2026-10-11--reviewer-3--reuse-integration.md).  
**Integration:** [PR #5](https://github.com/pedante/surlife/pull/5), head branch `review/r3-reuse-integration-20261011`, targeting R1's PR #4 branch rather than main.

## Executive conclusion

**REVISE R1; keep its trusted, small Python referee, SQLite transactional economy, strict model-money gateway, organism/referee separation, immutable artifacts, and staged growth.** Replace the *preference* for mini-SWE as the everyday M1 organism brain with an **evidence-first comparison against a native one-intent reference loop**; retain mini-SWE as a likely isolated **M2 coding worker** if its adapter wins. Establish **scientific calibration before paid model experiments**. Reuse libraries as bounded **adapters around one stable versioned data protocol**, not as overlapping permanent services.

**Updated RV1 disposition:** security deny-tests and explicit resource quotas are good additions, but alleged *existing* vulnerabilities have not been established. Replacing the trusted referee with a PettingZoo interface, or moving authoritative SQLite event logs into JSONL, is not justified by this review. **Priority of objections:** (1) scientific identifiability and trustworthy task/economy instrumentation, (2) no-hostile-code/no-unbounded-spend/no-leakage hard gates, (3) native vs upstream reuse economics, (4) long-run evolutionary freedom and interoperability. No synthesis recommendation alone authorizes the next iteration: a maintainer must accept/reject/defer items and commission the actual revision.

### Evidence and review completeness after the new Reviewer 1 report

| Input | What it actually supports | Limits and synthesis weight |
|---|---|---|
| **Reviewer 1 (RV1)** | Newly supplied **full report**, after maintainer-reported repository access. Alleges critical credential/sandbox failures and recommends **PettingZoo + LiteLLM + gVisor + DEAP**, discarding mini-SWE and the custom referee. See RV1 §§1–9. | Full primary text now stored; reviewer claims access, but provides no pinned commit, per-line source ledger, actual configuration or exploit trace. **Several factual premises contradict R1's explicit boundaries**. Completed supplied critique, **not security verification**. |
| **Reviewer 2 (RV2), declared Claude Sonnet 5.5** | Detailed evolution-science critique: selection vs learning, economic phase regimes, statistical promotion, baselines/replication and open-endedness. See **R1-RV2-F01–F10**. | **Edited/condensed incomplete supplied excerpt**, ending mid-F08; detailed F09/F10, appendices and any separately mentioned second review unavailable. No experiments run. **Substantive review, source-limited completeness**. |
| **Reviewer 3 (RV3), GPT-6** | Static code-level reuse assessment, exact upstream integration risks, license questions, proposed adapters and tests. See **R3-B01–B04, R3-F01–F12, R3-T01–T14**. | **Complete independent source-level review**, but static only: no Surlife runtime, full integration tests, actual cost savings, sandbox audit or empirical benchmarks. **Highest coverage for reuse choices; not verified performance**. |

The reviewers address different risks and have different access. Cross-review repetition is **not statistical validation**, a security certification, or proof of independent agreement. **RV1 now supplies a full report, but its allegations of an existing key leak and Docker/HTTP economy vulnerabilities are contradicted by R1's expressly required trust separation.** See [the critical evaluation](REVIEWER_1_CRITICAL_EVALUATION.md). RV2 remains incomplete; RV3 is source-level but static.

## 1. What they have in common

| Theme | Shared conclusion, carefully scoped | Sources | Consequence |
|---|---|---|---|
| **Trusted host vs untrusted organism** | All emphasize that organisms must not control world law, real credentials, rivals' state or evaluation authority. | RV1 §§2.1–2.2/2.7; RV2 verdict/F07; RV3-B01/F05/F08 | Keep one host-held authority and authenticated, typed data exchanges. |
| **True cost boundaries** | All support non-organism-controlled provider limits; RV2 additionally asks whether the ecology's costs select anything meaningful. | RV1 §3.A; RV2-F04/F05/F06; RV3-B02/F06 | Pre-call M reservations, uncertain-usage reconciliation, and separate E / tokens / real money / CPU records. |
| **Staged validation** | All discuss incremental tests, but RV1 prioritizes a four-framework stack plus 100-agent tests while RV2/RV3 prioritize no-cost calibration. | RV1 §8; RV2-F06/F10; RV3-F01/F09 | Begin with scripted two-agent scientific/authority tests, then scale if justified. |
| **Mini-SWE not a proven M1 fit** | All question whether a shell-oriented coding agent is right for a constrained world action. | RV1 §2.3; RV2-F07 (architectural autonomy); RV3-F01 | Benchmark restricted mini-SWE against a native runner, preserving optional isolated M2 coder. |
| **Benchmark and replay validity** | All value tests/traceability, though RV2 distinguishes technical replay from scientific causal validity. | RV1 §§2.7/6; RV2-F02/F03/F05; RV3-F07/T04/T09/T14 | Pair deterministic reducer tests with separate sealed behavioral/selection evaluation. |
| **Future evolution matters** | The system must grow beyond two static prompts without losing protected authority. | RV1 §2.4; RV2-F01/F07/F08; RV3-F04/F12 | Versioned capability/genome envelopes; no commitment to a fixed internal agent architecture. |

**Important non-consensus:** the choice of PettingZoo as the *primary* world, PostgreSQL on day one, Wasm as isolation technology, or GEPA as a committed dependency is **not agreed by all three**.

## 2. Where they differ—and how to resolve the disagreements

| Decision | RV1 | RV2 | RV3 | Synthesis / why |
|---|---|---|---|---|
| **What to optimize first** | Replace agent infrastructure with PettingZoo/LiteLLM/gVisor/DEAP; treat security as initial blocker | A valid scientific instrument, then lifetime learning, then hereditary selection | Minimal stable trusted core + empirical reuse gates | **Put scientific calibration and a minimal secure core in parallel; do not treat architecture elegance as evidence of evolution.** |
| **Routine organism brain** | Reject mini-SWE; isolated native Python loop | Do not freeze cognition's internal orchestration; organisms should eventually choose when to think/remember/act | Native one-intent outer runner first; mini-SWE optional M2 author | **Separate outer world-intent interface from organism-owned internal cognitive policy.** A simple v0 runner is not a permanent cognition ceiling. |
| **World framework** | **Replace** referee with PettingZoo Parallel (disputed: API ≠ economic engine) | Scripted, calibrated ecology; framework is secondary | Native reducer/ledger, optional outward PettingZoo; later Mesa | **Native two-agent world first.** PettingZoo is an interoperability facade, not a settlement authority. Test parity before adoption. |
| **Storage** | SQLite current state; JSONL or DuckDB event streams (atomicity risk) | Instrument survival/economy; does not demand PostgreSQL | SQLite single-writer plus immutable blobs; scale later | **Keep SQLite at M0.** Revisit only after a measured concurrency/replay/size bottleneck; DuckDB only if analytics needs it. |
| **Generated-code isolation** | Mandate runsc/gVisor and network airgap (deployment config still needs review) | Code ownership must allow evolvable cognition within safety limits | Demands independently reviewed confinement, without prescribing a runtime | **Specify a threat model and adversarial acceptance profile first; then select verified technology.** Wasm, gVisor, VM/microVM are candidates, not automatic guarantees. |
| **Provider abstraction** | LiteLLM proxy mandatory (not necessarily a hard billing cap) | Real model usage and economic price mapping should be testable | Official provider SDK first; optional typed abstraction later | **Use one official SDK initially; implement trusted reservation outside it.** Add LiteLLM/Pydantic AI only for demonstrated routing/integration value. |
| **Optimization reuse** | DEAP from outset; reject DGM/OpenEvolve without supporting compatibility tests | Null/positive mutation controls and independent promotion statistics, no specific package required | GEPA offline for prompts, mini-SWE M2, DEAP/OpenEvolve at population scale | **Trial GEPA offline against naive prompt mutation** only after promotion gate and holdout design exist; never make optimizer the authority. |
| **Scientific notion of evolution** | Quick generations from survival; no calibrated causal fitness or heredity controls | Strong objection: M1–M3 demonstrate at most lifetime learning, not heredity/selection | Warns against equating more tokens/energy/longevity with evolved skills | **Adopt RV2's terminology and falsification criteria**. Reserve evolution claims for measurable inheritance + differential selection. |
| **Timing of external benchmark** | Environment/proxy integration then 10-turn LLM proof and 100-agent stress test | Calibrate multiple task ladders and resource regimes | Separate ecology-free OpenSpiel/external benchmark control | **Do both selectively:** external benchmark can falsify learning cheaply; calibrated world is needed to answer ecology questions. |
| **Scoring outcome** | Agent-stack 61, proposed PettingZoo stack 88; **R1 0** based on a disputed claimed exploit | R1 57; staged instrument 76 | R1 80.3; thin-waist 89.0 | **Do not average.** Different criteria, unsupported claims and untested dependencies. |

A false choice to avoid: “use existing code” versus “build everything.” **Buy proven generic machinery, write unique world laws, borrow only permitted patterns, adapt specialized tools through small replaceable boundaries.** Treat total maintained adapter code, dependency upgrades, security/trust surface and reproducible scientific usefulness—not raw lines reused—as the measure.

## 3. What the reviews show is already sound in R1

Retain from [PROPOSAL.md](PROPOSAL.md) §§0, 2, 4–9, with tighter tests rather than rewriting from zero:

- **Host-side deterministic world reducer, transactionally authoritative SQLite E ledger**, idempotent settlement, recorded external outputs for reducer replay, immutable code/genome hashes.
- **Private per-organism souls/memories** and untrusted public observation and skill-sharing boundaries.
- **True host-side provider token/currency gateway**, separately accounted from simulated E and capped human-approved model calls.
- **M0 scripted organisms / M1 controlled cognition / M2 isolated code mutation / M3+ social, ecology, heredity** with explicit stop gates.
- **Objective TaskPack, practice/held-out split, shadow promotion and static/prompt/code/hybrid comparators** as *intentions needing operational definitions*.
- **Descartes-style escalation, evidence and promotion patterns** as conceptual inspirations only: Descartes inspected license is UNLICENSED, so do not copy its code without permission (RV3-B03).

R1 **already** warns against default mini-SWE shell access, Docker-as-sandbox, uncontrolled model spend and all-at-once frameworks. The needed revision is to settle ordering, simplify early choices, make claims/gates precise, and leave cognition evolvable—not to undo the trust model.

## 4. Recommended changes to the plan, in priority order

These are **proposed maintainer decisions**, not edits to R1 or the canonical plan.

| ID | Proposed decision | Why / trace | Decision status |
|---|---|---|---|
| **S-01** | **Keep one small Python/SQLite referee**; task scoring and E settlement are separate; PettingZoo optional output/adapter, Mesa later. | RV1 §§2.4/2.6 (with corrections), RV3-F02/F09 | Recommend accept |
| **S-02** | **Default to native M1 outer decision runner**; test same fake responses against restricted mini-SWE wrapper, count adapter LOC, dependencies, privileged surfaces, restarts and token overhead. Use mini-SWE for sealed M2 code authoring if it wins. | RV1 §2.3, RV3-F01/T06, R1 §§0/4 | Recommend accept with reversal gate |
| **S-03** | **Move zero-model-cost scientific calibration ahead of provider usage**: task headroom, economy viability and mutation-gate false positives. | RV2-F02–F06, RV3-F07/T09/T14 | Highest priority |
| **S-04** | **Define selection, heredity, death and competence separately.** Label pre-reproduction work “lifetime learning”; only later test heritable differential reproduction and open-endedness. | RV2-F01/F08, RV3-F12 | Highest priority for research claims |
| **S-05** | **Make world intent vs cognitive operations distinct.** Stable versioned data envelope; internal think/reflect/remember/skill orchestration can evolve, but each provider/work operation is host-metered. | RV2-F07, RV3-F04/F05 | Recommend accept |
| **S-06** | **Adopt official provider SDK plus host-side pre-call money reservation** with bounded retries/outputs, idempotence, reconciliation of unknown usage and limits across concurrent requests. | RV1 §3.A, RV3-B02/F06 | Blocker before any paid M1 |
| **S-07** | **Define code-worker security acceptance profile before picking Wasm/gVisor/VM.** No secret/host/peer/network access; quota, teardown, malformed protocol tests. | RV1 §§2.1–2.2, RV3-B01/F08 | Blocker before M2 |
| **S-08** | **Physically separate final sealed holdouts**; promoter uses fresh paired seeds with error-rate discipline and null/known-bad/known-good spike-ins; no answer-revealing feedback. | RV2-F02/F03; RV3-B04/T10 | Blocker for scientific promotion claims |
| **S-09** | **Introduce real competing controls:** static, prompt, code, hybrid; plus expert prompt, random edit, shuffled feedback, test-time compute and neutral selection as phase appropriate. Pair tasks and compare real allowances. | RV2-F05/F06, RV3-F07/T14 | Recommend accept, stage arms within cost cap |
| **S-10** | **GEPA offline and OpenSpiel benchmark are first optional reuse spikes**; Inspect AI only if research harness work measurably drops; DEAP/OpenEvolve at actual population scale. | RV3-F03/F07/F09, RV2-F03 | Conditional |
| **S-11** | **Do not commit to PostgreSQL, vector DB, full nanobot/Letta service, full OpenEvolve, Mesa, LiteLLM, shell-capable mini-SWE or host-admin Descartes runtime in v0.** | RV1 §§2.6/2.7, RV3 component catalog/F09 | Defer on measured need |
| **S-12** | **A versioned flexible genome/capability manifest, not hardcoded speculative future Python subclass taxonomy.** Child forks must enforce ownership, new identities, explicit inherited blobs and lineage provenance. | RV2-F01/F07/F09, RV3-F04/F12 | Recommend accept |

### Reuse map—what to adopt, adapt, study, or leave for later

| Role | Initial choice | Later proof-gated option | Own Surlife-specific responsibility |
|---|---|---|---|
| Persistence/tests | Python sqlite3/hashlib, pytest; Hypothesis as useful | PostgreSQL on measured load | Balances, event law, actor authority, replay semantics |
| Model decision | One provider SDK + native mockable runner | Restricted mini-SWE/smolagents/Pydantic AI only if adapter wins | Budget reservation, privacy, caps, world-intent validation |
| Prompt evolution | Simple baseline candidate/trial archive | **GEPA**, offline and holdout-separated | Promotion authority, costed trials, rollback |
| Code evolution | **None executable in M0/M1** | **mini-SWE M2**, only inside reviewed isolated worker | Skill admission, identity, hashes, tests, activation |
| Tasks/science | Scripted scored task ladder + pytest | **OpenSpiel** tasks, later Inspect AI | E conversion, blinded holdouts, controls and attribution |
| Environment | Tiny custom reducer | PettingZoo API facade; Mesa when spatial/event complexity justifies | World state, permissions, escrow, economic physics |
| Populations/selection | Explicit simple deterministic researcher selection experiment | DEAP/OpenEvolve/MAP-Elites when diversity warrants | Fitness/heritability definition, rights, lineage, capital |
| Agent memory/skills | Per-agent bounded files and immutable hashes/SQLite references | SQLite FTS5; borrow nanobot/Letta/Voyager retrieval *patterns* | Visibility, compatibility, autonomy, no shared writes |
| Descartes family | Borrow escalation, shadow promotion, adversarial gate *ideas* | Separate legal review if actual source desired | All privilege boundaries and experimental validation |

**Every optional adoption needs:** exact pinned upstream repo/release and verified license/file rights, reproducible fixtures, measured adapter + transitive maintenance burden, unchanged authority and ledger tests, and a written reversal/removal condition. No unlicensed Descartes code copied. No upstream framework replaces isolation or a financial spending guard.

## 5. Proposed experiment and integration ladder (stop conditions first)

| Gate | Zero/paid scope | Evidence needed before next gate | Stop or reverse if... |
|---|---|---|---|
| **E0 — instrument validation** | Zero LLM: scripted policies, planted competence and neutral variants | Scores distinguish known ability; no “progress” from neutral edits or replay artifacts | Metrics label null drift as improvement |
| **E1 — task headroom** | Zero LLM: >1 difficulty rung, reference/greedy/solver, multiple regimes/families | Nontrivial strategy ordering, zero-shot/expert baselines planned, independent final family locked | Universal no-op or trivial solver dominates |
| **E2 — economy phase diagram** | Zero LLM: sweep starting E, upkeep, reward, regeneration, stake, abstention and forced opportunities | Insolvency/death defined; inactivity not automatically best; competence/energy alignment and chance wealth dispersion characterized | Survival is disconnected from useful tasks; innovation never affordable |
| **E3 — promotion validation** | Zero LLM: null, known-good and known-bad mutation fixtures; paired fresh seeds | Error-rate and effect threshold preregistered; held-out secrecy provable | Repeated selection promotes neutral variations too often |
| **P0 — trusted protocol and replay** | Zero LLM: two scripted agents, native referee/SQLite; failures/crashes injected | Actor ACL, unique intent id/payload, atomic E settlement, exact reducer replay from recorded outputs, private data separation | Double settlement, injected actor, unexplained state drift or private leakage |
| **P0-R — dependency decision** | Zero LLM fake model: native vs restricted mini-SWE; optional external task and PettingZoo parity tests | Same outputs/intents/traces under fixtures; measured integration cost, shell/net absent; API parity plus E correctness | Upstream adds lifecycle/security burden without measurable gain |
| **M1 — paid lifetime-learning pilot** | Only after trusted budget cap + human approval | End-to-end true costs (tokens, money, CPU), sealed confirmation, matched opportunities/allowances, variance measured over **independent worlds**, not raw ticks | Cost cap or holdout isolation fails; too few independent replicates for claim |
| **M1-P — optional prompt optimizer** | Offline GEPA vs naive prompt mutation, only if budget approved | Equal full lifecycle allowances, no holdout contact, useful transfer on untouched conditions | Costs/overfits more than it helps |
| **M2 — code mutation** | Only after independently reviewed worker isolation | Immutable module staging, hostile-code denial tests, shadow compare, rollback, break-even over real use | Candidate can reach host/rivals/provider, or self-edit costs swamp gains |
| **S0 — selection/heredity study** | Scripted first, later bounded populations | Competence-vs-energy-vs-random parent selection, matched endowment, independent held-out descendants | Random wealth reproduces just as well as skill, or no heritable gains |
| **M3+ — social/ecological expansion** | Separately approved | Public/private skill effects, weather/niche interventions, ancestor tournaments, behavioral novelty vs neutral shadow | Only cosmetic diversity or ecological storytelling improves |

Do **not** claim evolutionary effect from M1 pilot (it may only estimate variance and affordability), nor treat ticks inside one world as independent statistical replicates. A trusted staged reducer is necessary but **not sufficient** for scientific validity.

### Critical attack tests to put in the next revision's acceptance suite

1. Retry same action ID with same payload and then conflicting payload; settle **exactly once**, reject conflicting replay (RV3-T02/T03).
2. Spoof rival actor in otherwise well-formed action; deny by **authenticated channel**, not action text (RV3-T01).
3. Crash before/after escrow commit; restart with recorded fake-model outputs, assert canonical event/state hashes (RV3-T04).
4. Attempt paid provider calls from concurrent actors with timeout, missing usage and duplicate retries; reservations never exceed approved M cap (RV1 §3.A, RV3-T07).
5. Try public malicious instruction and private memory fetch; opponent cannot cross visibility boundary (RV1 §2.7, RV3-T05).
6. Verify native/mini-SWE fake adapters produce the same one world intent with no shell/network authority (RV1 §2.3, RV3-T06).
7. Demonstrate reference policies beat idle survival in selected economic regimes and rank reasonably on unseen seeds; include negative cases (RV2-F03/F04, RV3-T09).
8. Inject null mutations and repeated testing; sealed independent promoter does not reward luck beyond the predeclared tolerance (RV2-F02, RV3-T10).
9. In a **disposable reviewed test environment, never the personal host**, try hostile generated code against secrets, files, peers, network and resource quotas; every route denied (RV1 §§2.1–2.2, RV3-T12).
10. Test forged skill hash and child fork; invalid versions never activate, mutable state never aliases parent/sibling (RV3-T11).

## 6. Which conclusions are not yet justified

- **Architecture scores are non-comparable.** RV1's new full report claims **61/88/0** (including R1 zero due to an unproven vulnerability premise); RV2's 57/76 concern scientific validity and RV3's 80.3/89.0 are architecture estimates. None is a benchmark, safety audit or basis for averaging.
- **No framework has been integration-benchmarked in Surlife.** The recommended thin-waist architecture is a robust *prior*, not a proven time-saving or safety superiority.
- **No benchmark shows that adaptive prompts, executable skills or hybrid policies improve real held-out utility.** Pretraining, extra inference at test time, overfitting, random luck and survivor bias remain viable counter-explanations.
- **No evidence establishes actual Darwinian evolution or open-endedness.** R1 itself distinguishes these aims in §1; RV2 insists the experimental machinery must do so operationally.
- **No chosen Wasm, gVisor, Docker or VM configuration has passed isolation review.** Docker or a code-execution tool's existence is not security evidence.
- **No financial API/sdk/proxy is proven to enforce a hard externally billed spend ceiling.** Pre-reservation and reconciliation reduce risk; enforce provider-side limits when available and acknowledge price/usage uncertainty.
- **No source review establishes permission to copy Descartes code.** Conceptual patterns are not a license grant.

## 7. Decision record to ask the maintainer for next

**Proposed acceptance bundle (not auto-approved):**

**A. Preserve:** R1's referee / immutable laws / private genomes / real-money gateway / economy / staged milestones (S-01, S-06, S-07, S-08).  
**B. Revise now:** native M1 reference runner and library comparison (S-02), zero-cost scientific preflight and truthful claims (S-03, S-04, S-09), generic genome/worker wire and internal cognition freedoms (S-05, S-12).  
**C. Explicitly defer:** up-front PettingZoo-as-referee, PostgreSQL, Mesa, full nanobot/Letta, large population engine, live GEPA/OpenEvolve, OS/admin Descartes (S-10, S-11).  
**D. Request source-backed verification of Reviewer 1's allegations** (exact R1 commit/lines, claimed leaked keys, unsafe worker network, ledger mounts or live economy endpoint) rather than requesting the full report, which is now received. Request Reviewer 2's missing appendices if available. No alleged exploit has been demonstrated.

### Recommended next deliverable

Produce an **R2 proposal** (new candidate revision or properly governed immutable iteration **only after maintainer approval**) containing:

1. One-page protected-authority diagram + small serialized organism/world/genome/task contracts, not a zoo of speculative policy classes.
2. A scientific preregistration stub: task ladder, E2 regime sweep, null mutation gate, exact matched arms, independent replication unit and no-claim thresholds.
3. A P0 acceptance matrix for economy/privacy/replay/model-budget/security, linked to reviewer finding IDs.
4. A dependency-spike worksheet for mini-SWE M1 vs native, GEPA and optional OpenSpiel/PettingZoo: actual total-maintenance evidence, pinned versions, rights and removal triggers.
5. A phase diagram of what can be claimed as **lifetime learning**, **selection/heredity evolution**, then **open-ended adaptation**.

**Do not modify the current R1 proposal, canonical PLAN, original review files, statuses or executable code as a side effect of this synthesis.** Human choice precedes plan revision. Record each accepted/deferred reviewer finding in the next change log so later agents can trace the decision.

---

**Synthesis method:** Compared all three supplied reviews to frozen R1; separated actual source requirements, attributed reviewer assertions, runtime tests not performed, and future conditional security threats. Added independent critical evaluation of the new RV1. Scores are reviewer estimates, not measurements. **No Surlife code or paid model experiment executed.**
