# Texas TEKS 2012 Grades 1–9 — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-14 ·
Manifest: `tx_teks_2012_grades1_9.expectations.v1.json`

## Scope

463 student expectations extracted from TEA's official TAC Chapter 111 PDFs:
grades 1–5 (§111.3–.7, ch111a), 6–8 (§111.26–.28, ch111b), Algebra I
(§111.39, ch111c). TEKS IDs follow `{grade}.{KS}{letter}` (e.g., `3.2A`);
Algebra I rows use the `A1.{KS}{letter}` convention.

| Grade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | A1 |
|---|---|---|---|---|---|---|---|---|---|
| Expectations | 50 | 50 | 53 | 53 | 44 | 58 | 48 | 51 | 56 |

## Findings

1. **Texas is the largest single-jurisdiction inventory so far** — 463
   expectations, because every lettered student expectation counts
   separately (TX splits what CCSS bundles into one standard).
2. **Zero repository coverage** — all rows `NO_REPOSITORY_CANDIDATE`.
3. **KS 1 (A–G) is a cross-cutting process standard** at every grade —
   63 of the 463 rows are the same seven process expectations repeated
   per grade. Like Ontario's strand A, these should map to shared
   process identities, not 63 distinct content skills.
4. **Supersedes the 88-row intake artifact** (`national_tx_grades7_9`),
   which listed IDs with null scope text and partial grade coverage.
5. **TEKS↔CCSS crosswalk is nontrivial** — TX ordering, emphasis, and
   personal-financial-literacy strand don't align 1:1 with CCSS; expect
   dedicated canonical review.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Decide KS-1 dedup policy; TEKS↔canonical crosswalk approach |
| Math Review | Spot-verify parsed letters against TAC source (extraction is mechanical) |
| Content | Greenfield; TX financial-literacy strand is new content territory |

## Safety

`activation: FORBIDDEN` · zero canonical IDs · zero learner-evidence mutation.
