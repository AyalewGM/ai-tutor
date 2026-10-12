# District of Columbia Grades 6–8 CCSS expectation inventory and gap report

Status: **DRAFT / PROPOSED / NOT VERIFIED**
Inventory: `docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json`
Authority: Office of the State Superintendent of Education (OSSE)
Source checked / inventory as of: 2026-10-12

## Authoritative source

The District of Columbia adopted the **Common Core State Standards** verbatim through OSSE ([DC standards](https://osse.dc.gov/page/dc-standards)). Expectation identifiers are the canonical CCSS codes (`{grade}.{domain}.{cluster}.{number}`); the standards text is published at [thecorestandards.org](https://www.thecorestandards.org/Math).

**Unlike Maryland's 2025 re-domained MCCRS (NOS/AT/GR/DS), DC retains the legacy CCSS domains** — RP (Ratios & Proportional Relationships), NS (The Number System), EE (Expressions & Equations), G (Geometry), SP (Statistics & Probability), F (Functions). The Maryland crosswalk's legacy column and DC's live identifiers use the same codes; these are separate jurisdictions whose expectations must never be merged by identifier similarity.

This completes the DMV Grade 6–8 inventory set alongside `md_grades6_8_2025.expectations.v1.json` and `va_grades6_8_2023.expectations.v1.json`, closing the evidence-acquisition gap named in `grades1_9_gap_triage.wave1.md` for all three existing elementary-pack jurisdictions.

## Official expectation inventory

**81 top-level CCSS expectations** across Grades 6–8:

| Grade | RP | NS | EE | G | SP | F | Total | Seed-linked | Unmapped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 3 | 8 | 9 | 4 | 5 | — | 29 | 12 | 17 |
| 7 | 3 | 3 | 4 | 6 | 8 | — | 24 | 16 | 8 |
| 8 | — | 2 | 8 | 9 | 4 | 5 | 28 | 0 | 28 |
| **Total** | | | | | | | **81** | **28** | **53** |

## Repository state

- `scripts/seed_dc_grade6.py` (`DC_MATH_6`): 5 skills — `DC6.RP.RATIO`, `DC6.RP.UNIT_RATE`, `DC6.NS.FRACTION`, `DC6.EE.EXPR`, `DC6.EE.EQUATION`
- `scripts/seed_dc_grade7.py` (`DC_MATH_7`): 5 skills — `DC7.RP.PROPORTIONAL`, `DC7.RP.PERCENT`, `DC7.NS.RATIONAL`, `DC7.EE.EQUATION`, `DC7.SP.PROBABILITY`
- **Grade 8: no DC seed rows exist** (`DC_MATH_8` has no seed script; `seed_dc_algebra1.py` covers the separate Algebra I course).

### Material findings

1. **Grade 8 is a complete repository gap** — all 28 expectations unmapped: irrational numbers, exponents and scientific notation, slope and linear equations, systems, functions, transformations/congruence/similarity, Pythagorean Theorem, **cone/cylinder/sphere volume (8.G.C.9)**, and bivariate data. Identical pattern to Virginia's Grade 8 gap and nearly identical to Maryland's `8.AT.*`/`8.GR.*` unmapped clusters — DC, MD, and VA converge on the same missing pre-algebra bridge.

2. **`DC7.SP.PROBABILITY` is an extreme composite** — a single seed row provisionally linked to all eight `7.SP` expectations (sampling, inference, probability scale, models, compound events). It cannot transfer mastery to distinct atomic identities per the #293 precedent.

3. **DC geometry coverage is zero across all three grades** — no `*.G.*` expectation has any linked seed (13 unmapped: area/volume/nets at G6, circles/angles/scale at G7, all of G8 geometry).

4. **Integer/rational-number scope is thin locally** — `6.NS.C.5`–`6.NS.C.8` (negatives, coordinate plane, absolute value) unmapped, mirroring the same gap in MD (`6.NOS.C.*`) and VA (`6.NS.2`, `6.CE.2`). A jurisdiction-agnostic integer learning experience exists (merged `GuidedIntegerNumberLine` work) but any local reuse needs Standards Mapping acceptance, not assumption.

5. **`6.EE.C.9`** (two-variable relationships) has no candidate — the `DC6.EE.EQUATION` seed covers one-variable equations only.

## Six independent readiness dimensions

- **28 expectations** carry provisional repository links (`REPOSITORY_EXISTING_UNVERIFIED`) — none accepted.
- **53 expectations** have no repository-specific candidate.
- **0 expectations** claim verified coverage on any dimension.

## Safety

- Activation: **FORBIDDEN**. No canonical IDs created. No learner evidence mutation. No verified coverage claim.
- Standards Mapping and Independent Mathematical Review approval required before any mapping, generator, or package work proceeds.

## Handoffs

1. **Standards Mapping:** reconcile DC6/DC7 seed scopes against exact CCSS wording; decompose `DC7.SP.PROBABILITY`; authorize a `DC_MATH_8` seed scope.
2. **Independent Math Review:** exact atomic targets only.
3. **Content Production:** Grade 8 is the priority surface (28 unmapped), followed by Grade 6 geometry and rational-number scope.
4. **Engineering (Devin):** no work until mappings are accepted; this manifest is coordination data only.

### Versioned provenance correction (2026-10-12)

- Neutral inventory identifier: `DC_CCSS_MATH_GRADES_6_8` (not a 2024–25 course adoption assertion).
- Official CCSS adoption: **July 2010**; implementation began **2011–12** and reached full implementation by **2014–15**. These milestones are distinct from the inventory's checked date.
- Authority: [OSSE Common Core State Standards — Mathematics](https://osse.dc.gov/page/common-core-state-standards-mathematics). Canonical CCSS expectation identifiers remain unchanged and all Mihur mappings remain provisional.

### Official-text completeness correction and 81-row evidence ledger (2026-10-12)

The previous draft omitted **8.G.C.9** from Grade 8 Geometry. The [published CCSS Grade 8 Geometry domain](https://www.thecorestandards.org/Math/Content/8/G/) lists **nine** standards, including `8.G.C.9` (cone, cylinder and sphere volumes), not eight. The corrected counts are **29 Grade 6 + 24 Grade 7 + 28 Grade 8 = 81** top-level standards, 28 provisional repository links, and **53** gaps. The new [81-row locator ledger](dc_grades6_8_ccss.source_fidelity_locators.v1.json) records each expectation's domain/cluster, individual standard and domain-section URLs, publisher, 2010 version, and all published lettered subpart identifiers. The CCSS text website identifies itself as an *unofficial republication* of ©2010 NGA/CCSSO text; [OSSE](https://osse.dc.gov/page/common-core-state-standards-mathematics) is the DC adoption authority. No PDF page numbers are invented for HTML standards. Editorial summaries remain source-review inputs, not accepted full-scope transcriptions. All 81 remain provisional; zero accepted coverage or mastery.
