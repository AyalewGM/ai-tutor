# New York Grades 6–8 (NGMLS 2017, updated 2019) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-16 ·
Manifest: `ny_ngmls_2019_grades6_8.expectations.v1.json`

## Scope

82 expectations extracted from the authoritative NYSED P-12 PDF.

| Grade | Expectations | Flagged for review | Notes |
|---:|---:|---:|---|
| 6 | 35 | 1 | one `NY-6.SP.6` phantom row deduplicated (fraction `3/6` column artifact) |
| 7 | 20 | 4 | SP is intentionally sparse: `SP.1,3,4,8` — NY restructured probability |
| 8 | 27 | 3 | |
| **Σ** | **82** | **8** | |

## Findings

1. **Zero repository coverage** — all 82 rows
   `NO_REPOSITORY_SPECIFIC_MAPPING_FOUND`.
2. **Grade 7's 20 expectations are real, not missing rows** — raw-PDF
   verification confirms NY-7.SP numbering `1, 3, 4, 8`; NY consolidated
   probability content differently than CCSS's 8-standard SP strand.
3. **NY-7.NS signed-number work maps to the strongest existing asset** —
   the merged `GuidedIntegerNumberLine`/`M7.NS.RAT` learning experience is a
   prime reuse candidate for `NY-7.NS.1–3`, pending review.
4. **The shared DMV G8 gap does NOT exist in NY's structure** — NY-8 already
   includes transformations and systems; but the *repository* G8 gap means
   NY-8 content coverage still requires the same authoring wave.
5. **8 extraction rows flagged** (`EXTRACTION_REVIEW_REQUIRED`), mostly
   mid-statement column-boundary truncation.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | NY-7.NS.1–3 is the cheapest NY reuse proposal — the integer line experience is jurisdiction-agnostic |
| Content Review | Repair 8 flagged statements from the PDF (page locators per row) |
| Content | G8 authoring wave now serves DC/MD/VA/IL/NY alike |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
