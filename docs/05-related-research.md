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
