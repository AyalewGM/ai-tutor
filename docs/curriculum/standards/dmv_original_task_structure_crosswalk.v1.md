# DMV Original Task-Structure Crosswalk v1

Status: **DRAFT_UNVERIFIED — runtime disabled**  
Evidence snapshot: `main@313c13c9df4d530777cf89fb34f21dcedd91f454`

This is a reuse-first research crosswalk, not a curriculum-coverage claim. Maryland, Virginia, and Washington, DC remain versioned many-to-many mappings onto one jurisdiction-neutral mathematical core. The matrix contains no copied teacher questions, diagrams, videos, or protected source material.

## Source and version controls

| Jurisdiction | Current authority used | Version boundary | Use in this artifact |
|---|---|---|---|
| Maryland | [MSDE Mathematics Standards](https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics) | 2025 revised MCCRS; Algebra I implementation in 2026–27 | Exact IDs listed only where already source-linked in merged repository evidence; all mappings remain provisional |
| Maryland assessment | [MCAP public release portal](https://mcap.msde.maryland.gov/public/) | Public collection inspected 2026-10-11 | Response structures and cognitive demand only; no copied items |
| MCPS | [Algebra 1 curriculum](https://www.montgomeryschoolsmd.org/curriculum/math/high/algebra1/) | Public support pages inspected 2026-10-11 | Internal structure research only; no learner-facing video links or embeds |
| Virginia | [2023 Mathematics SOL](https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics) | Approved 2023-08-31 | Source family verified; exact IDs intentionally withheld pending document-level verification |
| Virginia instruction | [2023 SOL instructional resources](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources/) | 2023 guides/playbook | Instructional demand categories only |
| Virginia tasks | [Rich Mathematical Tasks](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/instructional-resources/rich-mathematical-task) | **Aligned to 2016 SOL** | Structure-only research; 2016 codes are not current mappings |
| Washington, DC | [OSSE assessments](https://osse.dc.gov/assessments) | DC CCSS mathematics | Source family verified; exact IDs pending official-document check |
| Washington, DC assessment | [DC CAPE Next 2026–27 design](https://osse.dc.gov/page/dc-cape-next-content-and-test-design-changes-2026-27-school-year-and-beyond) | Computer-adaptive component plus performance task | Public design evidence only; no invented specifications |

No inspected page stated a reusable content license. All sources are therefore recorded as research references; nothing is copied or rehosted.

## Ranked weak or missing task structures

| Rank | Reusable task structure | Grades | Decision | Existing identity/evidence | Material gap |
|---:|---|---|---|---|---|
| 1 | Multi-step equations: verify solution class and critique error | 7–9 / Alg I | REUSE | `MATH.EE.EQUATION.TWO`, `MATH.EE.EQUATION.MULTISTEP`; signed distribution is only draft PR #340 evidence | One/no/infinitely-many cases, independent oracle, misconception routing, and unseen transfer are not jointly evidenced |
| 2 | Proportional relationships across representations | 6–8 | EXTEND | PR #328 may overlap; exact canonical atoms are not reconciled | Architecture must pin reusable atoms before more implementation |
| 3 | Place value: construct, regroup, and explain invariance | K–3 | REUSE | `MATH.PLACE_VALUE.TENS_ONES`; draft PR #327 | K–3 source IDs and boundary with `MATH.NS.PLACE_VALUE` remain open |
| 4 | Fraction equivalence with visual/number-line justification | 3–5 | EXTEND | Draft PR #327; legacy alias is not authority | Approved atomic identity and independent assessment are missing |
| 5 | Percent contexts with explicit reference base | 6–9 | EXTEND | Existing `MATH.PCT.*`; draft PR #327 | Commission, fees, and measured/reference percent error depth remain weak |
| 6 | Linear model construction, comparison, and transfer | 7–9 / Alg I | EXTEND | Existing partial generators plus draft PR #327 | Jurisdiction-neutral identity, misleading-scale critique, and routed unseen transfer need reconciliation |
| 7 | Exponent laws and scientific-notation equivalence | 8–9 / Alg I | PROPOSE IDENTITY REVIEW | No exact existing core identity confirmed in this audit | Audit first; only Architecture/Math Review may approve a genuinely new atom |
| 8 | Polynomial divided by monomial with restrictions | 8–9 / Alg I | EXTEND | `MATH.EE.POLYNOMIAL_OPERATIONS` | Denominator restrictions, equivalent forms, independent verification, and targeted cancellation errors are unproven |
| 9 | Construct and compare distributions | 6–9 | EXTEND | `MATH.DATA.HISTOGRAM.BIN`, `MATH.DATA.IQR`, `MATH.DATA.FIVE_NUMBER`; draft PR #328 | Full box-plot construction and contextual independent assessment remain weak |
| 10 | Nets, surface area, and rational-edge volume | 5–8 | EXTEND | `MATH.GEO.NET.CUBE.SURFACE`, `MATH.GEO.SURFACE.PRISM`, `MATH.GEO.VOLUME.PRISM`; draft PRs #327/#328 | Spatial foldability plus dimensional reasoning and trusted assessment are not jointly evidenced |
| 11 | Pythagorean proof, classification, and dimensional model | 8–9 | EXTEND | Partial existing implementation | Maryland evidence specifically exposes missing proof and acute/obtuse inequality depth |
| 12 | Theoretical probability versus seeded simulation | 6–8 | REUSE | Four draft scope-card atoms merged via PR #326 | Scope review is not implementation, mapping, assessment, or QA evidence |

## Reconciliation rules

- PR #325 is merged source-linked evidence, but the same Standards Mapping role does not independently accept its own mappings.
- PRs #327 and #328 are draft implementation evidence. This crosswalk does not duplicate their packages or imply their heads are integrated.
- PR #340 is a draft signed-distribution MVE slice, not mathematical, pedagogical, or QA acceptance.
- A blank Virginia or DC standard-ID list means **not yet independently verified**, not “not covered.”
- `PROPOSE_IDENTITY_REVIEW` is a request to audit and decide, never authority to mint or activate a skill.
- Every downstream package still needs independent mathematical review, pedagogical review, standards acceptance, external Muse QA, exact-head CI/AppSec, and a real routed student-flow demonstration.

## Required next handoffs

1. **Standards Mapping:** verify exact 2023 Virginia SOL and DC CCSS identifiers against official documents and append only source-proven many-to-many relations.
2. **Architecture:** resolve the proportional, fraction-equivalence, linear-function, exponent/scientific-notation, and Pythagorean identity references without jurisdiction-specific forks.
3. **Content/MVE/Frontend/Backend:** reconcile PRs #327, #328, and #340 before starting duplicate work; deepen the highest-ranked gaps through Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify.
4. **Independent reviewers/Muse:** issue exact-head verdicts; until then all rows stay `DRAFT_UNVERIFIED` and runtime disabled.
