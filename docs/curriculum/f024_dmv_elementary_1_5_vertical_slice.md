# F-024 DMV Grades 1–5 Curriculum Expansion — First-Pass Exhaustive Coverage

## Summary

This branch delivers first-pass comprehensive coverage for F-024's DMV elementary curriculum track:

- Maryland Grades 1–5.
- District of Columbia Grades 1–5.
- Virginia Grades 1–5.

Each grade pack contains curriculum-local skills mapped to authoritative state standards, original authored problems across diagnostic/guided/independent/mastery modes, and shared deterministic problem-family generators/visuals. Grades 1–2 and Grades 3–5 misconception/remediation catalogs are included, and cross-grade prerequisite edges within each jurisdiction are wired automatically after loading the packs. The work uses the declarative curriculum-pack loader merged in PR #93 and the jurisdiction/version/skill/prerequisite/canonical framework from PR #92/#93. This is a substantial step toward launch-ready coverage but still requires tutoring-engine integration, accessibility, and QA/PO/PM acceptance before marketing any grade/jurisdiction as supported.

## Authoritative sources

### Maryland

- Maryland State Department of Education (MSDE) revised mathematics standards hub: https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx
- Grade 3 crosswalk: https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Crosswalk-A.pdf

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

### Cross-grade prerequisite wiring

Prerequisite edges within a grade come from each declarative pack. Edges that connect lower-grade skills to higher-grade skills within the same jurisdiction are added by `app/services/elementary_cross_grade_prerequisites.py` after all packs are loaded. The topology is declared once in grade/suffix form and reused across Maryland, DC, and Virginia, ensuring consistent pedagogy while keeping skill IDs and evidence isolated per curriculum.

### Problem families and generators

Deterministic generators added or extended for the expanded grades:

| Family | Typical grade(s) | Canonical concept area |
|---|---|---|
| `NUMBER_SEQUENCE` | 1–2 | Counting and number sense |
| `COMPARE_NUMBERS` | 1–2, 4 | Number comparison |
| `ADDITION_WITHIN_20` | 1 | Arithmetic within 20 |
| `SUBTRACTION_WITHIN_20` | 1 | Arithmetic within 20 |
| `WORD_PROBLEM_ADD_SUB_20` | 1 | Word problems |
| `ADDITION_WITHIN_100` | 2 | Arithmetic within 100 |
| `SUBTRACTION_WITHIN_100` | 2 | Arithmetic within 100 |
| `WORD_PROBLEM_ADD_SUB_100` | 2 | Word problems |
| `NUMBER_PATTERN` | 2, 4, 5 | Patterns |
| `EQUATION_BALANCE` | 1 | Equations |
| `COMPARE_LENGTH` | 2 | Measurement |
| `TIME_TO_HOUR_HALF_HOUR` | 1–2 | Time |
| `TIME_TO_5_MINUTES` | 2, 3 | Time |
| `MONEY_COUNT` | 2 | Money |
| `PLACE_VALUE_BASE_TEN` | 1–4 | Place value |
| `ROUNDING` | 3–4 | Place value |
| `FRACTION_HALVES_THIRDS_FOURTHS` | 1–2 | Fraction basics |
| `UNIT_FRACTION` | 3 | Fraction basics |
| `FRACTION_NUMBER_LINE` | 3 | Fractions as numbers |
| `FRACTION_EQUIVALENCE` | 3–5 | Fraction equivalence |
| `FRACTION_COMPARE` | 3–4 | Fraction comparison |
| `FRACTION_ADD_SUBTRACT_LIKE` | 4–5 | Fraction operations |
| `MULTIPLY_FRACTION_BY_WHOLE` | 4 | Fraction operations |
| `FRACTION_MULTIPLY` | 5 | Fraction operations |
| `ADD_SUBTRACT_UNLIKE_FRACTIONS` | 5 | Fraction operations |
| `DIVIDE_FRACTIONS` | 5 | Fraction operations |
| `DECIMAL_PLACE_VALUE` | 4–5 | Decimals |
| `DECIMAL_OPERATIONS` | 5 | Decimal operations |
| `POWERS_OF_TEN` | 5 | Place value |
| `MULTI_DIGIT_MULTIPLICATION` | 4 | Multi-digit arithmetic |
| `LONG_DIVISION` | 4 | Multi-digit arithmetic |
| `EQUAL_GROUPS` | 3 | Multiplication |
| `MULTIPLICATION_WITHIN_100` | 3 | Multiplication |
| `EQUAL_SHARING` | 3 | Division |
| `DIVISION_WITHIN_100` | 3 | Division |
| `WORD_PROBLEM_MULTIPLY_DIVIDE_100` | 3–4 | Word problems |
| `ELAPSED_TIME` | 3 | Time |
| `BAR_GRAPH_READ` | 1, 3 | Data |
| `PICTURE_GRAPH_READ` | 1, 3 | Data |
| `RECTANGLE_AREA` | 3 | Area |
| `AREA_PERIMETER_RECTANGLE` | 3 | Area/perimeter |
| `MEASUREMENT_CONVERSION` | 4–5 | Measurement |
| `VOLUME` | 5 | Volume |
| `ANGLE_MEASUREMENT` | 4 | Angles |
| `LINES_PARALLEL_PERPENDICULAR` | 4 | Lines |
| `CLASSIFY_SHAPE` | 1, 3–5 | Geometry |
| `COORDINATE_PLANE` | 5 | Coordinate geometry |

