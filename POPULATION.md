# Population interfaces — multiple interchangeable organisms and arenas

**Implemented: population-v1 (2026-10-12).** Pure Python, opt-in, offline, **no real LLM requests**, no dynamic code execution. This is a foundation for many-agent evolution and future web observation; it does **not** claim the old M0–M2.1-C two-agent mutation experiments can already run with N evolving agents.

## Run it from the terminal

Install once: \`python -m pip install -e '.[test]'\`.

\`\`\`fish
# Eight individual organisms with their own identity and outcome history
surlife --multi --population 8 \
  --population-arena task-duel \
  --population-brains greedy,optimal,random,wait \
  --seed 17 --ticks 24 --provider fake \
  --benchmark-out out/population-8.json

# Verify from the report only: no provider calls, no environment access
surlife --verify-population-file out/population-8.json

# Same organisms, alternative task arena (no pairwise energy stakes)
surlife --multi --population 8 \
  --population-arena task-work \
  --population-brains greedy,optimal,random,wait \
  --seed 17 --ticks 24 \
  --benchmark-out out/work-comparison.json

# Prior M0 referee unchanged, via the common adapter boundary (2 organisms)
surlife --multi --population 2 --population-arena legacy-m0 \
  --population-brains greedy,optimal --seed 17 --ticks 24 \
  --benchmark-out out/legacy-m0.json

# OPTIONAL archived M2.0 ecology experiment, 2 organisms only
surlife --multi --population 2 --population-arena legacy-m20 \
  --population-brains steward,extractive --seed 17 --ticks 24 \
  --benchmark-out out/legacy-m20.json
\`\`\`

All paths must be new. Max 128 participants, max 512 ticks and max 4,096 organism-ticks per report protect artifact size and verification time. There is no deliberate delay; \`PopulationSession.step()\` can be called by an interactive controller once, paused by not calling it, or called in a tight loop for experiments.

## Implemented contracts

Located in \`src/surlife/population.py\`. These are Python protocols for **trusted adapters**, not permission to import organism-written modules directly.

- \`OrganismSpec(id, brain)\`: stable \`org-0001\` … \`org-0128\` identity, trusted strategy ID and content-derived genome hash.
- \`OrganismAdapter.decide(observation, rng) -> action\`: one per-organism runtime. \`feedback(own_result)\` receives only its own score/reward/energy, with an isolated bounded recent-outcome buffer. It must not receive a world/referee reference or rival private state.
- \`ArenaAdapter.observations() -> {organism_id: observation}\`: separate scoped view for each organism, with *no future challenges*. \`step(actions, consultations=None)\` is the only authority to settle validated actions and balances. It returns an event-bearing referee record.
- \`action_contract\`: \`task-mask-v1\` for mask-selection brains and \`habitat-action-v1\` for the optional old ecology policies. Incompatible combinations reject **before** running.
- \`PopulationSession.step()\`: freezes all observations, asks each brain for one action from an independent per-ID RNG, settles simultaneously, records one hash-linked event and sends only scoped private feedback.
- \`make_arena(name, seed, ids)\`: allowlisted trusted factory. The v1 controller does **not** support arbitrary Python import strings, downloadable brain plugins or unreviewed third-party frameworks.

Built-in arena adapters:

| Arena | Organisms | Action | What is reused |
|---|---:|---|---|
| \`task-duel\` | 2–128 | \`task-mask-v1\` | Existing M0 deterministic task generator/scorer, conservative energy rules; NEW rotating pair stakes and conservation checks |
| \`task-work\` | 2–128 | \`task-mask-v1\` | Same tasks/rewards, no pairwise staking; fairer cheap work baseline |
| \`legacy-m0\` | exactly 2 | \`task-mask-v1\` | **Original M0 Arena, untouched**, remapping only stable IDs and event field names |
| \`legacy-m20\` | exactly 2 | \`habitat-action-v1\` | **Original optional M2.0 PersistentArena**, untouched; cannot use model consultations |

Population pairing uses reproducible seeded **round-robin** matchups. Odd populations receive a rotating bye from *staking only*, not from opportunities to work on that tick. Live vs frozen model spending is **not** implemented by this population controller; the N-player mode uses trusted, offline reference brains.

## Viewer/report output

The new report has versioned keys \`manifest\`, \`events\`, \`summary\`, \`head\`. The manifest records stable organism IDs, each brain's contract/genome hash, arena rules and explicit zero-provider usage. Each \`events[]\` entry has:

- \`tick\`, \`arena\`, \`referee\` (raw task/environment outcomes, actions, transfers, pairings when relevant)
- \`energy\` for all organisms and \`genomes\` for inspected individuals
- \`previous_hash\` and \`event_hash\`, a deterministic hash chain starting from the manifest.

The report includes a simple summary of participants, ticks, survivors, per-agent energy, highest-energy organism and zero LLM spend. \`--verify-population-file\` replays all native and legacy scripted policies, scores and transfers from the manifest. It detects inconsistent modifications but **does not cryptographically authenticate** a report from someone able to replace the report and hashes.

This is the backend foundation for an upcoming browser observatory. It is deliberately not a UI: no web server, graphics, artificial rendering delay or unsafe live intervention endpoints have been introduced. A future interactive backend can own a single \`PopulationSession\`, call \`.step()\` or stop, and stream its events to many viewers without inventing a second simulation.

## How previously studied frameworks fit

Reuse research is **not abandoned**. See [foundation/research/REUSE_CANDIDATES.md](foundation/research/REUSE_CANDIDATES.md) and its [evaluation protocol](foundation/research/EVALUATION_PROTOCOL.md). Actual external projects have **not** passed those evaluations and are **not** dependencies of this milestone.

1. **PettingZoo / OpenSpiel / MAgent2:** candidate \`ArenaAdapter\` behind explicit, tested observation/action contracts. A PettingZoo wrapper cannot replace Surlife's sole ledger/referee authority or independently mint balances. Measure dependency overhead against this native multi-agent implementation first.
2. **mini-SWE-agent / nanobot:** candidate \`OrganismAdapter\` reasoning loops. Strip shell/browser/filesystem/model credentials; the host-owned gateway meters calls and returns only bounded model results to the organism.
3. **OpenEvolve / Darwin Gödel Machine:** candidate mutation archives and code-trial evaluators for M2.2. Generated source must be staged and tested inside a *real tested isolated worker*, never \`exec\` or an unconfined subprocess.
4. **Igor / Letta:** retain inspiration for bounded skills, versioned memories and lineage. Do not import trusted sysadmin facilities into organisms.

Evaluate **one** external arena and **one** brain against these small native references, with seeded tasks, full replay, independent agent state, no secret access, no unfunded transfers and reduced complexity. If a candidate fails, keep the adapter boundary without importing its package.

## What comes next

1. Test the PettingZoo Parallel API adapter against the native 2–8-player referee, then record an adopt/adapt/reject decision. Do not change trusted accounting simply to satisfy a library.
2. Connect M2.1-C response-bank and prompt mutation state to \`OrganismAdapter\`; now only *reference strategies* can inhabit the population API. Explicit scoped per-agent/model budgets and offline provider-bank replay are required before multi-agent LLM runs.
3. Add a minimal event-fed local web observatory. First focus on population overview, one-organism inspect, prompt/code diff where real data exists, tick scrubber and simple experiment report. The world is still a testing surface, not a physical simulation.
4. M2.2 generated Python modules only after hostile sandbox isolation passes. A shared API is **not** itself a sandbox.
