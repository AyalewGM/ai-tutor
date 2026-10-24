# One-variable data: original learning sequence (DRAFT)

**Scope:** reusable statistics mathematics, informed by private Ontario Grade 9 classroom demand. This document is not a published student lesson, accepted Ontario standards mapping, or runtime-ready course. The actual student interface, trusted scoring and mastery gates are not implemented.

## Teaching objective

Learners will classify data, select an appropriate display, compute and justify measures of center and spread, construct data satisfying simultaneous constraints, calculate quartiles under a stated convention, and distinguish ordinary and modified box plots. They will compare distributions on a common scale without treating an outlier as a data error or an IQR fence as an observed whisker endpoint.

**Quartile convention for this author slice:** order the observations, find the overall median, exclude that middle observation from the halves when the sample size is odd, and take the median of each half. Other legitimate quartile algorithms can give different values; the method must be explicit in prompts, scoring and accessible visual instructions.

## Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify

1. **Observe (concrete):** Learners inspect original community-data contexts: category labels, whole-number counts, measured distances, and a price restricted to quarter-unit increments. They predict whether values between two observed values are permitted. A discrete variable need not be integer-valued.
2. **Predict (visual):** Given a specific analytical question, learners choose a bar chart, histogram, circle chart or box plot. They predict how category gaps, numerical intervals, or the shared box-plot scale affect interpretation. Avoid the false rule that histograms require continuous-only data.
3. **Manipulate (concrete → visual):** Arrange movable observation cards in ascending order, divide an odd/even dataset into halves, identify Q1/median/Q3, and drag or keyboard-adjust labelled box landmarks. A sorted text table is an equivalent interaction.
4. **Explain (visual → symbolic):** Justify the IQR as Q3−Q1 and contrast the range with the middle-half spread. Show how an extreme observation can move the mean without moving the median nearly as much. No claim that the median is always the best center.
5. **Practice (symbolic):** Construct *any* valid five-observation nonnegative-integer dataset with specified mean, median, unique mode and range. Check the sum, ordering, frequency and extremes separately. The sample oracle is not the only acceptable answer.
6. **Diagnose (observed response):** Wrong answers lead to an error-specific Socratic question only in guided mode. Examples: mistaking quartiles for endpoints, using the mean despite an extreme, or ending a modified whisker at an outlier. Unrecognized responses receive neutral probing, not a fabricated diagnosis.
7. **Transfer (unseen):** Learners apply the same mathematical competency to numerically fresh independent tasks with different context/representation. Independent and mastery payloads have no hints, teacher answers or misconception exemplars.
8. **Verify (independent):** Teacher-only exact oracles and structured predicates check mathematical evidence. Server-trusted parsing, scoring, mode eligibility and mastery-event authority remain **NOT IMPLEMENTED** in this draft.

## Ordinary versus modified box plots

- **Ordinary min–max:** box edges are Q1/Q3; the median is the internal line; whiskers extend to the observed minimum and maximum. This does not identify outliers.
- **Modified 1.5×IQR:** compute lower fence `Q1 - 1.5*IQR` and upper fence `Q3 + 1.5*IQR`. Values strictly outside are marked separately. Whiskers stop at the smallest/largest **observed non-outlier** values, not at the fence numbers. A point on a fence is not an outlier by the strict rule.
- Use one labelled numerical scale for side-by-side comparisons; announce min, Q1, median, Q3, max, IQR, whiskers, fences and outlier values in reading order. Support keyboard controls, focus recovery, reduced motion, and non-colour equivalents.

## Boundaries and review

The eight generator families are a **bounded draft depth wave**, not proof of the Research-Driven Content Production Contract's 8–12 distinct families per substantial canonical skill. Existing mean/median/missing-mean and box-plot draft work is reused rather than forked. There is no new canonical skill identity, Ontario coverage credit, learner-facing lesson registration, question seeding, API route, trusted scorer, or historical Attempt/DiagnosticAttempt/MasteryEvent/variant change.

**Source policy:** private classroom handouts supplied only abstract task demand and page locators; no worksheet questions, datasets, figures or answer keys are reproduced. Ontario 2021 MTH1W D1.2 is an official *candidate* context pending independent mapping. NIST EDA and Penn State STAT 200/800 inform mathematical-method comparison; no external worked examples or graphics are copied.

**Handoffs:** Independent Math (oracles, alternative valid datasets, quartile convention, outlier endpoints); Independent Pedagogy (misconception diagnosis and true transfer); Independent Standards (publisher version, exact scope, licensing); Architecture (identity reuse); Assessment Backend (trusted equivalent-response and mode contract); Frontend/MVE (accessible box/graph interactions); Muse QA (synthetic browser and independence verification). No merge or activation until separately accepted.
