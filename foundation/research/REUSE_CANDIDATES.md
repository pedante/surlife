# Existing life agents, evolution engines and arenas — reuse shortlist

**Research snapshot:** 2026-10-11. **Status:** sources/README and many top-level LICENSE files inspected; no candidate has been installed, tested, security-audited or proven compatible with Surlife. This is a research backlog, **not** an implementation selection or a change to the frozen iteration 0001 proposal.

**Question:** What existing software lets us *avoid reimplementing* the arena, agent loop, evaluation, memory and evolution **without surrendering the trusted referee and reproducible economics**?

See [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) for repeatable evidence gates and [CANDIDATES.json](CANDIDATES.json) for machine-readable entries. Historical agent-only comparison: [../../docs/03-agent-frameworks.md](../../docs/03-agent-frameworks.md).

## Selection principles

1. Evaluate **adoption of a whole component** against **a small adapter** against **fresh minimal code**. The winner is the least total complexity, not the most features.
2. Favor Python, strict action/observation schemas, seeded deterministic tests, reusable objective scorers, offline testing and few dependencies.
3. Keep **one outside-the-organism referee**, ledger, true usage gateway, secrets and isolation. No candidate's built-in scoring, console, shell or LLM game master is automatically trustworthy.
4. Separate source availability from licensing: MIT/Apache/GPL have obligations; repo assets, models and dependency licenses may differ; **unknown or noncommercial means no copying without explicit clearance**.
5. Agent diaries, apparent autonomy and general intelligence claims are not results. Measure improved held-out work per *actual* model tokens at matched budgets.

## First evaluation batch (recommended, not yet approved)

- **Arena interface:** W02 PettingZoo versus 100–300 lines of bespoke two-agent API. Verify that its wrapper can preserve deterministic replay and exact accounting.
- **Simple arena options:** W03 OpenSpiel (objective duels), W04 MiniGrid (small held-out tasks), W01 Mesa (ecology/scheduling), W05 Crafter (true survival). **Pick one objective M0 slice**, not all four.
- **Brain options:** G01 mini-SWE-agent versus G02 nanobot versus a tiny self-contained mockable loop. Never expose their normal shell/chat tools.
- **Evolution option for M2 only:** G04 Darwin Gödel Machine archive/evaluator versus G05 OpenEvolve versus a minimal 3-candidate archive.
- **Methodology cross-check:** W13 Avida for hereditary evolution experiments; W08 Melting Pot for held-out social generalization; they are not obvious M0 dependencies.

## Curated candidates

**Priority**: P0 = first comparison; P0-M2 = only when M2 begins; P1 = second comparison/optional future; P2 = study/defer; P1-study / P2-study = methods-only until viability/license clears. Priority is a *hypothesis*, not a quality score.

