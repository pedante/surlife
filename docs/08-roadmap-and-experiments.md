# 08 — Roadmap, feasibility, risks and experimental evaluation

## 1. Research objectives, in order

**Primary question:** Does giving an agent the ability to rewrite its prompt *and* develop reusable code produce better measured performance per actual model token than prompt-only evolution?

**Secondary questions:** Do public rival observations help? Does environmental manipulation reward anticipation? Can good testing/recovery strategies emerge under a survival budget? Does offspring inheritance retain progress? Does diversity persist?

These are hypotheses, **not outcomes**.

## 2. Milestones and explicit gates

| Stage | Build | Required evidence to continue |
|---|---|---|
| **M0: Sim-only** | Referee, ledger, weather and deterministic reference policies; zero LLM | Correct economics, deterministic tests and replay |
| **M1: Prompt organisms** | Two–four souls, memory, observations, gateway, one competitive game | Agents act autonomously, token caps work, events reproducible |
| **M2: Hybrid mutation** | One isolated Python module, candidate testing and rollback | Valid candidate can improve benchmark; invalid candidate cannot damage host/world |
| **M3: Social & weather** | Public code exposure, rival analysis, priced drought/fog | Agents can adapt to environmental shifts without breaking invariants |
| **M4: Heredity** | Cloning, selected memory inheritance, parent→child resource split | Parentage/recombination and capital conservation are correct |
| **M5: Advanced ecology** | Aging, serious illness, mating, assimilation and optional novel declarative weather | Meaningful experimental advantage over simpler worlds; acceptable cost |

**Stop rule:** do not add features to mask a failure at an earlier gate. A simpler honest simulation is preferable to a feature-rich but scientifically unreadable one.

## 3. The minimum meaningful controlled experiment

Use one task arena with hidden task instances and seeded conditions. Start with **the same trusted core and the same initial executable strategy**; vary souls using a fixed documented seed. Duplicate the population into treatment groups with equivalent starting budget.

| Group | Can edit soul? | Can edit code? | Can inspect rivals? |
|---|---|---|---|
| Control | No | No | Observes public results only |
| P: prompt-only | Yes | No | Same public results |
| C: code-only | No | Yes | Same public results |
| H: hybrid | Yes | Yes | Same public results |
| H+social | Yes | Yes | Paid public-code inspection |

Run with the same weather schedule and opportunities where possible. Later randomize weather and introduce environmental interventions. Use multiple random seeds and enough repeated matches to estimate uncertainty, instead of reporting one winning lineage.

## 4. What to measure

### Useful performance

- **Held-out score** (unseen opponents/tasks) at the same evaluation budget.
- **Energy efficiency:** verified reward or correct tasks per 1,000 **actual** LLM tokens, plus CPU/runtime cost.
- **Survival:** duration active under given resources; distinguish healthy activity from idle survival.
- **Skill reuse:** actions completed using inherited/deterministic code without LLM calls.

### Evolution and inheritance

- Parent→offspring gain under the **same** starting balance and difficulty.
- Diversity of executable strategies (behavioral profiles and code hashes, not just different names).
- Mutation success/regression rate, test cost, rollback rate and repeated failures.
- Genotype changes correlated with success across independent worlds.

### Social/ecological effects

- Gains from studying competitors' published code and publicly visible mistakes.
- Relative fitness after drought/fog/storm vs normal conditions.
- Cost and net return on purchased environmental interventions.
- Resource inequality, population collapse, cooperative trades and frequency of extinction.

### Reliability / reproducibility

- Model/API tokens per turn, billed costs, failed calls, truncated contexts.
- Percentage of valid action JSON responses and benchmark replays.
- Validation failures, crashes, sandbox termination and policy violations.
- Integrity checks on ledger, genealogy and event-stream replay.

## 5. Confounders and failure modes

| Risk | How it can mislead us | Required countermeasure |
|---|---|---|
| Rich-get-richer | Early luck creates unstoppable capital advantage | Start-budget normalization; compare agent at equal capital |
| Reward hacking | Exploits game implementation rather than useful ability | Held-out tasks, independent scorer, negative tests |
| Inconsistent judge | LLM referee changes standards | Deterministic scoring whenever possible |
| Model upgrade | Provider changes model over generations | Log model ID/version; pin where possible |
| More thinking = higher score | Hybrid may simply spend more | Equal actual token/cost conditions and efficiency metrics |
| Hidden intervention effects | World change accidentally benefits sponsor only | Public rules and effect logs; self-applied effects |
| Bad code crashes | False 'death' from environment defect | Sandbox/run tests; distinguish host failure vs game defeat |
| Prompt injection | Rival's published code tries to override core instructions | Trust separation; sanitize tool outputs; no credentials in runtime |
| Overcomplexity | Hard to determine which feature helped | Ablations; release gates; small module boundaries |
| Species monoculture | One lineage eliminates all alternatives | Independent populations and quality-diversity analyses |

## 6. Budgets and pragmatic feasibility

Begin with deterministic M0 tests **without calling any LLM**. Then choose a hard real spend ceiling (e.g. €5–€10 for a small first research run), separately from virtual energy. A gateway can enforce maximum per-request tokens, aggregate real-budget allowances, concurrency and call counts; a provider-side account ceiling is an additional defense.

A very small LLM budget may support only dozens to hundreds of useful deliberations depending on model, prompt length, test feedback and model pricing. Do not promise a specific generation count. Estimate cost from measured runs; track input and output tokens separately.

Development estimates discussed earlier (several weeks for a small ecosystem, several months for reliable code-evolving populations) are **order-of-magnitude guesses for an experienced solo developer**. They are not confidence-calibrated probabilities or independently validated schedules. A scientific claim of sustained open-ended improvement has no credible completion estimate.

## 7. Engineering tasks for M0 / M1

- [ ] World rules schema and deterministic reducer.
- [ ] Separate secret-free organism workspaces and identities.
- [ ] Immutable virtual token ledger with invariant tests.
- [ ] A measurable game with non-LLM reference agents.
- [ ] Weather update and one bounded environmental intervention.
- [ ] Action schema, invalid-action penalties and event log.
- [ ] LLM gateway with real usage measurement, concurrency and spend cap.
- [ ] Soul prompt, episode memory and optional reflection.
- [ ] Two-agent match that persists state across process restarts.
- [ ] Frozen evaluation task set and separate hidden test set.

## 8. Engineering tasks for M2

- [ ] One tiny, safe, fixed contract for a mutable Python strategy module.
- [ ] Per-organism snapshots and candidate hashes.
- [ ] Isolated worker with hard CPU/memory/time/output limits.
- [ ] Static parser, import checks and schema tests.
- [ ] A repeatable trial comparing candidate against parent.
- [ ] Mutation transaction with activation at tick boundary.
- [ ] Observation logs the agent can cite when explaining an improvement.
- [ ] No leaked secrets, privileged mounts or unrestricted network.

## 9. Possible initial research outcomes

1. **No meaningful evolution:** prompts change, but held-out performance remains flat. Interesting negative result; revisit incentives and task diversity.
2. **Prompt-only wins:** code writing/maintenance isn't economically worthwhile in this world; change task recurrence and compare.
3. **Hybrid wins:** measured efficiency rises because executable skills amortize LLM costs; confirm against baselines and matched budgets.
4. **Population collapse:** resource inflow/upkeep mismatch; learn about economics before adding biologically inspired mechanics.
5. **Environmental arms race:** interventions shift advantages back and forth; test whether this creates innovation or merely wasted energy.

**Success for v0 is a trustworthy, replayable experiment—not spectacular artificial intelligence.**
