# New York Grades 1–5 (NGMLS 2017, updated 2019) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-16 ·
Manifest: `ny_ngmls_2019_grades1_5.expectations.v1.json`

## Scope

142 expectations extracted programmatically from the authoritative NYSED
P-12 standards PDF (`NYSED_NGMLS_P12_2017_UPDATED_2019`). NY identifiers are
jurisdiction-native (`NY-{grade}.{domain}.{n}[letter]` — no cluster letters,
lettered sub-standards like `6a`/`6b`).

| Grade | Expectations | Flagged for review |
|---:|---:|---:|
| 1 | 24 | 3 |
| 2 | 31 | 2 |
| 3 | 30 | 0 |
| 4 | 31 | 3 |
| 5 | 26 | 4 |
| **Σ** | **142** | **12** |

## Findings

1. **Zero repository coverage** — all 142 rows
   `NO_REPOSITORY_SPECIFIC_MAPPING_FOUND`.
2. **Extraction fidelity is bounded by the PDF's two-column layout.** 12
   statements are `EXTRACTION_REVIEW_REQUIRED` (column-boundary truncation /
   mid-word splits); 130 are `AUTHORITATIVE_STATEMENT_EXTRACTED`. The count
   itself is extraction-derived — no independent NYSED count was reconciled
   (documented blocker in `reconciliation.warning`).
3. **NY restructured CCSS, not renamed it.** Numbering, sub-standard
   lettering, and some grade placements differ from CCSS; do not crosswalk
   by string similarity. The `coherence` chains preserved per-row are NY's
   own published vertical-alignment links — usable as prerequisite hints
   after review.
4. **Mathematical content still overlaps CCSS heavily** — DMV elementary
   packs cover the same arithmetic/fractions/place-value core, so reuse
   candidates exist, but only through Standards Mapping + Math Review.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Reconcile row counts against a second authoritative NYSED listing (crosswalk doc or snapshot) |
| Content Review | Repair the 12 flagged statements from the PDF directly (page locators recorded per row) |
| Math Review | Any DMV-pack reuse proposal must compare mathematical scope, not identifier similarity |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
