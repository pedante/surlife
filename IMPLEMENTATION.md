# Surlife M0 — first executable experiment

**Status:** runnable offline, model-free **reference baseline**; neither self-evolving LLM organisms nor a production-grade deployment.

## Run

Python 3.10+; the runtime uses the standard library only. `pytest` is optional for tests.

```bash
python -m pip install -e '.[test]'
surlife --seed 7 --ticks 12 --a greedy --b optimal --db out/surlife.sqlite
surlife --db out/surlife.sqlite --replay <run_id_from_output>
pytest -q
```

Without installation: `PYTHONPATH=src python -m surlife.cli --seed 7 --ticks 12`.

This program runs two scripted organism policies over the same seeded knapsack puzzle. It reports objective correctness, competitive wins and balances, and proves every stored turn replays with exactly the same actions/outcomes. This is a **deterministic fixture**, not proof of learning.

## Implemented contract

- Two policies (`a`, `b`) chosen from `random`, `greedy`, `optimal`, `wait`. They are trusted bundled functions, not generated organism code.
- Each tick both see the same five-item task; choose a bitmask of items subject to capacity. A deterministic scorer evaluates the choice.
- The world periodically mints energy and charges upkeep (normal=1, fog=2, drought=3). Both actors must have a valid entry and an equal stake; escrow transfers to the winning answer or is refunded for a tie. No negative player/escrow energy.
- SQLite saves each accepted round, its double-entry transfers and event hash in a **single transaction**. One run/tick key prevents duplicate settlement. Replay reconstructs the state from stored submitted actions.
- Task and agent random streams are independent. No LLM, credentials, network, dynamic Python loading, mutable prompts, code mutation or reproductive evolution.

## Existing technology to reuse

| Component | Present choice | When to reconsider |
|---|---|---|
| Python `sqlite3`, `dataclasses`, `random`, `hashlib` | **Using** | No need to replace correctly scoped standard-library functionality |
| `pytest` | **Using for tests** | Add Hypothesis for systematic fuzzing in calibration |
| LLM provider's official SDK | **M1** | Host-owned calls, provider-aware reservation, fake-model tests before any paid calls |
| [GEPA](https://github.com/gepa-ai/gepa) | **M1 evolution candidate** | Reflective prompt optimization, benchmark vs random and native edits; charge all search cost |
| [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) | **M2 code-author candidate** | Restricted code writing and trajectories, not an unrestricted everyday shell agent |
| [PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/) | **Optional adapter** | Multi-agent RL interoperability if parity with referee/ledger is demonstrated |
| [OpenSpiel](https://github.com/google-deepmind/open_spiel) | **Later task source** | External standardized objective games and evaluation |
| [DEAP](https://github.com/DEAP/deap) | **Later inheritance/selection** | Only when actual population evolution is implemented |
| gVisor / sandboxed VM | **Not necessary at M0** | Required selection and adversarial testing before LLM-authored arbitrary Python executes |

The system avoids importing mini-SWE, PettingZoo, LiteLLM and DEAP at once: none of them supplies Surlife's trusted world economy and such a stack would obscure the first control experiment.

## Deliberately lightweight security

**M0 is local, single-operator, trusted-code only.** It does not run model-generated Python or issue paid model calls, so it does not need a hardened multi-tenant container or external provider proxy at this stage. This is *not permission* to implement M2 using unsandboxed `exec`/`eval`, shell tools or imported untrusted organism modules. Before M2, enforce isolation from host files, credentials, network, referee ledger, rival state and the billing gateway with tests and resource quotas.

## Sequence toward real evolving organisms

1. **M0 calibration:** run many independent seeds, test replay/crash consistency, assess reward headroom, and compare random, greedy, optimal, abstaining policies. Stop if tasks saturate or the economy fails too quickly.
2. **M1 prompt souls:** per-agent versioned prompt/memory, initially fake-model responses, then optional low-budget host-owned provider integration with explicit human-approved money ceiling. Evaluate fixed, random-edit and revisable prompt arms on sealed held-out tasks.
3. **Reuse benchmark:** trial GEPA against native edits; trial a restricted mini-SWE cognitive adapter against a native one-intent runner. Adopt only if integration and maintenance evidence favors it.
4. **M2 code mutation:** stage one candidate, validate exact immutable bytes, trial/rollback in a confined worker, charge model/code/trial costs, never import it into the referee. Later add PettingZoo/OpenSpiel comparison and DEAP inheritance.
5. **Ecology expansion:** heterogeneous tasks, weather engineering, reproduction, age and social adaptation only after early scientific signals.

**Research warning:** current `correct` counts are conditional on entering a match, not on all assigned tasks; future experiments must report assigned-task accuracy, abstentions, model tokens (including optimization), money, CPU, uncertainty and independent replication.
