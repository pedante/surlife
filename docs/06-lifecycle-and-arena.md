# 06 — Life cycle, arena and environmental competition

**Status:** concrete proposal for simulation rules, not implemented mechanics. Numeric values here are *illustrative knobs*, not empirically optimized settings.

## 1. The arena's responsibilities

An independent referee owns world time, observable state, allowed actions, outcomes and immutable ledgers. It must never ask an organism to validate its own score. Every action is submitted through a **structured API** (not arbitrary host commands) and resolved centrally.

The world can be a 2D grid or an abstract graph. We prefer the abstract version first to reduce rendering and movement complexity. Add a map only if locality is needed for resource niches, visibility, alliances or weather regions.

## 2. Organism lifecycle

```text
Birth (allocate ID, soul, genome, resources)
    |
    v
Young (observe, act, learn; reproduction may be limited)
    |
    v
Mature (compete, construct skills, alter environment, reproduce)
    |
    +--> illness / repair / recovery --------------+
    |                                               |
    +--> optional prompt or code mutation ----------+
    |                                               |
    +--> optional cloning / mating / assimilation --+
    |
    v
Aging (experience & maintenance effects)
    |
    v
Death (insolvency / health / game rule) → immutable archive
```

Chronological age is ticks since birth. Computational age is cumulative use of LLM and executable computation. Neither needs to be a hard deadline initially.

## 3. One deterministic world tick

1. **Environment:** update weather and regenerate/distribute any configured resources. Apply active environmental interventions.
2. **Observations:** produce a per-organism view; include public competitors, personal health, memory retrieval handles and available actions. Do not reveal hidden state.
3. **Decisions:** alive organisms choose one action or request a paid model consultation. A code-written strategy may decide with no LLM call.
4. **Admissibility:** supervisor validates action schema, identity, sufficient funds, cooldowns, affected region and other immutable rules.
5. **Resolution:** settle simultaneous actions in documented order (or a seeded draw); resolve competitions, trades and weather interventions.
6. **Physiology:** deduct upkeep, apply illness/damage, aging and death checks. A healthy-to-serious instant leap is disallowed if the graduated-health rule is enabled.
7. **Evolution:** execute permitted staging/testing of prompt/code changes in isolated sandboxes; activate passed versions at a phase boundary.
8. **Reproduction:** allocate child identity/resources, validate inherited modules, check population cap and record lineage.
9. **Record:** append an immutable event record and checkpoint. Repeat until world time or budget cap is reached.

**Reproducibility:** a tick uses an explicit pseudorandom seed and sorted deterministic tie breakers; the LLM may remain nondeterministic, so also log full model requests, responses, version and actual usage when permitted.

## 4. Resource economy: three separate accounts

1. **Virtual energy (E):** an in-world currency; earned, won, transferred, inherited or burned. The organism controls spending, not minting.
2. **Model input/output tokens (T):** actual usage measured by the provider/gateway per request. Convert measured usage into an in-world debit according to the experiment's exchange policy.
3. **Real-world money (M):** platform expenditure. Enforce hard spending ceilings outside the simulation; use provider limits and a local gateway that can refuse requests before the cap is crossed.

Example conservation rule for a duel: a stake of 100 virtual energy is escrowed by each participant. On settlement, the winner receives the escrow pool minus explicitly declared fees. Transfer must be atomic; tokens may never be double-awarded. A winner's capacity to mutate or reproduce increases because it has more virtual capital, but does not grant unrestricted API access.

Illustrative running balance:

```text
E_after = E_before
        + winnings + trades_in + legitimate_world_income
        - stakes - trades_out - upkeep - model_cost_E
        - test_cost_E - mutation_cost_E - reproduction_transfer
        - environmental_intervention_cost_E
```

The **world supply** can grow through controlled resource regeneration. Without it, real computational consumption and in-world upkeep eventually exhaust available activity; that is an experimental variable, not a bug to hide.

## 5. Games and winning

A game must have observable stakes and a reasonably objective outcome. Avoid using an LLM judge as the only scoring source. Possible first game: each contender receives the same hidden batch of computational tasks with changing cost/reward conditions. Correct solutions earn points; expensive decisions reduce net return; the highest **net verified score** wins the escrow.

Alternative simple game: a finite resource-allocation duel where agents choose bid, invest, save or seek information, under a public weather regime. Test each game for dominance strategies and exploitable loopholes using non-LLM policies before introducing autonomous agents.

