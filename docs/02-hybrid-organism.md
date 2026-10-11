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
