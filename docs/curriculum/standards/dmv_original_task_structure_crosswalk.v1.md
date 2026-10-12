# DMV Original Task-Structure Crosswalk v1 — R4 review-evidence reconciliation

Status: **DRAFT_UNVERIFIED — runtime disabled**  
Evidence snapshot: `main@317612d2668eba6b172dec2b02543eb65c51a656`

This is a reuse-first research crosswalk, not a curriculum-coverage claim. Maryland, Virginia, and Washington, DC remain versioned many-to-many mappings onto one jurisdiction-neutral mathematical core. The matrix contains no copied teacher questions, diagrams, videos, or protected source material.

## Source and version controls

| Jurisdiction | Current authority used | Version boundary | Use in this artifact |
|---|---|---|---|
| Maryland | [MSDE Mathematics Standards](https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics) | 2025 revised MCCRS; Algebra I implementation in 2026–27 | Exact IDs listed only where already source-linked in merged repository evidence; all mappings remain provisional |
| Maryland assessment | [MCAP public release portal](https://mcap.msde.maryland.gov/public/) | Public collection inspected 2026-10-11 | Response structures and cognitive demand only; no copied items |
| MCPS current listing | [Mathematics Middle School](https://www.montgomeryschoolsmd.org/curriculum/math/ms/) | Current page inspected 2026-10-11; school-year effective date not stated | District adoption evidence only: Amplify Desmos Math for Math 6–8, accelerated 6/7, Algebra 1; IM Geometry for Honors Geometry. Not Maryland standards authority |
| Amplify vendor sequence | [Grade 6–Algebra 2 Caregiver Hub](https://amplify.com/caregiver-hub/amplify-desmos-math-6-12/) | Published 2025-01-16; metadata modified 2026-09-23; inspected 2026-10-11 | Unit/topic sequence and abstract task-structure research only; no copied/rehosted content or learner-facing links |
| MCPS historical support | [2019 IM Algebra 1 support pages](https://www.montgomeryschoolsmd.org/curriculum/math/high/algebra1/) | 2019 IM summary track; inspected 2026-10-11 | Historical research only; not current adoption proof or Maryland standards authority |
| Virginia | [2023 Mathematics SOL](https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics) | Approved 2023-08-31 | Source family verified; exact IDs intentionally withheld pending document-level verification |
| Virginia instruction | [2023 SOL instructional resources](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources/) | 2023 guides/playbook | Instructional demand categories only |
| Virginia tasks | [Rich Mathematical Tasks](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/instructional-resources/rich-mathematical-task) | **Aligned to 2016 SOL** | Structure-only research; 2016 codes are not current mappings |
| Washington, DC | [OSSE assessments](https://osse.dc.gov/assessments) | DC CCSS mathematics | Source family verified; exact IDs pending official-document check |
| Washington, DC assessment | [DC CAPE Next 2026–27 design](https://osse.dc.gov/page/dc-cape-next-content-and-test-design-changes-2026-27-school-year-and-beyond) | Computer-adaptive component plus performance task | Public design evidence only; no invented specifications |

No inspected page stated a reusable content license. All sources are therefore recorded as research references; nothing is copied or rehosted.


## Current MCPS course listing and Amplify topic sequence

The district page currently lists the following products; the Amplify page supplies the vendor unit titles below. These are two distinct evidence layers. Neither source supplies Maryland expectation IDs, and no ID is inferred from a unit title.

| MCPS course | Current listed curriculum | Vendor units recorded for progression research |
|---|---|---|
| Math 6 | Amplify Desmos Math Grade 6 | Area/Surface Area; Ratios; Rates/Percentages; Dividing Fractions; Decimal Arithmetic; Expressions/Equations; Signed Numbers; Data |
| Accelerated Math 6 | Amplify Desmos Math Accelerated Grade 6 | Area/Surface Area; Ratios/Rates; Fractions/Decimals; Expressions/Equations; Proportions; Percentages; Signed Numbers; Distributions |
| Math 7 | Amplify Desmos Math Grade 7 | Scale Drawings; Proportions; Circles; Percentages; Signed Operations; Expressions/Equations/Inequalities; Angles/Triangles/Prisms; Probability/Sampling |
| Accelerated Math 7 | Amplify Desmos Math Accelerated Grade 7 | Transformations; Similarity; Equations/Inequalities; Linear Relationships/Systems; Functions; Data Associations; Volume/Surface Area; Exponents/Scientific Notation; Pythagorean/Irrational Numbers |
| Math 8 | Amplify Desmos Math Grade 8 | Transformations/Congruence; Dilations/Similarity/Slope; Proportional/Linear Relationships; Linear Equations/Systems; Functions/Volume; Data Associations; Exponents/Scientific Notation; Pythagorean/Irrational Numbers |
| Algebra 1 | Amplify Desmos Math Algebra 1 | Patterns/Sequences; Linear Equations/Inequalities; Data; Functions; Linear Systems/Inequalities; Exponentials; Quadratics; Quadratic Equations |
| Honors Geometry | Illustrative Mathematics Geometry | Listed by MCPS separately; not represented as an Amplify course sequence in this correction |

The machine-readable artifact preserves exact vendor unit titles and unit numbers. Topic overlap with a Mihur task row is `VENDOR_UNIT_TOPIC_SEQUENCE_ONLY`; it is not an accepted standards mapping, canonical identity decision, generator implementation, routed lesson, independent assessment, or QA verdict.

## Historical research tracks

- MCPS pages carrying 2019 Illustrative Mathematics Algebra 1 lesson summaries remain `HISTORICAL_RESEARCH_ONLY_NOT_CURRENT_ADOPTION_PROOF`.
- The owner-provided 2020 Rosa Parks summer Algebra 1 readiness packet remains historical prerequisite/task-structure research. Its original public URL is not independently verified, so it contributes no current course, standards, or mapping claim.
- Neither track may be copied, rehosted, embedded, or linked from student-facing Mihur learning.

## Architecture boundary reconciliation

Issue #282 decision [6107538656](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6107538656) now controls three algebra rows that were broader in R2. This records Architecture's decision; it does not publish a canonical identity or accept a standards relation.

- Exponent product, quotient, power-of-power, zero-exponent (nonzero base), and negative-exponent/reciprocal evidence remain separate collision-audited DRAFT scopes. The historical `MATH.NS.EXPONENTS` meaning is not expanded.
- Scientific-notation conversion/normalization, multiplication, and division remain separate collision-audited DRAFT scopes. The historical `MATH.NS.SCIENTIFIC_NOTATION` meaning is not expanded.
- Polynomial division requires proposed DRAFT `MATH.POLY.DIVIDE_MONOMIALS` and `MATH.POLY.DIVIDE_POLYNOMIAL_BY_MONOMIAL`; the latter requires the former. Historical `MATH.EE.POLYNOMIAL_OPERATIONS` receives no new division mastery.
- Combined tasks are reporting-only `ALL_OF`: one response has one primary atom, with no back-credit or duplicate mastery. Domain restrictions, multiplication reconstruction, substitution, and structured explanations are evidence dimensions, not extra identities.

Architecture has now confirmed all eleven PR #349 labels for DRAFT identity/granularity at `79f272a6`; this does not publish canonical rows or accept standards mappings. Independent Mathematical Review approved all eleven cards. Exact trusted-backend integration, standards acceptance, real routed-package evidence, and package-level external QA remain open.

## Review-evidence reconciliation

- [Architecture r2 confirmation 6109385883](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6109385883) carries forward all eleven PR #349 labels and their granularity for DRAFT review at `79f272a6`; no canonical publication, mapping acceptance, or runtime authority follows.
- [Independent Mathematical Review 6109037688](https://github.com/AyalewGM/ai-tutor/issues/337#issuecomment-6109037688) records **11 APPROVE / 0 REQUEST CHANGES** on PR #349. The corrected scientific-notation multiplication card now reflects the attainable normalized-input product boundary, and polynomial-by-monomial canonicalization now applies its 2+-term boundary to the original written dividend.
- PR #346's exact root scorer mathematics is approved at `58bc5f37` for negative, zero, positive-square, and positive-nonsquare radicands, but trusted backend reconciliation and exact-head AppSec remain open.
- PR #350's guided MVE was merged, but live route authority is not accepted. Follow-up PR #351 keeps the component default-off pending an approved server-owned capability; current-main routed-package and trusted-assessment acceptance remain open.
- These verdicts refine content-depth and implementation evidence only. Accepted standards mappings remain **0**, QA-approved packages remain **0**, and runtime remains disabled.

## Ranked weak or missing task structures

| Rank | Reusable task structure | Grades | Decision | Existing identity/evidence | Material gap |
|---:|---|---|---|---|---|
| 1 | Multi-step equations: verify solution class and critique error | 7–9 / Alg I | REUSE | Existing equation atoms; PR #343 service-rate units/reconstruction mathematically approved | One/no/infinitely-many cases, independent oracle, misconception routing, and unseen transfer are not jointly evidenced |
| 2 | Proportional relationships across representations | 6–8 | EXTEND | PR #328 may overlap; exact canonical atoms are not reconciled | Architecture must pin reusable atoms before more implementation |
| 3 | Place value: construct, regroup, and explain invariance | K–3 | REUSE | `MATH.PLACE_VALUE.TENS_ONES`; draft PR #327 | K–3 source IDs and boundary with `MATH.NS.PLACE_VALUE` remain open |
| 4 | Fraction equivalence with visual/number-line justification | 3–5 | EXTEND | Draft PR #327; legacy alias is not authority | Approved atomic identity and independent assessment are missing |
| 5 | Percent contexts with explicit reference base | 6–9 | EXTEND | Existing `MATH.PCT.*`; draft PR #327 | Commission, fees, and measured/reference percent error depth remain weak |
| 6 | Linear model construction, comparison, and transfer | 7–9 / Alg I | EXTEND | Existing partial generators plus draft PR #327 | Jurisdiction-neutral identity, misleading-scale critique, and routed unseen transfer need reconciliation |
| 7 | Exponent laws and equivalent forms | 8–9 / Alg I | PROPOSE IDENTITY REVIEW | Five DRAFT labels architecture-accepted and 5/5 scope cards mathematically approved; historical `MATH.NS.EXPONENTS` is not expanded | Publication, routed interaction, complete independent assessment, standards acceptance, and no-double-credit QA remain open |
| 8 | Scientific-notation conversion, multiplication, and division | 8–9 / Alg I | PROPOSE IDENTITY REVIEW | Three DRAFT labels architecture-accepted and 3/3 scope cards mathematically approved | Publication, routed interaction, trusted assessment, standards acceptance, and QA remain open |
| 9 | Polynomial divided by monomial with restrictions | 8–9 / Alg I | PROPOSE IDENTITY REVIEW | Both DRAFT labels and scope cards approved; PR #352 preserves the PR #348 draft contract; PR #351 keeps routing default-off | PR #346 generator correction awaits limited Math re-review/AppSec; real route, trusted assessment, standards acceptance, and package QA remain open |
| 10 | Construct and compare distributions | 6–9 | EXTEND | `MATH.DATA.HISTOGRAM.BIN`, `MATH.DATA.IQR`, `MATH.DATA.FIVE_NUMBER`; draft PR #328 | Full box-plot construction and contextual independent assessment remain weak |
| 11 | Nets, surface area, and rational-edge volume | 5–8 | EXTEND | `MATH.GEO.NET.CUBE.SURFACE`, `MATH.GEO.SURFACE.PRISM`, `MATH.GEO.VOLUME.PRISM`; draft PRs #327/#328 | Spatial foldability plus dimensional reasoning and trusted assessment are not jointly evidenced |
| 12 | Pythagorean proof, classification, and dimensional model | 8–9 | EXTEND | Partial existing implementation | Maryland evidence specifically exposes missing proof and acute/obtuse inequality depth |
| 13 | Theoretical probability versus seeded simulation | 6–8 | REUSE | Four draft scope-card atoms merged via PR #326 | Scope review is not implementation, mapping, assessment, or QA evidence |

## Reconciliation rules

- PR #325 is merged source-linked evidence, but the same Standards Mapping role does not independently accept its own mappings.
- PRs #327 and #328 are draft implementation evidence. This crosswalk does not duplicate their packages or imply their heads are integrated.
- PR #340 is a draft signed-distribution MVE slice, not mathematical, pedagogical, or QA acceptance.
- A blank Virginia or DC standard-ID list means **not yet independently verified**, not “not covered.”
- A vendor-unit citation is topic/progression research only. It can never populate a Maryland standard ID, prove statewide adoption, or promote a mapping.
- Current MCPS adoption evidence and historical IM/readiness research are stored separately and cannot substitute for each other.
- `PROPOSE_IDENTITY_REVIEW` records an Architecture-approved collision-audit/drafting lane only; it is never authority to publish, map as accepted, activate, or transfer historical mastery.
- Every downstream package still needs independent mathematical review, pedagogical review, standards acceptance, external Muse QA, exact-head CI/AppSec, and a real routed student-flow demonstration.

## Post-merge stabilization reconciliation (R6)

This revision updates implementation evidence only; the MCPS/Amplify source hierarchy, vendor-unit transcription, official-MSDE-only expectation authority, Virginia/DC source boundaries, ranked dispositions, and all provisional standards relations are unchanged.

- Current `main@a740e51d` contains PR #344's draft generators and PR #350's guided polynomial MVE, but merge presence is not standards acceptance or a trusted learner route.
- Independent Mathematical Review found PR #346 `cec599a2` could generate written “polynomial” dividends with negative exponents. Assessment Backend corrected that boundary at `2bfc1110`: dividend exponents are nonnegative while valid negative quotient exponents and original divisor restrictions remain. CI #1452 passes; exact-head AppSec is absent and limited mathematical re-review is pending.
- PR #351 `859f98ca` removes display-name/regex/provisional-code routing authority and keeps the guided polynomial MVE default-off pending an approved server-owned capability. CI #1449 and AppSec #818 pass; Architecture accepted the fail-closed boundary.
- PR #352 `ecb83965` preserves the reviewed PR #348 package files on current main as a draft-only artifact. CI #1450 and AppSec #819 pass; Architecture confirms the legacy `MATH.EE.POLYNOMIAL_OPERATIONS` family field is provenance only, not alias/mastery authority.
- These facts do not accept a Maryland, Virginia, DC, or Ontario mapping; accepted mappings remain **0**, QA-approved complete packages remain **0**, and runtime remains disabled.

## Required next handoffs

1. **Independent Standards reviewer:** verify this MCPS/Amplify evidence hierarchy and exact course/unit transcription; separately verify Maryland expectation IDs only from official MSDE sources.
2. **Standards Mapping:** verify exact 2023 Virginia SOL and DC CCSS identifiers against official documents and append only source-proven many-to-many relations.
3. **Architecture:** resolve the remaining proportional, fraction-equivalence, linear-function, and Pythagorean identity references without jurisdiction-specific forks; the eleven PR #349 algebra labels are already confirmed for DRAFT review at r2.
4. **MVE/Frontend/Backend:** preserve the corrected PR #349 cards and PR #346 root boundaries; reconcile the accepted PR #348 evidence contract and bounded PR #350 guided interaction onto a real routed package with trusted backend assessment, without duplicating existing work. Deepen the highest-ranked gaps through Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify.
5. **Independent reviewers/Muse:** issue exact-head verdicts; until then all rows stay `DRAFT_UNVERIFIED` and runtime disabled.
