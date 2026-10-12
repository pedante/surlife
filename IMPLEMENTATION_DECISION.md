# Implementation decision IMPL-0001 — bounded offline M0

**Date:** 2026-10-11. **Status:** user-authorized prototype scope; merging still requires human maintainer review.

The maintainer expressly requested to proceed to actual implementation, preferring reuse where it genuinely reduces work, a small first experiment and proportionate rather than production-hardening security. **Approval is scoped to trusted, offline, model-free M0.** It does not authorize shell execution of model-generated code, access to secrets or unlimited provider usage.

## Accepted

- Small Python-native deterministic referee and two trusted reference organisms, objectively graded seeded resource-allocation task, virtual-energy mint/upkeep/stakes and conservation.
- SQLite one-transaction event + balance transfer journal with idempotent tick identity and deterministic replay from saved actions.
- Standard-library runtime and pytest contract tests; no third-party runtime agent services initially.

## Deferred with a falsifiable adoption gate

- **GEPA:** prompt mutation M1, compare candidate selection against a native baseline, include all optimizer model/verification costs.
- **mini-SWE-agent:** optional M2 code author, never unrestricted shell as the normal world action interface.
- **PettingZoo:** outward Parallel API adapter when an external RL policy is needed; verify environment parity including transfers and replay.
- **OpenSpiel:** held-out objective task sources for transfer tests.
- **DEAP:** population selection and inheritance only when lineages are real.
- **gVisor/VM:** host isolation decision before executing arbitrary LLM-generated Python, not for known bundled M0 policies.

## Security and epistemic limits

This local single-operator prototype contains **no API calls, credentials or untrusted code execution**. It makes no claim of safe adversarial sandboxing. Host model access, budget enforcement and later generated-code isolation remain separate admission gates. It also does **not** demonstrate self-learning, heredity, open-ended evolution or emergent intelligence.

**Evidence inputs:** the main repository charter and frozen iteration 0001, unmerged PRs #1–#6, and Reviewer 1 follow-up on PR #5. This decision neither merges R1/PR #4 nor rewrites any frozen proposal or previous critique.

**Stop/revisit:** if identical inputs fail to replay, conservation fails, test task headroom vanishes, or a candidate framework demonstrably reduces total maintenance and keeps the trust boundaries, re-evaluate the chosen baseline.
