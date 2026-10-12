# Maryland Grades 6–8 MCCRS 2025 expectation inventory and gap report

Status: **DRAFT / PROPOSED / NOT VERIFIED**
Inventory: `docs/curriculum/standards/md_grades6_8_2025.expectations.v1.json`
Authority: Maryland State Department of Education (MSDE)
Source checked: 2026-10-12

## Authoritative source

The governing documents are MSDE's revised MCCRS Mathematics crosswalks, **adopted July 29, 2025, implemented SY 2026-2027**:

| Grade | Crosswalk | Companion |
|---|---|---|
| 6 | https://msde.maryland.gov/media/17816 | https://msde.maryland.gov/media/17817 |
| 7 | https://msde.maryland.gov/media/17818 | https://msde.maryland.gov/media/17819 |
| 8 | https://msde.maryland.gov/media/17820 | https://msde.maryland.gov/media/17821 |

The 2025 framework re-domains the 2010 CCSS strands into **NOS** (Number and Operation Sense), **AT** (Algebraic Thinking), **GR** (Geometric Reasoning and Measurement), and **DS** (Data, Statistics, and Probability / Data and Statistics at Grade 6). Legacy identifiers (`6.NS.*`, `7.RP.*`, `8.EE.*`, `8.F.*`, `8.SP.*`) appear only in the crosswalk's previous-standards column and are **not** new-framework expectation IDs.

**This manifest completes the Grade 6–8 evidence-acquisition task named in `grades1_9_gap_triage.wave1.md`.** The earlier `md_grades6_8_2025.seed_skill_reconciliation.v1.json` reconciled 28 existing local seeds against official IDs; this inventory enumerates **all 79** top-level expectations so coverage and gaps are measured against the complete official set. Virginia's counterpart is `va_grades6_8_2023.expectations.v1.json`.

## Official expectation inventory

| Grade | NOS | AT | GR | DS | Total | Seed-linked rows | Unmapped |
|---|---:|---:|---:|---:|---:|---:|---:|
| 6 | 9 | 11 | 4 | 6 | 30 | 16 | 14 |
| 7 | 3 | 9 | 4 | 6 | 22 | 19 | 3 |
| 8 | 5 | 11 | 5 | 6 | 27 | 11 | 16 |
| **Total** | **17** | **31** | **13** | **18** | **79** | **46** | **33** |

Seed linkage is copied verbatim from the merged reconciliation (`md_grades6_8_2025.seed_skill_reconciliation.v1.json`), including its provisional relation kinds (`COMPOSITE_SCOPE`, `PARTIAL_SCOPE`, `NARROW_SUBSCOPE`, `CLOSE_SCOPE_REVIEW_REQUIRED`, `PARTIAL_OR_EXTRA_SCOPE`, `CROSS_GRADE_COMPOSITE`). None are accepted mappings.

## Material findings

1. **Grade 8 is the thinnest coverage.** 16 of 27 Grade 8 expectations have no repository row at all — including the entire slope/linear-relationships cluster (`8.AT.A.*`), all equation/inequality/systems standards (`8.AT.B.*`), `8.AT.C.8`/`8.AT.D.9` (new standards), the angle/triangle geometry cluster (`8.GR.A.*`), the exponent/root/scientific-notation cluster (`8.NOS.B.*`), and both categorical-data standards (`8.DS.C.*`). This is the pre-algebra→Algebra-I bridge and the highest-priority authoring surface.

2. **Grade 6 integer and coordinate-plane scope is absent locally.** `6.NOS.C.5`–`6.NOS.C.9` (rational opposites, number lines, four-quadrant graphing, absolute value) have no linked seed — despite integer content existing elsewhere in the repository under other jurisdictions/identities. Reuse must be decided by Standards Mapping, not assumed.

3. **Grade 6 inequality and percent work is absent.** `6.AT.C.9`/`6.AT.C.10` (contextual inequalities) and `6.AT.A.4` (percent of a quantity) have no linked seed.

4. **Data-cycle and probability sampling gaps.** `6.DS.A.1`/`6.DS.A.2` (statistical questions, likelihood language) and `7.DS.A.1`/`7.DS.A.2`/`7.DS.B.3` (sampling, population inference, distribution comparison) are unmapped; `7.DS.C.*` links are `CROSS_GRADE_COMPOSITE` because the single `M7.SP.PROB` seed straddles grades.

5. **Composite seeds cannot transfer mastery.** `M6.G.GEO`, `M6.SP.STAT`, `M8.F.FN`, `M8.SP.STAT`, `M7.NS.RAT`, `M7.EE.*` each span multiple distinct expectations. Per the #293 review precedent, broad seeds are not range-equivalent and cannot carry verified coverage — they are authoring anchors only.

6. **Cross-grade placement findings preserved.** The merged reconciliation already records that two Grade 7 local seeds straddle Grade 7/8 placement and two Grade 8 seeds fall outside the 2025 Grade 8 placement — those Architecture decisions are incorporated by reference, not re-decided here.

## Six independent readiness dimensions

- **46 expectations** carry provisional repository links (`REPOSITORY_EXISTING_UNVERIFIED`) — none accepted.
- **33 expectations** have no repository-specific candidate.
- **0 expectations** claim verified coverage on any dimension.

## Safety

- Activation: **FORBIDDEN**. No canonical IDs created. No learner evidence mutation. No verified coverage claim.
- Standards Mapping and Independent Mathematical Review approval required before any mapping, generator, or package work proceeds.
- Inventory unit is the top-level standard; lettered sub-skills (a, b, c…) in the official statements are not separately enumerated.

## Handoffs

1. **Standards Mapping:** extend `md_grades6_8_2025.seed_skill_reconciliation.v1.json` to cover the 33 unmapped expectations; decompose composite seeds into atomic candidates.
2. **Independent Math Review:** review of exact atomic targets only — composite/broad seeds cannot be approved as equivalents per the #293 precedent.
3. **Content Production:** Grade 8 linear relationships (`8.AT.*`) and Grade 6 rational-number/coordinate scope (`6.NOS.C.*`) are the priority authoring surfaces.
4. **Engineering (Devin):** no work until mappings are accepted; this manifest is coordination data only.
