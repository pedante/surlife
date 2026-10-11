# 09 — Decision log and open questions

Document purpose: prevent the project from drifting and preserve why an option was chosen. These are **discussion-derived preferences**, not irrevocable decisions.

## Decision record

| ID | Direction | Status | Reason |
|---|---|---|---|
| D-01 | Use a **hybrid of mutable prompts and tested executable code** | Preferred | Lower entry cost of prompt edits + long-term efficiency of code |
| D-02 | Soul = an initial, heritable, **editable persona prompt** | Preferred | Individuality without pretending to model consciousness |
| D-03 | Life mission/world rules are distinct from the soul | Preferred | Everyone understands the same arena but may have different identities |
| D-04 | Start from **one shared protected player core** | Preferred | Shared interfaces and simpler reproduction/testing |
| D-05 | Python for referee and life core; Bash/Python skills optional | Preferred | Ecosystem support; integrates lessons from existing agents |
| D-06 | Keep prompt/code/memory versioned **per organism** | Preferred | Makes evolution and lineage measurable |
| D-07 | Competition moves **virtual tokens** from loser to winner | Preferred | Scarcity gives strategic meaning to thought and growth |
| D-08 | Prefer **environmental engineering** to directly editing rival code | Preferred | Richer indirect competition, simpler isolation |
| D-09 | Allow organisms to inspect public behavior and published code | Preferred | Social learning and imitation without privileged read access |
| D-10 | Add inheritance, mixing and assimilation after basic mutation | Sequenced | Arbitrary program recombination is difficult |
| D-11 | Health, age, recovery and death form simulated lifecycle | Tentative | Interesting evolutionary effects, but not required for first test |
| D-12 | Agents may evolve their own memory/repair/metabolism strategies **inside contracts** | Preferred | Preserve the more open-ended 'option B' direction |
| D-13 | The referee's accounting, API keys, immutable rules and sandbox boundaries are never editable by organisms | Hard constraint | Integrity, safety and meaningful measurement |
| D-14 | Reuse concepts from Igor/nanobot/Letta/DGM rather than merge full repositories | Recommended | Avoid accidental monolith and incompatible abstractions |
| D-15 | Validate actual improvement using held-out tests and matched spend | Hard scientific constraint | Protect against luck and reward hacking |

## Open design questions with first-pass recommendations

**O-01 — What is the first game?**  
*Recommendation:* an objectively scored, low-cost task duel plus reference deterministic agents. Avoid subjective LLM judges in v0.

**O-02 — Must organisms keep thinking continuously?**  
*Recommendation:* no. Choosing cheap deterministic actions or waiting is legitimate, but maintenance costs and limited opportunities prevent infinite idling from counting as success.

**O-03 — What counts as a virtual token?**  
*Recommendation:* create a unit called **energy**, distinct from actual provider tokens; use a priced conversion rule based on measured API use.

**O-04 — How much of a rival is visible?**  
*Recommendation:* public scores, actions and opt-in published modules; paid inspect for additional public detail. Private data stays private.

**O-05 — How much mutability in the 'laws of life'?**  
*Recommendation:* allow genome-owned physiology strategies and declarative environment proposals, not direct edits to supervisor source or billing.

**O-06 — What is inherited?**  
*Recommendation:* active tested modules, soul prompt, selected summaries, runbooks and small funded resources; parent provenance explicit.

**O-07 — Can a dead organism's code be assimilated?**  
*Recommendation:* only previously public/escrowed abilities until there is a well-defined privacy and loot contract.

**O-08 — Should weather be controlled or random?**  
*Recommendation:* partially stochastic with known parameters and fixed seeds for fair evaluation; interventions are bounded and observable.

**O-09 — Is there a population cap?**  
*Recommendation:* yes, initially very small (2–4) and enforce a total simultaneous model-call cap.

**O-10 — How is age modeled?**  
*Recommendation:* count chronological ticks and computational usage; introduce biological costs only after simpler dynamics work.

**O-11 — Are all organisms initially related?**  
*Recommendation:* common core and code interface, different soul prompts in first experiment; multiple ancestral genome architectures in a later ablation.

**O-12 — May the organism choose its model?**  
*Recommendation:* begin with a single model for scientific comparability; later add bounded model selection at explicit energy prices.

**O-13 — What do we import from existing projects?**  
*Recommendation:* audit nanobot and mini-SWE-agent against a tiny custom core. Borrow Igor runbooks and Letta-style memory layout; investigate DGM/OpenEvolve for candidate testing when needed.

**O-14 — How should illnesses affect code?**  
*Recommendation:* start with simulated constraints and costs, not random corruption of generated source. Physical code degradation may add noise without insight.

**O-15 — What proves the experiment has value?**  
*Recommendation:* descendants outperform parents and baselines on independent conditions **at matched actual token and energy budgets**, ideally across multiple seeds.

## Deferred concepts (do not silently reintroduce into v0)

- Direct write access to opponents' strategy/core files.
- Exposure of real API credentials as a result of in-world illness or defeat.
- Arbitrary agent-authored executable changes to the referee.
- Full desktop/browser/host shell control for every organism.
- Unlimited reproduction and unrestricted real-world spending.
- Automatic code recombination without interface validation.
- Claims that soul prompts create actual emotion or consciousness.

## How to update this log

For any design change, add a short entry containing date, owner, alternatives considered, decision, costs/tradeoffs, tests needed and whether it modifies the immutable experiment boundary. Keep design hypotheses separate from implemented behavior, and executed test results separate from expected outcomes.
