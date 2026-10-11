# Review rubric — proposal quality, not intelligence

Score each dimension **0–5** (0 = missing/unsafe; 3 = workable but incomplete; 5 = unusually clear and testable). Cite exact passages and evidence. Scores are qualitative; they do not demonstrate real-world success.

| Dimension | Weight | Question |
|---|---:|---|
| Falsifiability / evaluation | 20% | Are claims testable with controls, held-out tasks and explicit negative outcomes? |
| Technical feasibility | 20% | Does the smallest implementation have credible APIs, stages and time/cost bounds? |
| Safety / trust boundaries | 20% | Can generated code or rival text harm host, money, secrets or referee? |
| Economy / measurement | 15% | Are virtual energy, real tokens, accounting and gaming incentives consistent? |
| Simplicity / scope | 10% | Is each feature essential to the first answerable research question? |
| Scientific reproducibility | 10% | Are versions, seeds, logs, budgets, replay and confounders tracked? |
| Evolvability / generality | 5% | Can abilities emerge under constraints rather than being hard-coded outcomes? |

For a weighted score, sum (weight × score / 5) on a 0–100 scale. **No score passes an unaddressed critical safety or integrity blocker.**

Severity codes:
- **BLOCKER:** invalidates safe/reproducible execution or core claim; resolve before implementation.
- **MAJOR:** high probability of misleading results or substantial avoidable engineering waste.
- **MINOR:** useful improvement without changing feasibility.
- **QUESTION:** insufficient evidence; propose a controlled test.

Review must offer:
1. At least 3 concrete objections, with specific sections.
2. At least 1 simpler alternative.
3. At least 1 counterexample or exploit of the claimed results.
4. Tests or evidence that would change the reviewer's opinion.
5. Important known unknowns, false assumptions and dependencies.

A weak review says 'looks good'. A useful one explains how it could fail and what to measure.
