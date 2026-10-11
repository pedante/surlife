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