| ID | Project / role | Priority | License (initial reading) | Reusable piece | First discriminating probe | Main blocker |
|---|---|---|---|---|---|---|
| W01 | [Mesa](https://github.com/mesa/mesa) · arena substrate | P0 | Apache-2.0 | Python agent scheduler, grids, deterministic model experiments | Run seeded 2-agent zero-LLM model; compare with tiny custom loop | Scheduling/event ordering and replay must be verified |
| W02 | [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) · arena interface | P0 | MIT | Standard multi-agent reset/step/action/observation contract | Wrap minimal Surlife duel with AEC or Parallel API and run API tests | API is not an economy, referee, or event ledger |
| W03 | [OpenSpiel](https://github.com/google-deepmind/open_spiel) · game library | P0 | Apache-2.0 | Objective two-player games, simple baseline policies, evaluation | Run a simple turn game with two deterministic policies and compare scoring | C++/Python build complexity; game rewards are not virtual energy |
| W04 | [Minigrid](https://github.com/Farama-Foundation/Minigrid) · task arena | P0 | MIT | Small seeded puzzles and held-out configurations | Seeded goal/key-door trial; compare 2 simple policies on held-out maps | Single-agent by default; would need duel wrapper |
| W05 | [Crafter](https://github.com/danijar/crafter) · survival arena | P0 | MIT | Lightweight 2D survival, hunger/resources and achievement scoring | Smoke test scripted agent across seeds, measure time/achievements | More world complexity than M0; image/action translation for LLM |
| W06 | [MAgent2](https://github.com/Farama-Foundation/MAgent2) · many-agent arena | P1 | MIT | Competitive grid world and PettingZoo-compatible examples | Run reference environment with simple policies and reproduce scores | Designed for many agents; may overcomplicate two-organism M0 |
| W07 | [Neural MMO](https://github.com/NeuralMMO/environment) · survival ecology | P1 | MIT | Resource competition, survival tasks and scripted baselines | Test smallest world and scripted policy without model calls | Large RL-oriented stack and environment assumptions; check pinned 2.1 branch |
| W08 | [Melting Pot](https://github.com/google-deepmind/meltingpot) · social benchmark | P1 | Apache-2.0 | Existing cooperation/competition substrates and held-out social scenarios | Reuse a tiny substrate or benchmark only; check reproducibility | DeepMind Lab2D, TensorFlow/assets build and complexity |
| W09 | [Concordia](https://github.com/google-deepmind/concordia) · LLM social arena | P1 | Apache-2.0 | Game-master/referee pattern, scenarios and social memory | Mock model interface and inspect how GM authority is separated | LLM adjudication is unsuitable for an objective money/ledger referee |
| W10 | [AgentSociety 2](https://github.com/tsinghua-fib-lab/AgentSociety) · LLM social simulation | P1 | Apache-2.0 EXCEPT commercial subtree | Persistent agent workspaces, flexible environments, replay traces | Run smallest local example without network; inspect workspace boundaries | Ray/service stack; never copy commercial directory without rights |
| W11 | [Sotopia](https://github.com/sotopia-lab/sotopia) · social evaluation | P1 | MIT | Multi-agent social scenarios, evaluation pipeline, local JSON backend | Try two-agent scenario with mocked evaluator and local storage | Subjective LLM graders cannot serve as trusted objective scorer |
| W12 | [AI Town](https://github.com/a16z-infra/ai-town) · persistent virtual society | P2 | MIT (code; review assets separately) | Persistent characters, events, world state and visualization | Inspect event flow and memory schema, no external deployment | TypeScript, Convex service, visual assets and service complexity |
| W13 | [Avida](https://github.com/devosoft/avida) · digital evolution laboratory | P1-study | UNVERIFIED: no top-level license found | Inheritable programs, mutation, evolution experiment controls | Review mutation/fitness/replay method on small documented experiment | C++ and submodules; confirm license before code reuse |
| W14 | [ASAL](https://github.com/SakanaAI/asal) · artificial life search | P2 | Apache-2.0 | Search and novelty metrics for life-like dynamics | Review metrics for novelty without embedding JAX/GPU workloads | Optimizes cellular life substrates, not LLM organisms |
| W15 | [Lenia](https://github.com/Chakazul/Lenia) · cellular artificial life | P2 | MIT | Ecological dynamics and possible future weather/visual world | Run simple CPU pattern offline if needed for secondary experiment | Continuous automata mismatch current objective game |
| W16 | [Genesis Engine](https://github.com/teknium1/genesis-engine) · experimental life substrate | P2 | MIT | Browser metabolism, mass conservation, evolvable genome concepts | Inspect accounting invariants and minimal seeded run | New/small WebGL2 experiment; claims not independently checked |
| W17 | [AgentVerse](https://github.com/OpenBMB/AgentVerse) · LLM simulation framework | P2 | Apache-2.0 | Prisoner's dilemma and other agent interaction scenarios | Inspect release-0.1 simulation branch and run deterministic mock | README says simulation framework being refactored |
| W18 | [OpenLife](https://arxiv.org/abs/2606.31046) · paper-only precedent | P2-study | NO VERIFIED OFFICIAL CODE/LICENSE | Budget-metabolism, persistent autonomous processes and identities | Record paper methods and request official implementation if one exists | Open-world payments/network access conflict with Surlife safety model |
| G01 | [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) · minimal agent loop | P0 | MIT | Compact model→action→feedback loop | Replace shell with strict JSON world actions; mock LLM and count calls | Default shell access must never reach referee/host |
| G02 | [nanobot](https://github.com/HKUDS/nanobot) · light agent core | P0 | MIT | Python model adapters, tools, prompt and memory loop | Extract smallest loop into mocked arena adapter; compare LOC/dependencies | Assistant tools and channels add unnecessary authority |
| G03 | [Voyager](https://github.com/MineDojo/Voyager) · lifelong skills | P1 | MIT (source; Minecraft separate) | Versioned executable skill library, iterative test/fix cycle | Study standalone skill index; verify one reusable non-Minecraft skill | Full Minecraft/Node integration inappropriate for M0 |
| G04 | [Darwin Gödel Machine](https://github.com/kew-lab/darwin-godel-machine) · code mutation | P0-M2 | Apache-2.0 | Candidate lineage archive and test-driven self-rewrite | Extract archive + evaluator protocol; simulate three mock mutations | Generated code must run outside referee with no credentials |
| G05 | [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) · code evolution | P0-M2 | Apache-2.0 | Mutation archive, evaluator, quality/diversity | Test deterministic toy function optimizer, no paid model | Full optimization pipeline may outweigh tiny M2 experiment |
| G06 | [Agent Zero](https://github.com/agent0ai/agent-zero) · tool-writing agent | P2 | MIT | Tools, durable projects, editable prompts, self-built abilities | Study tool registration and repair-loop interfaces | Desktop, Docker, shell and browsing features overly broad |
| G07 | [Letta Code](https://github.com/letta-ai/letta-code) · editable memory/identity | P1 | Apache-2.0 | Persistent versioned memory blocks and identity | Compare file/SQLite memo versioning with relevant architecture | TypeScript/full harness makes Python integration costly |
| G08 | [Generative Agents / Smallville](https://github.com/joonspk-research/generative_agents) · agent society | P1 | Apache-2.0 | Observation→memory→reflection→plans in simulated town | Inspect memory retrieval and fake-model simulation | No mutation/evolution; heavyweight prompt/memory token load |
| G09 | [EMAS](https://github.com/FrogSnot/EMAS) · evolving prompt agents | P2-study | PolyForm Noncommercial 1.0.0 | Prompt genotype, crossover/mutation and team selection | Study documentation only pending legal review | Noncommercial license prohibits treating as freely reusable open source |
| G10 | [AgentScope](https://github.com/agentscope-ai/agentscope) · LLM agent infrastructure | P2 | Apache-2.0 | Agent orchestration, tracing and model routing | Mock 2-agent exchange and instrument actual model usage | General-purpose orchestration is not an evolution arena |
| G11 | [Igor](https://github.com/pedante/igor_core) · local prior art | P1-study | GPL-3.0 claimed in README; verify per file | Runbooks, module contracts, diagnostics, rollback and model cost patterns | Trusted sysadmin shell components are unsafe for organism execution | undefined |

## Specific integration opportunities to test

**M0**, without any LLM: test `PettingZoo + OpenSpiel`, `PettingZoo + MAgent2`, `Mesa`, and *a minimal hand-written Python referee* on the same narrowly defined rules if straightforward. In all variants Surlife must own the atomic virtual ledger, world interventions, retry idempotency, seed and event hash. A candidate's reward is **data**, never authorization to mint/transfer energy.

**M1**, with tightly metered model calls: attempt **one** `LifeCore` adapter with two separate prompt/memory stores and a fake-model fixture first. Compare mini-SWE-agent, nanobot and in-house implementation on dependency surface, reliable action parsing, actual usage reporting, secrets isolation and ability to survive a restart. Concordia/AgentSociety/Smallville provide design patterns, not evidence their referee is safe.

**M2**, code mutation: borrow lineage/fitness conventions from DGM/OpenEvolve/Voyager, but only use a worker that cannot reach secrets, network, opponents or supervisor. Candidate code is untrusted; passing import/syntax tests is not isolation.

## Explicit exclusions and caveats

- **OpenLife (W18)** is a *published open-world experiment*; no official reusable source or license verified in this snapshot. Do not substitute a third-party project with a similar name for its implementation.
- **EMAS (G09)** source is licensed **PolyForm Noncommercial 1.0.0** at inspection time; keep as intellectual precedent unless compatible rights are established.
- **Avida (W13)** top-level and `avida-core/` did not expose a `LICENSE` at the paths inspected. License is unresolved, even though the source is public.
- **AgentSociety 2 (W10)** explicitly excludes a `commercial` subtree from its Apache-2.0 statement.
- **AI Town, Voyager and Neural MMO** may depend on assets/services/game distributions with terms distinct from code licenses. Inspect transitive obligations before packaging.
- **Neural MMO**: use `NeuralMMO/environment`, not the archived early `openai/neural-mmo` tree.
- **Versioning:** current branch names are entry points, not pins. For every evaluated candidate record commit SHA, resolved dependency lock and license notices. Don't treat today's README as a stable API.
- The broader list in `docs/03-agent-frameworks.md` remains valid background; repeated entries here are intentional so arena candidates and brains can be tested in one decision process.

## Falsifiable recommendation

Do **not** choose a new arena solely because it already looks alive. Compare at least two *existing* candidate components with the minimal custom M0 baseline. If none passes replay + ledger + isolation + simplicity gates, retain the custom core while importing only tests, patterns, datasets or APIs. If one *does* pass and saves meaningful maintenance, adopt the smallest defensible part and write a decision record after human review.

**No code, packages, API keys or game servers have been run during this inventory.**
