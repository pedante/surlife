# Igor Life / Primordial Arena

*Artificial life fights for survival.*
## First runnable prototype (M0)

**A small offline, deterministic arena is now implemented in this branch.** It has two scripted organisms, a scored puzzle duel, virtual-energy transfers, a transactional SQLite journal, replay and automated tests. **It does not yet implement LLM organisms, evolving prompts, generated code or reproduction.**

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for exact commands, tested scope, reuse decisions and next stages; [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md) records the user-authorized experimental scope.

## Bounded LLM organisms (M1)

**Experimental implementation:** M1 introduces separate versioned souls, bounded memory and one JSON action per hosted model consultation. It supports the OpenRouter free tier with no extra runtime SDK or a deterministic fake provider for offline tests. See [M1.md](M1.md) for Fish shell API-key setup, CLI examples, provider restrictions and scientific limitations. The M1 default is pinned to the general-purpose free Qwen3.8 27B model and requires structured JSON output. The optional random `openrouter/free` route is discouraged for controlled comparisons.

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
