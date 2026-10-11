# 04 — What counts as 'life' in this experiment?

**Status:** brainstorming and possible operational definitions. A simulation may exhibit life-like processes without being conscious or biologically alive.

## 1. Minimal operational definition

Call an entity a **digital organism** when it has all of:

1. **Persistent identity** across distinct turns.
2. **Boundary:** its own mutable genome, memory and allocated virtual resources.
3. **Metabolism:** consumes finite resources when processing, acting and maintaining itself.
4. **Perception:** senses at least some external state and its own internal state.
5. **Agency:** chooses actions that can affect later states.
6. **Variation / adaptation:** its strategy or internal state can change as a function of experience.
7. **Lifecycle:** can be born, age, decline and die within the world.

A *self-evolving population* additionally needs inheritance, variation among descendants and differential persistence/reproduction. In v0 we can build organisms without implementing the full population genetics.

## 2. Soul = editable initial identity

The 'soul' is a concise, heritable **agent-owned prompt**, e.g. values, curiosity, willingness to cooperate, preferred problem-solving style, self-description and what it considers worthwhile. The life mission is a separate **noneditable arena prompt**: survive within the laws, act, observe and learn.

Soul influences choices but is not an emotion meter. An aggressive initial soul may become cooperative; a cautious one may learn to take risks. It can rewrite its soul at token cost and preserve the revisions. Different initial souls can seed diversity even with identical core code.

### Open ideas

- Can an agent split identity from transient mood/state?
- Should descendants inherit the parent's original soul, latest soul, or a weighted combination?
- Can it intentionally discard inherited priorities?
- Can long-term memory be valuable even if no longer included in the prompt?

## 3. Code as body; prompts as soft genetic material

An organism possesses an editable strategy, tools and runbooks. Some behaviors come from the prompt, some from executable code. The code is valuable because it can perform repeatable work without new model calls. Code may also break. Testing/rollback mechanisms can be evolved as survival advantages, but an external sandbox is mandatory.

**Avoid conflating mechanisms:** self-description ≠ actual self-knowledge; prompt edit ≠ neural network training; code rewrite ≠ evidence of improved fitness.

## 4. Health and illness

Proposed health tiers: `healthy → mild → serious → critical → dead`. A healthy organism may initially receive **at most mild damage in one incident**; subsequent risks may worsen with existing illness. Recovery, rest and repaired modules can improve health. This is an *arena rule*, not a realistic medical model.

Potential game effects:

| Tier | Observable impact | Simulated vulnerability |
|---|---|---|
| Healthy | Full allowed actions | No special penalty |
| Mild | Small maintenance cost or action inefficiency | Increased chance of future damage |
| Serious | Restricted tool budget, memory/reliability disruption | Slower recovery, fewer opportunities |
| Critical | Little remaining effective agency | Can die if untreated |
| Dead | No new actions | Archived only |

An organism cannot access or change real LLM credentials, provider spending limits or the referee because it is 'critically ill'. Impairment is represented by simulator-controlled virtual budgets and capabilities.

**Research question:** would automatically recovering from every invalid code modification eliminate selection pressure for evolved testing? Compromise: never endanger the world, but let invalid mutations impose in-world costs (resource loss, missed actions or recoverable illness).

## 5. Age and development

Keep two separate measures: **chronological age** (arena ticks since birth) and **computational age** (cumulative model tokens / machine compute). Experience and memory can grow with age; maintenance burden, risk, rigidity or illness may increase. No rigid death clock is necessary.

Aging may generate novel strategies: conservation, teaching offspring, knowledge compression, retiring from competition, delegating, or deciding to reproduce sooner. It should not automatically guarantee wisdom.

## 6. Reproduction as inheritance

- **Asexual cloning:** copy versioned soul, genome and selected memories, then mutate. Parent transfers energy to offspring.
- **Two-parent recombination:** choose compatible prompt fields / module APIs from two parents and validate the offspring; fund from both or according to explicit contract.
- **Assimilation:** extract a capability, lesson or released public code from an organism after a contest or voluntary transaction; integrate with compatibility checks. *Not* a host file takeover.
- **Lineage:** parent IDs, birth tick, inherited modules, mutations and resource transfers are always recorded by the arena.

Offspring is a distinct identity and receives its own runtime state. The shared core is **not physically copied as evolutionary material**, though compatible modules can be inherited.

## 7. Death and persistence

Death ends the organism's ability to act. The supervisor archives its score, code hash, public history and genealogy. Private memory policies remain respected; death does not automatically grant opponents unlimited access to secrets. Resources can be burned, recycled or inherited according to explicit economic rules.

**Counterfactual:** should an organism be able to voluntarily terminate and redirect its resources to an offspring? Potentially interesting, but defer until reproduction is stable.

## 8. Observation, imitation and relationships

Agents see actions, public results, released strategy excerpts and perhaps coarse health/wealth signals. They can ask their LLM what another agent does better, infer errors or imitate an algorithm. Observed actions and published source are data, not privileged orders. They may compete, exchange, cooperate, imitate, lie or make wrong inferences inside the fictional world; these are behaviors to measure, not preinstalled human feelings.

A rival's success could induce **jealousy-like competitive behavior**, but we should not assign subjective jealousy unless studying an explicitly modeled emotion system.

## 9. Niche construction: agents change their environment

A key later insight: rather than writing into rivals' code, organisms spend scarce tokens to shift the conditions shared by everyone. Droughts, fog, abundance, resource redistribution and temporary reward shifts are examples. They affect the instigator too, making plans and anticipation relevant. This is **environmental engineering** or *niche construction* rather than direct software sabotage.

## 10. What is evolution here?

Keep three outcomes separate:

- **Learning in a lifetime:** memory/prompt/code improves during one organism's existence.
- **Inheritance:** descendant begins with useful elements without paying the original discovery cost.
- **Population-level evolution:** repeated differential success changes which traits and architectures persist.

A fourth concept, **open-endedness**, means continuing to develop novel useful structures rather than optimizing one fixed objective indefinitely. That is an ambitious *research question*, not a guaranteed feature.

## 11. Questions for discussion

- Should all organisms share one LLM model, or can they invest in different models?
- Does the ability to sleep/freeze preserve resources or merely delay death?
- Should memory take up virtual energy or only context tokens when retrieved?
- Should reproduction require maturity, a compatibility check or only capital?
- What should count as an agent's valuable 'part' during assimilation?
- Should world weather be predictable, partially predictable or random?
- Should a species identity emerge from ancestry instead of being assigned?
- Should agents have private goals beyond the survival mission?
- Can agents author new **environment effects** using limited declarative contracts?
- How do we measure genuine intelligence improvements independent of luck, lifespan and capital?

**Working answer:** start with the smallest operational definition capable of producing meaningful variation and cost-sensitive learning; add biological metaphors only when they produce testable effects.
