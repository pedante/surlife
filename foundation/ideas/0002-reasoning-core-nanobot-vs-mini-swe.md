# Candidate: mini-SWE-style reasoning loop vs nanobot for Surlife organisms

**Status:** proposed research recommendation; **not** a selected dependency, accepted design decision, or implementation authorization.  
**Date:** 2026-10-11  
**Related:** [current proposal](../PLAN.md) (especially M0–M2 and §10), [frozen proposal 0001](../iterations/0001/PROPOSAL.md), [existing framework survey](../../docs/03-agent-frameworks.md), [evaluation rubric](../RUBRIC.md).

## Problem and decision

Surlife needs a protected, common inference mechanism for many independently evolving organisms. Individuals own mutable `soul.md`, private episode memories and (at M2) validated `strategy.py` modules. The trusted referee owns the world, action validation, ledger, token/money caps, score and isolation. **Do not confuse a capable general assistant or coding agent with an evolving organism.**

**Provisional recommendation:** use a **mini-SWE-agent-inspired minimal reasoning loop** as the M1 baseline, borrow selected **nanobot context/memory design patterns**, and keep the Surlife lifecycle, economy and action API independent. At M2, consider a mini-SWE-style coding worker *inside* a hardened isolated environment to propose and test organism-owned modules. Prefer a small purpose-built Python adapter over embedding either complete framework until a benchmark shows otherwise.

This preserves the option of switching runners; it does not pre-approve copied code.

## What the upstream code actually supports

Sources inspected on 2026-10-11 (pin these commits for a later integration spike):

