# 07 — Proposed programming architecture

**Status:** proposed Python-first implementation. Not a working library or a reviewed security design. Prioritize isolation and measurement before adding fancy ecology.

## 1. Three independently owned systems

```text
                    RESEARCHER / CONFIGURATION
                                |
                     +----------v----------+
                     | ARENA / SUPERVISOR   |
                     | ticks, outcomes, RNG |
                     | health, age, energy  |
                     | spending, lineage    |
                     | immutable audit log  |
                     +-------+-------+-----+
                             |       |
                observations |       | validated actions
                             v       ^
                     +-------+-------+-----+
                     | TRUSTED LIFE CORE    |
                     | context, LLM gateway |
                     | per-agent state I/O  |
                     | candidate staging    |
                     +-------+-------+-----+
                             |       |
                    isolated |       | read-only world view
                  execution  v       ^
                      +------+-------+------+
                      | ORGANISM WORKSPACE  |
                      | soul.md             |
                      | memory/*.jsonl      |
                      | runbooks/*          |
                      | genome/strategy.py  |
                      | genome/tools/*      |
                      | snapshots/*         |
                      +---------------------+
```

The model gateway receives API credentials from a host-side secret store **never mounted into any organism's execution sandbox**. Agent text cannot override cost limits, action validation or the arena's physical laws.

## 2. Proposed repository structure

```text
igor-life/
  README.md
  pyproject.toml
  configs/arena.yaml
  life_core/
    model_gateway.py          # measured calls, spend cap, request boundary
    context_builder.py        # fixed mission + editable soul + observed data
    organism_runtime.py       # choose action, update individual state
    memory.py                 # episodes, summaries, retrieval
    genome.py                 # versioned prompt and code modules
    skills.py                 # discovery of organism-owned modules
    mutation.py               # stage/test/archive candidate mutations
  arena/
    engine.py                 # deterministic event loop
    laws.py                   # immutable rule validation
    economy.py                # double-entry energy ledger
    weather.py                # state machine and effects
    contest.py                # objectively scored competition
    physiology.py             # health and age transitions
    reproduction.py           # later: cloning, mixing, assimilation
    observations.py           # private/public views
  execution/
    sandbox.py                # container process execution only
    validator.py              # contracts + test runner
  organisms/
    001/{soul.md,manifest.json,memory/,runbooks/,genome/}
    002/{soul.md,manifest.json,memory/,runbooks/,genome/}
  experiments/
    baselines.py
    evaluate.py
    heldout_worlds/
  tests/
  outputs/                    # gitignored: JSONL events, trial snapshots
```

We should *not* copy Igor's entire shell platform into the runtime. Igor's module/runbook designs are a useful influence, but the new arena must enforce independent per-organism state and stricter boundaries.

## 3. Agent boundaries and interface contracts

Every agent has a private, immutable `organism_id`, live genome hash, parent IDs, virtual balance, health, age and event cursor. The agent receives a **filtered observation** and returns a single schema-validated intent. Examples are in [`examples/`](examples).

Illustrative contract:

```python
from typing import Protocol, Any

class OrganismStrategy(Protocol):
    def decide(self, observation: dict[str, Any]) -> dict[str, Any]: ...

# Valid intent examples:
# {"action": "wait"}
# {"action": "observe", "target_id": "agent-002"}
# {"action": "compete", "game_id": "task-duel", "stake": 30}
# {"action": "environment_intervention", "effect": "fog", "duration_ticks": 1}
# {"action": "propose_mutation", "candidate_id": "local-commit-ab12"}
```

The proposed v0 strategy may use LLM calls through the trusted `model_gateway` tool or return an action from a deterministic algorithm. **Never let generated code invoke the LLM directly with real credentials.** The gateway meters actual input and output tokens, debits virtual energy and blocks calls past caps.

## 4. Memory model

### Independent layers

- `episodes.jsonl`: immutable per-agent events delivered by the arena.
- `beliefs.json`: organism-authored beliefs with source IDs, timestamps and confidence.
- `soul.md`: compact editable identity or policy context, with version history.
- `runbooks/`: named learned procedures, preconditions, expected benefit and empirical evidence.
- `genome/`: executable strategy and skills, with version hash and compatibility contract.
- `archive/`: older snapshots that the organism may choose to maintain (subject to cost).

