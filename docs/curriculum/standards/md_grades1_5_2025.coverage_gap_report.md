# Maryland Grades 1–5 (2025 MCCRS) — Coverage Gap Report

Status: `DRAFT_PROPOSED_NOT_VERIFIED` · Companion inventory to `md_grades6_8_2025` ·
Generated: 2026-10-13 · Manifest: `md_grades1_5_2025.expectations.v1.json`

## Scope

131 official MSDE 2025 MCCRS expectations, extracted from archived copies of the
grade-level crosswalk PDFs (`media/17806`–`17814`; direct MSDE fetch returns 403).
Identifier set verified 1:1 against table extraction. New-scheme domains only —
legacy CCSS codes (`*.OA.*`, `*.NBT.*`, `*.NF.*`, `*.MD.*`, `*.G.*`) appear in the
crosswalk's second column and are explicitly excluded.

| Grade | Expectations | With provisional link | Unmapped |
|---:|---:|---:|---:|
| 1 | 24 | 21 | 3 |
| 2 | 24 | 19 | 5 |
| 3 | 26 | 24 | 2 |
| 4 | 30 | 28 | 2 |
| 5 | 27 | 24 | 3 |
| **Σ** | **131** | **116** | **15** |

## How the provisional links were derived (stronger than name-matching)

Pack skills carry **legacy** `standard_refs` (`"1.OA"`, `"3.NF"`). The official
crosswalk maps every new identifier to its legacy predecessor. Links here follow
that official column: `1.NOS.C.7` ↔ legacy `1.OA.B.3` ↔ pack `MD1.OA.*`.

This is still `REPOSITORY_EXISTING_UNVERIFIED` — it means the pack plausibly
touches the right scope through the state's own crosswalk, nothing more.

## Findings

1. **The 15 unmapped expectations are disproportionately new-in-2025 content** —
   crosswalk rows whose legacy column reads "Not applicable" plus geometry/measure
   work the packs never covered (`1.GR.C.6` composing shapes, `2.GR.C.*` time/money,
   `4.GR.A.4` symmetry, `5.NOS.D.14` volume).
2. **Same strand-generation mismatch as Virginia.** Pack codes are legacy CCSS
   strands (OA/NBT/NF/MD/G); the 2025 scheme is NOS/AT/GR/DS. The crosswalk's
   legacy column is the *only* honest bridge — reviewers must verify each pair.
3. **DS domain is thin.** `*.DS.A.1` exists per grade but pack data skills are
   minimal; Data Science as a named 2025 domain has no direct pack counterpart.
4. **Packs are composites.** `MD4.NF.FRACTIONS` spans a half-dozen
   `4.NOS.B/E/F.*` expectations — cannot transfer mastery until decomposed.

## Handoffs

| Owner | Action |
|---|---|
| Standards Mapping | Verify each provisional link against the official crosswalk row; produce EQUIVALENCES only after Math Review |
| Math Review | Decompose composite pack skills; confirm the 15 unmapped are genuinely absent vs. covered under different codes |
| Content | Author the 15 missing expectations (new-in-2025 + geometry gaps) |
| Engineering | Wire manifest into `audit_curriculum_mapping_coverage` coverage automatically on merge |

## Safety

`activation: FORBIDDEN` · zero canonical IDs created · zero learner-evidence
mutation · `verified_mastery_evidence: NO_AND_MUST_NOT_BE_INFERRED` on all rows.
