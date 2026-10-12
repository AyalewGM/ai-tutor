# District of Columbia Grades 6–8 CCSS expectation inventory and gap report

Status: **DRAFT / PROPOSED / NOT VERIFIED**
Inventory: `docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json`
Authority: Office of the State Superintendent of Education (OSSE)
Source checked: 2026-10-12

## Authoritative source

The District of Columbia adopted the **Common Core State Standards** verbatim through OSSE ([DC standards](https://osse.dc.gov/page/dc-standards)). Expectation identifiers are the canonical CCSS codes (`{grade}.{domain}.{cluster}.{number}`); the standards text is published at [thecorestandards.org](https://www.thecorestandards.org/Math).

**Unlike Maryland's 2025 re-domained MCCRS (NOS/AT/GR/DS), DC retains the legacy CCSS domains** — RP (Ratios & Proportional Relationships), NS (The Number System), EE (Expressions & Equations), G (Geometry), SP (Statistics & Probability), F (Functions). The Maryland crosswalk's legacy column and DC's live identifiers use the same codes; these are separate jurisdictions whose expectations must never be merged by identifier similarity.

This completes the DMV Grade 6–8 inventory set alongside `md_grades6_8_2025.expectations.v1.json` and `va_grades6_8_2023.expectations.v1.json`, closing the evidence-acquisition gap named in `grades1_9_gap_triage.wave1.md` for all three existing elementary-pack jurisdictions.

## Official expectation inventory

**80 top-level CCSS expectations** across Grades 6–8:

| Grade | RP | NS | EE | G | SP | F | Total | Seed-linked | Unmapped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 3 | 8 | 9 | 4 | 5 | — | 29 | 12 | 17 |
| 7 | 3 | 3 | 4 | 6 | 8 | — | 24 | 16 | 8 |
| 8 | — | 2 | 8 | 8 | 4 | 5 | 27 | 0 | 27 |
| **Total** | | | | | | | **80** | **28** | **52** |

## Repository state

- `scripts/seed_dc_grade6.py` (`DC_MATH_6`): 5 skills — `DC6.RP.RATIO`, `DC6.RP.UNIT_RATE`, `DC6.NS.FRACTION`, `DC6.EE.EXPR`, `DC6.EE.EQUATION`
- `scripts/seed_dc_grade7.py` (`DC_MATH_7`): 5 skills — `DC7.RP.PROPORTIONAL`, `DC7.RP.PERCENT`, `DC7.NS.RATIONAL`, `DC7.EE.EQUATION`, `DC7.SP.PROBABILITY`
- **Grade 8: no DC seed rows exist** (`DC_MATH_8` has no seed script; `seed_dc_algebra1.py` covers the separate Algebra I course).

### Material findings

1. **Grade 8 is a complete repository gap** — all 27 expectations unmapped: irrational numbers, exponents and scientific notation, slope and linear equations, systems, functions, transformations/congruence/similarity, Pythagorean Theorem, and bivariate data. Identical pattern to Virginia's Grade 8 gap and nearly identical to Maryland's `8.AT.*`/`8.GR.*` unmapped clusters — DC, MD, and VA converge on the same missing pre-algebra bridge.

2. **`DC7.SP.PROBABILITY` is an extreme composite** — a single seed row provisionally linked to all eight `7.SP` expectations (sampling, inference, probability scale, models, compound events). It cannot transfer mastery to distinct atomic identities per the #293 precedent.

3. **DC geometry coverage is zero across all three grades** — no `*.G.*` expectation has any linked seed (12 unmapped: area/volume/nets at G6, circles/angles/scale at G7, all of G8 geometry).

4. **Integer/rational-number scope is thin locally** — `6.NS.C.5`–`6.NS.C.8` (negatives, coordinate plane, absolute value) unmapped, mirroring the same gap in MD (`6.NOS.C.*`) and VA (`6.NS.2`, `6.CE.2`). A jurisdiction-agnostic integer learning experience exists (merged `GuidedIntegerNumberLine` work) but any local reuse needs Standards Mapping acceptance, not assumption.

5. **`6.EE.C.9`** (two-variable relationships) has no candidate — the `DC6.EE.EQUATION` seed covers one-variable equations only.

## Six independent readiness dimensions

- **28 expectations** carry provisional repository links (`REPOSITORY_EXISTING_UNVERIFIED`) — none accepted.
- **52 expectations** have no repository-specific candidate.
- **0 expectations** claim verified coverage on any dimension.

## Safety

- Activation: **FORBIDDEN**. No canonical IDs created. No learner evidence mutation. No verified coverage claim.
- Standards Mapping and Independent Mathematical Review approval required before any mapping, generator, or package work proceeds.

## Handoffs

1. **Standards Mapping:** reconcile DC6/DC7 seed scopes against exact CCSS wording; decompose `DC7.SP.PROBABILITY`; authorize a `DC_MATH_8` seed scope.
2. **Independent Math Review:** exact atomic targets only.
3. **Content Production:** Grade 8 is the priority surface (27 unmapped), followed by Grade 6 geometry and rational-number scope.
4. **Engineering (Devin):** no work until mappings are accepted; this manifest is coordination data only.
