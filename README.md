# Igor Life / Primordial Arena

*Artificial life fights for survival.*
## First runnable prototype (M0)

**A small offline, deterministic arena is now implemented in this branch.** It has two scripted organisms, a scored puzzle duel, virtual-energy transfers, a transactional SQLite journal, replay and automated tests. **It does not yet implement LLM organisms, evolving prompts, generated code or reproduction.**

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for exact commands, tested scope, reuse decisions and next stages; [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md) records the user-authorized experimental scope.

## Bounded LLM organisms (M1)

**Experimental implementation:** M1 introduces separate versioned souls, bounded memory and one JSON action per hosted model consultation. It supports the OpenRouter free tier with no extra runtime SDK or a deterministic fake provider for offline tests. See [M1.md](M1.md) for Fish shell API-key setup, CLI examples, provider restrictions and scientific limitations. The M1 default is pinned to a catalog-listed free Dots3-Note Preview model and validates current free pricing and structured JSON support before any real inference. The optional random `openrouter/free` route is discouraged for controlled comparisons.

## Feedback-aware, evaluated souls (M1.1)

**New opt-in experiment:** `surlife --m11` separates action from post-outcome
reflection, records valid/invalid moves and normalized score quality, and queues
reusable strategy hypotheses without immediately changing active prompts.
Use `surlife --evaluate-soul out/souls/RUN/a.json` to compare original vs
candidate prompts on matched held-out tasks before accepting any revision.
`--cognition selective|always|never` controls a **host-owned**, resource-gated
cognition schedule, not yet an evolved metacognitive ability.
See [M11.md](M11.md) for runnable commands, external request budgets and caveats.

## Conservative evolution evaluations (M1.2)

**Opt-in:** `surlife --m12` preserves the existing arena but logs a shadow
Greedy score beside actual LLM actions, retains complete bounded puzzle
fingerprints for holdout exclusion, and adds an explicit multi-cohort,
strictly capped soul evaluation mode: `surlife --m12 --evaluate-soul ...`.
A candidate is never accepted if any cohort regresses or its invalid
actions increase. Provider failures abort without discarding the pending
proposal. See [M12.md](M12.md) for the command sequence and scientific
limitations; the environment still does not execute model-generated code.

## Constrained action menus (M1.3)

**Opt-in:** `surlife --m13 --action-contract menu` exposes the complete set of
cost-feasible action masks, without providing optimal rewards. A dynamic JSON
schema encourages the LLM to select an admissible mask, but all answers are
still referee-scored without silent correction. Use
`--m13 --action-contract raw` for the unconstrained interface control.
The original model scored illegally in all four LLM turns of a real M1.2
experiment, so this stage tests environment affordances rather than claiming
evolved intelligence. Read [M13.md](M13.md) for trials and limitations.

## Headroom-calibrated survival tests (M1.4)

**Opt-in:** `surlife --m14` generates larger deterministic puzzle families
with measurable Greedy-vs-optimal headroom, then settles identical tasks
under the existing referee in parallel no-inference Greedy, classical
dynamic-programming solver, unpriced brute-force oracle, and optionally bounded
LLM arms. The benchmark has a separate JSON audit
with offline `--verify-benchmark-file` replay, not the historical SQLite
journal. A positive model score does not prove survival advantage after
consultation costs. See [M14.md](M14.md) for the experiment protocol,
run commands and important caveats about constructed Greedy traps.

## Google Gemini free-tier API experiments (M1.5)

M1.5 adds an optional `google-genai` Interactions provider for the
headroom benchmark: `surlife --m14 --provider google`. It reads
`GOOGLE_API_KEY` from the local environment, accepts only reviewed
free-tier Gemini model identifiers (default `gemini-3.8-flash`) and
preserves the current referee, request caps, no-retry behavior and
independent JSON replay. Model availability and a free-tier pricing
listing do **not** establish that a particular Google project is
on a free billing tier. Read [M15.md](M15.md) for installation,
local key setup and one-call pilot. Older model-provider paths remain
unchanged.

## Adaptive cognition and inherited metacognition (M1.6 / M1.7)

**Opt-in experimental implementations:** `surlife --m16` replaces the
host-owned fixed consultation schedule with a bounded, organism-owned
two-context policy. It learns from post-outcome virtual-energy advantage
versus a no-inference Greedy counterfactual. The policy sees only current
public task features and its own prior learning state; model requests remain
bounded and independently billed by the gateway. See [M16.md](M16.md).

