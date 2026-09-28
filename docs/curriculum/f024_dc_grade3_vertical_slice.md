# F-024 research and architecture decision: District of Columbia Grade 3 vertical slice

## Decision

The second DMV Grades 1–5 implementation slice is **District of Columbia Grade 3**, based on the Common Core State Standards adopted by DC through the Office of the State Superintendent of Education (OSSE), school year 2024–25.

Grade 3 is deliberately representative rather than exhaustive. It exercises the same four elementary structures as the Maryland slice — equal groups, equal sharing, unit fractions, and rectangular area — so that the architecture can demonstrate cross-jurisdiction reuse of canonical concepts, problem generators, and visual representations without any sharing of learner evidence.

This slice does **not** claim support for all DC Grade 3 standards or any other DMV grade/jurisdiction. Remaining packs stay gated by their own authority/version review and content-depth acceptance.

## Authority and effective version

Primary authority: **Office of the State Superintendent of Education (OSSE)**.

- DC Standards of Learning overview: https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0
- Adjusted Blueprint Mathematics Grades 3–5 (target sampling and assessment targets): https://osse-migrate.dc.gov/sites/default/files/dc/sites/osse/page_content/attachments/mathematics-adjusted-blueprintGrades3_0.pdf

The District of Columbia has adopted the Common Core State Standards for Mathematics through OSSE. The curriculum identity therefore uses version `CCSS-OSSE-2024-25`; it does not silently overwrite a different DC framework version.

## Standards decomposition

The slice maps reviewed DC/Common Core standards structures to tutor-usable local skills:

| Curriculum-local skill | Standards basis | Canonical identity |
|---|---|---|
| Interpret Multiplication as Equal Groups | 3.OA.A / represent and solve problems involving multiplication and division | `MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS` |
| Interpret Division as Equal Sharing | 3.OA.A / represent and solve problems involving multiplication and division | `MATH.ELEMENTARY.DIVISION.EQUAL_SHARING` |
| Unit Fractions as Numbers | 3.NF.A / develop understanding of fractions as numbers | `MATH.ELEMENTARY.FRACTION.UNIT` |
| Rectangle Area with Unit Squares | 3.MD.C / understand concepts of area | `MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA` |

Mappings are metadata-only. `StudentSkill`, attempts, mastery events, sessions, review schedules, and awards continue to reference the DC Grade 3 local `Skill` IDs. Canonical identity must never transfer learner evidence between curricula, grades, jurisdictions, or versions.

## Prerequisite decisions

- Equal-groups multiplication precedes equal-sharing division because the slice uses multiplication/division as inverse structures.
- Equal-groups multiplication precedes rectangle area because rows × columns supplies the unit-square structure.
- Equal-sharing division precedes unit fractions in this slice because fair sharing supplies the equal-partition concept.

All edges are curriculum-local and seed-time validation rejects cross-curriculum edges.

## Original-content design

All prompts are authored for AI Tutor and carry explicit `AUTHORED` provenance and proprietary license metadata. No textbook, worksheet, assessment-bank, or commercial tutoring content was copied.

Each represented skill has four curated prompts across interpretation, computation, and short context forms, plus an application-owned parametric generator for fresh independent evidence. Parameters are stored with generated/curated mathematical state so visuals and answers are deterministic.

The slice is intentionally below the eventual launch-depth gate. Before DC Grade 3 can be labeled fully supported, every decomposed standard needs deeper diagnostic, guided, independent, remediation, misconception, mixed-review, and mastery-check inventories.

## Cross-jurisdiction reuse

This slice intentionally reuses the same canonical concepts and problem families as the Maryland Grade 3 slice:

- `MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS`
- `MATH.ELEMENTARY.DIVISION.EQUAL_SHARING`
- `MATH.ELEMENTARY.FRACTION.UNIT`
- `MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA`

The problem-family registry (`EQUAL_GROUPS`, `EQUAL_SHARING`, `UNIT_FRACTION`, `RECTANGLE_AREA`) and deterministic visual representations (array model, fraction bar) are also reused. This demonstrates the architectural goal: canonical mathematical identity enables shared generators and representations while learner evidence remains strictly tied to jurisdiction/version-local skills.

## Elementary UX and visualization decision

`EQUAL_GROUPS` and `RECTANGLE_AREA` problems emit an `array_model` visualization spec from stored rows/columns. `UNIT_FRACTION` problems emit a `fraction_bar` spec. The React renderer draws SVG circles, unit squares, or fraction bars and provides a text alternative. Coordinates and mathematical labels are application-computed; no LLM or image model determines the representation.

The representation is static in this slice, so it is naturally compatible with reduced-motion preferences. Future interaction must retain keyboard/non-drag alternatives and cannot alter correctness or mastery.

## Data and security impact

This curriculum/content slice adds no learner or parent PII and no external data flow. Tests use synthetic learners. No award, session, voice, analytics, or recording expansion is introduced.

## Remaining F-024 work

1. Implement Virginia Grade 3 as a separate declarative pack using the same loader.
2. Run the architecture validation checkpoint after MD + DC + VA Grade 3 to confirm cross-jurisdiction reuse and evidence isolation before expanding to Grades 1, 2, 4, and 5.
3. Add shared ten-frame, base-ten, clock, money, measurement, geometry, and elementary graph specs/renderers where needed by the Grade 3 concepts.
4. Add misconception catalogs and remediation paths per skill.
5. Add tablet/mobile accessibility and synthetic E2E coverage for younger learners.
6. Complete QA, Security/Data Impact, PO, and PM acceptance before any pack is marketed as supported.
