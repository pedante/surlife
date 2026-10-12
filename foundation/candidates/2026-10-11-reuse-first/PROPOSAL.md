# Candidate proposal R1 — Reuse-first evolutionary Surlife

**Status:** architectural candidate for independent criticism; NOT accepted, NOT an implementation instruction.  
**Date:** 2026-10-11  
**Evidence:** original design documents, frozen iteration 0001, and open PRs [#1](https://github.com/pedante/surlife/pull/1), [#2](https://github.com/pedante/surlife/pull/2), [#3](https://github.com/pedante/surlife/pull/3), including their unmerged research branches. No existing Surlife runtime has been built or benchmarked.  
**Decision discipline:** never edit frozen iteration 0001. Canonical `foundation/PLAN.md` and `foundation/STATUS.json` remain unchanged pending independent reviews, synthesis and explicit maintainer acceptance; see [REVIEW_HANDOFF.md](REVIEW_HANDOFF.md).

## 0. Executive decision

**Recommended architecture:** a **small authoritative Python referee**, a **mini-SWE-agent-based / mini-SWE-compatible organism reasoning adapter** (select code reuse after an offline spike), **organism-owned versioned soul, memory and callable skills**, **a separately metered host-side model gateway**, **one isolated M2 code worker**, and **plug-in task packs**. Use existing software where it already solves a hard problem; do not outsource world authority or inherit general-purpose shell/desktop powers.

Adopt architecture patterns selectively from Descartes (cheap deterministic cognition → expensive reasoning, evidence provenance, shadow promotion), Voyager (reusable skills), DGM/OpenEvolve (mutation archives and comparisons), Letta/nanobot (separated memory and bounded context) and Foundry (independent hidden evaluation). They are **study/adapt candidates, not additional permanent runtime services**. License and benchmark findings constrain direct code copying.

Keep a tiny core, **not a permanently tiny world**: early contracts must support multiple task packs, social observation, weather/niche construction, transferable skills, inheritance, illness/repair, organism-selected cognitive/metabolic policies and later population ecology *without changing the trusted contract or executing organism code in the referee*.

Primary claim to test: *after paying for training, reflection, code generation, verification and failure, do mutable prompt+skill lineages gain transferable held-out competence for less true model computation than static, prompt-only and code-only alternatives?* Competition and reproduction are later environmental pressures, not substitutes for this measurement.

## 1. Scope and the life we eventually want

Preserve the original project ambition (docs/01, 02, 04, 06, 09): distinct persistent organisms with their own editable soul, episodic memory, executable abilities, experience, individuality, survival economy, eventual age/health, social learning, public/private knowledge, energy-funded weather engineering, reproduction, inheritance and possible assimilation. The world is a bounded **research ecology**, not a claim of consciousness.

Three distinct kinds of progress must never be confused:
- **Lifetime learning:** an individual revises a prompt, memory policy or code and improves on *new* tasks.
- **Evolution:** inherited variants are selected differently across generations under controlled conditions.
- **Open-ended adaptation:** new robust and useful capabilities continue to emerge across varied ecological niches. A v0 task-duel cannot by itself demonstrate this.

**Not in M0–M2:** fully biological health, complex mating, arbitrary agent-written world law/code, direct writing to rival private modules, unrestricted external tools, full desktop, general-purpose agent services or unlimited population growth. Record those as explicitly deferred but architecturally possible through tested extension contracts.

## 2. Trust model — choose the smallest reliable split

```text
 RESEARCH HARNESS (controls, frozen unseen tasks, run comparisons)
        |                             |
        v                             v
 HOST-SIDE AUTHORITY: custom Python referee + SQLite ledger
   - versioned seeded state machine / objective scorer / weather
   - clock, escrow, idempotency, death/birth later
   - filtered per-agent observations + action validation
   - durable canonical events / deterministic replay
        |
        +--> HOST-SIDE MODEL GATEWAY (tokens, money, reservations,
        |    model identity, limits and privacy)
        |
        +--> HOST-SIDE GENOME / TRIAL REGISTRY
        |    hashes, versions, provenance, candidate status
        |
        +--> ISOLATED ORGANISM WORKER (one at a time in v0)
                    |
              organism-owned soul, beliefs, skills, strategy
                    |
         deterministic rule/skill OR mini-SWE reasoning
                    |
                typed ACTION INTENT
                    |
               referee validates
        |
        +--> ISOLATED M2 CODE/TRIAL WORKER
             staged code → tests → evidence → activation boundary

 OPTIONAL OUTSIDE THE AUTHORITY CHAIN:
 PettingZoo environment adapter / OpenSpiel games / later worlds
 offline DGM/OpenEvolve experiments / third-party analyses
```

**Referee process never imports or evaluates organism-authored Python, generated test code or opponent-provided modules.** No credentials or trusted ledger handles in an organism worker. Only schema-checked data crosses boundaries. Processes must not be conflated with security isolation: M2 execution requires an actual reviewed OS/VM confinement profile. A generic local subprocess or default mini-SWE local/Docker environment is NOT an adequate isolation claim.

### Own vs adapt vs defer (hard recommendation)

| Component | Recommendation | Why |
|---|---|---|
| Referee state transitions / ledger / weather / observation filtering | **Implement in Python, stdlib + SQLite** | These encode unique world laws and must be audited as one authority; none of PettingZoo/OpenSpiel/Mesa supplies this exact contract. |
| Organism reasoning | **First attempt an adapted mini-SWE-agent kernel**, restricted to one structured intent, plus fake-model baseline | Reuse model/trajectory/step logic if feasible; never forward its normal `command` actions. Do not promise its full runner is a safe drop-in. |
| LLM provider and real billing | **Trusted narrow gateway** with one provider initially | Agent/framework-reported cost or internally set step limits are not independent pre-call billing enforcement. |
| Persistence | **SQLite transactional event/ledger store**, immutable content-addressed blobs for genome snapshots | Lower operational complexity than event broker + external memory server + distributed DB; proven transaction primitive. |
| Memory | Small per-organism episodes/beliefs/skills with retrieved references | Borrow nanobot/Letta retrieval design; do not bring full assistant servers. |
| Reusable task ecology | **Versioned `TaskPack` interface** with an objective scorer; start with one simple pack | Allows existing public benchmark games later without entangling economy. |
| PettingZoo | Optional thin adapter **after** referee parity check | Standard RL ecosystem, not authoritative world. |
| OpenSpiel | Optional isolated task source/baseline at evaluation gate | Objective established games; do not embed C++/Python stack in every world tick. |
| Mutation | Small proposal/archive/test state machine first; compare DGM and OpenEvolve modules at M2 | Real gain comes from lineage and evaluation, not importing optimizer complexity blindly. |
| Isolation | M0 no arbitrary code; M1 model-only intents; M2 disposable locked-down worker/VM | Isolation is more important than framework familiarity. |
| Descartes / Foundry / Third Thoughts / Igor | Extract ideas and tests, NOT a runtime dependency by default | Privilege surfaces, language mismatches and licensing caveats; see [TRADEOFFS.md](TRADEOFFS.md). |

**Adoption principle:** measure `B0 fresh tiny implementation` vs `B1 upstream library` vs `B2 isolated adapter` vs `B3 pattern only` under the *same contracts*. Adopt external code if it reduces the total trusted burden (code + dependencies + upgrade effort) while passing all hard gates. A project's README is not a compatibility test.

## 3. Contracts that keep the ambitious future possible

Write schemas and contract tests before choosing adapter internals. Version names are examples, not implemented code.

```python
class TaskPackV1(Protocol):
    id: str
    version: str
    def generate(self, seed: int, regime: dict) -> dict: ...
    def score(self, instance: dict, submission: dict) -> dict: ...

class WorldV1(Protocol):
    def reset(self, seed: int, config: dict) -> dict: ...
    def observe(self, agent_id: str) -> dict: ...
    def submit_intent(self, intent: dict) -> dict: ...
    def advance_tick(self) -> dict: ...  # deterministic resolution
    def replay(self, recorded_events: list[dict]) -> dict: ...

class OrganismRunnerV1(Protocol):
    def decide(self, observation: dict, context_refs: list[str],
               allowance: dict) -> dict: ...  # ONE intent only

class StrategyV1(Protocol):
    def decide(self, observation: dict, public_memory: dict) -> dict: ...
```

`TaskPack` is **trusted, researcher-installed** software, not something an organism may inject into the referee. It may be an adapter for external games. The referee validates schema/seed/task version and scores the result. Future world expansions can supply more *trusted* rule packs with explicit migrations. Organism-created abilities remain sandboxed and propose **intents**, not arbitrary world functions.

An intent has `schema_version`, `actor_id`, `tick`, `intent_id` (idempotency key), `kind`, `parameters` and an optional `max_energy_debit`. The host authenticates actor identity *from the worker channel*, never from self-asserted JSON. Validation checks phase, budget, ownership, allowed arguments, visibility and cooldown. No shell commands, raw paths, network URLs or arbitrary code are legal world actions.

**Distinguish two action planes** so M0–M2 do not become inconsistent:
1. **World actions:** wait, enter challenge, bounded public observation, priced weather intervention (after test), optional publish/trade/birth later. Applied only by referee.
2. **Cognitive operations:** reflect, retrieve memory, compose prompt, propose new soul, stage candidate, request trial, activate known candidate. Mediated by trusted LifeCore/registry/gateway with explicit prices; they do not count as an instantaneous world move unless the tick policy says so.

`WorldV1` is a logical interface; resolution order is host-owned and explicit:
`environment update → filtered observations → decisions/optional paid cognition → reserve eligible stakes/actions → deterministically resolve concurrent intents → settle atomic ledger → maintenance/terminal checks → commit events and versions`.
Candidate promotion occurs only at a recorded tick boundary. Later reproduction follows an additional defined phase. Weather intervention must have a clear effective tick (prefer **next** tick to avoid same-tick retroactivity). Separate world RNG from task RNG and record seed and PRNG implementation/version. Do not rely on wall-clock ordering for outcomes.

### Genome and optional evolution slots

A genome is **a versioned manifest of compatible pieces**, not one source file:

```text
organism/<id>/
  manifest.json  # immutable logical identity; active versions by hash
  soul.md        # editable strategy/persona, never system authority
  memories/      # private beliefs and summaries with evidence IDs
  skills/        # registered callable skills: signatures, tests, hashes
  policies/      # memory retrieval / LLM escalation / model choice (later)
  candidates/    # proposed, trialled, rejected and retired versions
```

Start with one `StrategyV1`. Reserve versioned capability slots for `MemoryPolicyV1`, `EscalationPolicyV1`, `SkillRegistryV1`, `PhysiologyPolicyV1` (simulated cost selection, never real billing), `InheritancePolicyV1` and `WorldInterventionProposalV1` (declarative numeric modifiers only). **Do not implement these future slots before demonstrated need**; preserve independent genome components, provenance and hashes so future migrations do not rewrite every entity.

Two organisms may share binary code blobs but **never writable state**. Inheritance is an explicit content-addressed fork with new identity, selected memories, ledger-funded allocation and lineage record. Social learning may fetch *only explicitly public versions* through an untrusted-data channel.

## 4. Mini-SWE integration, exactly

PR #3 inspected mini-SWE-agent `DefaultAgent` at commit `04d809ceab9df28f9adaed044884180159172930`. Its basic query/step/trajectory design is useful. Its `LocalEnvironment.execute` launches shell commands on the host, and its Docker backend also executes commands; **neither may receive referee authority or credentials**. Its built-in cost checks are around model calls, not a pre-call guaranteed hard spend ceiling.

**Pilot M1:**
1. Build a fake-model `OrganismRunnerV1` with one decision/JSON-schema outcome, deterministic memory selection and zero shell abilities.
2. Try adapting mini-SWE's model/action/trajectory code to this contract in a *single process that holds no secrets or world authority*. Compare to the fewest-line Python native loop with identical fixtures.
3. Allow bounded `reflect` as a separately metered cognitive operation, not an unbounded mini-SWE autonomous coding session.
4. Choose **adapter if it saves measurable maintenance without greater trust surface**; otherwise retain mini-SWE-compatible interaction/trajectory principles and use actual mini-SWE **only** for M2 code authoring in a sealed worker. If neither safe or cheap, drop the dependency. That is an intentional, falsifiable fallback, not a change of scientific goal.

**Pilot M2:** use the mini-SWE coding loop to author edits to one `StrategyV1` module inside a disposable private staging workspace, run outside-host contract tests, shadow-compare with parent under paid trial caps, store hashes and trial evidence, activate/revert at boundaries. No dynamic import of candidate source into the host process.

### Reasoning economy inspired by Descartes (without copying its code)

`L0`: deterministic safe actions; `L1`: organism-owned evolved skills and heuristics; `L2`: paid mini-SWE/LLM consultation for novelty and repair. Organisms should eventually own their **escalation policy**, not a universally hard-coded shared optimum; world retains absolute bounds and offers a conservative fallback. A new skill has a real *discovery + testing + maintenance* cost, not only runtime benefit. Compare always-LLM, fixed-reflex and evolvable-escalation controls.

Descartes is a **design source only**: as inspected its `package.json` declares `UNLICENSED`. Do not copy code without permission. Foundry's hidden red/green evaluation barrier is a methodology idea; do not accidentally leak held-out test cases through agent-facing diagnostic feedback.

## 5. Minimal meaningful game: useful, repeatable, falsifiable

M0 should not begin with elaborate social life. Pick a **family** of seeded, objectively scored resource-allocation/planning puzzles that can be solved by several strategies (simple greedy, exhaustive optimal on small instances, constrained heuristic) with weather-linked input/reward modifiers. Do not let a trivial one-step puzzle give the false appearance of 'intelligence' or make adaptation impossible.

For first tests:
- Each task version specifies a generated instance, public legality rules, optimal/reference scorer, bounded action schema and deterministic resolution.
- Practice distributions and separate hidden distribution families/seeds are **physically inaccessible** to organism workers.
- Use two reference policies with measurably different strengths across at least two parameter regimes. If greedy and optimal never differ, reject this pack before M1.
- Treat matches and virtual stakes as **ecological consequences**; evaluate held-out raw task correctness separately from earnings/survival.
- Maintain both `score` (task correctness or utility) and `energy` (competitive balance) in different fields. No self-reported 'wins'.

**Alternative scientific route:** benchmark static, prompt-only, code-only and hybrid on an existing game/task pack *outside* the ecology first. If the custom duel has no nontrivial regimes or is easy to game, choose OpenSpiel or another independently scored task; do not force the novel game merely because it matches the story.

## 6. Conservation, money and event replay are permanent invariants

**Three accounts, never conflated:**
1. Simulated energy E: balanced, atomic transfers, escrow, explicit world mint/burn/upkeep, deterministic pricing; no negative accounts permitted (system mint/burn contra accounts must be explicit).
2. True model tokens T: actual prompt/output/cached/reasoning usage as supported by provider reporting; request failures, uncertain usage and retries are logged. The cost of memory retrieval via prompt is real tokens.
3. Actual money M: independent host-side estimated/reserved upper bound and settled cost with provider rates/version, request count and concurrency cap.

A trusted pre-call reservation must cover worst-case permitted output under configured limits and conservative pricing, or reject. When final usage is unavailable, keep a conservative charge and flag uncertainty. Begin with **one outstanding model call at a time**, an approved small spend allowance, and provider/account-side limits where available. A local ledger is not a guarantee about provider billing; fail closed on uncertainty rather than claiming true hard provider-side enforcement where unavailable.

Use **SQLite transactions** for event/ledger atomicity. One transaction records the accepted intent, state transitions, balanced debits/credits, escrow settlement and unique idempotency key. Append-only logical history may be projected to JSONL for inspection; JSONL writes alone are not transaction-safe for restart/crash semantics. Cached balances must be recomputable and reconciled.

**Replay contract:** given a frozen configuration, recorded external outputs/actions and the same PRNG implementation, the reducer recovers identical event/state hashes and balances. Re-calling an external LLM is *not* required or expected to regenerate identical text. Store provider traces separately with restricted access and privacy filtering; in public traces store hashes/usage and explicit visible results.

## 7. Milestones and stop gates

| Milestone | Narrow deliverable | Pass/fail evidence | External calls |
|---|---|---|---|
| **P0 — dependency/contract spike** | Four small interfaces; compare minimal loop to mini-SWE adapter; TaskPack design; threat model and license pins | Static tests, mock sessions, adapter size/dependencies, actionable go/no-go | **None** |
| **M0 — deterministic economy/world** | 2 scripted agents, 1 challenge family, normal/fog/drought seeds, SQLite ledger, replay and private observations | Event hashes equal on replay, balances conserved, duplicate settlements impossible, regimes discriminate strategies | **None** |
| **M1 — persistent soul agents** | 2 independent souls, bounded memory, mini-SWE-compatible decision adapter, gateway, prompt mutation and optional deterministic action | True usage and caps, independent versioned histories, no shell authority, billed/failed calls accounted | Human-approved capped pilot only |
| **M2 — code evolution** | 1 sandboxed `StrategyV1`, proposal→trial→shadow→activate/rollback, lineage hashes | Host and rival isolation, valid candidate survives restart, invalid candidates rejected, amortization reported | Bounded, charged to organism and run |
| **M3 — social/niche ecology** | Published skills, paid inspection, priced next-tick weather intervention, richer TaskPacks | No private leakage, no violation of conservation, social ablations and weather-response controls | Budgeted |
| **M4 — heredity & population** | Cloning, selected memories/skills, parent→child funded fork, several independent niches | Conservation, lineage validation, offspring held-out transfer and diversity under matched starting capital | Budgeted |
| **M5 — advanced biological-inspired policies** | Aging, staged illness, repair, two-parent compatibility, trading/assimilation, broader worlds | Each mechanic changes measurable selection pressures, not just narrative; no new privilege | Separate approval |
| **M6 — open-ended ecology experiments** | Multi-world, multiple model strategies/species, optional evolving declarative environmental effects | Cross-world generalization, novelty and continued adaptation vs fixed-world controls | Separate approval |

**Stops:** M0 must pass before external LLM use; M2 never runs until a truly isolated worker and adversarial test gate pass. Stop after negative results instead of decorating the world to manufacture progress. Reproduction and social mechanics require separate scientific hypotheses.

## 8. Experimental controls; honest measures

Four matched groups: `static`, `prompt-only`, `code-only`, `hybrid`. Later compare `hybrid+social`; for Descartes-style escalation use `always-LLM`, `fixed-escalation`, `evolvable-escalation`. Use frozen model/provider/version when possible, repeated seeds, matched practice and evaluation opportunities, matched actual token and energy budgets and common starting code/soul treatments. Explicitly report sample size, confidence/uncertainty and failure rates.

**Primary endpoints (jointly reported):**
- Held-out **correct utility per episode** at matched capital and real resource allowance, and score distribution across seeds.
- **Total lifecycle cost**: training/reflection + mutation + testing + retries + evaluation input/output tokens, estimated real currency, CPU/wall time and storage.
- **Net energy** and survival under equivalent opportunities, distinct from capability.
- **Skill break-even**: initial discovery/testing token cost / verified tokens saved per later successful use, with usage count and failures; a zero-token policy can be valuable but makes naive 'per 1,000 tokens' undefined, so never rely on that ratio alone.
- **Generalization / lineage**: held-out environments/opponents, skill inheritance transfer, behavior/code diversity, regression and rollback rates.

**Anti-claims:** more generations, longer life, longer context, convincing autobiographies, winning more energy or differing prompts do **not** alone prove self-improvement. Record simulated stories separately from measured results.

## 9. Threats, risks and things this proposal gives up

- Mini-SWE's default shell must be replaced at the action boundary; a Docker backend is not permission to run adversarial code. Host shell + environment vars is a **critical** boundary.
- Weak candidate isolation is a **blocker**, not a trade-off that more scoring points can offset. M2 can use a disposable hardened VM/microVM or reviewed alternative; if unavailable, keep code mutation design-only.
- Objective games can reward brittle memorization; freeze hidden tasks in a different storage/trust domain, verify no answer leakage in logs, and measure transfer.
- World economic thresholds are inherently normative. Keep named regimes and compare against ecology-free benchmark controls; tune only on practice, not held-out scores.
- Tiny core still risks bespoke interface bugs. Use property tests for idempotency, zero-sum settlement, version migration, visibility, seeded replay and crash recovery. Do not claim 'small means safe'.
- A code skill may reduce LLM tokens while increasing CPU, failure rate or maintenance; cost accounting must show these separately.
- Adding all lifecycle features early would conflate reasons for gain. Keeping them out initially sacrifices the social/biological story until its fundamentals work.
- If mini-SWE adaptation becomes heavier than an 80–200-line mockable decision loop, decline runtime dependency; it can still be used later for isolated code authoring.
- SQLite is suitable for a small serialized local referee. Scaling to distributed or high-write multi-world deployments later may require replacing the storage adapter, not changing event semantics.

## 10. What must be decided, not assumed

**Proposed decisions (human acceptance required):**
- C-R1: custom Python world reducer + SQLite transactional ledger is authoritative.
- C-R2: mini-SWE adaptation is the **first runtime reuse spike**, with no default shell; exact package adoption depends on tests.
- C-R3: TaskPackV1 and versioned genome/runner interfaces are the extension seam.
- C-R4: no paid LLM calls before trusted budget gateway + deterministic M0 pass.
- C-R5: M2 is isolated, versioned, shadow-tested with rollback; DGM/OpenEvolve optional.
- C-R6: subsequent ambition (weather/social/inheritance/health/assimilation) is preserved as separately gated phases, not quietly discarded.

**Open:** exact M0 challenge family and scoring protocol; sandbox implementation for the user's actual Linux host; model/provider ceiling reliability; direct upstream license/reuse pins; how expensive an LLM decision should be relative to upkeep; whether an external OpenSpiel task demonstrates transfer better than the bespoke allocation family.

See [TRADEOFFS.md](TRADEOFFS.md) for scored alternatives and [REVIEW_HANDOFF.md](REVIEW_HANDOFF.md) for source map and independent critique questions.

**No architecture here is claimed proven, approved or implemented.** Do not merge this candidate as a substitute for the foundation review process.
