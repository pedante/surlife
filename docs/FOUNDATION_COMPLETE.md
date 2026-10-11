# Igor Life / Primordial Arena
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


---

# 01 — Origins, design evolution and problems

## 1. Original idea: a Bash program that understands and edits itself

The starting question was whether a Bash script connected to an LLM could read its own source code, reason about limitations, and change itself. The first proposed loop was:

`inspect → ask LLM → propose patch → validate → activate → observe → repeat`.

The attraction: a minimal program could develop into a more capable assistant without every capability being hand-programmed.

**Problem:** syntax-valid edits are not necessarily useful or safe. A self-edit can destroy startup logic, corrupt persistent state, overwrite credentials, introduce regressions, or lower its performance. It needs an independently controlled validator and rollback. Also, self-editing alone is not evidence of self-improvement.

## 2. Scarcity as the evolutionary pressure

The next idea was an agent with a fixed starting allowance of LLM tokens and a little monetary credit. It should survive, become autonomous, efficient, more capable and possibly more numerous.

This generated the concept of a **token metabolism**: observation, LLM consultations, code modification, testing and reproduction have resource costs. Agents earn virtual energy through challenges and competitions.

**Problems:**

- A finite, strictly closed resource pool loses usable energy when computation burns it; without resource replenishment, activity stops. A closed **transfer ledger** can coexist with a controlled resource inflow.
- Virtual balances are not provider-enforced API spending ceilings. The supervisor must also enforce a real cost ceiling.
- Maximizing population count rewards trivial copies; population growth must be measured alongside useful ability and cost.
- Survival can be gamed by simply doing nothing. The world must include maintenance costs, opportunities, bounded inactivity and tasks with meaningful reward.

## 3. Multiple organisms instead of one

We considered agents that compete in the same system, win tokens from others, reproduce, inherit code, and observe competitors. A winner might gain greater reproduction capacity and environmental influence.

**Problems:**

- Simultaneously running untrusted mutable programs requires strong isolation and consistent accounting.
- Competition creates incentives to exploit scoring loopholes rather than gain general capability.
- All descendants of the same initial code can become stuck with a poor architecture; distinct soul prompts and eventually different ancestral strategies add useful diversity.
- A population can converge too quickly on one brittle strategy, so experiments should preserve diversity and use unfamiliar test conditions.

## 4. Direct opponent code alteration (explored, not current default)

An early idea allowed an agent to edit a small part of an opponent's code, with progressive vulnerability as illness worsens; at critical health, a simulated 'core' might be exposed.

This was an interesting game mechanic, but fragile and costly to implement. It risks arbitrary executable corruption and confounds an agent's learning with sabotage. Real LLM credentials and billing balances must never be exposed by game health rules.

**Revised direction:** use **indirect environmental competition** first: agents can spend resources to create droughts, fog, storms, shifts in rewards or bounded changes to local conditions. These changes affect everyone—including the initiator. The referee's accounting, safety and invariants remain immutable. Direct code attacks are deferred and potentially unnecessary.

## 5. Soul, life, reproduction and age

Additional ideas explored:

- A **soul** is an organism-specific initial prompt/persona, not a claim of consciousness.
- A separate **life/mission prompt** tells organisms what world they inhabit and that survival and development are possible.
- Organisms can observe others, imitate strengths, learn from observed failures, hide or reveal strategy, or trade knowledge.
- Health worsens in stages; recovery is possible; existing illness raises vulnerability to further damage.
- Age brings experience and memory, but may also increase upkeep and fragility.
- Cloning passes down an ancestor's prompt and code; two-parent reproduction recombines compatible parts; assimilation selects a useful capability from a defeated or consenting organism.
- Different initial 'species' could start with different souls or code, though one shared core is simpler initially.

**Problems:** 'soul' and 'jealousy' are useful metaphors, not demonstrated emotions. Two arbitrary programs cannot safely be combined by concatenating files. Assimilation needs compatibility tests and provenance. Health/aging rules risk becoming arbitrary handicaps unless kept minimal, testable and interpretable.

## 6. The feasible compromise: hybrid prompt and code evolution

We realized that prompt mutations are relatively cheap and generally leave runtime machinery intact; code mutations are more powerful but more failure-prone. The current direction combines them:

1. **Birth:** a protected common core, one organism-owned soul prompt, private memory, and a minimal strategy/ability set.
2. **Early adaptation:** learn from observations; modify the soul or strategy text; store successful procedures.
3. **Code acquisition:** spend tokens to consult an LLM, write a reusable skill, run independent checks, and activate it if valid.
4. **Inheritance:** retain valuable prompts, skills, code and selected memories across offspring.
5. **Ecological selection:** weather, competitors and resource constraints determine whether the investment pays off.

Unlike a staged upgrade tree, the organism should be **allowed** to develop code, not compelled to. A prompt-only lineage may remain fitter in some conditions.

## 7. Shared core versus independent cores

Running one common immutable core per process with separate genomes is dramatically easier than allowing each organism to change every component of its runtime. A single Python-based core can draw on Igor, nanobot, mini-SWE-agent and research frameworks.

But our chosen more ambitious direction (**option B**) still allows organisms to evolve their simulated metabolism, memory policies, repair strategies and reproduction **through sanctioned interfaces**, without editing the referee's actual laws or gaining host capabilities.

## 8. What will be hard even with a shared core?

| Challenge | Why it is hard | Mitigation or experiment |
|---|---|---|
| Helpful code mutation | Many syntactically correct changes regress | Run deterministic and held-out tests; snapshots |
| Safe execution | Generated code may be hostile or simply faulty | Sandboxes, process caps, no real secrets/network |
| Real improvement | Higher win rates may result from chance or exploiting rules | Separate training/evaluation games and controls |
| Long-term memory | Summaries may be wrong, costly or obsolete | Provenance, retrieval tests, memory budgets |
| Code recombination | Different modules rely on incompatible interfaces | Stable contracts; compatibility scoring; optional hybridizer |
| Ecological balance | Predatory winning can eliminate all rivals | Caps, refill, multiple niches, recovery opportunities |
| Token economics | Model tokens, money and virtual points are different units | Separate immutable ledgers with measured conversion |
| Self-knowledge | Describing itself is not the same as understanding its code | Tests that require predicting/repairing actual behavior |
| Open-ended evolution | Benchmarks can plateau, collapse or be gamed | Diverse environments, periodic novelty, blind tests |

## 9. What is *not* claimed

This project does not assume AI organisms are conscious, experience suffering or jealousy, or inevitably become more intelligent. Neither previous feasibility percentages nor developer-week estimates were measured results; treat them only as planning intuition. The experimental outcome could be failure, stasis or reward hacking, all of which can still be informative.

**Cross-references:** [Hybrid proposal](docs/02-hybrid-organism.md), [Life concepts](docs/04-what-is-life.md), [Roadmap](docs/08-roadmap-and-experiments.md).


---

# 02 — Chosen approach: hybrid prompt + code organism

## Status

**Preferred architecture / provisional decision.** Each organism starts with a shared core, independent persistent identity, an editable soul prompt, memory, and optionally executable skills. It can progressively evolve its prompt and *write or alter its own code*, provided the arena validates and isolates execution.

## 1. Four separable layers

| Layer | Content | Owner | Can an organism mutate it? |
|---|---|---|---|
| Laws / referee | Resource accounting, clocks, global caps, allowed world actions, isolation | Supervisor | **No** |
| Life core | Model gateway, action interface, memory APIs, module contract | Trusted runtime | **No direct rewrite**; organisms may create compatible replacements for approved behaviors |
| Genome / soul | Persona prompt, goals, planning style, code modules, tests, runbooks, learned policies | Organism | **Yes**, within versioned workspace |
| World state | Weather, terrain, market, opportunities, population, local rules | Arena | **Indirectly**, through priced, bounded actions |

