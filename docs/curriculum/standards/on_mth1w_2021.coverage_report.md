# Ontario MTH1W (2021) standards coverage and gap report

Status: **DRAFT / PROPOSED / NOT VERIFIED**  
Inventory: `docs/curriculum/standards/on_mth1w_2021.expectations.v1.json`  
Authoritative authority: Ontario Ministry of Education  
Source checked: 2026-10-09

## Scope and provenance

This report inventories all 43 specific expectations in strands B–F of the official Grade 9 de-streamed Mathematics course (MTH1W, 2021). Ontario issued the course on 2021-06-09 for implementation beginning September 2021.

Primary sources:

- [Official MTH1W course](https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w)
- [Official expectations by strand](https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w/strands)
- [Official overall and specific expectations chart](https://assets-us-01.kc-usercontent.com/fbd574c4-da36-0066-a0c5-849ffb2de96e/2c41223a-5f39-4dd2-b94c-c75d2fae1fbd/Math_9_strand%20chart_AODA_06-May-21.pdf)

The JSON contains editorial scope summaries and links to the authoritative wording. It does not reproduce the full official text and does not claim source-fidelity acceptance.

## Inventory result

| Strand | Specific expectations | Existing repository-specific crosswalks | Independently accepted under current taxonomy gate |
|---|---:|---:|---:|
| B — Number | 10 | 0 | 0 |
| C — Algebra | 15 | 4 expectations (C1.2–C1.5) | 0 |
| D — Data | 8 | 0 | 0 |
| E — Geometry and Measurement | 6 | 0 | 0 |
| F — Financial Literacy | 4 | 0 | 0 |
| **Total** | **43** | **4** | **0** |

Broad seed rows such as `MTH1W.B`, `MTH1W.C`, and `MTH1W.F` are not counted as specific-expectation mappings.

## Existing repository evidence

The current MTH1W seed provides specific expectation rows for C1.2, C1.3, C1.4, and C1.5 and maps them through curriculum-local skills. `scripts/map_canonical_curricula.py` then crosswalks those local skills to existing `MATH.*` codes.

These are recorded as **repository-existing / unverified under the current taxonomy gate**, not as accepted coverage:

- C1.2 → `MATH.EE.EXPR`
- C1.3 → `MATH.EE.LIKE_TERMS`
- C1.4 → `MATH.EE.LIKE_TERMS` and `MATH.EE.POLYNOMIAL_OPERATIONS`
- C1.5 → `MATH.EE.EQUATION.ONE`, `MATH.EE.EQUATION.TWO`, and `MATH.EE.EQUATION.MULTISTEP`

PR #229 proves that draft ingestion/publication mechanics can keep Ontario and Maryland identities isolated. Its representative C1.5 mapping is pipeline proof only; it is not evidence that all of C1.5—or MTH1W generally—is covered.

## Material gaps

1. **Canonical authority is blocked.** PR #308 intentionally leaves the production taxonomy empty. Existing database codes and generator targets cannot be treated as independently reviewed canonical identities.
2. **Thirty-nine specific expectations have no repository-specific mapping.** The largest unmapped families are Number, Data, Geometry/Measurement, Financial Literacy, coding, relations, and mathematical modelling.
3. **The four existing crosswalked expectations need decomposition review.** Each Ontario expectation is broader than one procedural label. For example, C1.5 includes creating contextual equations, solving them, and verifying solutions; the current crosswalk must prove complete or explicitly partial coverage.
4. **Capability evidence is separate.** Generator availability, validated practice, assessment readiness, and mastery evidence remain unverified for every expectation in this inventory. No field is inferred from another.
5. **Integrated strands are not standalone mastery shortcuts.** MTH1W Strand A and the SEL expectation are integrated through instruction and assessment contexts; this inventory does not invent standalone canonical IDs for them.

## Required independent review sequence

1. Standards Mapping reviewer checks identifiers, strand placement, source version, and scope summaries against the official Ontario publication.
2. Architecture confirms only reviewed atomic canonical identities may be mapping targets and records composite/partial mapping semantics.
3. Independent Mathematical Review assesses each proposed target's mathematical scope; generator existence is not evidence.
4. Muse QA independently verifies any declared generator, practice, assessment, and evidence status.
5. Only after explicit acceptance may a mapping move from PROPOSED to REVIEWED. No learner records or historical mastery are rewritten.

## Next coherent mapping batch

Start with **C1 Algebraic Expressions and Equations (C1.2–C1.5)** because repository-local and canonical crosswalk candidates already exist. Review them as potentially partial mappings, with C1.5 specifically decomposed across equation creation, solution classes, contextual modelling, and verification. Do not extend the PR #229 proof assertion into coverage credit.

Maryland Algebra I remains a parallel priority, but its existing proof identifier is explicitly Mihur-labelled. Official MSDE expectation identifiers must be extracted and reviewed before a Maryland mapping manifest can claim authoritative identifiers.