### Deterministic visual specs

Visual specs are computed from stored parameters, never from an LLM:

- `ten_frame` for addition/subtraction within 20
- `base_ten` for place value
- `money` for coin collections
- `clock` for hour/half-hour/five-minute time
- `angle` for angle measurement
- `coordinate_plane` for ordered pairs
- `array_model` and `fraction_bar` reused for Grade 3 concepts
- `ruler`, `shape`, `bar_graph`, and `picture_graph` for measurement and data

## Pack inventory

| File | Jurisdiction | Grade | Skills | Problems |
|---|---|---|---|---|
| `md-grade1-mccrs-2026_27.json` | Maryland | 1 | 8 | 64 |
| `md-grade2-mccrs-2026_27.json` | Maryland | 2 | 9 | 72 |
| `md-grade3-mccrs-2026_27.json` | Maryland | 3 | 9 | 72 |
| `md-grade4-mccrs-2026_27.json` | Maryland | 4 | 10 | 80 |
| `md-grade5-mccrs-2026_27.json` | Maryland | 5 | 9 | 72 |
| `dc-grade1-ccss-2024_25.json` | DC | 1 | 8 | 64 |
| `dc-grade2-ccss-2024_25.json` | DC | 2 | 9 | 72 |
| `dc-grade3-ccss-2024_25.json` | DC | 3 | 9 | 72 |
| `dc-grade4-ccss-2024_25.json` | DC | 4 | 10 | 80 |
| `dc-grade5-ccss-2024_25.json` | DC | 5 | 9 | 72 |
| `va-grade1-sol-2024_25.json` | Virginia | 1 | 8 | 64 |
| `va-grade2-sol-2024_25.json` | Virginia | 2 | 9 | 72 |
| `va-grade3-sol-2024_25.json` | Virginia | 3 | 9 | 72 |
| `va-grade4-sol-2024_25.json` | Virginia | 4 | 10 | 80 |
| `va-grade5-sol-2024_25.json` | Virginia | 5 | 9 | 72 |

All 15 packs total: **135 curriculum-local skills, 1,080 original authored problems**.

## Content generation helpers

- `scripts/generate_elementary_packs.py` — original one-time content-authoring utility for Grades 3–5.
- `scripts/generate_elementary_packs_1_2.py` — expanded Grades 1–2 packs.
- `scripts/generate_elementary_packs_3_5.py` — expanded Grades 3–5 packs.
- `app/services/elementary_cross_grade_prerequisites.py` — reusable cross-grade prerequisite wiring.
- `scripts/wire_elementary_cross_grade_prerequisites.py` — CLI wrapper for the wiring service.
- `app/services/elementary_misconception_loader.py` — loads JSON misconception catalogs into the database.
- `docs/curriculum/state_curriculum_addition_runbook.md` — guide for adding future state curricula.

These scripts are not runtime code. The committed JSON packs are the source of truth for the loader.

## Verification

- Ruff clean on all changed Python files.
- All 15 packs parse and validate against `ElementaryPack`.
- `scripts/seed_all_elementary_packs.py` loads all 15 packs idempotently and wires cross-grade prerequisites.
- Misconception catalogs: `docs/curriculum/misconceptions/grades_1_2.json` and `docs/curriculum/misconceptions/grades_3_5.json`.
- Added `app/services/elementary_cross_grade_prerequisites.py` to wire cross-grade prerequisite edges within each jurisdiction.
- Added `app/services/elementary_misconception_loader.py` to populate `Misconception` rows from the JSON catalogs for every curriculum-local skill.
- Added elementary misconception detection rules in `app/services/evaluation.py`.
- Added visual/accessibility metadata tests in `tests/test_elementary_visualization.py`.
- Added `docs/curriculum/state_curriculum_addition_runbook.md` documenting how to add future state curricula using the declarative framework.
- Comprehensive test suite: all 15 packs, cross-jurisdiction canonical reuse, evidence isolation, prerequisite-edge isolation, cross-grade prerequisite wiring, skill-code uniqueness, Grades 1–5 misconception catalog validation, misconception loading, and accessibility metadata.
- Full backend suite on a fresh isolated database: **296 passed, 1,762 warnings**.

## Scope and remaining work

All DMV Grades 1–5 now have broader standards coverage, Grades 1–5 misconception/remediation catalogs, cross-grade prerequisite wiring, and a state curriculum addition runbook. This is a substantial step toward launch readiness but is not yet exhaustive. Remaining before any grade/jurisdiction can be marketed as supported:

- Additional visual types (e.g., fraction number lines, place-value disks, 3D volume nets) and full tablet/mobile accessibility.
- Synthetic E2E coverage for younger learners covering diagnostic placement, guided practice, independent practice, mastery verification, review scheduling, and remediation flows.
- Full problem-generation tests for every new problem family.
- QA, Security/Data Impact, PO, and PM acceptance per `docs/qa/DEFINITION_OF_DONE.md`.

No Ontario/MTH1W (F-025) files were modified.