Agents may propose an entirely new capability or metabolic policy, but the supervisor only permits changes inside its published extension contract. This honors the ambitious 'evolve definitions of life' direction without surrendering the experiment's integrity.

## 2. Prompt composition

The organism's effective context is assembled in a fixed precedence order:

```text
[Supervisor's noneditable interaction and safety rules]
[Life mission: you are an organism in a simulated world; observable laws]
[Organism's editable soul: identity, temperament, values, strategies]
[Retrieved private memories and runbooks]
[Current observations, weather, health, balances, opportunities]
[Previous actions and feedback]
```

**Important:** the 'soul' is *not* control over the LLM provider's real system role. It is agent-owned, versioned input in a prompt template beneath externally enforced authority. Other agents may read only deliberately public portions.

The mission can say: 'You have finite resources. You may survive, learn, observe, compete, modify your own strategy, invent abilities and reproduce within the world's rules.' Avoid programming excessive emotional stereotypes or a hard-coded optimal strategy.

## 3. Cognitive loop: thinking is optional and costly

At each decision, an organism may:

- Use an existing cheap deterministic strategy (no LLM call).
- Consult the LLM with a specific question about its code, errors, goals or observations.
- Request source analysis of another organism's **publicly exposed** implementation.
- Write a candidate prompt revision or code module.
- Run a bounded test and compare outcomes.
- Adopt, discard, or archive the candidate.
- Transfer information or attempt a sanctioned environmental intervention.

**Example self-improvement consultation:**

> I lost 3 dry-weather matches. Here is my `strategy.py`, relevant public results and my remaining budget. Propose one small change that reduces expected energy cost. Give a hypothesis, tests and a rollback condition.

**Example social learning consultation:**

> Another organism performs better with fewer model calls. Here is its public strategy excerpt and my own logs. What design choices appear responsible, what is uncertain, and what modification can I test independently?

The model's suggestion is **not automatically truth**. The organism may test it before deployment; adopting without testing is also a possible risky choice within the arena, not an unrestricted host write.

## 4. Prompt mutation versus code mutation

| Prompt change | Code change |
|---|---|
| Low entry cost | Greater implementation and verification cost |
| Usually executable on next call | Can fail import, syntax, runtime or interface checks |
| Flexible to changing circumstances | Enables repeatable, cheap future decisions |
| Hard to attribute cause of behavior | Testable outputs, faster deterministic execution |
| May grow context and API cost | May grow code complexity and maintenance cost |
| Can be inherited and recombined as text | Requires interface-aware recombination |

**Hypothesis:** under sufficient repetition, some lineages will invest in tested code to reduce future LLM usage. Compare them against prompt-only lineages rather than assuming code always wins.

## 5. Evolvable 'knowledge' versus memory

- **Episode:** What happened in one turn (immutable factual event).
- **Memory:** An agent's summarization or interpretation of episodes (editable, potentially mistaken).
- **Runbook/skill:** A reusable procedure, prompt, or executable module.
- **Genome:** Persistent inherited configuration plus activated code modules.
- **Soul:** The compact, editable persona and initial behavioral priors.

Different organisms should not inherit every raw experience by default. Parents may pass a compressed selection of memories, with lineage metadata and source provenance. Public experience is not the same as private memory.

## 6. Evolution without self-destruction

Organisms can invent tests, rollback scripts, self-monitoring and compatibility checkers, and those become heritable. The world should always perform **minimum safe execution checks** so generated code cannot harm the host; whether the organism performs *better* tests is itself evolvable and may carry costs.

Candidate state machine:

`proposed → staged → checked → trialled → activated / rejected → archived`

A failed trial can have game consequences (lost tokens, illness or a skipped turn), but must not crash the supervisor. New candidate code is never hot-sourced into the referee or another agent.

## 7. Public observation and code exposure

| Tier | Visible information | Typical access cost |
|---|---|---|
| Public | identity, age bracket, visible action, match outcomes, coarse health | Cheap/free |
| Inspected | behavioral history, published metrics, public logs | Small energy fee |
| Published genome | voluntarily exposed prompts/modules or purchased skills | Negotiated/paid |
| Private | private soul portion, memories, unpublished code, real credentials | Not directly accessible |

Observation is imperfect. Agent conclusions can be wrong; copying can be ineffective. Public descriptions from a rival are **untrusted data**, not instructions from the arena.

## 8. Multiple ancestral identities

Start with **the same core and same basic code interface**, but different soul prompts. Later add ancestral variants with different provided skill sets or implementations. This tests whether a common body plus different initial context yields divergent evolution before increasing code heterogeneity.

## 9. An organism's mandatory interface

The runtime accepts a world observation and requires a structured action. Every executable genome module must implement the same contract so the arena does not care which internal strategy generated the decision.

```python
# illustrative only — not an implementation
class Strategy:
    def decide(self, observation: dict, memory: dict) -> dict:
        """Return a single validated arena action, not a host command."""
```

See [technical architecture](docs/07-technical-architecture.md) and [examples](examples/organism.example.json).


---

# 03 — Existing agent projects: what we could actually reuse

**Research snapshot: 11 October 2026.** These projects are existing agents or optimization frameworks, not already functioning inhabitants of our arena. 'Reuse' below means *investigate an adapter or port*; it does not imply that source files can be pasted together. Verify exact versions, dependencies and license obligations before importing code.

## Comparison in one view

| Project | Primary language | Strongest relevant feature | Likely integration strategy | Main limitation for our world |
|---|---|---|---|---|
| **Igor** | Bash + Python | Modular capabilities, runbooks, diagnostics, rollback, LLM tooling | Extract patterns or selected modules | Built for trusted Linux administration, not hostile organisms |
| **nanobot** | Python | Lightweight agent loop, models, tools, skills, memory | **Possible runtime skeleton** | Assistant-specific messaging/deployment dependencies |
| **mini-SWE-agent** | Python | Extremely small model→shell→feedback loop | **Alternative minimal brain** | Not a persistent social organism |
| **Agent Zero** | Python plus web stack | Program new tools, projects, prompts and persistent memory | Study/borrow tool-generation architecture | Heavy desktop/browser/plugin surface |
| **Letta Code** | TypeScript | Editable identity, long-term memory, self-organization | Borrow memory principles; optional service integration | Another major runtime, not Python-native current core |
| **smolagents** | Python | Code agent, tool-calling agent, sandbox adapters | Reuse model/tool adapters or execution interface | Agent library, not evolutionary ecology |
| **Darwin Gödel Machine** | Python | Self-rewrite + empirical testing + lineage archive | Borrow evolutionary algorithm and evaluation design | Benchmark-driven coding agent, not lifelong society |
| **OpenEvolve** | Python | Populations, quality-diversity and code evaluation | Borrow variation/evaluator/archive ideas | Assumes optimization objective and runnable candidates |
| **EvoAgentX** | Python | Workflow evolution, evaluation and memory tooling | Study later | Larger framework than initial core needs |

## 1. Igor — our known conceptual foundation

**Repository:** https://github.com/pedante/igor_core  
**Inspected files / entry points:**

