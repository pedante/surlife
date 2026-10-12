# ADR-0003 — Population and adapter seams before the viewer

**Date:** 2026-10-12  
**Status:** accepted for the *opt-in offline infrastructure milestone* by user request  
**Supersedes:** none; M0–M2.1-C and ADR-0002 stay in effect.

## Context

Surlife has a hardcoded two-organism M0 referee and several historically versioned experiments. The user wants many interchangeable organisms and arenas, a future local-web spectator viewer, readable batch reports and an explicit path to reusing existing projects. Building an observer specifically for fixed `a`/`b` would make future research costly, while blindly adopting a large new arena/brain framework would threaten reproducibility, ledger authority, provider billing and simplicity.

## Decision

Introduce an additive `population-v1` reference controller: stable N-organism IDs, a typed organism decision/feedback protocol, an arena observation/settle protocol, contract compatibility checks, native small multi-agent task worlds and adapter wrappers around the **unchanged** two-player M0 and optional M2.0 fixtures. Record versioned events and scoped genomes/energy for a future viewer. Keep the default simulation fast and deterministic, allow a controller to pace session steps externally, and maintain full offline replay.

**Do not** reimplement all historical M2.1-C prompt mutation within population-v1 yet. The initial population controller only uses trusted built-in scripted policies and no real provider calls or generated Python. It introduces no third-party runtime dependencies.

## Reasoning and alternatives

- **Hardfork all M0 protocols to N:** rejected because historical report verification and evaluation results would break.
- **Adopt PettingZoo or OpenSpiel immediately:** deferred; research inventory is static, no candidate has passed the existing security/replay/economy evaluation.
- **Build a graphical world first:** rejected as opposite to evolution-first direction; design the viewer over events and genome diffs, not simulated scenery.
- **Thin interfaces + native comparison:** chosen because a future external arena or brain can be inserted only after proving it passes seeded replay, strict action contracts and accounting.

## Scope, caveats and next checks

- `task-duel` uses deterministic round-robin two-player stakes within an N-player population, not an emergent social game.
- `task-work` provides a non-dueling objective control. One-person genome snapshots are constant in this milestone.
- The M2.0 ecology is an *optional compatibility fixture*, not the new project direction.
- Explicit maximum population and work bound reports and verifier runtime.
- Test sizes 2/3/4/5/8/16/64/128; task referee conservation; fair rotating byes; two-agent equivalence; legacy reports; invalid action preflight; incompatible brain refusal; deterministic replay and tampering; unchanged earlier CI.
- Next: evaluate PettingZoo/mini-SWE-agent against the native controllers using [reuse gates](../research/EVALUATION_PROTOCOL.md); human review required before bringing in external runtime dependencies.
