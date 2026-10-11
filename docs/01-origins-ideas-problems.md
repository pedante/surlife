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
