# Batch 1 mapping review — Grade 1 aliases (#282, Devin proposals)

**Status:** PROPOSED — awaiting independent mathematical review. `reviewed_by` is intentionally null; Devin does not approve its own proposals.
**Evidence basis:** DC/MD/VA pack skill descriptions, standards refs, pack problem families, sampled pack problems, and runtime `FAMILIES` family coverage. Pack problems flagged where seed data looks wrong.

## Records

### 1. `MATH.ELEMENTARY.NUMBER_SENSE.COUNT_COMPARE_TO_120`
- **Concept:** Count, represent, compare, and order whole numbers up to 120.
- **Grade:** 1. **Standards:** 1.NBT.
- **Pack evidence:** `NUMBER_SEQUENCE`, `COMPARE_NUMBERS` families; samples count forward and compare two-digit numbers.
- **Proposed targets (ALL_OF):** `MATH.NS.COUNTING` (count forward/backward/skip, sequence, between), `MATH.NS.COMPARE_ORDER` (compare/order whole numbers).
- **Caveat:** canonical targets are unbounded ranges; source constrains to ≤120. "Read and write numerals" is partially covered (no dedicated numeral-writing skill — `MATH.NS.WORD_FORM`/`MATH.NS.EXPANDED_FORM` are adjacent but not the G1 expectation).
- **Confidence:** High for the core pair.

### 2. `MATH.ELEMENTARY.PLACE_VALUE.TENS_ONES`
- **Concept:** Two-digit numbers represent tens and ones; special cases (10 as a bundle; teen numbers).
- **Grade:** 1. **Standards:** 1.NBT.
- **Pack evidence:** `PLACE_VALUE_BASE_TEN`; samples ask "how many tens and ones make 45".
- **Proposed targets (ALL_OF):** `MATH.NS.PLACE_VALUE` (identify place, digit value), `MATH.NS.COMPOSE_DECOMPOSE` (compose/decompose place-value parts).
- **Caveat:** targets span multi-digit ranges beyond two-digit; decomposition into 10-as-a-unit vs 10 ones is G1-specific.
- **Data flag:** one pack sample asks "hundreds, tens, and ones make 385" under a G1 tens/ones skill — misplaced seed item.
- **Confidence:** High.

### 3. `MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20`
- **Concept:** Add and subtract within 20 with strategies (counting on, making ten, add/sub inverse relationship); fluency within 10.
- **Grade:** 1. **Standards:** 1.OA.
- **Pack evidence:** alias backs two jurisdiction skills (`*.OA.ADDITION_20`, `*.OA.SUBTRACTION_20`); `ADDITION_WITHIN_20`, `SUBTRACTION_WITHIN_20` families; samples are direct facts.
- **Proposed targets (ALL_OF):** `MATH.NS.ADDITION`, `MATH.NS.SUBTRACTION`.
- **Caveat:** canonical skills are broader (multi-digit regrouping, estimation, properties). The mapping claims the ≤20 band of both operations; range constraint must be enforced at problem parameters, not the skill level.
- **Confidence:** High for the operation pair; review should confirm the range-subset claim is acceptable.

### 4. `MATH.ELEMENTARY.ARITHMETIC.WORD_PROBLEM_WITHIN_20`
- **Concept:** Single-step contextual add/sub problems ≤20; add-to, take-from, put-together, take-apart, compare; unknowns in various positions.
- **Grade:** 1. **Standards:** 1.OA.
- **Pack evidence:** `WORD_PROBLEM_ADD_SUB_20`; samples are result-unknown contexts.
- **Proposed targets (ALL_OF):** `MATH.NS.ADDITION`, `MATH.NS.SUBTRACTION` — both skills carry `WORD.*` families covering result/change/start-unknown and comparison subtypes.
- **Caveat:** identical target set to alias 3 — correct but exposes a granularity issue: the canonical taxonomy does not separate computational fluency from contextual application. Reviewers may prefer a dedicated `MATH.NS.WORD_PROBLEMS` skill.
- **Data flag:** pack sample "15 birds, 7 fly away → 22" is a wrong seed answer (should be 8).
- **Confidence:** Medium — correct targets, but granularity decision belongs to reviewers.

### 5. `MATH.ELEMENTARY.ARITHMETIC.EQUATION_BALANCE`
- **Concept:** Meaning of the equal sign; determine unknown whole numbers in add/sub equations.
- **Grade:** 1. **Standards:** 1.OA.
- **Pack evidence:** `EQUATION_BALANCE`; samples are missing-addend form (`5 + __ = 9`).
- **Proposed targets (ALL_OF):** `MATH.NS.ADDITION`, `MATH.NS.SUBTRACTION` — covers missing-addend/subtrahend/minuend families.
- **Gap:** **no canonical skill covers the meaning of equality** (true/false equations such as `6 = 6`, `7 = 8 − 1`). `MATH.EE.EQUATION.ONE` is algebraic one-step solving (inverse operations on `x + a = b`) — wrong grade and wrong operation. Recorded as missing capability; reviewers decide whether partial mapping suffices or a new canonical skill is required.
- **Confidence:** Medium — unknowns covered; equality meaning uncovered.

### 6. `MATH.ELEMENTARY.GEOMETRY.IDENTIFY_COMPOSE_SHAPES` — **UNMAPPED (documented gap)**
- **Concept:** Defining vs non-defining attributes; build/draw shapes; compose 2-D shapes into larger shapes.
- **Grade:** 1. **Standards:** 1.G.
- **Pack evidence:** `GEOMETRY_SHAPES`; samples count sides of basic shapes.
- **Nearest canonical:** `MATH.GEO.SHAPES` — "classify quadrilaterals by properties" (attribute classification, G3–5 band). G1 identify/compose is a different operation; not a valid target.
- **Disposition:** left `UNMAPPED`; missing canonical capability recorded rather than forcing a bad equivalence.

### 7. `MATH.ELEMENTARY.MEASUREMENT.TELL_TIME_HOUR_HALF_HOUR` — **UNMAPPED (documented gap)**
- **Concept:** Tell and write time to hour and half-hour on analog and digital clocks.
- **Grade:** 1. **Standards:** 1.MD.
- **Nearest canonical:** `MATH.MEAS.TIME` — its families are unit conversion (hours↔minutes) and elapsed time. Clock-face reading is a different operation; not a valid target.
- **Disposition:** left `UNMAPPED`; missing canonical capability recorded.

## Batch summary

| Disposition | Aliases |
|---|---|
| Straightforward composite (`ALL_OF`, high confidence) | 1, 2, 3 |
| Proposed with caveat/gap (medium) | 4, 5 |
| Impossible today (missing canonical capability) | 6, 7 |

## Reviewer asks

1. Is the unbounded-range caveat on `MATH.NS.*` acceptable for "within 20 / to 120" sources, or must the contract record a range constraint?
2. Aliases 3 and 4 share identical targets — acceptable taxonomy granularity?
3. Should missing capabilities (equal-sign meaning, G1 shape identification/composition, clock reading) become new canonical skills (Curriculum-owned) rather than recorded gaps?
4. Two pack seed answers are wrong (12,13,14,15,16,→13; 15 birds → 22). Flagged for Curriculum — not corrected here.
