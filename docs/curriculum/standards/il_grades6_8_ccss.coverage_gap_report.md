# Illinois Grades 6–8 (CCSS) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-16 ·
Manifest: `il_grades6_8_ccss.expectations.v1.json`

## Scope

81 official expectations from the Illinois Learning Standards for
Mathematics (incorporating the Common Core), Grades 6–8 — identical to the
canonical CCSS identifier set (verbatim ISBE adoption). Generated as a
jurisdiction-swapped clone of the reviewed DC grades 6–8 inventory.

| Grade | RP | NS | EE | G | SP | F | Total | Unmapped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 3 | 8 | 9 | 4 | 5 | — | 29 | 29 |
| 7 | 3 | 3 | 4 | 6 | 8 | — | 24 | 24 |
| 8 | — | 2 | 8 | 9 | 4 | 5 | 28 | 28 |
| **Σ** | | | | | | | **81** | **81** |

## Findings

1. **Zero repository coverage** — all 81 rows
   `NO_REPOSITORY_SPECIFIC_MAPPING_FOUND`.
2. **The DC/MD/VA Grade-8 gap is not an Illinois curriculum decision.**
   `8.G.C.9`, transformations, systems, and the pre-algebra bridge are all
   required by Illinois Learning Standards — they are absent only because
   *no* jurisdiction has the content yet, not because Illinois skips them.
   Filling the G8 content gap once covers DC, MD, VA, and IL simultaneously.
3. **Same jurisdiction-isolation rule** — shared CCSS identifiers must never
   merge across state rows.
4. **M7.NS.RAT signed-number work maps directly** — the jurisdiction-agnostic
   integer learning experience (`GuidedIntegerNumberLine`, merged) is the
   strongest existing candidate for Illinois `7.NS.A.*` coverage, pending
   review.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Defer IL crosswalk work until the shared DMV G8 gap closes — one content wave covers both |
| Math Review | Same as G1–5: shared identifiers do not imply shared acceptance |
| Content | G8 remains the priority surface; IL is now a fourth jurisdiction needing it |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
