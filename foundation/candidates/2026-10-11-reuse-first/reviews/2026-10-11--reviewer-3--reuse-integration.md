# R1-R3 — Independent Software Reuse and Integration Review

**Executive verdict: REVISE R1.** Keep its small authoritative Python/SQLite referee, separately metered LLM gateway, versioned genomes and hard hostile-code boundary. Reject any presumption that mini-SWE-agent should be the first *routine* organism reasoning engine: a one-intent native runner is the simpler baseline. Reuse mini-SWE for code mutation **if** its isolated coding worker beats that baseline; test GEPA as a separate offline prompt evolution engine, OpenSpiel for objective game benchmarks, PettingZoo as an optional multi-agent API, Mesa for larger ecologies and Inspect AI for external research evaluation.

**Reviewer:** GPT-6 / OpenAI. **Review date:** 2026-10-11. **Perspective:** independent senior open-source architect, software integrator and agent/evolution framework researcher. **Proposal:** PR #4, R1 at `foundation/candidates/2026-10-11-reuse-first/PROPOSAL.md`. **Exact proposal commit reviewed:** `8b4a23d23db30adaa5b3008ad419089cf7697735`. **Not** the older `foundation/PLAN.md`.

**Review inputs:** repository `AGENTS.md`, `foundation/AGENTS.md`, `foundation/CONTEXT.md`, `foundation/RUBRIC.md`, `foundation/REVIEW_PROTOCOL.md`, reviewer prompt/template, all R1 candidate proposal/tradeoff/handoff files, original `docs/01`–`09` and [unmerged PR #1](https://github.com/pedante/surlife/pull/1), [PR #2](https://github.com/pedante/surlife/pull/2), [PR #3](https://github.com/pedante/surlife/pull/3). **Independence:** did **not** open or read Reviewers 1/2 or any other review of R1; R1's author handoff is contextual proposal documentation, not a critique.

**Evidence levels:** [V] verified by inspected upstream source/documents; [J] engineering judgment, **not** measured; [U] unresolved. No library was installed/executed, no benchmark or penetration test run, no model money spent. Repository pushes are only activity indicators, not proof of stable maintenance. Initial license declarations do not establish file-by-file redistribution rights.

## 1. Most consequential findings

**R3-F01 — MAJOR: R1 overprivileges mini-SWE for normal cognition.** R1 `0, `2, `4 and decision C-R2 propose an adapted mini-SWE-compatible daily loop. [V] Its [DefaultAgent](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/agents/default.py) calls `run → step → query → execute_actions`, with actions delegated to `env.execute`; [LitellmModel](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/models/litellm_model.py) uses shell-oriented `BASH_TOOL` parsing. [LocalEnvironment](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/environments/local.py) runs host shell subprocesses and includes environment values. [pyproject.toml](https://github.com/SWE-agent/mini-swe-agent/blob/main/pyproject.toml) pulls LiteLLM, Pydantic, Jinja2, CLI and other dependencies. Its model cost is updated after invocation, not a guaranteed pre-call allowance. [J] A one-action world interface needs replacement of its multi-action parser, terminal signal, call boundary, context assembly and cost policy; little distinctive reusable agent loop may remain. **Recommendation:** native fake-model one-turn M1 runner; mini-SWE inside a sealed M2 code author when it can actually edit source safely. **Falsifier:** a public-extension-point mini-SWE adapter safely emits exactly one intent and demonstrably has lower *total maintained adapter + dependency* complexity than the native runner.

**R3-F02 — MAJOR: referee necessity is narrower than simulator ownership.** [V] [PettingZoo ParallelEnv](https://github.com/Farama-Foundation/PettingZoo/blob/main/pettingzoo/utils/env.py) has the reset/step multiagent API and [parallel_api_test](https://github.com/Farama-Foundation/PettingZoo/blob/main/pettingzoo/test/parallel_test.py), but not a money ledger or inheritance. [Mesa Model](https://github.com/mesa/mesa/blob/main/mesa/model.py) and [EventList](https://github.com/mesa/mesa/blob/main/mesa/time/events.py) support event scheduling and agents; its inspected main is moving, so pin a suitable release. [OpenSpiel evaluate_bots](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/evaluate_bots.py) handles turn, chance and simultaneous games through compiled pyspiel. [J] Two organisms and one scheduled tick justify a tiny native reducer. PettingZoo can be an *outward adapter*, Mesa may replace substantial scheduling only in larger worlds, and OpenSpiel avoids writing bespoke challenge games without becoming the ecological referee. **Falsifier:** equivalent fixed-seed Mesa/PettingZoo prototype demonstrably eliminates more tested, trusted Surlife code than its new integration creates.

**R3-F03 — MAJOR: study component-level optimization, not giant agent stacks.** New high-value candidate [GEPA](https://github.com/gepa-ai/gepa), specifically [GEPAAdapter/EvaluationBatch](https://github.com/gepa-ai/gepa/blob/main/src/gepa/core/adapter.py) and [optimize](https://github.com/gepa-ai/gepa/blob/main/src/gepa/api.py), evolves text/prompt components under external evaluation. Its inspected [pyproject.toml](https://github.com/gepa-ai/gepa/blob/main/pyproject.toml) declares MIT, Python and no mandatory base package dependencies. **Adapt offline** to prompt mutation using train/validation and a second *physically separate* final holdout. It does not replace organism autonomy or billing. [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) offers an [evaluation runner](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/_eval/eval.py) and scorers, potentially replacing experiment scaffolding outside the world. Standard pytest is initially enough.

**R3-B01 — BLOCKER: hostile generated code.** R1 ``2, 4, 7, 9. The referee must never import or execute organism source. A process, default container, OpenEvolve evaluator or agent runner is not adequate isolation merely by itself. Until independent OS/VM confinement (no credentials, network, host/peer mounts, quotas and adversarial tests) exists, **M2 remains design-only**.

**R3-B02 — BLOCKER: real-money usage.** R1 ``4, 6. Framework step/cost counters cannot authorize API spending. Trusted pre-call conservative budget reservation, provider output bound, retry/concurrency cap and reconciliation are mandatory; unknown usage must be recorded rather than claimed as exact provider billing.

**R3-B03 — BLOCKER: rights.** [Descartes package.json](https://github.com/Lightless-Labs/descartes/blob/main/package.json) explicitly says **UNLICENSED**. Public source does not grant copying. Avida's effective license remains unverified. Asset/model/commercial subtree and transitive grants need audit before code reuse.

**R3-B04 — BLOCKER: hidden evaluation.** No generated organism code, prompt optimizer or agent can access sealed final tests or detailed answer-revealing feedback. A callback to a framework evaluator is not itself a privacy/information barrier.

**R3-F04 — MAJOR: future architecture restriction.** R1 `3 `StrategyV1.decide(observation, public_memory)` and many speculative policy subclasses unnecessarily couple privacy, Python type choices and future organism cognition. Stable **versioned wire envelopes** plus an open capability manifest preserve evolution better than prematurely inventing physiology/reproduction APIs.

## 2. Top ten ways not to reinvent infrastructure

| # | Reuse | Eliminates / does not eliminate | Verdict |
|---:|---|---|---|
| 1 | Python `sqlite3` transactions/UNIQUE, `hashlib` | Custom broker, ledger persistence; **not** world-law logic | **A adopt + D rules** |
| 2 | [pytest](https://github.com/pytest-dev/pytest), [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | Test/property framework, not scientific hypothesis | **A adopt** |
| 3 | One official provider SDK | Auth/transport/usage parsing, not pre-call financial authority | **A SDK + D gateway** |
| 4 | GEPA `GEPAAdapter` | Text/prompt evolutionary optimizer, not economy | **B offline if useful** |
| 5 | mini-SWE `DefaultAgent` | Coding worker, not one-action organism brain | **B M2** |
| 6 | OpenSpiel `evaluate_bots` and games | Reference strategies/game task library, not escrow | **B external task** |
| 7 | PettingZoo `ParallelEnv` and compliance tests | MARL interoperability, not world scoring/ledger | **B optional** |
| 8 | [DEAP selection](https://github.com/DEAP/deap/blob/master/deap/tools/selection.py) or EvoAgentX MAP-Elites | Generic selection operators, not ownership/lineage | **B later** |
| 9 | Inspect AI eval/scorers | Research harness and logs, not live referee | **B later** |
| 10 | SQLite FTS5 + immutable blobs + trusted Git provenance | Memory/index/genome-history microservices | **A/C initially** |

**Risk of false reuse:** mini-SWE for trivial one-intent loop, Letta Code for a file of memories, OpenEvolve ProgramDatabase for one mutated skill, and Mesa event scheduling for two organisms may cost **more to integrate than to implement their exact M0/M1 equivalent**. All comparisons remain hypotheses until adapter measurements.


## 3. Reusable component catalog — actual classes/modules, costs and rights

**Decision letters:** **A adopt** as a dependency, **B adapt** only through an isolated narrow wrapper, **C borrow design** without copying unauthorized code, **D build** Surlife-specific functionality. Integration burden L/M/H is an engineering judgment, **not estimated labor hours**. An “active” repository showed recent 2026 pushes, but this is not proof of release/API stability. Every import requires a **full commit or release pin**, dependency lock/SBOM, security review and exact license notice obligations.

| Source-level upstream candidate | Language / declared license / maintenance observation | Library vs full service; what it replaces | Integration and recommendation |
|---|---|---|---|
| [mini-SWE DefaultAgent](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/agents/default.py), [LitellmModel](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/models/litellm_model.py), [LocalEnvironment](https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/environments/local.py) | Python, **MIT**, active Oct 2026 | Package/CLI for model→command→feedback coding | **H M1, M M2; B M2**. Shell parser, many deps, no automatic isolation. |
| [nanobot AgentRunner](https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/runner.py), [MemoryStore](https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/memory.py), [ToolRegistry](https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/tools/registry.py) | Python, **MIT**, active Oct 2026 | Assistant runtime with provider, context compaction, tools and file memory | **H; C/B selective**. Rich messaging/session/tool assumptions; whole runtime not needed. |
| [smolagents MultiStepAgent/ToolCallingAgent/CodeAgent](https://github.com/huggingface/smolagents/blob/main/src/smolagents/agents.py) | Python, **Apache-2.0**, active | Library for structured tools and multi-step decisions | **M/H; B when justified**. Tool execution must be policy-restricted; local executor not a hostile-code sandbox. |
| [Pydantic AI Agent](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/agent/__init__.py) and [TestModel](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/models/test.py) | Python, **MIT**, active | Typed model calls and fake-model test utilities | **M; B if provider/output variety grows**, avoid unnecessary full agent graph. |
| [Letta Code memory-filesystem/skill modules](https://github.com/letta-ai/letta-code/tree/main/src/agent) | TypeScript, **Apache-2.0**, active | Persistent editable memory/identity in an agent harness | **H; C**. Cross-language/host process and tool privilege complexity; not a standalone SQLite memory library. |
| [Agent Zero agent.py](https://github.com/agent0ai/agent-zero/blob/main/agent.py) and [tools](https://github.com/agent0ai/agent-zero/tree/main/tools) | Python + web stack; **MIT LICENSE text verified** although repo metadata did not clearly classify it; active | Autonomous tool-building assistant with shell/browser | **H; C**. Host privileges, Docker/desktop/web dependencies and memory ownership mismatch. |
| [Voyager SkillManager](https://github.com/MineDojo/Voyager/blob/main/voyager/agents/skill.py) | Python + Minecraft JS; **MIT** source, last pushed 2024 observed | Skill retrieval and descriptions, Chroma/OpenAI embeddings | **H; C** skill-catalog design. Full Minecraft/node/embedding service overkill. |
| [GEPA GEPAAdapter/EvaluationBatch](https://github.com/gepa-ai/gepa/blob/main/src/gepa/core/adapter.py), [optimize](https://github.com/gepa-ai/gepa/blob/main/src/gepa/api.py) | Python, **MIT**, active; inspected base `pyproject.toml` has `dependencies=[]` | Offline reflective prompt/text optimization **library**, not daemon | **M; B**. Promising direct reuse, but must record proposal/trial costs and segregate final holdouts. |
| [Darwin Gödel Machine DGM_outer.py](https://github.com/kew-lab/darwin-godel-machine/blob/main/DGM_outer.py), [self_improve_step.py](https://github.com/kew-lab/darwin-godel-machine/blob/main/self_improve_step.py) | Python/Docker, **Apache-2.0**; last observed push Aug 2025 | Coding/SWE-bench evolutionary application with ancestor archive | **H; C**. Bench-specific harness/LLM settings; container is not security proof. |
| [OpenEvolve ProgramDatabase](https://github.com/algorithmicsuperintelligence/openevolve/blob/main/openevolve/database.py), [Evaluator](https://github.com/algorithmicsuperintelligence/openevolve/blob/main/openevolve/evaluator.py), [selection](https://github.com/algorithmicsuperintelligence/openevolve/blob/main/openevolve/selection.py) | Python, **Apache-2.0**, active | Islands/population archive and evaluator library | **H; B/C M4**. Very substantial database; evaluator has dynamic-import/subprocess code paths. |
| [EvoAgentX MapElitesOptimizer](https://github.com/ANative-Lab/EvoAgentX/blob/main/evoagentx/optimizers/map_elites_optimizer.py), [EvopromptOptimizer](https://github.com/ANative-Lab/EvoAgentX/blob/main/evoagentx/optimizers/evoprompt_optimizer.py) | Python, **MIT** per `pyproject.toml`; 0.1.x status | Quality-diversity, workflow and prompt optimizers | **H whole / M isolated; B/C M4**. Declares LiteLLM/OpenAI/Pandas/NumPy/NetworkX/tree-sitter and others. |
| [DEAP selection.py](https://github.com/DEAP/deap/blob/master/deap/tools/selection.py) including `selTournament`, `selLexicase` | Python/NumPy, **LGPL-3.0**, 2026 activity | Small library of established selection operators | **M; B population scale** with legal/compliance assessment, not for one candidate. |
| [PettingZoo ParallelEnv/AECEnv](https://github.com/Farama-Foundation/PettingZoo/blob/main/pettingzoo/utils/env.py), [parallel_api_test](https://github.com/Farama-Foundation/PettingZoo/blob/main/pettingzoo/test/parallel_test.py) | Python, **MIT**, active | Standard multi-agent API/test library, Gymnasium spaces | **M; B facade only**. It does not implement escrow, idempotency, private observations or true-call cap. |
| [Mesa Model](https://github.com/mesa/mesa/blob/main/mesa/model.py), [time/events.py](https://github.com/mesa/mesa/blob/main/mesa/time/events.py) | Python, **Apache-2.0**, active developmental API | Scheduling, agent/spatial/time event abstractions | **M/H; B later** only when spatial/event dynamics eliminate substantial custom scheduling. |
| [OpenSpiel evaluate_bots](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/evaluate_bots.py) and game types | C++/Python binding, **Apache-2.0**, active 2026 | Trusted task/game challenge benchmarks/reference policies | **M/H; B external TaskPack**. Compiled deps; scores never directly authorize E transfers. |
| [Crafter Env](https://github.com/danijar/crafter/blob/main/crafter/env.py) | Python/NumPy+rendering, **MIT**, last observed 2024 | Single-agent achievement/survival environment | **M/H; B later**. Visual observation conversion and multiagent wrapper increase costs. |
| [Neural MMO Env(ParallelEnv)](https://github.com/NeuralMMO/environment/blob/2.1/nmmo/core/env.py) | Python/PettingZoo/Gymnasium, **MIT**, last observed 2024 | Large multiagent resource/survival world | **H; B later external world**. RL-oriented environment semantics and dependencies. |
| [Avida](https://github.com/devosoft/avida) | C++, **effective license unverified** | Digital heredity/evolution methodological precedent | **H; C study only** pending rights; not v0 candidate dependency. |
| [Inspect AI eval](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/_eval/eval.py), [scorer package](https://github.com/UKGovernmentBEIS/inspect_ai/tree/main/src/inspect_ai/scorer) | Python, **MIT**, active | Standalone evaluation/experiment/logging framework | **M; B research harness only**, never scoring/ledger authority. |
| [Descartes model-ladder.js](https://github.com/Lightless-Labs/descartes/blob/main/tools/descartes-cli/src/model-ladder.js), [promotion-store.js](https://github.com/Lightless-Labs/descartes/blob/main/tools/descartes-cli/src/promotion-store.js) | Node/JS, **UNLICENSED** in [package.json](https://github.com/Lightless-Labs/descartes/blob/main/package.json); active | Escalation, shadow promotion, evidence methodology | **C conceptual only; NO source copying** without license grant. Its approval gates are not self-directed organism evolution. |
| [Foundry adversarial skill](https://github.com/Lightless-Labs/foundry/blob/main/plugins/foundry/skills/foundry-adversarial/SKILL.md) | Agent Skills/JS; **MIT declared in package.json**, full file/asset rights not verified | Red/green hidden-test prompt/information barrier, public plugin | **C methodology**, not a ready Python sandbox or private engine. |
| [Third Thoughts SPC script](https://github.com/Lightless-Labs/third-thoughts/blob/main/scripts/021_spc_control_charts.py) | Python+Rust, **AGPL-3.0**, active | Session quality/drift statistical analysis | **C later**. Corpus mismatch; importing many dependencies/AGPL obligations not worthwhile v0. |
| [Refinery Engine](https://github.com/Lightless-Labs/refinery/blob/main/crates/refinery_core/src/engine.rs) / [ModelProvider](https://github.com/Lightless-Labs/refinery/blob/main/crates/refinery_core/src/lib.rs) | Rust, **MIT**, limited 2026 activity | Bounded multi-model critique/consensus **library/CLI** | **B optional research-only**. Consensus cannot be a live organism referee. |
| [Willikins apply/SinkToken](https://github.com/Lightless-Labs/willikins/blob/main/crates/willikins-core/src/apply.rs) | Rust, **AGPL-3.0**, active | Typed plan/apply approval, privileged tool semantics | **C pattern only**, cross-language rights and host administration overkill. |
| [Pessimal host agent](https://github.com/Lightless-Labs/pessimal/blob/main/agents/host/pessimal_agent_host/src/main.rs) | Rust, **AGPL-3.0**, active | OTLP multi-host resource telemetry as daemon | **Reject v0**, normal structured local process/resource logs suffice. |

**Legal and vendor-lock-in conclusion:** Most permissive packages are lawful to *consider* with notice obligations, but safe inclusion depends on exact file and transitive dependencies. LGPL and AGPL introduce compliance questions, not blanket bans. Avoid vendor ontology lock-in by exporting only canonical wire data, not library-specific model-message types, agent objects, genome source trees or RL reward fields. In particular, do not fork a giant provider/assistant to maintain a tiny custom path.

## 4. Every subsystem: adopt, adapt, borrow design or build?

| Subsystem | A Adopt | B Adapt | C Borrow design | D Build unique rules | Preferred choice / lifetime complexity |
|---|---|---|---|---|---|
| Agent reasoning | Existing mini-SWE/smolagents possible | mini-SWE sealed code worker | simple model→feedback loop | native one-intent M1 call | **D M1 / B M2**; avoids rewriting shell multi-step internals |
| LLM provider and accounting | provider official SDK | Pydantic AI/LiteLLM when ≥2 providers justified | provider usage conventions | trusted reservation/settlement | **A+D**, no bespoke transport but budget nondelegable |
| Persistent memory | SQLite/FTS5 | specialized retriever on evidence | nanobot/Letta tiers | ACL/provenance/retention | **A+C+D**; avoid full service/vector store |
| Tool and skill registry | typed JSON/file manifests | smolagents tools optional | nanobot registry/Voyager skill catalog | capability admission/permissions | **C+D**, never dynamic-import skills in referee |
| Mutation and candidate generator | GEPA externally | GEPA research adapter; mini-SWE coder | DGM search patterns | trial/activation state machine | **B optional+D**, domain-specific gating cannot be outsourced |
| Evolution archive/selection | DEAP at scale | OpenEvolve/EvoAgentX offline | MAP-Elites/ancestor archive | identity/lineage integrity | **C+D initially**, B when diversity demands it |
| Multi-agent environment API | PettingZoo | outward ParallelEnv | standard observation envelope | world reducer/escrow | **D native + B optional**, one authority |
| Challenges/benchmark | OpenSpiel/Crafter | researcher-installed TaskPack | adversarial baseline structure | task score→energy mapping | **B+D**, existing objective games valuable |
| Experiment orchestration | pytest and possible Inspect | Inspect external adapter | matched-seed ablations | scientific budget and holdout protocol | **A+B optional+D** |
| Event history/replay | SQLite transactions/hashes | JSONL export only | event sourcing conventions | deterministic reducer/canonical events | **A+D**, avoid event broker |
| Adversarial evaluation | pytest/Hypothesis/Inspect | external hidden test runner | Foundry red/green barrier | actual hidden ACL/scorer authority | **A+C+D**, no unlicensed code |
| Genome versioning/inheritance | hashes, immutable blobs, Git researcher-side | later population algorithms | Letta skill-memory versioning | parentage/compatibility/privacy/capital | **A+C+D**, not generic genome VM |


## 5. Four-plus complete implementation strategies, with weighted scores

**User-weighted criteria:** reliable reusable functionality **30%**, ease of integration/maintenance **25%**, future evolution **20%**, security/isolation compatibility **15%**, scientific reproducibility **10%**. Each criterion scored 0–100 as **[J] architecture judgment, not measured engineering effort or scientific evidence**. An actual critical safety or license failure **disqualifies** deployment regardless of score. All choices require the same host-held money, secrets and referee boundaries.

| Complete strategy | Reuse 30 | Integration 25 | Future 20 | Security 15 | Reproducibility 10 | Total /100 | Trade-off |
|---|---:|---:|---:|---:|---:|---:|---|
| **A — R1**: custom referee + attempted mini-SWE M1 adapter + modular genomes | 73 | 75 | 90 | 84 | 90 | **80.3** | Strong boundaries, questionable amount of reusable coding-agent code in routine decisions |
| **B — Native minimal**: stdlib+SQLite world, provider SDK, tiny runner, few adapters | 55 | 94 | 82 | 86 | 88 | **78.1** | Least moving parts, but may reinvent sophisticated optimization later |
| **C — Maximum framework reuse**: smolagents + Mesa + PettingZoo + OpenEvolve + Inspect, independent financial layer | 90 | 38 | 75 | 45 | 70 | **65.3** | Many overlapping lifecycles/schedulers/execution owners; **not eligible** until strict isolation/cost/privacy gates pass |
| **D — Recommended thin waist**: custom world + native M1/SDK/pytest + optional GEPA offline, mini-SWE isolated M2, OpenSpiel/Inspect externally, PettingZoo when needed | 85 | 90 | 92 | 88 | 94 | **89.0** | Clear contract discipline and empirical dependency gates needed |
| **E — Benchmark first**: external objective tasks + native decision/cost gate, postpone persistent ecological economy | 80 | 92 | 55 | 94 | 97 | **81.8** | Most direct falsification of learning hypothesis but *not yet* artificial-life survival |

**Scoring explanations:** A is high on future modularity and replay but loses points for a probable agent-loop adapter tax. B removes dependencies and is auditable, though it could become a growing handmade optimizer if the team refuses later libraries. C superficially maximizes code “reused” but incurs competing scheduling, model, tool, evaluator and persistence authorities. D preserves the irreducible Surlife-specific authority and selectively adopts proven external components without making their internal APIs Surlife's genome. E greatly simplifies early scientific controls at the cost of deferring the survival/social hypothesis. No claim that D's 89.0 is empirical performance; it is a decision prior reversible by evidence.

**Sensitivity:** If a mini-SWE restricted fake-model wrapper has fewer total maintained adapter + transitive obligations than the native M1, upgrade A. If GEPA overfits, exposes final data, requires unsupported API access or costs more than useful prompt evolution, drop GEPA with no architectural change. If Mesa replaces significant measured custom spatial scheduling while meeting referee parity, adopt Mesa behind the world interface. No high score licenses unconfined code.

**Independent foundation rubric cross-check:** [`foundation/RUBRIC.md`](https://github.com/pedante/surlife/blob/8b4a23d23db30adaa5b3008ad419089cf7697735/foundation/RUBRIC.md) is a different proposal-quality measure: R1 falsifiability **4.0/5**, feasibility **3.5**, security **3.5**, economy **4.0**, scope **3.0**, reproducibility **4.0**, evolvability **4.0** ⇒ **74/100** weighted by the original rubric. Reasoning: genuine controls and replay aspiration, but unbuilt challenge/adapter/worker and premature future slots. **Blockers override scores.**

## 6. Recommended architecture and narrow integration map

~~~text
  RESEARCH HARNESS: matched seeds, capital, budgets and sealed holdouts
     pytest/Hypothesis | optional Inspect AI | optional GEPA/OpenSpiel
                                |
              HOST AUTHORITY (Python stdlib, SQLite)
         +----------------------+----------------------+
         | WorldRules: seeded reducer, clock, task score |
         | E ledger: escrow, mint/burn, atomic idempotency|
         | Visibility: per-actor observation filtering  |
         | ModelBudgetGateway: pre-call money reservation |
         | Genome/Skill registry: hashes, trial provenance|
         +----------------------+----------------------+
                                |
                  versioned DATA-ONLY interface
                                |
           UNTRUSTED ORGANISM DECISION CONTEXT
             own soul / memories / admitted skills
          deterministic policy OR paid model reasoning
                 ONE VALIDATED WORLD INTENT
                                |
                 optional DIFFERENT M2 process
         mini-SWE code author in disposable, reviewed sandbox
                 -> external contract and shadow tests
                 -> trusted promotion at a tick boundary

  OPTIONAL ADAPTERS (NEVER ACCOUNTING AUTHORITIES)
   WorldBackend -> PettingZoo ParallelEnv compatibility
   WorldBackend -> Mesa only for a richer ecology later
   TaskEvaluator -> OpenSpiel tasks/games via controlled adapter
   ResearchOptimizer -> GEPA, later DEAP/OpenEvolve offline
~~~

**Contracts should be *versioned serialized data*, not a dependence on one agent framework.** The following Python Protocol shapes are illustrations, not implementation specifications:

~~~python
class OrganismRunner(Protocol):
    def decide(self, observation: dict, genome_ref: str,
               allowance: dict) -> dict: ...
    # One proposed WORLD intent. Internal cognition may be multi-step,
    # but every model call remains subject to externally enforced caps.

class TaskEvaluator(Protocol):
    def generate(self, seed: int, regime: dict) -> dict: ...
    def score(self, task: dict, sealed_submission: dict) -> dict: ...
    # Trusted objective score; NEVER direct virtual energy transfer.

class WorldBackend(Protocol):
    def initial(self, seed: int, rules_version: str) -> dict: ...
    def observe(self, state: dict, authenticated_actor: str) -> dict: ...
    def resolve(self, state: dict, intents: list, rng) -> tuple: ...
    # No model I/O, shell or untrusted Python import.

class CapabilityManifest(Protocol):
    # Immutable ID, type/version, code/content hash,
    # runtime/language and typed I/O contract,
    # dependencies, visibility, evidence, permissions.
    ...
~~~

**Observation envelope V1:** world/rules version, actor-scoped visible state, phase, tick, capabilities/allowed world intent kinds and host-controlled resource allowances. **Intent envelope V1:** schema/version, turn ID, intent ID, kind, validated payload, active genome hash and optional maximum virtual-energy debit. Actor identity is derived from authenticated worker channel **not self-asserted JSON**. Store a canonical payload hash for each actor/world/idempotency key: identical retry replays the original outcome; reuse with a different payload rejects without effect. Resolve same-tick decisions in a documented deterministic order. LLM responses and provider usage are recorded externally for reducer replay; fresh nondeterministic model calls are **not** byte-for-byte replay.

**Critical two planes:** World intents cause trusted environment/economy changes at the phase boundary. Cognitive operations—reflect, update soul, retrieve private memory, propose mutation, test candidate—are *internally metered* operations, not arbitrary world writes. A one-intent outer API must **not** limit future organisms to one thought or one cognitive architecture. Do not allow generated code to call the provider or alter the referee directly.

**Genome:** a versioned manifest referencing independently content-addressed soul prompt, memory roots, admitted skill blobs, cognitive policy configuration and ancestry. Shared **immutable** code can be inherited/published; no shared mutable per-agent memory. A child receives a **new identity**, explicitly selected inherited items, funded starting E, compatibility-tested skills and lineage provenance. Avoid hardcoding every future slot like `PhysiologyPolicyV1`, `InheritancePolicyV1` or universal `StrategyV1.decide(observation, public_memory)`: these could block differently structured lineages and accidentally imply public access to private memory.

**Storage:** one SQLite source of truth with transactions for action acceptance, escrow, balanced transfer, mint/burn and event commitment. Immutable blobs store candidate/genome versions; JSONL is an **export**, not competing truth. Design replay against recorded outputs, reducer/rules and PRNG versions, canonical serialization/state hashes. Abstract the *storage wire* when actual scale requires it, not at two-organism M0.

## 7. Smallest truly unavoidable Surlife implementation

1. **Authority and visibility policy:** actor/channel authentication, schema/version checks, private/public observation and capability admission.
2. **World rules plus E accounting:** deterministic objective evaluator-to-ecology conversion, validated actions, weather later, funded escrow/mint/burn, idempotent settlement and atomic commit.
3. **Real usage authority:** provider-SDK pre-call reservation, total limit, concurrency/failure/retry accounting and conservative reconciliation; T tokens, M actual money and simulated E recorded separately.
4. **Genome/skill ownership and trial state:** immutable hashes, private memory roots, public skills, proposal → staged → validated → shadowed → activated/reverted provenance, compatible inheritance.
5. **Scientific controls:** precommitted tasks/seeds, blinded research holdouts, matched opportunity/energy/true-token experiments, lifecycle cost, negative outcomes, rollback and lineage measures.
6. **Security admission policy:** independently reviewed external worker confinement, contract validation and researcher-controlled promotion; **reuse** a vetted isolation provider rather than writing a home-made sandbox.

These are responsibilities, **not** six servers. Begin in a small Python repository with logical modules and a single serialized M0 referee writer.

## 8. Components explicitly not worth building now

Do not author a general multi-provider HTTP client, giant agent framework, vector DB, semantic-memory server, distributed event broker, separate evaluator microservice, custom genetic algorithm package, universal game catalog, new multiagent API, universal genome VM, web/desktop tool runtime, custom OS sandbox, separate transaction coordinator or all future social/biological mechanics. Do not transplant Letta, nanobot, mini-SWE, OpenEvolve and Descartes as concurrent core services. Conversely, do not reject mature specialized libraries when concrete evidence shows they reduce total maintenance at M2/M4.

## 9. Dependency integration order with stop/reversal gates

| Milestone | Narrow activity (not implementation authorization) | Gate or measured reversal |
|---|---|---|
| **P0-A, no LLM** | Native two-agent world, scripted decisions, SQLite E ledger, canonical event schema | Strict conservation, no duplicate settlement, privacy and replay on crash/restart |
| **P0-B** | Fixed policies on objective seeded task regimes; optional existing OpenSpiel game | Reference/greedy scores differ nontrivially across regimes; no trivial optimal “idle” exploit |
| **P0-C** | Fake-model native M1 decision vs restricted mini-SWE wrapper (optionally smolagents) | Same structured intent/observations, zero shell/net, equivalent traces, actual adapter LOC/deps/testing burden |
| **M1** | Official provider SDK and separate organism memories, host-reserved capped calls, prompt mutation | Reconcile tokens and M including failures; match fixed/prompt controls; human-approved spending only |
| **M1-P** | Offline GEPA vs naive prompt variations, practice/validation and fully sealed research holdout | Count all mutation and evaluation calls; independent improvement at equal actual lifecycle budget |
| **M2-P** | Threat model, reviewed disposable code-worker sandbox | No network/host/peer/credential access, CPU/memory/timeout/output enforcement; safety review |
| **M2** | mini-SWE code author if adapter wins; stage one StrategyV1 candidate, test/shadow/revert | Code never imported in referee; immutable trial/parent records; code vs prompt controls |
| **M3** | Published skills, bounded priced next-tick interventions, extra TaskPacks | No private memory leakage or E/score conflation; changed ecology tested with ablations |
| **M4** | Child/genome fork, version-compatible inheritance, population selection | New private identity, capital conservation, diversity and held-out transfer, optional DEAP/OpenEvolve if worthwhile |
| **M5–M6** | Heterogeneous cognition, reproduction/recombination, environmental construction, Mesa-scale ecology | Unchanged organism wire and authority; novelty/ability gains across new worlds per full lifecycle cost |

**Record at every candidate spike:** upstream tag/commit, dependency lock and license/SBOM, code added to the trusted boundary, actual adapter tests and upgrade work, SDK usage/billing uncertainty, runtime latency and resource measurements on stated hardware, state hashes, security failures and held-out performance. No projected “weeks saved” without evidence. An API compliance test alone is not an economy/sandbox certification.

## 10. Growth path to open-ended evolution

**First two organisms:** different souls, private episode memories and identical trusted action contract; compare scripted and LLM baselines. **Acquired abilities:** code written in disposable workers becomes an immutable, interface-tested skill, independently activated and revisable at controlled cost. **Social learning:** individuals may inspect *published* skills/results; rival prompts/code are untrusted inputs; exchange is priced and ownership explicit. **Environmental manipulation:** priced bounded next-tick world interventions affect the initiator too. **Reproduction:** fork compatible inherited prompt/skill/memory references with new identity, no shared writable state; test parents/offspring at matched capital. **Diverse species/cognitive architectures:** accept different internal worker strategies, model choice, memory/retrieval and skill languages behind the same typed world intent; trusted budgets/privileges remain immutable. **Multiple worlds/open-endedness:** replace WorldBackend/TaskEvaluator with trusted versioned modules, add spatial/social ecologies and evaluate cross-world novel competencies rather than mere population growth or varied autobiographies.

**Premature decisions to avoid:** embedding Python skill objects in the referee, assuming all genomes share one source layout, coupling task score directly to virtual E, one immutable internal reasoning architecture, fixed catalog of 7 future policy interfaces, single provider's message format as the genome schema, unrestricted tool creation or task-side control of economic authority.


## 11. Specific proposed changes to R1, by section and reason

**These are requested revisions, not edits performed by this reviewer.** Human acceptance, synthesis and a new frozen iteration remain required.

| Finding / severity | Exact location | Change to consider |
|---|---|---|
| **R3-F01 MAJOR** | `PROPOSAL.md` ``0, 2 table, 4 mini-SWE, 10 C-R2 | Native fake-model decision runner first; compare mini-SWE as optional M1 experiment, preferentially use it for sealed M2 code authoring; choose by adapter+dependency cost. |
| **R3-F02 MAJOR** | ``2, 3, 5 | Clarify that PettingZoo is an outward RL compatibility API, Mesa is an optional trusted scheduling backend at ecological scale, OpenSpiel a source of external objective games; none authorizes ledger transfers. |
| **R3-F03 MAJOR** | ``2, 4, 7; `TRADEOFFS.md` `2 | Add GEPA evaluator-driven prompt mutation, Inspect AI evaluation harness and Pydantic AI as a conditional provider adapter to the measured component comparison; distinguish external research vs live authority. |
| **R3-F04 MAJOR** | `3 `StrategyV1`, `Genome and optional evolution slots` | Define a generic typed, versioned CapabilityManifest/GenomeManifest; remove presumption all strategies use a universal `public_memory` argument; do not implement named future policy subclasses before need. |
| **R3-F05 MAJOR** | ``3 and 6 | Formalize channel-authenticated actor, action ID and payload conflict rules, deterministic phase resolution, state/event hash canonicalization, separation of cognitive calls from world intents. |
| **R3-F06 MAJOR** | ``4 and 6 | Explicit official SDK + pre-call price upper-bound reservation, retry/timeout and missing usage accounting, provider-side cap caveat. |
| **R3-F07 MAJOR** | ``5, 7, 8 | Include a benchmark-first, ecology-free control; require nontrivial fixed-policy discrimination and physically separate final held-out tests prior to claims of improvement. |
| **R3-F08 BLOCKER** | ``2, 4, 7, 9 | Replace loose “isolated worker” language with an independently reviewed hostile-code confinement acceptance profile. |
| **R3-F09 MINOR** | ``2, 3, 6 | SQLite and hashed blobs suffice; defer vector store, event broker, optimizer service and distributed genome registry. |
| **R3-F10 QUESTION** | `TRADEOFFS.md` ``1–3 | Include recommended thin-waist and benchmark-first complete alternatives; label all rankings contingent and enumerate reversal conditions. |
| **R3-F11 MAJOR** | `TRADEOFFS.md` Descartes/Foundry/AGPL lines | Separate source availability, upstream license declaration, file rights and transitive dependencies; UNLICENSED is no-copy until permission. |
| **R3-F12 QUESTION** | `7 M4–M6 | Specify future worker/genome/world contract migration tests, not a permanent taxonomy of speculative interfaces. |

### Adversarial counterexample R3-X01: progress without intelligence

An organism develops a zero-token “always wait” strategy and outlives rivals under a convenient upkeep/reward rule; it appears *energy-efficient* while completing no useful challenge. Alternatively, an offline prompt optimizer receives raw failure details from repeatedly queried “hidden” tests, memorizes that set and improves reported score without transfer. A lucky first winner can accumulate virtual wealth independently of skill. None shows genuine evolution. Report **task coverage, useful utility per opportunity, held-out family shifts, matched capital, full mutation/testing/LLM cost, confidence and invalid action rate**; exclude sealed final samples from organism/optimizer storage and diagnostic feedback.

### A substantially simpler falsification design

Before running even an ecological two-agent world, compare **fixed vs prompt-only vs code-only vs hybrid** on a single **existing objectively scored task suite** (OpenSpiel or similar) with a trusted host budget gateway. This avoids survival/escrow/weather confounders and could refute the supposed benefit of code skills with much less custom world code. It **does not** answer resource scarcity, reproduction, niche construction or social evolution; therefore make it an **external control** while retaining R1's small world for the long-term experiment.

## 12. Required evidence: offline integration tests with pass/fail signals

All test cases below are **proposed, NOT executed**. Prefer fake models and no network or provider credentials. Never run adversarial code-execution probes against a personal developer host.

| ID | Setup / controls | Required observable result |
|---|---|---|
| **R3-T01 — actor authentication** | A valid-shaped intent lies about actor ID; peer workspace private | Referee uses authenticated worker identity; no cross-organism read/write |
| **R3-T02 — atomic E transfer** | Scripted duel of two 20-E stakes; crash between escrow, result and commit | Exactly one committed settlement; explicit world mint/burn, conserved transfers, no negative balances |
| **R3-T03 — idempotency** | Same actor/world/intent ID repeated unchanged and then with a different payload | Unchanged retry returns original result; changed payload rejected without side effect |
| **R3-T04 — replay** | Same seeds, scripted actions and **recorded** fake nondeterministic model outputs after restart | Identical canonical event/state hashes and balance projection |
| **R3-T05 — privacy/injection** | Rival publicly publishes a malicious instruction and requests other's private memory | Untrusted text does not override world intent schema or private ACL |
| **R3-T06 — agent adapter** | Identical fake model fixtures for native runner, restricted mini-SWE and optional smolagents | At most one valid world intent; no shell/network; log dependencies, maintained adapter LOC and failure paths |
| **R3-T07 — model budget** | Fake provider times out, retries, reports missing or unexpectedly high usage | Pre-reserve conservative upper bound; reject over-cap calls and flag uncertain usage; exact token field distinctions |
| **R3-T08 — PettingZoo parity** | Native and ParallelEnv wrapper run same policies/seeds; include `parallel_api_test` | Same task scores, states, legal-action outcomes, event hashes and E balances |
| **R3-T09 — objective task quality** | Greedy/reference/exhaustive policies on 2+ task regimes | Nontrivial action-sensitive score spread without a single dominating no-op |
| **R3-T10 — GEPA prompt evolution** | Mock proposer, practice/validation tasks and **physically sealed** final evaluation | Recover candidate/trial provenance, no final holdout access, measure full lifecycle cost |
| **R3-T11 — capability inheritance** | Stage module, corrupt its hash, fork child, share public immutable blob | Invalid module never activates; child has own writable state; parentage/compatibility verified |
| **R3-T12 — hostile M2 sandbox** | In separate vetted disposable isolation, attempt secret, peer, host and network access; CPU/memory exhaustion | No access or host changes; quota and teardown work; failure blocks M2 |
| **R3-T13 — Inspect benchmark parity** | Run same fake task with pytest and optional Inspect harness | Objective score/trace equivalence; reject dependency if it saves no measurable maintained work |
| **R3-T14 — experimental attribution** | Static/prompt/code/hybrid, equal task opportunities, full training/trial/evaluation budgets | Report distributions/seeds, real tokens/money, E, CPU/wall-time, failure/rollback and uncertainty separately |

**Evidence needed to reverse this review:** a source-pinned, license-cleared mini-SWE M1 adapter that is simpler and just as safe as the native runner; a PettingZoo/Mesa backend that demonstrably reduces tested trusted code and preserves replay/ledger; GEPA/Inspect delivering held-out utility or research reproducibility after their full added costs; and an independently vetted execution boundary. An **API-level smoke test is necessary but not sufficient** for financial or sandbox safety.

## 13. Verification trail and remaining unknowns

**Inspected Surlife sources:** R1 HEAD at `8b4a23d23db30adaa5b3008ad419089cf7697735`; root and foundation instructions/contract/rubric/protocol; R1 PROPOSAL, TRADEOFFS and author REVIEW_HANDOFF; original nine `docs/` foundation background documents; PR #1 candidate catalog, machine-readable queue and evaluation protocol; PR #2 arena comparison and PR #3 nanobot versus mini-SWE comparison. All three research PRs were unmerged at inspection, and should not be treated as endorsed dependencies. **No R1 Reviewer 1/2 or other review reports were read.**

**Inspected upstream entry points**, linked above in the component catalog and findings: mini-SWE `src/minisweagent/agents/default.py`, `environments/local.py`, `models/litellm_model.py`, `pyproject.toml`; nanobot `agent/runner.py`, `agent/memory.py`, `agent/tools/registry.py` and context governance; smolagents `src/smolagents/agents.py`; Pydantic AI `agent/__init__.py` and `models/test.py`; Letta Code `src/agent/` memory/skill modules; Agent Zero `agent.py`, tools and `LICENSE`; Voyager `voyager/agents/skill.py`; GEPA `src/gepa/core/adapter.py`, `src/gepa/api.py`, `pyproject.toml`; DGM `DGM_outer.py` and `self_improve_step.py`; OpenEvolve `database.py`, `evaluator.py` and `selection.py`; EvoAgentX `map_elites_optimizer.py`, `evoprompt_optimizer.py`, `pyproject.toml`; DEAP `tools/selection.py`; PettingZoo `utils/env.py`, `test/api_test.py` and `test/parallel_test.py`; Mesa `mesa/model.py`, `mesa/time/events.py`; OpenSpiel `open_spiel/python/algorithms/evaluate_bots.py`; Crafter `crafter/env.py`; Neural MMO `nmmo/core/env.py`; Inspect AI `src/inspect_ai/_eval/eval.py`, `scorer/`; Descartes `package.json`, `model-ladder.js`, `promotion-store.js`; Foundry `package.json` and canonical/adaptor adversarial skills; Third Thoughts `package.json`, `scripts/021_spc_control_charts.py`; Refinery `crates/refinery_core/src/lib.rs`/`engine.rs`; Willikins `crates/willikins-core/src/apply.rs`; Pessimal `agents/host/pessimal_agent_host/src/main.rs`. Avida repository was identified, but effective license **not established**.

**Some inspected file blob SHAs (not whole repository dependency pins):** mini-SWE `default.py` `ca310e37d7c61888c576f73f5e1790ac769407b1`, `local.py` `2b12d33ec90c8db7bb8a36002ba09706be6e7f45`; GEPA `core/adapter.py` `6f59b20c9156eb97d9c83f688c0471931181e136`; OpenEvolve `evaluator.py` `084d1c04ca41b22407c4ecf4227a69539f6379dc`; Mesa `model.py` `f59fbddb68761189c6cb07a64ba982e2a497f367`. All source-level findings refer to the then-inspected upstream states; **production imports must record whole-repository commits/tags** and retest chosen versions.

**Known limitations:** static inspection only, no full clone/installation or security audit; specific first nontrivial M0 challenge, provider caps/billing certainty, actual host sandbox choice, exact allowed cognitive/tool permissions, long-term memory-retrieval benefit, prompt mutation efficiency, source maintenance longevity and true held-out diversity remain unresolved. GEPA's empty base dependency list does **not** imply its optional model adapters cost nothing. OpenSpiel/Mesa/PettingZoo tests were not executed. Rights clearance may invalidate any seemingly attractive dependency. The proposed scores are reasoned priorities, **not measured performance or saved development time**.

**Final recommendation to the maintainer:** **REVISE R1**, preserving its trusted referee/economy/scientific gates and replacing default mini-SWE preference with a **native one-intent reference runner and evidence-gated reusable research/coding adapters**. Human synthesis must decide; this review itself does **not** modify the proposal, `foundation/PLAN.md`, prior reviews or implementation, and does not authorize paid calls or hostile-code execution.

**Answer to the key question:** Starting Surlife from zero, the smallest dependable collection is **Python stdlib + SQLite + one provider SDK + pytest/Hypothesis as needed**, with Surlife-specific rules and admission in the host. **GEPA** is the first promising standalone evolution extension; **mini-SWE** can write code outside the authority domain; **OpenSpiel** can replace invented objective games; **PettingZoo**, **Mesa**, and **Inspect AI** remain adapters chosen by measured need. Preserve one small versioned organism/world wire protocol so none of these libraries defines the organism's future or obtains the right to govern its world.