Memory cost policy is an experimental parameter: charge for retrieval and LLM context tokens, and optionally charge virtual storage rent. Episodic records are for replay and audit; the agent must not be allowed to edit the referee's evidence.

## 5. Mutations

A mutation request should describe `target` (`soul`, `module`, `runbook`, `memory_policy`), candidate bytes, parent version, reason, test plan and estimated spend. The engine stages files in the organism's private workspace. A separate test worker performs:

1. Static parse / import and path policy validation.
2. Interface / JSON action contract checks.
3. Resource limits and timeouts.
4. Small deterministic smoke tests and parent-versus-candidate trial.
5. Optional agent-authored tests and known regression cases.
6. Snapshot and activation at a tick boundary.

Some validity tests are mandatory for host safety; better survival tests can be evolved and paid for by the organism. Never run agent tests with host authority or inside the supervisor process. A syntax check is insufficient protection.

## 6. World economy implementation

Use an immutable append-only **double-entry** ledger rather than mutable balances written by agents. Every transfer is atomic and balanced, e.g. escrow entry (debit A 30, credit escrow 30), then escrow payout. System mint/burn accounts must be explicit, with event type and rationale. Derive balances from ledger events, with cached materialized views checked against recomputation.

Two other budgets are independent:

- **Token ledger:** actual usage from API response/provider or conservative gateway cap if usage is missing.
- **Financial ledger:** gateway-level estimate/actual billed consumption with a hard real-money threshold and no auto-top-up or unbounded fan-out.

Pricing and model versions should be recorded on every call, not trusted from a static cost table alone.

## 7. The sandbox is a security boundary

Generated code may be accidentally harmful or adversarial. Use a restricted container/VM with:

- Non-root UID, no privileged mode, no Docker socket, no host networking.
- No outbound network by default; LLM requests only through brokered host action.
- Read-only runtime, private copy-on-write genome/workspace, explicit tiny writable scratch area.
- CPU, memory, process count, wall-clock, disk and output size quotas.
- No secrets, cloud metadata, host/home mounts, other organisms' directories or kernel device nodes.
- Denial of syscall/permission elevation routes via a layered sandbox policy.
- Enforced termination on timeout and safe parsing of returned JSON.

**Caveat:** Docker alone is not an infallible hostile-code security boundary. If experiments become adversarial, consider a stronger VM sandbox and expert review. Treat agent-provided prompts and source fragments as untrusted data, including prompt-injection attempts embedded in rivals' public code.

## 8. Event system

Every meaningful transition should produce JSONL event entries containing:

```json
{
  "event_id": "evt-000501",
  "run_id": "run-2026-001",
  "tick": 17,
  "actor_id": "agent-001",
  "type": "mutation_trial_completed",
  "payload": {"candidate_sha256": "...", "success": false, "cost_energy": 24},
  "parent_event_id": "evt-000499",
  "world_seed": 1234
}
```

Archive model parameters, input/output usage, effective prompt hash, code hash, benchmark version, environment conditions and source-provenance IDs. Avoid retaining external provider secrets or unrelated private data in public logs.

## 9. Recommended v0 technology and build order

- Python 3.11+, standard library and simple JSON/SQLite persistence; `pytest` for tests.
- Adapter for one provider or local model; do not build a multi-provider router before basic economics works.
- Separate one-iteration `decide()` from long-running agent chat. Spawn a new isolated process with retained memory between turns.
- One minimal game with a reference deterministic agent, then two LLM organisms.
- First mutate **soul prompts**, then one constrained Python strategy module.
- No distributed workers, Kubernetes, browser integration, email or arbitrary internet access initially.

### First vertical slice acceptance criteria

1. Two agents receive **different filtered observations** and submit valid independent actions.
2. A scored match transfers the correct virtual tokens once, under retries and process crashes.
3. Model gateway refuses further calls at a configured cap.
4. A bad code candidate is rejected/penalized without crashing world or affecting another agent.
5. A valid candidate persists across restart and can be reverted through explicit lineage.
6. Every state transition can be replayed from logs and model artifacts (allowing for recorded LLM nondeterminism).

## 10. What not to build initially

Browser agents, language migration across runtimes, arbitrary on-the-fly physics code, direct edit of opponent files, unrestricted system administrators, free-form internet access, parallel multi-region economies or agent-written evaluator rules. These can all obscure whether the basic learning/evolution mechanism actually works.
