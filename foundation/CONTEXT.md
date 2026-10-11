# Reviewer context pack — Surlife

**Status:** design, not software. **Context version:** 2026-10-11. **Primary source:** [PLAN.md](PLAN.md).

## Research ambition
Could a population of autonomous software organisms, sharing a small protected life core, become measurably more capable per actual model token or unit of computation through learning, evolving prompts, writing reusable code, competing for finite virtual resources, observing rivals, and later inheriting improvements?

This is an empirical hypothesis, NOT a claim of artificial consciousness or general intelligence.

## Core concept
- **Soul:** an individual, heritable, editable persona/strategy prompt. It is *not* the provider's privileged system prompt.
- **Life mission:** externally authored statement of the world and survival objective, identical for all agents.
- **Genome:** soul + individually owned strategy code + reusable skills/runbooks + selected inherited knowledge.
- **Shared core:** common interface for reasoning, observation, memory and action. Agents can extend approved behaviors but cannot rewrite the host supervisor.
- **Arena:** independent Python referee with weather, competitions, health/age (later), virtual-energy conservation, history and deterministic tests.
- **Economic pressure:** thinking with an LLM consumes real API tokens and priced virtual energy; winning games transfers virtual energy; constructing reusable code may amortize thinking cost.
- **Indirect competition:** organisms may purchase bounded weather/world interventions that affect *everyone*, including themselves. They do not directly patch rival code.
- **Social learning:** observe public decisions and optional published modules, ask an LLM about competitors' advantages, test adaptations.
- **Evolution:** prompts mutate first; generated executable modules may later be staged, sandboxed, evaluated and inherited; reproduction and code recombination arrive only when core mechanics work.

## Non-negotiable boundaries
External referee alone controls money, real model credentials, cost accounting, arbitrary host access, safety enforcement, competition scoring, world clock and official history. Its implementation is not an organism genome. Rival-generated text/code is untrusted. Agents cannot run unrestricted host commands. Virtual balances never authorize real spending beyond configured hard limits.

## Scientific controls
Measure held-out game outcomes and useful work at **matched actual-token and energy budgets**, not just wins or population growth. Compare fixed, prompt-only, code-only and hybrid baselines. Use deterministic reference policies, seeded weather, multiple trials, transparent event logs and rollback-aware mutation metrics.

## Focus of iteration 0001
Review the **smallest falsifiable vertical slice**: deterministic arena and ledger first; then two prompt-owning LLM agents; then exactly one testable mutable Python strategy module.

Do not derail review into implementing age, elaborate disease, mating, multiple programming languages, recursive self-editing of the referee, or broad social simulation.

## Background sources inside repository
- [Origins and risks](../docs/01-origins-ideas-problems.md)
- [Hybrid organism](../docs/02-hybrid-organism.md)
- [Agent frameworks](../docs/03-agent-frameworks.md)
- [What is digital life?](../docs/04-what-is-life.md)
- [Related experiments](../docs/05-related-research.md)
- [Lifecycle / arena](../docs/06-lifecycle-and-arena.md)
- [Programming architecture](../docs/07-technical-architecture.md)
- [Experimental method](../docs/08-roadmap-and-experiments.md)
- [Prior design decisions](../docs/09-decisions-and-open-questions.md)

If this context conflicts with [PLAN.md](PLAN.md), flag the conflict; do not silently reconcile it.
