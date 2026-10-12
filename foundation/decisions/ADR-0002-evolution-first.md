# ADR-0002 — Evolution-first Surlife: the arena serves the organisms

**Date:** 2026-10-12  
**Status:** Accepted project-direction decision (human conversation); implementation milestones below remain proposals until tested.  
**Owner:** Project maintainer  
**Supersedes:** No historical experiment or frozen proposal; clarifies implementation priority after M2.0.

## Problem

The repository has progressed through M1.x cognition benchmarks and M2.0's shared-resource ecology. M2.0 proves useful deterministic properties (shared consequences across ticks, simultaneous decisions, replay, energy accounting), but its stock/soil/harvest/tend dynamics risk shifting attention toward building an elaborate ecological simulation.

**Surlife's object of study is the evolving software organism, not the environment.** The desired organism autonomously allocates a limited, potentially earned and gradually increased allowance of model consultations to survive competition and improve an organism-owned prompt, memory, strategy, and later executable modules. The central hypothesis is that tested reusable adaptations can make descendants more effective per actual model token and compute spent.

## Decision

1. **Evolution first.** Prioritize organism-owned, persistent, versioned **prompt mutations** and then **Python module mutations** with a measurable propose → stage → test → accept/reject → rollback lifecycle. An agent must ultimately make these decisions within host-enforced action and cost limits; a human manual evaluator alone is not the target.
2. **Keep the referee small, authoritative and immutable to organisms.** Enforce observation filtering, real model usage/budget caps, virtual-energy ledger, challenge scoring, experiment replay, and isolated execution of any generated code. Changes to the arena's immutable rules are never a form of mutation.
3. **Treat the world as selection pressure.** Favor minimal, objectively scored competitive tasks with changing conditions and priced actions. A larger terrain/world, physical positions, soil, harvest, agriculture and graphical simulation are not prerequisites.
4. **Preserve M2.0 as an optional test fixture.** Its physical stock and soil are specific mechanics of that fixture, **not** required universal organism attributes or the future main game. Preserve M0–M2.0 replay/version compatibility rather than silently repurposing their flags or reports.
5. **Keep bounded environment/weather interventions as an indirect competitive action.** Weather means a named, typed modifier of cost, information or reliability. An organism may pay to create a condition anticipated to advantage its strategy or disadvantage a rival, but the effect operates through the common referee, affects the purchaser under the same rules, and is capped in energy, duration, scope and cooldown. No freeform rule rewrite, secret exposure, targeted file modification or privilege escalation.
6. **Scientific validity comes before theatrical survival.** Compare evolving organisms with frozen prompts, prompt-only, code-only, hybrid and stronger deterministic baselines on disjoint held-out challenges. Account for the FULL development budget: proposal calls, candidate tests, failed mutations, model tokens, computation and virtual energy. Resource-rich winners are not automatically more capable.
7. **Build a read-only organism evolution viewer, not a graphical physical world, if a UI is desired.** Display prompt/module history, action and spending decisions, tested hypotheses, competitive outcomes and lineage through verified event streams. Do not invent mental states or world geometry.

## Why not just expand M2.0?

The ecology fixture has multi-tick consequences but its currently implemented agents are trusted hard-coded functions. Further soil/harvest/weather sophistication cannot demonstrate autonomous prompt or code self-improvement. Continuing that path risks optimizing what is easiest to simulate rather than testing the main hypothesis.

## Direction of implementation

- **Next: M2.1 — Autonomous prompt-mutation tournament**, reusing existing `Soul` / `EvolutionSoul`, bounded gateway and evaluation controls where feasible. First offline fake-provider experiment; gated provider pilot only after independent real-usage limits and evidence capture are verified.
- **Then: M2.2 — Organism-owned Python modules**, one frozen interface, isolated worker/sandbox threat model and actual mutation-versus-control trials. Merely storing source strings is not demonstrated code evolution.
- **Then: M2.3 — Priced competitive interventions**, including bounded weather. They must be demonstrably useful strategic pressures, not another world-building milestone.
- **Later: inheritance/selection/reproduction**, only after mutations have demonstrated value over matched-budget, held-out controls.

Detailed gates: [Evolution-first implementation plan](../EVOLUTION_FIRST.md).

## Costs, risks and reconsideration

- A prompt mutation may improve an arena score while losing money/energy once training and evaluation calls are priced.
- LLM-generated code needs a *real* isolation boundary; `exec`, importing organism files or relying on in-process timeouts is not acceptable.
- A constant evaluator or narrow puzzle family can be overfitted. Changed conditions and disjoint holdouts are required.
- Weather attacks can become arbitrary griefing. Cap costs and worst-case effects, compare against an intervention-free control, and measure whether they improve adaptation.
- Revisit this decision if a minimal evolving organism cannot produce reproducible improvements despite several honest, bounded comparisons. Do not silently replace the research target with ever-richer scenery.

## Evidence and traceability

The user's October 12, 2026 course correction explicitly prioritizes evolving prompts/code and survival under scarce model calls. Existing repository evidence: `docs/02-hybrid-organism.md`, `docs/06-lifecycle-and-arena.md`, `docs/09-decisions-and-open-questions.md`, `foundation/PLAN.md`, `M11.md`, `M111.md`, and `M20.md`. These show earlier intent, implemented partial mutation/evaluation machinery, separate bounded cognition research, and the M2.0 ecology fixture respectively.

No benchmark improvement or code-mutation safety property is claimed by this ADR.