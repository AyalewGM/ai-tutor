# Batch 2 mapping review — Grade 2 aliases (#282, Devin draft)

**Status:** DRAFT ANALYSIS — not submitted to the manifest. Held pending
batch-1 reviewer answers (#293) on range constraints, shared targets,
and missing-skill handling, since the same questions apply here.
`reviewed_by` is intentionally empty everywhere; Devin does not approve
its own proposals.

Scope: seven of eight Grade-2 aliases. `TELL_TIME_FIVE_MINUTES` deferred
to a measurement batch — clock-face reading is already a documented gap
from batch 1 (`TELL_TIME_HOUR_HALF_HOUR`), and it shares that gap.

## Records

### 1. `MATH.ELEMENTARY.NUMBER_SENSE.SKIP_COUNTING_PATTERNS`
- **Concept:** Skip-count by 5s/10s/100s; identify and extend number patterns within 1000.
- **Grade:** 2. **Standards:** 2.NBT.
- **Pack evidence:** `NUMBER_PATTERN`, `NUMBER_SEQUENCE`; samples continue skip-count sequences.
- **Candidate targets (ALL_OF):** `MATH.NS.COUNTING` (`WN.COUNT.SKIP`), `MATH.PATTERN.NUMERIC` (additive/multiplicative pattern continuation and rule diagnosis).
- **Caveat:** targets unbounded vs ≤1000.
- **Confidence:** High — both components have direct generator coverage.

### 2. `MATH.ELEMENTARY.PLACE_VALUE.HUNDREDS_TENS_ONES`
- **Concept:** Three-digit numbers as hundreds/tens/ones; count within 1000; read and write numbers to 1000.
- **Grade:** 2. **Standards:** 2.NBT.
- **Pack evidence:** `PLACE_VALUE_BASE_TEN`, `NUMBER_SEQUENCE`; decompose and missing-term samples.
- **Candidate targets (ALL_OF):** `MATH.NS.PLACE_VALUE`, `MATH.NS.COMPOSE_DECOMPOSE`, `MATH.NS.COUNTING`.
- **Caveat:** "read and write to 1000" partially covered (`NS.EXPANDED_FORM`, `NS.WORD_FORM` adjacent).
- **Confidence:** Medium-high — counting inclusion is the reviewable judgment call.

### 3. `MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_100`
- **Concept:** Fluently add and subtract within 100 via place-value strategies.
- **Grade:** 2. **Standards:** 2.NBT.
- **Pack evidence:** `ADDITION_WITHIN_100`; two-digit add/sub samples incl. regrouping.
- **Candidate targets (ALL_OF):** `MATH.NS.ADDITION`, `MATH.NS.SUBTRACTION` — same shape as batch-1 alias 3; range caveat ≤100.
- **Confidence:** High (pending the shared range-constraint answer).

### 4. `MATH.ELEMENTARY.ARITHMETIC.WORD_PROBLEM_WITHIN_100`
- **Concept:** One- and two-step add/sub word problems ≤100, unknowns in all positions.
- **Grade:** 2. **Standards:** 2.OA.
- **Pack evidence:** `WORD_PROBLEM_ADD_SUB_100`; contextual result/change-unknown samples.
- **Candidate targets (ALL_OF):** `MATH.NS.ADDITION`, `MATH.NS.SUBTRACTION` (`WORD.*` families incl. `MULTISTEP` for two-step).
- **Data flag:** pack sample "72 sheets, 38 used → 110" is a wrong seed answer (should be 34). Curriculum-owned; flagged not fixed.
- **Confidence:** Medium — inherits the batch-1 granularity question.

### 5. `MATH.ELEMENTARY.GEOMETRY.SHAPES_EQUAL_SHARES`
- **Concept:** Identify/draw shapes by attributes; partition circles and rectangles into halves, thirds, fourths.
- **Grade:** 2. **Standards:** 2.G.
- **Pack evidence:** `GEOMETRY_SHAPES`, `FRACTION_HALVES_THIRDS_FOURTHS`; samples count sides and identify shaded fractions.
- **Candidate targets (ALL_OF, partial):** `MATH.NF.FRACTION_MEANING` covers partition-into-equal-shares/fraction-of-a-whole semantics.
- **Gap:** shape identification/attribute classification at G2 has no canonical target (same gap as G1 `IDENTIFY_COMPOSE_SHAPES`; `MATH.GEO.SHAPES` is G3–5 classification).
- **Confidence:** Medium — reviewers decide if a partial mapping is acceptable or the shape half needs a new canonical skill first.

### 6. `MATH.ELEMENTARY.MEASUREMENT.LENGTH_COMPARE` — **UNMAPPED (documented gap)**
- **Concept:** Measure, estimate, and compare lengths in standard units.
- **Grade:** 2. **Standards:** 2.MD.
- **Nearest canonical:** `MATH.MEAS.UNIT_CONVERSION` (unit conversion — different operation); `MATH.GEO.MEASURE.*` (area/perimeter/volume). No "measure/compare length" skill exists.
- **Disposition:** UNMAPPED; missing capability recorded. The comparison sub-skill is subtraction-in-context, not a valid target by itself.

### 7. `MATH.ELEMENTARY.MEASUREMENT.MONEY_COUNT` — **UNMAPPED (documented gap)**
- **Concept:** Value of coin/bill collections; money word problems with $/¢ symbols.
- **Grade:** 2. **Standards:** 2.MD.
- **Nearest canonical:** `MATH.FIN.*` (budgeting, interest, discount) — all later-grade financial literacy, not coin counting. No valid target.
- **Disposition:** UNMAPPED; missing capability recorded.

## Batch summary

| Disposition | Aliases |
|---|---|
| Proposed (`ALL_OF`, high confidence) | 1, 3 |
| Proposed with caveat (medium) | 2, 4, 5 (partial) |
| Impossible today (missing canonical capability) | 6, 7 |

## Open questions carried from batch 1

1. Range constraints (≤1000, ≤100, ≤20) are not expressible on canonical skill targets — confirm the parameter-level convention.
2. Repeated identical target sets (±20/±100 and word-problem pairs) — confirm granularity is acceptable.
3. Missing capabilities now total: equal-sign meaning (G1), shape identify/compose (G1–G2), clock reading (G1–G2), length measurement (G2), money counting (G2). These are candidate new canonical skills — Curriculum-owned decision.
4. Third wrong pack seed answer found (`72 − 38 → 110`). Cumulative data-quality flag for Curriculum.