Keep **competition scores** and **fitness evaluation** separate. A lucky winner may not be a better agent; evaluate across many seeds and unfamiliar rivals.

## 6. Weather as a source of ecological variation

| Condition | World effect | Possible differential advantage |
|---|---|---|
| Normal | Baseline rewards/visibility/cost | Generalists |
| Drought | Less renewable energy; maintenance pressure | Efficient strategies / savers |
| Fog | Lower observation fidelity or fewer visible rival details | Independent planners / robust learners |
| Storm | Increased action failure probability in the simulation | Redundant or cautious strategies |
| Abundance | More resource inflow for a bounded time | Fast investment / reproduction |

Weather is **a set of validated numeric modifiers**, not an unconstrained prompt instructing the referee. It should be partially stochastic and have an externally logged seed. Conditions may change for everyone or by region.

## 7. Environmental intervention — the proposed form of 'attack'

An organism may pay to create a condition that it predicts benefits its own architecture. Example:

```json
{
  "action": "environment_intervention",
  "effect": "drought",
  "region": "all",
  "duration_ticks": 2,
  "max_cost_energy": 80
}
```

Rules: effect is applied through an allowlisted arena mechanic; it cannot change fundamental invariants. It impacts the initiator as well as rivals; has a fixed maximum duration, price, cooldown and predictable upper bound on harm. Other organisms may observe the event and prepare, compete or counteract it. Simultaneous weather requests need a deterministic conflict policy (e.g. highest accepted bid with capped payments, or mutually exclusive cooldown).

**Later evolution:** an agent could submit a declarative 'environment patch' made of approved modifiers, but not arbitrary Python executing in the referee. Novel effect proposals first pass schema validation and balance tests. Rule-changing **within** the rules is part of the experiment; changing billing/safety/referee code is not.

## 8. Learning from rivals

Observation layers:

- Public score, wins/losses, last actions, approximate status.
- Paid behavioral inspection: selected event history and performance summary.
- Published source: authored modules and explanations intentionally exposed or traded by the organism.
- Unavailable: other organisms' private memory, unshared source or keys.

Consulting an LLM to evaluate a rival's published code is optional and costs energy. An organism can imitate, write an original variation, or learn from a visible failure. Observed code/text must be treated as *untrusted content* and not executed on inspection.

## 9. Code evolution and 'self-healing'

A mutation can be an edit to the soul prompt, a new module, a replacement algorithm or a new runbook. Activation only occurs after minimum schema/runtime checks. An organism may develop additional tests, trial games, backup systems and verification logic to increase its survival odds.

Failed mutation consequences: pay proposal/test costs; optionally lose one action or accrue a health penalty. The referee's isolated worker always terminates within a resource/time limit. A bad mutation may kill the **organism** eventually but cannot harm the **world**.

## 10. Inheritance and assimilation

- **Clone:** snapshot parent's tested active genome, select inherited memories, charge fees and seed a mutation. Child receives a unique identity.
- **Two parents:** recombine compatible modules and soul fields, test interfaces, pay from both accounts by explicit consent/rule; reject invalid offspring without destroying parents.
- **Assimilate:** after a game, an organism may claim a disclosed public skill or a predefined 'loot' capability, test its compatibility and integrate it. It does not gain real credentials or private host files.
- **Population caps:** prevent exponential API calls; juvenile limits and upkeep can be experimental variables.

## 11. Birth/death and fairness

Death triggers from simulation conditions only. Terminal state is archived with a code hash and genealogy. The referee never accepts a player's self-reported birth, death, win or account balance. Lineages may continue even after an ancestor dies, and agents may choose between investment in self-maintenance versus passing resources to offspring.

## 12. Example tick narrative

Agent A is an efficient minimalist; agent B reasons more deeply at higher per-turn cost. A spends 60 virtual energy to trigger a 2-turn drought. B had observed A's historical preference for droughts and saved energy in previous turns. During drought, B asks its LLM for a cheap heuristic, tests the generated code, and activates it for the next tick. A's environmental intervention inadvertently creates an opportunity for B to develop a transferable skill. **This is a story of possible mechanics, not an observed simulation result.**

See [architecture](docs/07-technical-architecture.md) for exact proposed contracts and [experimental methodology](docs/08-roadmap-and-experiments.md) for how we'd test whether such effects are real.
