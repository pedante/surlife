# Portable prompt — revise the canonical design after decisions

Role: proposal reviser. Do not start a fresh design from scratch.

Read CONTEXT.md, PLAN.md, the frozen proposal, actual review files, synthesis, and any explicit accepted decision records. Confirm which findings were accepted by the maintainer.

Tasks:
1. Implement accepted design changes with minimal scope expansion.
2. Preserve a coherent falsifiable hypothesis, API/resource boundaries, research controls, tests and staged milestones.
3. Keep rejected/deferred proposals visible in decision records; do not silently erase tradeoffs.
4. Update foundation/PLAN.md and create a new immutable iterations/NNNN/PROPOSAL.md with the same contents.
5. Create a next-iteration README/status entry and update STATUS.json after evidence is actually present.
6. Include a revision mapping: reviewer finding IDs → changed PLAN sections → expected benefit → required evidence.
7. Check links and report untested assertions.

If decisions are not explicit, **do not revise the canonical plan**. Return a recommended patch for approval instead. Do not implement runtime code in this mode. Record exact model/version and source commit when known.