`surlife --m17` aggregates independently replay-verified M1.6 policy
experience across runs, excludes overlapping training/held-out puzzles,
compares inherited versus cold-start strategies on matched task streams,
and optionally saves a data-only policy snapshot **only after** an
**M1.7-v2 dual-control gate**: improvement versus both cold-start and
no-inference Greedy across held-out seeds, with zero provider failures.
M1.6-v2 never confuses failed consultations with successful reasoning.
Model/provider/generation scoping prevents fake training from being
inherited into a live Gemini policy. Original v1 reports remain
offline-verifiable, but new training is required for v2 promotion. See [M17.md](M17.md). Neither stage executes model-generated
code or proves open-ended biological evolution. Classical exact DP remains
unpriced and superior in this narrow task family.

## Counterfactual cognition tournament (M1.8)

**Opt-in** `surlife --m18` constructs one bounded model response bank on
seeded M1.4 puzzles and then runs **never, always, selective, adaptive-fresh**
(and optional adaptive-inherited) strategies against the exact **same sampled
model answers**. Only initial bank construction makes real provider requests;
`--m18-bank-in` reuses a verified bank and recomputes all policy outcomes
completely offline with another virtual cognition cap. Reference weather
and task are identical across strategies; the model sees a fixed 30-energy
reference observation so a response is reusable across differing histories.
Virtual energy charges and real API requests are reported **separately**.
Existing Greedy, DP and oracle controls remain. This improves reproducibility
and removes some provider-response variance but **does not** prove the LLM
is preferable to cheap exact DP. See [M18.md](M18.md).

## Non-additive TaskPacks (M1.9)

**Opt-in offline** `surlife --m19` introduces two fully visible new
scoring rules: **coverage** (unique weighted features with diminishing
overlap returns), and **synergy** (bonuses only if particular pairs of
items are chosen together). Tasks can alternate in `mixed` mode.
Independent reference scoring and exact mask enumeration audit the new
rules while the existing M0-v2 referee retains the energy economy.
Compare the original singleton-ratio Greedy against **marginal-gain
Greedy, bounded beam search, and unpriced exact Oracle**. All of M1.9
runs offline, with zero hosted provider requests. This characterizes
new worlds before we spend inference calls or draw cognitive claims.
See [M19.md](M19.md).

## TaskPack cognition tournament (M1.10)

`surlife --m110` connects M1.8's shared-response bank to M1.9's
**coverage** and **synergy** TaskPacks. Pack-specific model prompts expose
only public scoring rules (unique weighted feature coverage or pairwise
bonuses) without disclosing reference solutions. Each organism's model
consultations cost one virtual energy, and the cheap fallback is the
**stronger marginal-gain strategy**, not the old ratio-Greedy. Compare
never, always, selective, and adaptive-fresh cognition against Greedy,
marginal, beam and an unpriced oracle. A one-time response bank can be
audited and reused with **zero additional API calls**; model/provider,
prompt/scoring version and taskpack settings must match. Inherited M1.7
knapsack policies are intentionally barred because their feedback
semantics are incompatible. The benchmark does **not** imply LLM
superiority or a persistent artificial-life ecosystem. See
[M110.md](M110.md).

## TaskPack cognition inheritance (M1.11)

`surlife --m111` aggregates separate bounded numeric cognition memories
for **coverage** and **synergy**, trained from independently verified
M1.10 response banks. It evaluates inherited against fresh cognition
on disjoint held-out banks with identical model answers, **without any
new API calls**. A policy snapshot is promoted only when it improves
final energy versus **both** fresh adaptation and no-inference
marginal-gain Greedy, with no seed-level regressions, provider errors or
legality regressions. Beam search and exact oracle remain visible
unpriced references. Old knapsack policies are not mixed into TaskPack
learning. See [M111.md](M111.md).

## Planning and recursive LLM reviews

**[Open the Surlife foundation workspace](foundation/README.md)** — current project plan, compact LLM context, independent review prompts, scoring criteria, decisions, iteration history and a future-idea backlog.

The **current proposal** is [foundation/PLAN.md](foundation/PLAN.md). The **first frozen review snapshot** is [foundation/iterations/0001/PROPOSAL.md](foundation/iterations/0001/PROPOSAL.md). Start a fresh Codex or other LLM review using [foundation/prompts/REVIEWER.md](foundation/prompts/REVIEWER.md). Independent design reviews now exist; see PRs #5 and #6. M0 has a runnable offline baseline, but no LLM/evolution experiments have been conducted.

## Foundation documents — concept and engineering research

