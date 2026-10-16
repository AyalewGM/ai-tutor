# California Grade 2 / Grade 3 author-side source handoff

Author data+test baseline commit: `9da76f604463f1ca3ff70d57da4d90968a7ac7cc`. This handoff is documentation only; verify the **current exact PR SHA** at review time.

Official publisher original: https://www.cde.ca.gov/be/st/ss/documents/ccssmathstandardaug2013.pdf, CDE 2013 modification / corrected 2014 electronic edition.

## New author evidence

- Grade 2: `ca_2013_grade2_pages21_22_source_author_slice.v1.json` covers CDE printed pp.21–22 (PDF zero-based 27–28), with 14 provisional editorial records: 2.NBT.8–9, 2.MD.1–6/8–10, 2.G.1–3. Paired regression: `tests/test_ca_grade2_pages21_22_source_author_slice.py`.
- Previous Grade 2 evidence: 10 p.20 author rows and 3 separately staged 2.NBT.7, **California-added 2.NBT.7.1**, and 2.MD.7. The three source files collectively contain 27 distinct Grade 2 draft author identifiers, **zero independent source approvals**.
- Grade 3: `ca_2013_grade3_page25_source_author_slice.v1.json` contains 10 provisional records (3.OA.1–9 and 3.NBT.1) on printed p.25 (zero-based PDF 31); this is **not complete Grade 3**. Paired regression: `tests/test_ca_grade3_page25_source_author_slice.py`.

## Independent Standards Source-Fidelity Reviewer

Verify original CDE publisher identifiers, printed page locators, full scopes and any California-specific additions/footnotes. Critical distinctions include Grade 2 2.MD.2 unit-size effects, 2.MD.9 whole-unit line plot, 2.G.3 equal partitions, Grade 3 3.OA.2 quotient interpretations, 3.OA.5 property terms not required, 3.OA.7 product fluency/memory, and 3.OA.8 whole-number answer and order-of-operations bounds. Return a bounded exact-SHA APPROVE or CHANGES_REQUIRED; **do not approve the full PR on the basis of these slices**.

## Incomplete accounting and gates

The national completion matrix currently lists only 194 other California authored placements because both attempts to update that existing file were blocked by connector safety checks. Provisional cross-file account is 21 Grade 1 + 27 Grade 2 + 10 partial Grade 3 + 24 Grade 7 + 28 Grade 8 + 62 Algebra I + 59 Mathematics I = **231 authored source rows**, not independently accepted standard coverage. That global matrix must be reconciled by Standards Mapping author before completion. Grade 3 remainder, Grades 4–6, Texas regular Grades 1–6, Washington publisher original-byte authentication, independent scope acceptance and canonical/assessment gates remain unresolved.

PR #384 remains draft and unmerged. No canonical promotion, activation, learner/mastery data changes, or author self-approval permitted.
