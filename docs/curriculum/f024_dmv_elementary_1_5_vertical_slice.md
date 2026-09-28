# F-024 DMV Grades 1–5 Curriculum Expansion — Representative Vertical Slice

## Summary

This branch delivers the remainder of F-024's first-pass DMV elementary curriculum expansion:

- Virginia Grade 3 (the third jurisdiction Grade 3 slice).
- Maryland Grades 1, 2, 4, and 5.
- District of Columbia Grades 1, 2, 4, and 5.
- Virginia Grades 1, 2, 4, and 5.

The work uses the declarative curriculum-pack loader merged in PR #93 and the jurisdiction/version/skill/prerequisite/canonical framework from PR #92/#93. Each pack is a representative slice: a small number of curriculum-local skills, original authored problems across diagnostic/guided/independent/mastery modes, and shared deterministic problem-family generators/visuals. It is intentionally not exhaustive launch-ready coverage for every standard.

## Authoritative sources

### Maryland

- Maryland State Department of Education (MSDE) revised mathematics standards hub: https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx
- Grade 3 crosswalk (used as the Grade 3 source; the remaining grades use the same revised MCCRS family): https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Crosswalk-A.pdf

### District of Columbia

- Office of the State Superintendent of Education (OSSE) standards page: https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0
- Grades 3–5 adjusted blueprint: https://osse-migrate.dc.gov/sites/default/files/dc/sites/osse/page_content/attachments/mathematics-adjusted-blueprintGrades3_0.pdf

### Virginia

- Virginia Department of Education (VDOE) 2023 Mathematics Standards of Learning: https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics
- 2023 SOL instructional resources: https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources

## Architecture and design decisions

### Canonical reuse with strict learner-evidence isolation

The approved separation is preserved:

```text
Authoritative standard
→ curriculum-local skill
→ canonical mathematical concept
→ eligible problem families / representations
→ deterministic generated problem instance
→ learner evidence attached to the curriculum-local skill
```

All 15 packs map to the same canonical taxonomy where the mathematics is equivalent, but every jurisdiction, grade, and curriculum version has its own local `Skill` rows. `StudentSkill`, attempts, mastery events, sessions, review schedules, interventions, and awards reference only the curriculum-local skill. Canonical identity never automatically transfers evidence or progression.

### New problem families and generators

The Grade 3 packs only needed `EQUAL_GROUPS`, `EQUAL_SHARING`, `UNIT_FRACTION`, and `RECTANGLE_AREA`. Grades 1, 2, 4, and 5 required additional deterministic generators:

| Family | Typical grade(s) | Canonical concept area |
|---|---|---|
| `ADDITION_WITHIN_20` | 1 | Arithmetic within 20 |
| `SUBTRACTION_WITHIN_20` | 1 | Arithmetic within 20 |
| `ADDITION_WITHIN_100` | 2 | Arithmetic within 100 |
| `SUBTRACTION_WITHIN_100` | 2 | Arithmetic within 100 |
| `PLACE_VALUE_BASE_TEN` | 1–2 | Place value (tens/ones/hundreds) |
| `MONEY_COUNT` | 2 | Money |
| `TIME_TO_HOUR_HALF_HOUR` | 1–2 | Time |
| `MULTI_DIGIT_MULTIPLICATION` | 4 | Multi-digit arithmetic |
| `LONG_DIVISION` | 4 | Multi-digit arithmetic |
| `FRACTION_EQUIVALENCE` | 4 | Fractions |
| `FRACTION_ADD_SUBTRACT_LIKE` | 4–5 | Fraction operations |
| `FRACTION_MULTIPLY` | 5 | Fraction operations |
| `DECIMAL_PLACE_VALUE` | 5 | Decimals |
| `ANGLE_MEASUREMENT` | 4 | Angle measurement |
| `COORDINATE_PLANE` | 5 | Coordinate geometry |

### New deterministic visual specs

Visual specs are computed from stored parameters, never from an LLM:

- `ten_frame` for addition/subtraction within 20
- `base_ten` for place value
- `money` for coin collections
- `clock` for hour/half-hour time
- `angle` for angle measurement
- `coordinate_plane` for ordered pairs
- existing `array_model` and `fraction_bar` reused for Grade 3 concepts

## Pack inventory

### Grades 1–2 exhaustive expansion (this branch)

| File | Jurisdiction | Grade | Skills | Problems |
|---|---|---|---|---|
| `md-grade1-mccrs-2026_27.json` | Maryland | 1 | 8 | 64 |
| `md-grade2-mccrs-2026_27.json` | Maryland | 2 | 9 | 72 |
| `dc-grade1-ccss-2024_25.json` | DC | 1 | 8 | 64 |
| `dc-grade2-ccss-2024_25.json` | DC | 2 | 9 | 72 |
| `va-grade1-sol-2024_25.json` | Virginia | 1 | 8 | 64 |
| `va-grade2-sol-2024_25.json` | Virginia | 2 | 9 | 72 |

Grades 1–2 totals: 6 packs, 51 curriculum-local skills, 408 original authored problems.

### Grades 3–5 representative vertical slices (merged in earlier PR)

| File | Jurisdiction | Grade | Skills | Problems |
|---|---|---|---|---|
| `md-grade3-mccrs-2026_27.json` | Maryland | 3 | 9 | 72 |
| `md-grade4-mccrs-2026_27.json` | Maryland | 4 | 10 | 80 |
| `md-grade5-mccrs-2026_27.json` | Maryland | 5 | 9 | 72 |
| `dc-grade3-ccss-2024_25.json` | DC | 3 | 9 | 72 |
| `dc-grade4-ccss-2024_25.json` | DC | 4 | 10 | 80 |
| `dc-grade5-ccss-2024_25.json` | DC | 5 | 9 | 72 |
| `va-grade3-sol-2024_25.json` | Virginia | 3 | 9 | 72 |
| `va-grade4-sol-2024_25.json` | Virginia | 4 | 10 | 80 |
| `va-grade5-sol-2024_25.json` | Virginia | 5 | 9 | 72 |

All 15 packs total: **141 curriculum-local skills, 1,104 original authored problems**.

## Content generation helper

`scripts/generate_elementary_packs.py` is a one-time content-authoring utility for Grades 3–5, and `scripts/generate_elementary_packs_1_2.py` produces the expanded Grades 1–2 packs. They are not runtime code. The committed JSON packs are the source of truth for the loader.

## Verification

- Ruff clean on all changed Python files.
- All 15 packs parse and validate against `ElementaryPack`.
- `scripts/seed_all_elementary_packs.py` loads all 15 packs idempotently.
- Added `scripts/generate_elementary_packs_3_5.py` to expand Grades 3–5 packs with comprehensive standards coverage.
- Added `docs/curriculum/misconceptions/grades_3_5.json` catalog mapping canonical concepts to deterministic misconception patterns and remediation strategies.
- Comprehensive test suite: all 15 packs, cross-jurisdiction canonical reuse, evidence isolation, prerequisite-edge isolation, skill-code uniqueness, and Grades 1–5 misconception catalog validation.
- Full backend suite on a fresh isolated database: **293 passed, 1,762 warnings**.

## Scope and remaining work

All DMV Grades 1–5 now have broader standards coverage and Grades 1–5 misconception/remediation catalogs. This is a substantial step toward launch readiness but is not yet exhaustive. Remaining before any grade/jurisdiction can be marketed as supported:

- Cross-grade prerequisite graph and review-scheduling wiring.
- Misconception detection integration into the tutoring engine and adaptive remediation flows.
- Additional visual types (number lines, rulers, bar graphs, picture graphs, shape geometry).
- Full tablet/mobile accessibility and synthetic E2E coverage for younger learners.
- Full problem-generation tests for every new problem family.
- QA, Security/Data Impact, PO, and PM acceptance per `docs/qa/DEFINITION_OF_DONE.md`.

No Ontario/MTH1W (F-025) files were modified.
