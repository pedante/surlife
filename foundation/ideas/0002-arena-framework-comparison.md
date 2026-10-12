# Idea 0002 — Arena choice: minimal Python referee, PettingZoo adapter, OpenSpiel benchmarks

**Status:** proposed; research recommendation, not an approved architecture decision or an implementation authorization.  
**Date:** 2026-10-11  
**Question:** Should Surlife adopt PettingZoo and/or OpenSpiel as its arena engine, or build the smallest custom Python world?  
**Related:** [current proposal](../PLAN.md), [iteration 0001](../iterations/0001/PROPOSAL.md), [lifecycle design](../../docs/06-lifecycle-and-arena.md), [framework research](../../docs/03-agent-frameworks.md), [reuse evaluation PR #1](https://github.com/pedante/surlife/pull/1).

## Recommendation (hypothesis to test)

**Keep the authoritative M0 world/referee as a minimal custom Python implementation. Add a PettingZoo Parallel API *adapter* early if a short compatibility spike demonstrates low incremental complexity. Use selected OpenSpiel games, policies and analytical tools as optional, independent benchmarks, not as the persistent life-world engine.**

This separates (a) a persistent economy/world in which organisms survive from (b) objectively scored games/tasks on which evolving strategies can be evaluated. PettingZoo and OpenSpiel are complementary, not mutually exclusive alternatives. **Do not approve either dependency until a small empirical integration test and dependency/license review.**

Surlife's [H1](../PLAN.md) asks whether prompt+code evolution improves correct work per true model token and matched virtual-energy budgets. That is not the same question as whether an arena can host a sophisticated game.

## What the alternatives supply

| Attribute | PettingZoo | OpenSpiel | Minimal custom Python |
|---|---|---|---|
| Primary abstraction | Standard multi-agent environment APIs | Games, game-theoretic algorithms and evaluation | Persistent Surlife world and referee |
| Python entry | Native Python API | Python bindings around substantial C++ core, plus Python algorithms/games | Native Python |
| Sequential / simultaneous decisions | AEC / Parallel API | Both game forms | Must specify and test |
| Ready-made games | Many environments | Many games and algorithms | Initially none |
| Host-controlled virtual energy / escrow / weather | Not built in; custom | Not built in; custom | World-specific implementation |
| Organism-owned prompt / code mutation | External | External | External workers and genome store |
| Atomic ledger / append-only events / exact replay | Must build | Must build | Must build |
| Isolation from hostile generated code | Not supplied | Not supplied | Not supplied: separate sandbox required |
| Main reuse opportunity | Portable agent/environment interface and API compliance tests | Existing games, baselines, analyses | Fewer adapters and complete authority over invariants |
| Main risk | Coupling persistent world to RL episode semantics | Forcing a lifelong world into game-state semantics, added integration complexity | Reinventing APIs, weak baseline coverage, bespoke bugs |

**Interpretation:** estimates of complexity here are engineering hypotheses, **not measured benchmark results**. A custom implementation is only preferable if its invariants and maintenance cost prove lower than adapting an existing framework.

### Why PettingZoo is useful

Its **Parallel API** receives a dictionary of actions for all live agents in one environment step. This is a natural external-facing representation for Surlife's two-agent simultaneous action round. Its **AEC API** models sequential agent turns. Its developer tools include environment API tests. However, PettingZoo does not resolve Surlife-specific weather conflicts, stake escrow, deterministic tie-breaking, cost billing or genome isolation.

**Do not** let the PettingZoo adapter own balances or clocks. The custom referee must remain the only authority. If some Surlife actions are sequential or multi-stage, do not force them into a Parallel step without explicit resolution rules; evaluate AEC or an explicit staged protocol instead.

### Why OpenSpiel is useful

OpenSpiel provides existing sequential/simultaneous, complete/imperfect-information games, and algorithms for research in game playing and learning dynamics. These can reduce the risk of evaluating all agent intelligence using a novel and potentially exploitable Surlife duel.

OpenSpiel's game representations are excellent for discrete competitions but do not naturally provide Surlife's long-running organism histories, metered external LLM requests, editable genomes or protected economy. Start with an **independent benchmark harness** that executes selected OpenSpiel games and reports scores to the evaluator; do not couple the referee to OpenSpiel internals at M0.

### Why a minimal custom world may be lower risk

The planned M0 only needs two reference agents, seeded weather, a small objective duel, energy maintenance and conservation, filtered observations, deterministic arbitration and replay. The tightest testable implementation can keep these rules explicit and auditable. It should be *smaller than* a multi-framework integration, but this is to be measured, not assumed.

## Proposed minimal architecture

```text
Organisms: fixed/LLM/strategy-code policies (untrusted)
       |
       v
Trusted life core and usage gateway
       |
       v
Custom Python referee  <-- authoritative actions, tick, rules, energy
   |      |      |
   |      |      +--> append-only event log + state/replay checker
   |      +---------> external benchmark/evaluation harness
   +----------------> optional PettingZoo adapter
                          |
                          +--> external RL policies / API tests

External evaluation harness --> optional OpenSpiel benchmark games
Mutation worker (isolated) --> validated candidate actions only
```

Possible narrow *internal* contract (illustrative; not runnable code):

```python
class Arena:
    def reset(self, seed: int) -> None: ...
    def observe(self, agent_id: str) -> dict: ...
    def step(self, actions: dict[str, dict]) -> dict: ...
    def replay(self, event_log: list[dict]) -> dict: ...
```

The interface must specify the exact phase order, legal-action checks, schema/version, terminal behavior, deterministic random draws, atomic settlement, action-id deduplication, and visibility/permission boundary before implementation. This sketch is **not** a substitute for those contracts.

For a PettingZoo adapter, conform to the real `ParallelEnv` API: `reset(seed)` returns observations and infos; `step(actions)` returns observations, rewards, terminations, truncations and infos; implement `agents`, `possible_agents`, action spaces and observation spaces. Keep reward mapping (verified task score vs in-world energy) explicit; do **not** treat energy as ordinary RL reward by accident.

## Experimental alternative: do not build a life world first

A simpler **controlled evolution benchmark** could put fixed, prompt-only, code-only and hybrid agents into an existing OpenSpiel game or another objectively scored task suite, while a separate trusted gateway prices actual model usage. It would test part of H1 earlier, without weather or virtual-resource ecology.

**What it sacrifices:** no evidence yet about persistence, scarcity, world interventions or long-term survival dynamics. This alternative is scientifically attractive because it removes variables. Consider it alongside the custom-world M0 rather than conflating them.

## Minimal test that could disprove this recommendation

No dependency installation or code is approved by this document. If M0 implementation is authorized, conduct these **bounded spikes**:

1. **Custom M0 referee:** one seeded two-agent duel, no LLM calls, explicit ledger, weather and public/private observation filters. Repeated runs with the same seed and same recorded actions must produce identical event/state hashes. Every transaction balances; invalid and duplicate actions cannot mint funds or settle escrow twice. Test deliberate malformed actions and restart/retry cases.
2. **PettingZoo adapter:** wrap **the same authoritative referee** as a `ParallelEnv`, pass PettingZoo's `parallel_api_test`, and run fixed agents through the native and adapted interfaces for the same seeds. Balances, action legality, events and game outcomes must match, apart from explicitly documented reward/termination formatting. Track adapter LOC, external dependency overhead and maintenance complexity.
3. **OpenSpiel benchmark:** choose one existing game with deterministic seeds and at least two baseline policies; run both agents outside the persistent world. Record game version, seeds, scores and separately measured token/energy costs. Compare against a trivial custom puzzle to see which is more discriminating and reproducible.
4. **Scientific check:** compare static/prompt-only/code-only/hybrid variants only at appropriate milestones and under matched resource allowances. Hold out evaluation games/seeds, log failures, uncertainty, real provider tokens and virtual energy separately. An apparent win rate increase without matched costs does not establish H1.
5. **Security check:** no untrusted agent prompt, published rival source or generated Python can modify referee rules, opponent data, model credentials or real spend limits. PettingZoo and OpenSpiel are **not** sandboxes. Test the worker isolation independently.

**Reject or defer the adapter** if it requires changing referee state semantics, hiding transaction invariants, or adding substantial untested translation code relative to the minimal core. **Prefer a pre-existing-game-only first experiment** if maintaining a novel duel makes measured agent improvement hard to interpret.

## Costs and tradeoffs

- **M0:** no provider tokens. Engineering/test cost is real but unmeasured; the world still needs careful replay and ledger tests.
- **PettingZoo spike:** added adapter maintenance, environment-space design and a dependency; potential long-term savings via portable policies and ecosystem tests. No assumed performance or LOC advantage without a prototype.
- **OpenSpiel spike:** installation/dependency and experiment integration costs; advantage of established games and algorithms. Running fixed policies need not require LLM tokens; LLM agent trials do.
- **M1/M2:** true model tokens and real money are metered independently of energy. Code mutation runs only in isolated workers. Neither third-party framework replaces that authority.

## Risks to interpretability

- New bespoke tasks may reward hacks or oversimplified heuristics rather than reusable skill.
- Running only against existing-game baselines may establish game competence, not artificial-life adaptation.
- A PettingZoo reward schema may blur *transfer of virtual currency* with *independent fitness metrics*.
- OpenSpiel and other environments can leak test distributions when public training data overlap held-out evaluation.
- Same-seed replay cannot reproduce a fresh nondeterministic model response; record the response and actual usage for exact replay.
- Simultaneous action conflicts must be resolved centrally in deterministic documented order.

## Decision gate

**Proposed:** custom referee first; PettingZoo optional adapter; OpenSpiel optional evaluation integration.  
**Not decided:** choose/PIN framework versions, expose a shared `gymnasium`-style observation schema, adopt a particular benchmark or register dependencies.  
**Not done:** no implementation, performance measurement, integration run, security test, license audit, or change to the approved design.  
**Promotion rule:** submit measured spike results and reviewer objections for maintainer decision under [REVIEW_PROTOCOL.md](../REVIEW_PROTOCOL.md); only then incorporate an accepted choice into `PLAN.md` and an appropriate new frozen iteration.

## Primary upstream references (accessed 2026-10-11)

- [PettingZoo documentation](https://pettingzoo.farama.org/)
- [PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/)
- [PettingZoo AEC API](https://pettingzoo.farama.org/api/aec/)
- [PettingZoo environment creation and tests](https://pettingzoo.farama.org/content/environment_creation/)
- [OpenSpiel repository and overview](https://github.com/google-deepmind/open_spiel)
- [OpenSpiel introduction](https://github.com/google-deepmind/open_spiel/blob/master/docs/intro.md)
- [OpenSpiel developer guide](https://github.com/google-deepmind/open_spiel/blob/master/docs/developer_guide.md)
