# F-024 research and architecture decision: Maryland Grade 3 vertical slice

## Decision

The first DMV Grades 1–5 implementation slice is **Maryland Grade 3**, revised Maryland College and Career Ready Standards (MCCRS), school year 2026–27.

Grade 3 is deliberately representative rather than exhaustive. It exercises four elementary structures that recur across Grades 1–5 and across Maryland, DC, and Virginia: equal groups, equal sharing, unit fractions, and rectangular area. It also requires an elementary deterministic visual (arrays), prerequisite remediation, generated fresh variants, and canonical-to-local mappings.

This slice does **not** claim support for all Maryland Grade 3 standards or any other DMV grade/jurisdiction. Remaining packs stay gated by their own authority/version review and content-depth acceptance.

## Authority and effective version

Primary authority: **Maryland State Department of Education (MSDE)**.

- Revised MCCRS overview and grade-level materials: https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx
- Grade 3 standards crosswalk: https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Crosswalk-A.pdf
- Grade 3 companion guide: https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Standard-Companion-Guide-A.pdf
- Maryland State Board adoption action (July 29, 2025): https://marylandpublicschools.org/stateboard/Documents/2025/0729/Maryland-College-and-Career-Ready-Standards-for-Math-A.pdf

The revised standards were adopted July 29, 2025 and identify implementation for school year 2026–27. The curriculum identity therefore uses version `MCCRS-revised-SY2026-27`; it does not silently overwrite the older Maryland/Common Core framework.

Secondary local context reviewed, but not treated as the standards authority for this state-level pack:

- MCPS Grade 3 mathematics: https://www.montgomeryschoolsmd.org/curriculum/math/elementary/grade3
- MCPS Grade 3 support sequence: https://www.montgomeryschoolsmd.org/curriculum/math-support/elementary/grade3

## Standards decomposition

The slice maps reviewed standards structures to tutor-usable local skills:

| Curriculum-local skill | Standards basis | Canonical identity |
|---|---|---|
| Interpret Multiplication as Equal Groups | 3.NOS.B / equal groups and composed units | `MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS` |
| Interpret Division as Equal Sharing | 3.NOS.B / partitive and quotative division | `MATH.ELEMENTARY.DIVISION.EQUAL_SHARING` |
| Unit Fractions as Numbers | 3.NOS.F / fractions built from unit fractions | `MATH.ELEMENTARY.FRACTION.UNIT` |
| Rectangle Area with Unit Squares | 3.GR.C / area and multiplication | `MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA` |

Mappings are metadata-only. `StudentSkill`, attempts, mastery events, sessions, review schedules, and awards continue to reference the Maryland Grade 3 local `Skill` IDs. Canonical identity must never transfer learner evidence between curricula, grades, jurisdictions, or versions.

## Prerequisite decisions

- Equal-groups multiplication precedes equal-sharing division because the slice uses multiplication/division as inverse structures.
- Equal-groups multiplication precedes rectangle area because rows × columns supplies the unit-square structure.
- Equal-sharing division precedes unit fractions in this slice because fair sharing supplies the equal-partition concept.

All edges are curriculum-local and seed-time validation rejects cross-curriculum edges.

## Original-content design

All prompts are authored for AI Tutor and carry explicit `AUTHORED` provenance and proprietary license metadata. No textbook, worksheet, assessment-bank, or commercial tutoring content was copied.

Each represented skill has four curated prompts across interpretation, computation, and short context forms, plus an application-owned parametric generator for fresh independent evidence. Parameters are stored with generated/curated mathematical state so visuals and answers are deterministic.

The slice is intentionally below the eventual launch-depth gate. Before Maryland Grade 3 can be labeled fully supported, every decomposed standard needs deeper diagnostic, guided, independent, remediation, misconception, mixed-review, and mastery-check inventories.

## Elementary UX and visualization decision

`EQUAL_GROUPS` and `RECTANGLE_AREA` problems emit an `array_model` visualization spec from stored rows/columns. The React renderer draws SVG circles or unit squares and provides a text alternative. Coordinates and mathematical labels are application-computed; no LLM or image model determines the representation.

The representation is static in this slice, so it is naturally compatible with reduced-motion preferences. Future interaction must retain keyboard/non-drag alternatives and cannot alter correctness or mastery.

## Data and security impact

This curriculum/content slice adds no learner or parent PII and no external data flow. Tests use synthetic learners. No award, session, voice, analytics, or recording expansion is introduced.

## Remaining F-024 work

1. Complete standards decomposition and content-depth readiness for Maryland Grades 1–5.
2. Independently verify and implement OSSE/DC Grades 1–5 and VDOE 2023 Grades 1–5 packs.
3. Add shared ten-frame, base-ten, clock, money, measurement, geometry, and elementary graph specs/renderers.
4. Add misconception catalogs and representation families per skill.
5. Add tablet/mobile accessibility and synthetic E2E coverage for younger learners.
6. Complete QA, Security/Data Impact, PO, and PM acceptance before any pack is marketed as supported.
