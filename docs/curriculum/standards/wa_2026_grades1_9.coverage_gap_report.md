# Washington 2026 Math Grades 1–9 — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-14 ·
Manifest: `wa_2026_grades1_9.expectations.v1.json`

## Scope

288 expectations converted from the OSPI 2026 adoption workbook extraction
(v3.1): 238 across grades 1–8 + 50 in the ALG 1 course for grade 9. The
2026 scheme uses four domains — Quantity, Relationships, Data Analysis,
Spatial Reasoning — and flags each expectation `new_in_2026` / `priority`.

## Findings

1. **Source verification still pending.** Rows inherit
   `AUTHOR_EXTRACTED_FROM_ADOPTION_WORKBOOK_PENDING_INDEPENDENT_SOURCE_VERIFICATION`
   — another agent's intake of the uploaded workbook, not an independent
   OSPI re-fetch. Workbook anomalies are catalogued in
   `wa_2026_v3_1_workbook_anomalies.v1.json` on the intake branch.
2. **Zero repository coverage.** Washington has no packs, seeds, or skills;
   all 288 rows are `NO_REPOSITORY_CANDIDATE`.
3. **New-domain taxonomy gap.** "Quantity" and "Relationships" don't map
   cleanly to existing `MATH.NS.*`/`MATH.EE.*` families — a taxonomy review
   is needed before any crosswalk.
4. **Dual pathway at grade 9.** This manifest uses ALG 1 (50 rows); the
   integrated pathway INT 1 (55 rows) exists in the source extraction for
   districts using integrated courses.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Independent OSPI verification pass before any link acceptance |
| Taxonomy | Review the 2026 four-domain scheme against the catalog |
| Content | Greenfield — no WA assets exist |

## Safety

`activation: FORBIDDEN` · zero canonical IDs · zero learner-evidence mutation.