- **mini-SWE-agent**, commit [`04d809ce`](https://github.com/SWE-agent/mini-swe-agent/tree/04d809ceab9df28f9adaed044884180159172930): [`DefaultAgent`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py), [default configuration](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/config/default.yaml), [local executor](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py), [Docker executor](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py).
- **nanobot**, commit [`a27f294f`](https://github.com/HKUDS/nanobot/tree/a27f294f52293c476ff8ccc546439be203b066ca): [agent runner](https://github.com/HKUDS/nanobot/blob/a27f294f52293c476ff8ccc546439be203b066ca/nanobot/agent/runner.py), [context](https://github.com/HKUDS/nanobot/blob/a27f294f52293c476ff8ccc546439be203b066ca/nanobot/agent/context.py), [context governance](https://github.com/HKUDS/nanobot/blob/a27f294f52293c476ff8ccc546439be203b066ca/nanobot/agent/context_governance.py), [memory](https://github.com/HKUDS/nanobot/blob/a27f294f52293c476ff8ccc546439be203b066ca/nanobot/agent/memory.py), [tool registry](https://github.com/HKUDS/nanobot/blob/a27f294f52293c476ff8ccc546439be203b066ca/nanobot/agent/tools/registry.py).

Verified code observations:

| Dimension | mini-SWE-agent | nanobot | Implication for Surlife |
| --- | --- | --- | --- |
| Reasoning and action | Small `query → execute_actions → observation` runner; sequential trajectory | Structured tool-execution runner with hooks, context and provider state | A mini-style loop is easier to constrain to one Surlife action per tick |
| Durable memory | Run trajectory serialization; organism memory needs implementing | Dedicated memory and context-management modules | Borrow concepts rather than assistant-specific persistence assumptions |
| Task focus | Code editing and shell command execution by default | Persistent assistant with tools, sessions and integrations | Neither is an arena referee, genome or social ecosystem |
| Extensibility | Models and execution environments are separated | Rich tools, hooks, agent orchestration | Additional abstraction is only useful if its actual benefit exceeds complexity |
| Execution security | Local environment executes shell commands on the host; Docker backend exists | Built-in tool execution is capable and must be policy-restricted | **Neither runner is a trust boundary by itself** |
| Limits and accounting | Exposes step, time and cost limits; default YAML allows zeros (disabled), and cost checks happen around calls | Usage reporting and extensive runtime plumbing | Referee's separately enforced **pre-call** budget is mandatory for both |
| Experiment audit | Explicit message trajectory with actions, observations and exit status | More elaborate message/session and runtime state | A small, immutable per-tick event record is easier to replay and compare |

The mini-SWE `DefaultAgent` module at the inspected revision contains about 190 lines; nanobot's `runner.py` is about 1,380 lines, **not** an apples-to-apples measure of total framework complexity or performance. Neither has been benchmarked inside Surlife. Vendor benchmark claims on coding tasks do **not** demonstrate evolutionary learning.

## How the hybrid should be bounded

### M0: no LLM, no agent framework

Keep the deterministic Python referee, reference policies, world transitions, ledger, weather, and exact replay tests. Importing either framework into M0 only increases surface area.

### M1: one bounded organism decision

Proposed logical interface (illustrative, not implemented):

```python
decide(observation, soul, selected_memory, budget) -> WorldAction
```

1. The host selects the organism, enforces a hard real-currency/request/token cap and calculates its allowed actions.
2. The shared core composes immutable mission/world rules with the organism's editable soul, selected private memory and filtered observation.
3. The LLM gateway meters **actual** input/output tokens (including failures/retries), verifies budget reservation and gives an action candidate.
4. The referee validates **one structured world action** (e.g. `wait`, `compete`, `reflect`, `propose_soul_revision`) and applies prices atomically. A prompt or tool result never authorizes new operations.
5. The event log stores observation hash, effective soul/memory/model/prompt version, action, validation outcome, usage/cost, and ledger effects. Store provider replies separately when privacy permits to support model-transition replay.
6. Revisions of `soul.md` are versioned and tested separately from memory consolidation. An observation that appears useful is not automatically heritable knowledge.

**Do not pass mini-SWE-agent's default unrestricted Bash action through to the referee.** Use a purpose-built structured-action adapter. A single tick may use zero model calls when a deterministic policy can act; reflection has a separate configured cap.

### M2: separate coding worker, not privileged core mutation

A coding-capable runner can propose candidate `strategy.py` revisions in an organism-owned staging workspace:

`propose → stage → validate schema/interface → run isolated tests → compare held-out outcome → activate at tick boundary or roll back → archive lineage`.

Use a disposable, resource-limited sandbox with no host network, credentials, referee source, other organism files or writable host mounts. Container availability alone is insufficient: explicitly restrict privileges, capabilities, mounts, network, processes, memory and CPU; review runtime escape assumptions. Only the referee can accept/activate modules after host-defined tests. Charge trials to the organism's simulated economy and independently track real provider/model cost.

## Three alternatives to evaluate

- **A — mini-style custom loop (preferred hypothesis):** implement the minimum action protocol and model gateway without adopting mini-SWE-agent's CLI, shell parser, TUI or configs. Least dependency burden; risks reimplementing parsing/retries/trajectory features incorrectly.
- **B — mini-SWE-agent adapted:** reuse its agent/model/environment classes behind a strict world-action adapter. May reduce implementation effort, but the runner is inherently a multi-step coding-task workflow and carries command-format assumptions.
- **C — nanobot runner adapted:** reuse its context, tool dispatch, memory and LLM machinery with non-world tools disabled. Potentially better long-term memory/functionality, but larger trusted code surface, more assistant-specific integration and hard-to-isolate prompt/context overhead.
- **Control — tiny from-scratch loop:** essential comparison even if A wins by design; no vendor framework should be assumed necessary.

Do **not** try to integrate the entire nanobot and mini-SWE-agent runtimes together. Reuse isolated ideas, adapters, or license-compliant modules only if a tested engineering advantage is demonstrated.

## Minimal falsifiable selection experiment (not executed)

**Prerequisites:** M0 acceptance gates pass; M1 spending guard is operational; a human approves a small fixed model budget and stopping condition.

- Pin framework/model/provider/config commits. Use the same tasks, seed schedules, allowed action semantics, model parameters, observation visibility, per-agent memory, prompt content, and matched *true* token and virtual-energy budgets.
- Prototype the custom minimal loop first, then the mini-adapted and nanobot-adapted alternatives **only if** adapter complexity is plausible. Budget the prototypes explicitly; fewer configurations are preferable to uncontrolled model spend.
- On practice and held-out puzzle/duel tasks, record successful legal actions, objective reward, true input/output tokens, provider bill, latency, invalid-action and retry rates, memory footprint, reproducibility evidence, code size/dependencies, and security-test failures. Report variance across independent runs.
- Add prompt-edit/no-edit and persistent-memory/no-memory arms **only after** basic runner equivalence is checked. A run with extra context/tool calls is not an equal-cost learning advantage.
- Attack the boundary: request arbitrary shell/network access, rival file reads, modifications to world rules/ledger, prompt injection via observations, unsupported actions, and runaway retries. Reject any variant that crosses the trust boundary, independent of performance.
- **Selection criterion:** prefer the smallest safe adapter that satisfies M1 acceptance and is not materially worse in held-out *correct reward per 1,000 true tokens* under equal energy, cost and task coverage. If performance intervals overlap, choose the simpler implementation; do not manufacture a winner. Report total experimental spend, including failed calls.
- **Refutation:** if mini-inspired integration adds more complexity, prompt overhead, or failures than a custom loop without a convincing reward-per-token benefit, drop it. If nanobot's memory consolidation yields no held-out gain net of its extra token costs, do not ship it for M1.

A proposed initial pilot can be small (e.g. a few seeds and a handful of tasks) but cannot support strong statistical claims. Trial count and hard external spend cap must be approved before executing any paid tests.

## Costs and scientific risks

| Cost category | Expected source | Management |
| --- | --- | --- |
| Engineering | Wrapping an external runner, prompt/action parser, memory store and tests | Measure actual effort in the spike, do not assume a 100-line core means a 100-line integration |
| Real model tokens/currency | Decisions, retries, reflection, memory compression, code mutation and tests | Gateway reservations/ceilings set independently of organism energy and the framework's in-process counters |
| Virtual energy | Actions, maintenance, LLM calls, mutation trials | Referee-owned prices, mint/burn accounting and balanced transfers |
| Experimental confounds | Longer prompts, better default tools, selective history or extra retries | Matched budgets, ablations, task coverage and held-out seeds |
| Security | Arbitrary command execution, code escape, prompt injection and memory leakage | Least privilege, isolation, opaque valid actions and adversarial tests |

## Disposition and follow-up

**Status: proposed; no tests or implementation performed.** The suggested order is M0 referee → M1 minimalist decision core → measured memory experiment → M2 isolated coding-worker spike. Preserve this comparison as an idea until independent review and maintainer decision; do **not** rewrite [`foundation/PLAN.md`](../PLAN.md), frozen iterations, or evaluation rules merely to match the recommendation.

If accepted after review, record the choice and its evidence in `foundation/decisions/`, and only then revise the current plan with proper iteration traceability.
