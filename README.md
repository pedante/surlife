# Igor Life / Primordial Arena

*Artificial life fights for survival.*
## Foundation documents — concept and engineering research

**Status:** design proposal, not implemented or experimentally validated  
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

**Next actual decision:** implement a two-organism, one-game, no-code-mutation vertical slice; then prove isolation and a single validated code mutation before expanding the population.
