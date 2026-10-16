# Illinois Grades 1–5 (CCSS) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Generated: 2026-10-16 ·
Manifest: `il_grades1_5_ccss.expectations.v1.json`

## Scope

126 official expectations from the Illinois Learning Standards for
Mathematics (incorporating the Common Core), identical to the canonical CCSS
identifier set — Illinois adopted CCSS verbatim via ISBE rulemaking effective
2010-10-28. Generated as a jurisdiction-swapped clone of the reviewed DC
grades 1–5 inventory: identical identifiers, identical official text,
independent jurisdiction provenance.

| Grade | Expectations | With provisional link | Unmapped |
|---:|---:|---:|---:|
| 1 | 21 | 0 | 21 |
| 2 | 26 | 0 | 26 |
| 3 | 25 | 0 | 25 |
| 4 | 28 | 0 | 28 |
| 5 | 26 | 0 | 26 |
| **Σ** | **126** | **0** | **126** |

## Findings

1. **Zero repository coverage.** No Illinois packs, seeds, or skills exist;
   all 126 rows are `NO_REPOSITORY_SPECIFIC_MAPPING_FOUND`.
2. **Jurisdiction isolation is the main correctness risk.** The identifiers
   are shared verbatim with every CCSS adopter — DC rows, MD's legacy
   crosswalk column, and (eventually) other states. An `IL 3.NF.A.1` row must
   never merge with a DC or national row by identifier similarity.
3. **Reuse path is jurisdiction-agnostic.** DMV elementary packs teach the
   same mathematical content (DC packs are CCSS-based). Any reuse of
   `DC*.OA.*`-style pack skills for Illinois coverage requires a Standards
   Mapping EQUIVALENCES proposal and Math Review acceptance — the shared
   identifiers make the mapping *proposal* cheap, not automatic.
4. **Cheapest full-state coverage on record.** Because the identifier set is
   a reviewed clone, Illinois moves straight to mapping review once the
   DMV pack review concludes — no new intake or text-verification pass needed
   beyond confirming ISBE adoption provenance.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Propose EQUIVALENCES from IL expectations to reviewed pack skills once DMV mappings are accepted |
| Math Review | Verify the shared-identifier rows teach the exact CCSS scope before any acceptance |
| Engineering | Wire manifest into `audit_curriculum_mapping_coverage` automatically on merge |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
