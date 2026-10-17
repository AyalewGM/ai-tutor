# New York Algebra I (NGMLS 2017, updated 2019) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-16 ·
Manifest: `ny_ngmls_2019_algebra1.expectations.v1.json`

## Scope

43 `AI-` prefixed expectations extracted from the NYSED P-12 PDF (Algebra I
section, pages 108–124). All 10 Appendix-A-style domains present:
N.RN, N.Q, A.SSE, A.APR, A.CED, A.REI, F.IF, F.BF, F.LE, S.ID.
NGMLS Algebra I has been the operative Regents standard since June 2024.

## Findings

1. **Zero repository coverage** — all 43 rows
   `NO_REPOSITORY_SPECIFIC_MAPPING_FOUND`.
2. **Cleanest extraction of the three NY manifests** — 0 rows flagged;
   the AI section's layout interleaved less than the elementary grades.
3. **AI numbering can be non-contiguous and course-shared** — `AI-A.APR`
   has 1 and 3 but not 2; 17 rows carry `(Shared standard with Algebra II)`
   annotations (preserved per-row in `notes`), and sub-lettered standards
   exist (e.g. `AI-A.REI.7a`, `AI-F.BF.3a`). Never assume sequential
   numbering or AI-only scope.
4. **Same algebra decomposition serves six jurisdictions now** — the
   atomic scope behind MD/DC/VA/IL algebra inventories is nearly
   co-extensive with NY AI; one Math-Review-accepted decomposition covers
   all, but the NY crosswalk still needs its own row-level proposal.
5. **Not inventoried yet:** NY Geometry (`GEO-`) and Algebra II (`AII-`)
   NGMLS — out of the product's current Grade 1–9 scope; the `+` standards
   likewise excluded.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Include NY-AI in the single cross-jurisdiction algebra decomposition wave |
| Content Review | Verify shared-course annotations (`Shared standard with Algebra II`) before scoping AI rows |
| Engineering | Consider `GEO-`/`AII-` manifests when the product extends past grade 9 |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