**Status:** broader concept remains unvalidated; offline M0 engineering baseline implemented  
**Version:** 0.1 · **Prepared:** 11 October 2026  
**Working title:** *Igor Life* (also called *Digital Evolution*, *Artificial Life*, or *Primordial Arena* in our discussions)

> **Research question:** Can a population of autonomous software organisms, sharing a minimal execution core but evolving their own prompts, memory, tools and code, progressively become more capable per unit of computational resource while surviving in a changing, competitive world?

### Start here

| Document | Purpose |
|---|---|
| [01 · Origins, ideas and problems](docs/01-origins-ideas-problems.md) | Complete discussion history; reasons earlier ideas became difficult |
| [02 · The chosen hybrid approach](docs/02-hybrid-organism.md) | Current proposed design: evolving prompts **and** executable code |
| [03 · Existing agents and reusable technology](docs/03-agent-frameworks.md) | Igor, nanobot, Agent Zero, Letta, mini-SWE-agent, DGM, OpenEvolve, EvoAgentX, smolagents |
| [04 · What is digital life?](docs/04-what-is-life.md) | Definitions, soul, health, age, reproduction, knowledge, inheritance and philosophical questions |
| [05 · Related experiments and research](docs/05-related-research.md) | Artificial-life precedents, prompt evolution, agent societies, lifelong learning |
| [06 · Lifecycle and arena mechanics](docs/06-lifecycle-and-arena.md) | Turn cycle, competition, virtual tokens, weather, environmental interventions, death |
| [07 · Programming architecture](docs/07-technical-architecture.md) | Concrete components, data contracts, source layout, safety architecture |
| [08 · Roadmap and experimental methodology](docs/08-roadmap-and-experiments.md) | Small first build, controls, metrics, costs, risks and decision gates |
| [09 · Decisions and unresolved questions](docs/09-decisions-and-open-questions.md) | Agreed directions versus design hypotheses and future decisions |
| [References](docs/REFERENCES.md) | Named external projects and published research with source links |

**Example files:** [organism manifest](examples/organism.example.json), [world rules](examples/world.example.json), and [proposed action contract](examples/action.example.json).

### Current direction in one paragraph

A **shared, protected Python life core** supplies observation, action submission, isolated code execution, model calls, and an interface with the world. Each organism owns an editable **soul prompt**, memory, runbooks, strategy and executable modules. The **arena/supervisor**—outside all organisms—enforces virtual token balances, actual provider spending limits, health, age, reproduction, weather, competition, rules and event logs. Organisms decide when it is worth spending scarce tokens to ask an LLM for advice, compare publicly observable rivals, mutate prompts or code, validate candidates and preserve useful capabilities. Competition normally acts **indirectly**, by changing common environmental conditions rather than editing opponents' files. Later experiments may add cloning, two-parent recombination, assimilation and evolvable biological mechanisms inside the supervisor's immutable resource/safety contracts.

### Hard distinctions

- **Documented fact:** existing papers and projects support parts of this approach (prompt evolution, persistent memory, code mutation, digital ecology).
- **Design choice:** our proposed world, soul, health, economy and environmental interventions.
- **Unproven hypothesis:** these components will generate open-ended, sustained, measurable progress in autonomous organisms.
- **Engineering constraint:** an organism may fail or die in the simulation, but it must not damage the computer, provider account, other protected agents' data or the referee.

### Intended audience and usage

Use this set as a project charter and living set of requirements before writing an implementation. It is not a claim that a working ecosystem exists. The suggested project directory and interface examples are **proposals**, not extracted working Igor code. External project features were checked against public documentation in October 2026; verify licenses, APIs and repository versions before copying code.

### Design summary

```text
                 ┌──────────────────────────────────────┐
                 │       ARENA / REFEREE (immutable)   │
                 │ economy · weather · age · health    │
                 │ outcomes · experiments · audit log  │
                 └──────────┬──────────────┬────────────┘
                            │              │
                  ┌─────────▼────┐  ┌──────▼─────────┐
                  │ Organism A   │  │ Organism B     │
                  │ soul + code  │  │ soul + code    │
                  │ memory/tools │  │ memory/tools   │
                  └─────────┬────┘  └──────┬─────────┘
                            └──────┬───────┘
                          shared LIFE CORE
                    (LLM gateway / tool contract)
```

**Current implementation:** a model-free two-organism, one-game M0 vertical slice is in the implementation branch. The next stage is experimental calibration, then versioned souls and capped model calls; generated-code isolation is required before any M2 execution.