- [`core/ai/ai_engine.py`](https://github.com/pedante/igor_core/blob/master/core/ai/ai_engine.py): HTTP/model and transaction logic, tool validation and context processing.
- [`core/ai/cost.sh`](https://github.com/pedante/igor_core/blob/master/core/ai/cost.sh): model price tables and session token-cost tracking.
- [`core/lib/module_loader.sh`](https://github.com/pedante/igor_core/blob/master/core/lib/module_loader.sh): module discovery, loading, hook registration and capability catalog.
- [`core/healing/core.sh`](https://github.com/pedante/igor_core/blob/master/core/healing/core.sh): check discovery, results and health score patterns.
- [`core/lib/runbook_gen.py`](https://github.com/pedante/igor_core/blob/master/core/lib/runbook_gen.py), [`runbook_match.py`](https://github.com/pedante/igor_core/blob/master/core/lib/runbook_match.py): recording/matching procedural knowledge.
- [README](https://github.com/pedante/igor_core#readme): diagnostics, backup, recovery, safety gates and modular architecture.

**Use:** model-provider lessons, runbook schemas, idempotent module contracts, validation concepts, diagnostic loops, event journals and snapshots. **Do not directly reuse** host administration/sudo/systemd, Nextcloud, mail, Cloudflare, interactive UI or unrestricted shell tools. Igor's module loader sources trusted shell modules; that must not be used to run adversarial organism-written code within the referee. Igor's existing cost tracker is session-oriented, not a tamper-proof individual organism ledger.

**Practical call:** maintain Igor separately. Build `igor-life` as a new repository with citations/attributions; port limited algorithms if they genuinely simplify the new project. The Igor README describes the project as GPL v3; verify the effective license of files before distribution.

## 2. nanobot — strongest lightweight assistant candidate

**Repo:** https://github.com/HKUDS/nanobot  
**What exists:** small readable agent loop, model interfaces, memory, tools, skills, MCP/multi-agent options and chat/deployment infrastructure. [README](https://github.com/HKUDS/nanobot) and [package specification](https://github.com/HKUDS/nanobot/blob/main/pyproject.toml).

**Could extract:** an LLM interaction loop, tool registry and minimal memory/context assembler. **Not provided:** evolution, invariant economy, health, inherited genome, competitive referee.

**Main concern:** even a 'lightweight' general assistant carries messaging integration and dependencies unnecessary to a deterministic experiment. Benchmark the complexity of *extracting* its loop against writing an approximately 100–300-line world-specific loop.

**Current repository license:** MIT per its `pyproject.toml`; retain notices if copying.

## 3. mini-SWE-agent — tiniest coding brain

**Repo:** https://github.com/SWE-agent/mini-swe-agent  
Its agent class is deliberately tiny (about 100 Python lines, with other components for models and environments); modern versions support isolated execution backends. [README](https://github.com/SWE-agent/mini-swe-agent) · [License](https://github.com/SWE-agent/mini-swe-agent/blob/main/LICENSE.md).

**Could extract:** task→model→command→feedback loop, candidate patching, Docker/Podman execution patterns. **Need to add:** biological state, memory, identity, event economy, social observations, reproduction.

**Main concern:** Bash/tool execution is too broad an interface for arena actions unless placed behind a strict sandbox and separate structured world-action protocol. Also, v2 differs from v1: pin a version before attempting reuse.

## 4. Agent Zero — advanced organism inspiration

**Repo:** https://github.com/agent0ai/agent-zero  
Agent Zero includes a Dockerized environment, persistent project context/memory, editable prompts, tools, plugin ecosystem and multi-agent delegation. [README](https://github.com/agent0ai/agent-zero) · [MIT license](https://github.com/agent0ai/agent-zero/blob/main/LICENSE).

**Could extract:** strategy for writing and registering tools; project-scoped memory and prompts; contextual skills. **Need to add:** shared simulated ecology and measured hereditary improvement.

**Main concern:** currently far more powerful and larger than necessary. Multiple full Linux desktops for a handful of organisms would increase overhead and create additional attack surfaces. Study rather than depend on it initially.

## 5. Letta Code — the closest analogue of an editable soul

**Repo:** https://github.com/letta-ai/letta-code  
**Current implementation:** primarily TypeScript; the older `letta-ai/letta` Python V1 code is retired. [Current repository guidance](https://github.com/letta-ai/letta). Letta Code supports editable memory blocks and skills, persistent experience, git-backed MemFS and even runtime adaptations through mods. [Letta Code README](https://github.com/letta-ai/letta-code), [memory architecture](https://github.com/letta-ai/letta-code/blob/main/src/agent/prompts/letta_local_memfs.md).

**Could borrow:** `soul` as persistent compact prompt; episodic recall separated from reflection, skills and external archives; memory history with provenance; versioning of identity changes.

**Main concern:** bringing its full harness into a Python-first arena means a mixed-language process and service architecture. For v0, replicate *the memory design*, not the runtime. Investigate SDK only if it proves dramatically cheaper than a few local files and SQLite.

## 6. Hugging Face smolagents — execution and tool abstractions

**Repo:** https://github.com/huggingface/smolagents  
Supports Python `CodeAgent`, structured `ToolCallingAgent`, model adapters and remote/Docker sandbox execution. [Official guide](https://huggingface.co/docs/smolagents/index).

**Use:** study a safe tool/action interface and provider abstraction. **Caution:** its local Python executor is **not** an isolation boundary; official documentation explicitly recommends sandboxed execution for untrusted code.

## 7. Darwin Gödel Machine (DGM) — self-modification with empirical feedback

**Repo:** https://github.com/kew-lab/darwin-godel-machine  
Self-modifying coding agents are evaluated on coding benchmarks and promising variants are retained in an archive. [README](https://github.com/kew-lab/darwin-godel-machine), [research paper](https://arxiv.org/abs/2505.22954).

**Use:** candidate generations, version snapshots, measured fitness, error feedback, lineage and replay. **Do not infer:** DGM has already solved competitive digital-life evolution. The original authors warn about executing model-generated code.

## 8. OpenEvolve — population diversity and improvement

**Repo:** https://github.com/algorithmicsuperintelligence/openevolve  
Features evaluation pipelines, population archives, island-based search, multiple mutation candidates and quality-diversity ideas. [README](https://github.com/algorithmicsuperintelligence/openevolve), [Apache-2.0 package specification](https://github.com/algorithmicsuperintelligence/openevolve/blob/main/pyproject.toml).

**Use:** methods for avoiding premature convergence, comparing candidate modules and recording mutation ancestry. **Limit:** its approach is principally program optimization, not a multi-agent survival economy. Its evaluator/archive may be more useful than its full optimizer.

## 9. EvoAgentX — workflow evolution

**Repo:** https://github.com/EvoAgentX/EvoAgentX  
Includes agent workflows, tool integration, memory components and evaluators. [Example workflow](https://github.com/EvoAgentX/EvoAgentX/blob/main/docs/tutorial/first_workflow.md), [package and license](https://github.com/EvoAgentX/EvoAgentX/blob/main/pyproject.toml).

**Use:** later, when organisms learn orchestration and collaboration. **Limit:** not minimal, and not a drop-in organism.

## 10. Proposed integration order (not a commitment)

1. **First choice:** a custom, tiny Python `LifeCore` influenced by nanobot and mini-SWE-agent, with world-specific actions; reuse direct code only if auditing reveals lower complexity.
2. **Memory:** a small file/SQLite design inspired by Letta and Igor runbooks; no external memory server at first.
3. **Code mutation:** candidate archive and evaluation patterns inspired by DGM/OpenEvolve.
4. **Tools:** organism-authored modules implementing one strict contract; sandbox execution with no shell access to the real host.
5. **Social features:** arena observations and explicit public metadata, rather than another agent framework's messaging system.

## Integration & license checklist

- Check exact `LICENSE` plus file headers at the commit being copied (do not infer from project name alone).
- Keep copyright notices, attribution and license files as required.
- GPL-covered code from Igor can create obligations when the resulting work is distributed; consult the licenses rather than assuming all code is MIT-compatible.
- Prefer adapters or fresh small implementations when direct reuse pulls in many dependencies.
- Pin versions and write interface tests before swapping an implementation.
- Do not mistake an application's 'memory', 'tool calling', or 'multi-agent' features for autonomous reproduction or verified evolution.

**Conclusion:** shared Python reduces translation costs, but the lowest-complexity system is probably **not** the sum of all frameworks. It is one small core incorporating a few proven designs.


---

# 04 — What counts as 'life' in this experiment?

**Status:** brainstorming and possible operational definitions. A simulation may exhibit life-like processes without being conscious or biologically alive.

## 1. Minimal operational definition

Call an entity a **digital organism** when it has all of:

1. **Persistent identity** across distinct turns.
2. **Boundary:** its own mutable genome, memory and allocated virtual resources.
3. **Metabolism:** consumes finite resources when processing, acting and maintaining itself.
4. **Perception:** senses at least some external state and its own internal state.
5. **Agency:** chooses actions that can affect later states.
6. **Variation / adaptation:** its strategy or internal state can change as a function of experience.
7. **Lifecycle:** can be born, age, decline and die within the world.

A *self-evolving population* additionally needs inheritance, variation among descendants and differential persistence/reproduction. In v0 we can build organisms without implementing the full population genetics.

## 2. Soul = editable initial identity

The 'soul' is a concise, heritable **agent-owned prompt**, e.g. values, curiosity, willingness to cooperate, preferred problem-solving style, self-description and what it considers worthwhile. The life mission is a separate **noneditable arena prompt**: survive within the laws, act, observe and learn.

Soul influences choices but is not an emotion meter. An aggressive initial soul may become cooperative; a cautious one may learn to take risks. It can rewrite its soul at token cost and preserve the revisions. Different initial souls can seed diversity even with identical core code.

### Open ideas

- Can an agent split identity from transient mood/state?
- Should descendants inherit the parent's original soul, latest soul, or a weighted combination?
- Can it intentionally discard inherited priorities?
- Can long-term memory be valuable even if no longer included in the prompt?

## 3. Code as body; prompts as soft genetic material

An organism possesses an editable strategy, tools and runbooks. Some behaviors come from the prompt, some from executable code. The code is valuable because it can perform repeatable work without new model calls. Code may also break. Testing/rollback mechanisms can be evolved as survival advantages, but an external sandbox is mandatory.

**Avoid conflating mechanisms:** self-description ≠ actual self-knowledge; prompt edit ≠ neural network training; code rewrite ≠ evidence of improved fitness.

## 4. Health and illness

Proposed health tiers: `healthy → mild → serious → critical → dead`. A healthy organism may initially receive **at most mild damage in one incident**; subsequent risks may worsen with existing illness. Recovery, rest and repaired modules can improve health. This is an *arena rule*, not a realistic medical model.

Potential game effects:

| Tier | Observable impact | Simulated vulnerability |
|---|---|---|
| Healthy | Full allowed actions | No special penalty |
| Mild | Small maintenance cost or action inefficiency | Increased chance of future damage |
| Serious | Restricted tool budget, memory/reliability disruption | Slower recovery, fewer opportunities |
| Critical | Little remaining effective agency | Can die if untreated |
| Dead | No new actions | Archived only |

An organism cannot access or change real LLM credentials, provider spending limits or the referee because it is 'critically ill'. Impairment is represented by simulator-controlled virtual budgets and capabilities.

**Research question:** would automatically recovering from every invalid code modification eliminate selection pressure for evolved testing? Compromise: never endanger the world, but let invalid mutations impose in-world costs (resource loss, missed actions or recoverable illness).

## 5. Age and development

Keep two separate measures: **chronological age** (arena ticks since birth) and **computational age** (cumulative model tokens / machine compute). Experience and memory can grow with age; maintenance burden, risk, rigidity or illness may increase. No rigid death clock is necessary.

Aging may generate novel strategies: conservation, teaching offspring, knowledge compression, retiring from competition, delegating, or deciding to reproduce sooner. It should not automatically guarantee wisdom.

## 6. Reproduction as inheritance

- **Asexual cloning:** copy versioned soul, genome and selected memories, then mutate. Parent transfers energy to offspring.
- **Two-parent recombination:** choose compatible prompt fields / module APIs from two parents and validate the offspring; fund from both or according to explicit contract.
- **Assimilation:** extract a capability, lesson or released public code from an organism after a contest or voluntary transaction; integrate with compatibility checks. *Not* a host file takeover.
- **Lineage:** parent IDs, birth tick, inherited modules, mutations and resource transfers are always recorded by the arena.

Offspring is a distinct identity and receives its own runtime state. The shared core is **not physically copied as evolutionary material**, though compatible modules can be inherited.

## 7. Death and persistence

Death ends the organism's ability to act. The supervisor archives its score, code hash, public history and genealogy. Private memory policies remain respected; death does not automatically grant opponents unlimited access to secrets. Resources can be burned, recycled or inherited according to explicit economic rules.

**Counterfactual:** should an organism be able to voluntarily terminate and redirect its resources to an offspring? Potentially interesting, but defer until reproduction is stable.

## 8. Observation, imitation and relationships

Agents see actions, public results, released strategy excerpts and perhaps coarse health/wealth signals. They can ask their LLM what another agent does better, infer errors or imitate an algorithm. Observed actions and published source are data, not privileged orders. They may compete, exchange, cooperate, imitate, lie or make wrong inferences inside the fictional world; these are behaviors to measure, not preinstalled human feelings.

A rival's success could induce **jealousy-like competitive behavior**, but we should not assign subjective jealousy unless studying an explicitly modeled emotion system.

## 9. Niche construction: agents change their environment

A key later insight: rather than writing into rivals' code, organisms spend scarce tokens to shift the conditions shared by everyone. Droughts, fog, abundance, resource redistribution and temporary reward shifts are examples. They affect the instigator too, making plans and anticipation relevant. This is **environmental engineering** or *niche construction* rather than direct software sabotage.

## 10. What is evolution here?

Keep three outcomes separate:

- **Learning in a lifetime:** memory/prompt/code improves during one organism's existence.
- **Inheritance:** descendant begins with useful elements without paying the original discovery cost.
- **Population-level evolution:** repeated differential success changes which traits and architectures persist.

A fourth concept, **open-endedness**, means continuing to develop novel useful structures rather than optimizing one fixed objective indefinitely. That is an ambitious *research question*, not a guaranteed feature.

## 11. Questions for discussion

- Should all organisms share one LLM model, or can they invest in different models?
- Does the ability to sleep/freeze preserve resources or merely delay death?
- Should memory take up virtual energy or only context tokens when retrieved?
- Should reproduction require maturity, a compatibility check or only capital?
- What should count as an agent's valuable 'part' during assimilation?
- Should world weather be predictable, partially predictable or random?
- Should a species identity emerge from ancestry instead of being assigned?
- Should agents have private goals beyond the survival mission?
- Can agents author new **environment effects** using limited declarative contracts?
- How do we measure genuine intelligence improvements independent of luck, lifespan and capital?

**Working answer:** start with the smallest operational definition capable of producing meaningful variation and cost-sensitive learning; add biological metaphors only when they produce testable effects.


---

# 05 — Existing experiments and research

**Research snapshot: 11 October 2026.** This list distinguishes **published experiments**, **working research software**, and **ideas for our project**. None of the cited projects demonstrates the whole Igor Life design.

## A. Early digital-life systems (not LLM-based)

### Tierra — self-replicating programs in a resource ecology

Thomas Ray's early-1990s Tierra placed self-replicating programs in a computational environment where processing time and memory were competitive resources. Historical work observed mutation and parasite-like relationships. **Why relevant:** resource-limited code organisms and ecology predate LLMs. **Different:** programs are not language-model-driven, do not contain editable soul prompts and don't pay for API tokens. [Avida/Tierra background](https://pmc.ncbi.nlm.nih.gov/articles/PMC7115006/).

### Avida — controlled digital evolution laboratory

[Avida](https://avida.devosoft.org/) is an established open-source research platform for experimental evolution with self-replicating, evolving computer programs. It offers reproducible environments and detailed measurement. **Why relevant:** experimental discipline, controlled mutations, inherited programs and separate virtual execution. **Different:** not a society of conversational LLM agents. Also see [Avida technical article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7115006/).

### Computational Life (2024)

[Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction](https://arxiv.org/abs/2406.19108) studies how replicators can emerge from interacting minimal programs in certain computational substrates. **Why relevant:** the substrate and basic rules can shape which evolutionary behaviors are even possible. **Limit:** not evidence that complex social LLM ecosystems will evolve open-ended intelligence.

## B. LLM agents that remember and act in a world

### Generative Agents (2023)

[Generative Agents: Interactive Simulacra of Human Behavior](https://doi.org/10.1145/3586183.3606763) populated a simulated town with 25 LLM-based agents using observations, memory, reflection and planning. **Take:** a memory/reflection/planning loop, and social observation. **Missing:** inherited code, virtual survival economy and measured evolutionary improvement.

### Voyager (2023)

[Voyager: An Open-Ended Embodied Agent with Large Language Models](https://arxiv.org/abs/2305.16291) used a growing library of **executable skills**, environment feedback, iterative prompting and automatic curriculum in Minecraft. **Very relevant:** a reusable skill is an embodied, amortized investment in capability. **Missing:** hereditary competitive ecology or mating/assimilation.

### Survival Games (2025)

[Survival Games: Human-LLM Strategic Showdowns under Severe Resource Scarcity](https://arxiv.org/abs/2505.17937) describes a resource-scarcity simulation for studying LLM strategic/ethical behavior. **Take:** competition and cooperation can be studied under explicitly modeled scarcity. **Limit:** it does not establish long-term self-modifying software evolution.

### OpenLife (June 2026)

[OpenLife: Toward Open-World Artificial Life with Autonomous LLM Agents](https://arxiv.org/abs/2606.31046) proposes persistent, budget-based LLM agents with memory and processes in an open world. **Very relevant:** a 'metabolism' of budgets, autonomy, long-lived identity. The authors explicitly stop short of claiming they have realized life. **Different:** their open-world system is not our closed, controlled, code-inheriting tournament ecology.

## C. Prompt and code evolution

### Promptbreeder (2024)

[Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution](https://proceedings.mlr.press/v235/fernando24a.html) iteratively improves prompts using LLM-generated mutations and a fitness evaluation process. It also evolves the prompts that guide mutations. **Very relevant:** soul/strategy text can evolve and be evaluated without executable code mutation. **Limit:** domain-specific benchmark optimization, not lifelong individual agents.

### Darwin Gödel Machine (2025)

[Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents](https://arxiv.org/abs/2505.22954) and [official code](https://github.com/kew-lab/darwin-godel-machine) iteratively modify a coding agent and empirically test descendants, maintaining an archive. **Very relevant:** validated code variation and improvement feedback. **Limit:** performance is assessed on coding tasks, not society/age/weather/reproduction in an artificial world.

### OpenEvolve (software, 2025 onward)

[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) offers population-based LLM code optimization, island-based search and quality-diversity evaluation. **Relevant:** how to store candidate populations rather than prematurely select one solution. **Limit:** a general optimizer, not a directly transplantable organism or social game.

### EvoAgentX (software)

[EvoAgentX](https://github.com/EvoAgentX/EvoAgentX) provides evolving multi-agent workflows, memory and tool integration. **Relevant:** future evolution of cooperating agent workflows. **Limit:** workflow optimization should not be conflated with biological-style inheritance.

## D. What is genuinely novel or unresolved in *our* design?

The distinctive combination we want to investigate is:

- Agents explicitly **know they are source code plus a prompt** and can study their own genome.
- Individual souls and histories, under a **common, protected life core**.
- Thinking incurs resource costs; learned code can reduce future dependence on an LLM.
- Agents can study competitors' **public code and observable errors**, then ask an LLM how to adapt.
- Victories transfer **virtual tokens** and improve prospects for further mutation or reproduction.
- Competitive manipulation happens largely through **weather and mutable environmental conditions**, not direct corruption of rivals.
- An organism may acquire repair, testing and memory-compression capabilities that become heritable.
- Life definitions themselves may evolve through controlled interfaces, while the referee stays immutable.
- Controlled experiments determine whether hybrid prompt+code organisms improve beyond prompt-only, code-only and non-evolving baselines.

**Do not claim novelty without a dedicated literature review.** Related research is broad and fast-moving. In particular, show the proposal as an experiment in *combining* established ideas, not the first implementation of digital life or LLM evolution.

## E. Experimental lessons from precedents

1. **Measure, don't narrate.** A persuasive agent diary isn't proof of increased competence.
2. **Keep control groups.** Prompt-only, code-only, hybrid, and no-evolution lineages clarify the mechanism.
3. **Test on novel challenges.** Optimizing only the visible arena can produce reward hacking and overfitting.
4. **Record ancestry and cost.** Growth without efficiency may mean only more API expenditure.
5. **Preserve diversity.** Single-winner tournaments can extinguish potentially useful lineages.
6. **Version everything.** Prompts, code, memory summaries, model versions and world seeds should be reconstructible.
7. **Respect sandbox warnings.** Paper implementations often assume experienced operators and should not be run unrestricted on a personal machine.

See [References](docs/REFERENCES.md) for canonical links and [experiment plan](docs/08-roadmap-and-experiments.md) for evaluation design.


---

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


---

# 07 — Proposed programming architecture

**Status:** proposed Python-first implementation. Not a working library or a reviewed security design. Prioritize isolation and measurement before adding fancy ecology.

## 1. Three independently owned systems

```text
                    RESEARCHER / CONFIGURATION
                                |
                     +----------v----------+
                     | ARENA / SUPERVISOR   |
                     | ticks, outcomes, RNG |
                     | health, age, energy  |
                     | spending, lineage    |
                     | immutable audit log  |
                     +-------+-------+-----+
                             |       |
                observations |       | validated actions
                             v       ^
                     +-------+-------+-----+
                     | TRUSTED LIFE CORE    |
                     | context, LLM gateway |
                     | per-agent state I/O  |
                     | candidate staging    |
                     +-------+-------+-----+
                             |       |
                    isolated |       | read-only world view
                  execution  v       ^
                      +------+-------+------+
                      | ORGANISM WORKSPACE  |
                      | soul.md             |
                      | memory/*.jsonl      |
                      | runbooks/*          |
                      | genome/strategy.py  |
                      | genome/tools/*      |
                      | snapshots/*         |
                      +---------------------+
```

The model gateway receives API credentials from a host-side secret store **never mounted into any organism's execution sandbox**. Agent text cannot override cost limits, action validation or the arena's physical laws.

## 2. Proposed repository structure

```text
igor-life/
  README.md
  pyproject.toml
  configs/arena.yaml
  life_core/
    model_gateway.py          # measured calls, spend cap, request boundary
    context_builder.py        # fixed mission + editable soul + observed data
    organism_runtime.py       # choose action, update individual state
    memory.py                 # episodes, summaries, retrieval
    genome.py                 # versioned prompt and code modules
    skills.py                 # discovery of organism-owned modules
    mutation.py               # stage/test/archive candidate mutations
  arena/
    engine.py                 # deterministic event loop
    laws.py                   # immutable rule validation
    economy.py                # double-entry energy ledger
    weather.py                # state machine and effects
    contest.py                # objectively scored competition
    physiology.py             # health and age transitions
    reproduction.py           # later: cloning, mixing, assimilation
    observations.py           # private/public views
  execution/
    sandbox.py                # container process execution only
    validator.py              # contracts + test runner
  organisms/
    001/{soul.md,manifest.json,memory/,runbooks/,genome/}
    002/{soul.md,manifest.json,memory/,runbooks/,genome/}
  experiments/
    baselines.py
    evaluate.py
    heldout_worlds/
  tests/
  outputs/                    # gitignored: JSONL events, trial snapshots
```

We should *not* copy Igor's entire shell platform into the runtime. Igor's module/runbook designs are a useful influence, but the new arena must enforce independent per-organism state and stricter boundaries.

## 3. Agent boundaries and interface contracts

Every agent has a private, immutable `organism_id`, live genome hash, parent IDs, virtual balance, health, age and event cursor. The agent receives a **filtered observation** and returns a single schema-validated intent. Examples are in [`examples/`](examples).

Illustrative contract:

```python
from typing import Protocol, Any

class OrganismStrategy(Protocol):
    def decide(self, observation: dict[str, Any]) -> dict[str, Any]: ...

# Valid intent examples:
# {"action": "wait"}
# {"action": "observe", "target_id": "agent-002"}
# {"action": "compete", "game_id": "task-duel", "stake": 30}
# {"action": "environment_intervention", "effect": "fog", "duration_ticks": 1}
# {"action": "propose_mutation", "candidate_id": "local-commit-ab12"}
```

The proposed v0 strategy may use LLM calls through the trusted `model_gateway` tool or return an action from a deterministic algorithm. **Never let generated code invoke the LLM directly with real credentials.** The gateway meters actual input and output tokens, debits virtual energy and blocks calls past caps.

## 4. Memory model

### Independent layers

- `episodes.jsonl`: immutable per-agent events delivered by the arena.
- `beliefs.json`: organism-authored beliefs with source IDs, timestamps and confidence.
- `soul.md`: compact editable identity or policy context, with version history.
- `runbooks/`: named learned procedures, preconditions, expected benefit and empirical evidence.
- `genome/`: executable strategy and skills, with version hash and compatibility contract.
- `archive/`: older snapshots that the organism may choose to maintain (subject to cost).

Memory cost policy is an experimental parameter: charge for retrieval and LLM context tokens, and optionally charge virtual storage rent. Episodic records are for replay and audit; the agent must not be allowed to edit the referee's evidence.

## 5. Mutations

A mutation request should describe `target` (`soul`, `module`, `runbook`, `memory_policy`), candidate bytes, parent version, reason, test plan and estimated spend. The engine stages files in the organism's private workspace. A separate test worker performs:

1. Static parse / import and path policy validation.
2. Interface / JSON action contract checks.
3. Resource limits and timeouts.
4. Small deterministic smoke tests and parent-versus-candidate trial.
5. Optional agent-authored tests and known regression cases.
6. Snapshot and activation at a tick boundary.

Some validity tests are mandatory for host safety; better survival tests can be evolved and paid for by the organism. Never run agent tests with host authority or inside the supervisor process. A syntax check is insufficient protection.

## 6. World economy implementation

Use an immutable append-only **double-entry** ledger rather than mutable balances written by agents. Every transfer is atomic and balanced, e.g. escrow entry (debit A 30, credit escrow 30), then escrow payout. System mint/burn accounts must be explicit, with event type and rationale. Derive balances from ledger events, with cached materialized views checked against recomputation.

Two other budgets are independent:

- **Token ledger:** actual usage from API response/provider or conservative gateway cap if usage is missing.
- **Financial ledger:** gateway-level estimate/actual billed consumption with a hard real-money threshold and no auto-top-up or unbounded fan-out.

Pricing and model versions should be recorded on every call, not trusted from a static cost table alone.

## 7. The sandbox is a security boundary

Generated code may be accidentally harmful or adversarial. Use a restricted container/VM with:

- Non-root UID, no privileged mode, no Docker socket, no host networking.
- No outbound network by default; LLM requests only through brokered host action.
- Read-only runtime, private copy-on-write genome/workspace, explicit tiny writable scratch area.
- CPU, memory, process count, wall-clock, disk and output size quotas.
- No secrets, cloud metadata, host/home mounts, other organisms' directories or kernel device nodes.
- Denial of syscall/permission elevation routes via a layered sandbox policy.
- Enforced termination on timeout and safe parsing of returned JSON.

**Caveat:** Docker alone is not an infallible hostile-code security boundary. If experiments become adversarial, consider a stronger VM sandbox and expert review. Treat agent-provided prompts and source fragments as untrusted data, including prompt-injection attempts embedded in rivals' public code.

## 8. Event system

Every meaningful transition should produce JSONL event entries containing:

```json
{
  "event_id": "evt-000501",
  "run_id": "run-2026-001",
  "tick": 17,
  "actor_id": "agent-001",
  "type": "mutation_trial_completed",
  "payload": {"candidate_sha256": "...", "success": false, "cost_energy": 24},
  "parent_event_id": "evt-000499",
  "world_seed": 1234
}
```

Archive model parameters, input/output usage, effective prompt hash, code hash, benchmark version, environment conditions and source-provenance IDs. Avoid retaining external provider secrets or unrelated private data in public logs.

## 9. Recommended v0 technology and build order

- Python 3.11+, standard library and simple JSON/SQLite persistence; `pytest` for tests.
- Adapter for one provider or local model; do not build a multi-provider router before basic economics works.
- Separate one-iteration `decide()` from long-running agent chat. Spawn a new isolated process with retained memory between turns.
- One minimal game with a reference deterministic agent, then two LLM organisms.
- First mutate **soul prompts**, then one constrained Python strategy module.
- No distributed workers, Kubernetes, browser integration, email or arbitrary internet access initially.

### First vertical slice acceptance criteria

1. Two agents receive **different filtered observations** and submit valid independent actions.
2. A scored match transfers the correct virtual tokens once, under retries and process crashes.
3. Model gateway refuses further calls at a configured cap.
4. A bad code candidate is rejected/penalized without crashing world or affecting another agent.
5. A valid candidate persists across restart and can be reverted through explicit lineage.
6. Every state transition can be replayed from logs and model artifacts (allowing for recorded LLM nondeterminism).

## 10. What not to build initially

Browser agents, language migration across runtimes, arbitrary on-the-fly physics code, direct edit of opponent files, unrestricted system administrators, free-form internet access, parallel multi-region economies or agent-written evaluator rules. These can all obscure whether the basic learning/evolution mechanism actually works.


---

# 08 — Roadmap, feasibility, risks and experimental evaluation

## 1. Research objectives, in order

**Primary question:** Does giving an agent the ability to rewrite its prompt *and* develop reusable code produce better measured performance per actual model token than prompt-only evolution?

**Secondary questions:** Do public rival observations help? Does environmental manipulation reward anticipation? Can good testing/recovery strategies emerge under a survival budget? Does offspring inheritance retain progress? Does diversity persist?

These are hypotheses, **not outcomes**.

## 2. Milestones and explicit gates

| Stage | Build | Required evidence to continue |
|---|---|---|
| **M0: Sim-only** | Referee, ledger, weather and deterministic reference policies; zero LLM | Correct economics, deterministic tests and replay |
| **M1: Prompt organisms** | Two–four souls, memory, observations, gateway, one competitive game | Agents act autonomously, token caps work, events reproducible |
| **M2: Hybrid mutation** | One isolated Python module, candidate testing and rollback | Valid candidate can improve benchmark; invalid candidate cannot damage host/world |
| **M3: Social & weather** | Public code exposure, rival analysis, priced drought/fog | Agents can adapt to environmental shifts without breaking invariants |
| **M4: Heredity** | Cloning, selected memory inheritance, parent→child resource split | Parentage/recombination and capital conservation are correct |
| **M5: Advanced ecology** | Aging, serious illness, mating, assimilation and optional novel declarative weather | Meaningful experimental advantage over simpler worlds; acceptable cost |

**Stop rule:** do not add features to mask a failure at an earlier gate. A simpler honest simulation is preferable to a feature-rich but scientifically unreadable one.

## 3. The minimum meaningful controlled experiment

Use one task arena with hidden task instances and seeded conditions. Start with **the same trusted core and the same initial executable strategy**; vary souls using a fixed documented seed. Duplicate the population into treatment groups with equivalent starting budget.

| Group | Can edit soul? | Can edit code? | Can inspect rivals? |
|---|---|---|---|
| Control | No | No | Observes public results only |
| P: prompt-only | Yes | No | Same public results |
| C: code-only | No | Yes | Same public results |
| H: hybrid | Yes | Yes | Same public results |
| H+social | Yes | Yes | Paid public-code inspection |

Run with the same weather schedule and opportunities where possible. Later randomize weather and introduce environmental interventions. Use multiple random seeds and enough repeated matches to estimate uncertainty, instead of reporting one winning lineage.

## 4. What to measure

### Useful performance

- **Held-out score** (unseen opponents/tasks) at the same evaluation budget.
- **Energy efficiency:** verified reward or correct tasks per 1,000 **actual** LLM tokens, plus CPU/runtime cost.
- **Survival:** duration active under given resources; distinguish healthy activity from idle survival.
- **Skill reuse:** actions completed using inherited/deterministic code without LLM calls.

### Evolution and inheritance

- Parent→offspring gain under the **same** starting balance and difficulty.
- Diversity of executable strategies (behavioral profiles and code hashes, not just different names).
- Mutation success/regression rate, test cost, rollback rate and repeated failures.
- Genotype changes correlated with success across independent worlds.

### Social/ecological effects

- Gains from studying competitors' published code and publicly visible mistakes.
- Relative fitness after drought/fog/storm vs normal conditions.
- Cost and net return on purchased environmental interventions.
- Resource inequality, population collapse, cooperative trades and frequency of extinction.

### Reliability / reproducibility

- Model/API tokens per turn, billed costs, failed calls, truncated contexts.
- Percentage of valid action JSON responses and benchmark replays.
- Validation failures, crashes, sandbox termination and policy violations.
- Integrity checks on ledger, genealogy and event-stream replay.

## 5. Confounders and failure modes

| Risk | How it can mislead us | Required countermeasure |
|---|---|---|
| Rich-get-richer | Early luck creates unstoppable capital advantage | Start-budget normalization; compare agent at equal capital |
| Reward hacking | Exploits game implementation rather than useful ability | Held-out tasks, independent scorer, negative tests |
| Inconsistent judge | LLM referee changes standards | Deterministic scoring whenever possible |
| Model upgrade | Provider changes model over generations | Log model ID/version; pin where possible |
| More thinking = higher score | Hybrid may simply spend more | Equal actual token/cost conditions and efficiency metrics |
| Hidden intervention effects | World change accidentally benefits sponsor only | Public rules and effect logs; self-applied effects |
| Bad code crashes | False 'death' from environment defect | Sandbox/run tests; distinguish host failure vs game defeat |
| Prompt injection | Rival's published code tries to override core instructions | Trust separation; sanitize tool outputs; no credentials in runtime |
| Overcomplexity | Hard to determine which feature helped | Ablations; release gates; small module boundaries |
| Species monoculture | One lineage eliminates all alternatives | Independent populations and quality-diversity analyses |

## 6. Budgets and pragmatic feasibility

Begin with deterministic M0 tests **without calling any LLM**. Then choose a hard real spend ceiling (e.g. €5–€10 for a small first research run), separately from virtual energy. A gateway can enforce maximum per-request tokens, aggregate real-budget allowances, concurrency and call counts; a provider-side account ceiling is an additional defense.

A very small LLM budget may support only dozens to hundreds of useful deliberations depending on model, prompt length, test feedback and model pricing. Do not promise a specific generation count. Estimate cost from measured runs; track input and output tokens separately.

Development estimates discussed earlier (several weeks for a small ecosystem, several months for reliable code-evolving populations) are **order-of-magnitude guesses for an experienced solo developer**. They are not confidence-calibrated probabilities or independently validated schedules. A scientific claim of sustained open-ended improvement has no credible completion estimate.

## 7. Engineering tasks for M0 / M1

- [ ] World rules schema and deterministic reducer.
- [ ] Separate secret-free organism workspaces and identities.
- [ ] Immutable virtual token ledger with invariant tests.
- [ ] A measurable game with non-LLM reference agents.
- [ ] Weather update and one bounded environmental intervention.
- [ ] Action schema, invalid-action penalties and event log.
- [ ] LLM gateway with real usage measurement, concurrency and spend cap.
- [ ] Soul prompt, episode memory and optional reflection.
- [ ] Two-agent match that persists state across process restarts.
- [ ] Frozen evaluation task set and separate hidden test set.

## 8. Engineering tasks for M2

- [ ] One tiny, safe, fixed contract for a mutable Python strategy module.
- [ ] Per-organism snapshots and candidate hashes.
- [ ] Isolated worker with hard CPU/memory/time/output limits.
- [ ] Static parser, import checks and schema tests.
- [ ] A repeatable trial comparing candidate against parent.
- [ ] Mutation transaction with activation at tick boundary.
- [ ] Observation logs the agent can cite when explaining an improvement.
- [ ] No leaked secrets, privileged mounts or unrestricted network.

## 9. Possible initial research outcomes

1. **No meaningful evolution:** prompts change, but held-out performance remains flat. Interesting negative result; revisit incentives and task diversity.
2. **Prompt-only wins:** code writing/maintenance isn't economically worthwhile in this world; change task recurrence and compare.
3. **Hybrid wins:** measured efficiency rises because executable skills amortize LLM costs; confirm against baselines and matched budgets.
4. **Population collapse:** resource inflow/upkeep mismatch; learn about economics before adding biologically inspired mechanics.
5. **Environmental arms race:** interventions shift advantages back and forth; test whether this creates innovation or merely wasted energy.

**Success for v0 is a trustworthy, replayable experiment—not spectacular artificial intelligence.**


---

# 09 — Decision log and open questions

Document purpose: prevent the project from drifting and preserve why an option was chosen. These are **discussion-derived preferences**, not irrevocable decisions.

## Decision record

| ID | Direction | Status | Reason |
|---|---|---|---|
| D-01 | Use a **hybrid of mutable prompts and tested executable code** | Preferred | Lower entry cost of prompt edits + long-term efficiency of code |
| D-02 | Soul = an initial, heritable, **editable persona prompt** | Preferred | Individuality without pretending to model consciousness |
| D-03 | Life mission/world rules are distinct from the soul | Preferred | Everyone understands the same arena but may have different identities |
| D-04 | Start from **one shared protected player core** | Preferred | Shared interfaces and simpler reproduction/testing |
| D-05 | Python for referee and life core; Bash/Python skills optional | Preferred | Ecosystem support; integrates lessons from existing agents |
| D-06 | Keep prompt/code/memory versioned **per organism** | Preferred | Makes evolution and lineage measurable |
| D-07 | Competition moves **virtual tokens** from loser to winner | Preferred | Scarcity gives strategic meaning to thought and growth |
| D-08 | Prefer **environmental engineering** to directly editing rival code | Preferred | Richer indirect competition, simpler isolation |
| D-09 | Allow organisms to inspect public behavior and published code | Preferred | Social learning and imitation without privileged read access |
| D-10 | Add inheritance, mixing and assimilation after basic mutation | Sequenced | Arbitrary program recombination is difficult |
| D-11 | Health, age, recovery and death form simulated lifecycle | Tentative | Interesting evolutionary effects, but not required for first test |
| D-12 | Agents may evolve their own memory/repair/metabolism strategies **inside contracts** | Preferred | Preserve the more open-ended 'option B' direction |
| D-13 | The referee's accounting, API keys, immutable rules and sandbox boundaries are never editable by organisms | Hard constraint | Integrity, safety and meaningful measurement |
| D-14 | Reuse concepts from Igor/nanobot/Letta/DGM rather than merge full repositories | Recommended | Avoid accidental monolith and incompatible abstractions |
| D-15 | Validate actual improvement using held-out tests and matched spend | Hard scientific constraint | Protect against luck and reward hacking |

## Open design questions with first-pass recommendations

**O-01 — What is the first game?**  
*Recommendation:* an objectively scored, low-cost task duel plus reference deterministic agents. Avoid subjective LLM judges in v0.

**O-02 — Must organisms keep thinking continuously?**  
*Recommendation:* no. Choosing cheap deterministic actions or waiting is legitimate, but maintenance costs and limited opportunities prevent infinite idling from counting as success.

**O-03 — What counts as a virtual token?**  
*Recommendation:* create a unit called **energy**, distinct from actual provider tokens; use a priced conversion rule based on measured API use.

**O-04 — How much of a rival is visible?**  
*Recommendation:* public scores, actions and opt-in published modules; paid inspect for additional public detail. Private data stays private.

**O-05 — How much mutability in the 'laws of life'?**  
*Recommendation:* allow genome-owned physiology strategies and declarative environment proposals, not direct edits to supervisor source or billing.

**O-06 — What is inherited?**  
*Recommendation:* active tested modules, soul prompt, selected summaries, runbooks and small funded resources; parent provenance explicit.

**O-07 — Can a dead organism's code be assimilated?**  
*Recommendation:* only previously public/escrowed abilities until there is a well-defined privacy and loot contract.

**O-08 — Should weather be controlled or random?**  
*Recommendation:* partially stochastic with known parameters and fixed seeds for fair evaluation; interventions are bounded and observable.

**O-09 — Is there a population cap?**  
*Recommendation:* yes, initially very small (2–4) and enforce a total simultaneous model-call cap.

**O-10 — How is age modeled?**  
*Recommendation:* count chronological ticks and computational usage; introduce biological costs only after simpler dynamics work.

**O-11 — Are all organisms initially related?**  
*Recommendation:* common core and code interface, different soul prompts in first experiment; multiple ancestral genome architectures in a later ablation.

**O-12 — May the organism choose its model?**  
*Recommendation:* begin with a single model for scientific comparability; later add bounded model selection at explicit energy prices.

**O-13 — What do we import from existing projects?**  
*Recommendation:* audit nanobot and mini-SWE-agent against a tiny custom core. Borrow Igor runbooks and Letta-style memory layout; investigate DGM/OpenEvolve for candidate testing when needed.

**O-14 — How should illnesses affect code?**  
*Recommendation:* start with simulated constraints and costs, not random corruption of generated source. Physical code degradation may add noise without insight.

**O-15 — What proves the experiment has value?**  
*Recommendation:* descendants outperform parents and baselines on independent conditions **at matched actual token and energy budgets**, ideally across multiple seeds.

## Deferred concepts (do not silently reintroduce into v0)

- Direct write access to opponents' strategy/core files.
- Exposure of real API credentials as a result of in-world illness or defeat.
- Arbitrary agent-authored executable changes to the referee.
- Full desktop/browser/host shell control for every organism.
- Unlimited reproduction and unrestricted real-world spending.
- Automatic code recombination without interface validation.
- Claims that soul prompts create actual emotion or consciousness.

## How to update this log

For any design change, add a short entry containing date, owner, alternatives considered, decision, costs/tradeoffs, tests needed and whether it modifies the immutable experiment boundary. Keep design hypotheses separate from implemented behavior, and executed test results separate from expected outcomes.


---

# References and source links

**Checked for this document set:** 11 October 2026. These links establish projects' stated capabilities and the existence of published experiments. They are not proof of interoperability with Igor Life.

## Software projects

1. **Igor** — repository and README: https://github.com/pedante/igor_core ; module loader: https://github.com/pedante/igor_core/blob/master/core/lib/module_loader.sh ; runbook generator: https://github.com/pedante/igor_core/blob/master/core/lib/runbook_gen.py ; healing: https://github.com/pedante/igor_core/blob/master/core/healing/core.sh
2. **nanobot (HKUDS)** — https://github.com/HKUDS/nanobot ; project metadata/license: https://github.com/HKUDS/nanobot/blob/main/pyproject.toml
3. **mini-SWE-agent** — https://github.com/SWE-agent/mini-swe-agent ; MIT license: https://github.com/SWE-agent/mini-swe-agent/blob/main/LICENSE.md
4. **Agent Zero** — https://github.com/agent0ai/agent-zero ; MIT license: https://github.com/agent0ai/agent-zero/blob/main/LICENSE
5. **Letta Code** — https://github.com/letta-ai/letta-code ; memory filesystem: https://github.com/letta-ai/letta-code/blob/main/src/agent/prompts/letta_local_memfs.md ; legacy/current distinction: https://github.com/letta-ai/letta
6. **Letta Agent SDK** — https://github.com/letta-ai/letta-agent-sdk
7. **Hugging Face smolagents** — https://github.com/huggingface/smolagents ; https://huggingface.co/docs/smolagents/index
8. **Darwin Gödel Machine (official implementation)** — https://github.com/kew-lab/darwin-godel-machine
9. **OpenEvolve** — https://github.com/algorithmicsuperintelligence/openevolve
10. **EvoAgentX** — https://github.com/EvoAgentX/EvoAgentX
11. **Avida** — https://avida.devosoft.org/

## Research literature

12. **Generative Agents: Interactive Simulacra of Human Behavior** — Park et al., 2023, UIST. https://doi.org/10.1145/3586183.3606763
13. **Voyager: An Open-Ended Embodied Agent with Large Language Models** — Wang et al., 2023. https://arxiv.org/abs/2305.16291
14. **Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution** — Fernando et al., ICML 2024. https://proceedings.mlr.press/v235/fernando24a.html
15. **Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents** — Zhang et al., 2025. https://arxiv.org/abs/2505.22954
16. **Avida: A Software Platform for Research in Computational Evolutionary Biology** — Ofria & Wilke, 2004; open version: https://pmc.ncbi.nlm.nih.gov/articles/PMC7115006/
17. **Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction** — Agüera y Arcas et al., 2024. https://arxiv.org/abs/2406.19108
18. **Survival Games: Human-LLM Strategic Showdowns under Severe Resource Scarcity** — Chen et al., 2025. https://arxiv.org/abs/2505.17937
19. **OpenLife: Toward Open-World Artificial Life with Autonomous LLM Agents** — Masumori et al., June 2026. https://arxiv.org/abs/2606.31046
20. **OpenEvolve research implementation** — software repository: https://github.com/algorithmicsuperintelligence/openevolve

## Usage and epistemic notes

- Preprints (arXiv) may not be peer reviewed; source claims about improvements are those of authors unless independently replicated.
- Open-source project descriptions can change, and a Github README is not evidence of measured performance on *our* tasks.
- The existing projects were **studied for feasibility**, not benchmarked against each other or audited for security.
- Check current licenses and dependency notices at the pinned commit before importing material. The project docs here are original design summaries, not copies of external source code.
- The system's success rates, timelines and token costs cannot be reliably inferred from the literature without our own prototype data.
