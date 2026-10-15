# Virginia Grades 6–8 SOL 2023 expectation reconciliation and gap report

Status: **DRAFT / PROPOSED / NOT VERIFIED**
Inventory: `docs/curriculum/standards/va_grades6_8_2023.expectations.v1.json`
Authority: Virginia Department of Education (VDOE)
Source checked: 2026-10-12

## Authoritative source

The authoritative framework is VDOE's [2023 Mathematics Standards of Learning](https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics), approved by the Virginia Board of Education on **2023-08-31** and fully implemented in **SY 2024-2025**. Per-grade instructional resources are linked from the [2023 SOL instructional resources page](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources).

The 2023 SOL uses strand-coded expectation identifiers (`{grade}.{strand}.{number}`) across five strands: Number and Number Sense (NS), Computation and Estimation (CE), Measurement and Geometry (MG), Probability and Statistics (PS), and Patterns, Functions, and Algebra (PFA).

**This inventory fills the evidence-acquisition gap named in `grades1_9_gap_triage.wave1.md`: no authoritative Grade 6–8 expectation inventory previously existed for Virginia.** Maryland's counterpart is `md_grades6_8_2025.seed_skill_reconciliation.v1.json`.

## Official expectation inventory

**46 top-level grade-level expectations** were inventoried:

| Grade | NS | CE | MG | PS | PFA | Total | Repository-linked rows | Gaps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 3 | 2 | 4 | 2 | 4 | 15 | 5 | 10 |
| 7 | 3 | 2 | 4 | 2 | 4 | 15 | 10 | 5 |
| 8 | 2 | 1 | 5 | 3 | 5 | 16 | 0 | 16 |
| **Total** | | | | | | **46** | **15** | **31** |

## Repository state

Existing Virginia seeds predate the reviewed-taxonomy gate and carry `MATH.*` canonical-looking targets with `"basis": "AI Tutor reviewed 2023 SOL mapping"` provenance — **self-labeled, not independently accepted**.

- `scripts/seed_va_grade6.py` (`VA_MATH_6`): 5 local skills — `VA6.PFA.RATIO`, `VA6.NS.RATIONAL`, `VA6.CE.FRACTION`, `VA6.PFA.EXPR`, `VA6.PFA.EQUATION`
- `scripts/seed_va_grade7.py` (`VA_MATH_7`): 5 local skills — `VA7.CE.RATIONAL`, `VA7.PFA.PROPORTIONAL`, `VA7.PFA.EQUATION`, `VA7.MG.GEOMETRY`, `VA7.PS.PROBABILITY`
- **Grade 8: no Virginia seed rows exist at all** (`VA_MATH_8` has no seed script).

### Material findings

1. **Grade 8 is a complete repository gap.** All 16 official Grade 8 expectations — real-number subsets, percent applications, angle relationships, Pythagorean Theorem, transformations, functions, and multistep equations/inequalities — have no repository-specific local skill. This is the largest single Virginia gap: pre-algebra completion and Algebra I readiness.

2. **Integer and rational-number work is underrepresented.** `6.NS.2` (integers/absolute value), `6.CE.2` (integer operations), `7.NS.2` (rational comparison), and `7.NS.3` (square roots) have no linked seed row, even though integer content exists elsewhere in the repository under Maryland and generic identities. Jurisdiction-local reuse must be decided by Standards Mapping, not assumed.

3. **Composite seeds span multiple expectations.** `VA7.MG.GEOMETRY` ("Geometry Applications") overlaps all four 7.MG expectations; `VA7.PS.PROBABILITY` ("Probability and Data") overlaps both 7.PS expectations; `VA6.PFA.RATIO` overlaps both 6.PFA.1 and 6.PFA.2. These are provisional topical overlaps only — composite rows cannot transfer mastery to distinct atomic identities.

4. **`VA6.PFA.EXPR` has no clear official expectation.** The 2023 Grade 6 SOL has no standalone expression-simplification standard (6.PFA.3 is one-step equations). The seed may partially relate to equation-writing but is not equivalent to any expectation — flagged as `seed_rows_without_clear_expectation`.

5. **Data-cycle expectations are Virginia-specific in emphasis.** Each grade names a representation focus (6.PS.1 circle graphs, 7.PS.2 histograms, 8.PS.2 boxplots, 8.PS.3 scatterplots). Mapped content must target the exact representation, not generic statistics.

6. **`8.PFA.3` carries an explicit boundary note** limiting linear-function work (y-intercept and ordered pairs); scope summaries must be verified against official wording during review.

## Six independent readiness dimensions

Every expectation is classified separately for repository standards mapping, independently reviewed mathematical skill, exact-target generator availability, validated practice, assessment readiness, and verified mastery evidence.

- **16 expectations** have provisional repository-row links (`REPOSITORY_EXISTING_UNVERIFIED`) — none accepted.
- **30 expectations** have no repository-specific candidate at all.
- **0 expectations** claim verified coverage on any dimension.

## Safety

- Activation: **FORBIDDEN**. No canonical IDs created. No learner evidence mutation. No verified coverage claim.
- Standards Mapping and Independent Mathematical Review approval are required before any mapping, generator, or package work proceeds from this inventory.

## Handoffs

1. **Standards Mapping:** reconcile `VA6.*`/`VA7.*` seed rows against the exact official expectation wording; decide composite decomposition; authorize a Virginia Grade 8 seed scope.
2. **Independent Math Review:** any accepted mapping requires review of the exact atomic target — broad `MATH.*` seed targets are not range-equivalent per the #293 precedent.
3. **Content Production:** Grade 8 is the highest-priority authoring surface (16 unmapped expectations covering pre-algebra completion); Grade 6 integer/negative-number scope is second.
4. **Engineering (Devin):** no work required until mappings are accepted; the inventory is coordination data only.

### Official grade-document provenance (corrected 2026-10-12)

| Grade | Authoritative VDOE 2023 SOL document | Published standard version | Status |
|---|---|---|---|
| 6 | [Mathematics Standards of Learning for Virginia Public Schools — 2023 Grade 6](https://www.doe.virginia.gov/home/showpublisheddocument/48936/638296739041730000) | August 2023; Grade 6, printed page 1 | Standards authority |
| 7 | [Mathematics Standards of Learning for Virginia Public Schools — 2023 Grade 7](https://www.doe.virginia.gov/home/showpublisheddocument/48908/638741650017470000) | August 2023; Grade 7 section, printed page 49 (within the VDOE K–12 compilation) | Standards authority |
| 8 | [Mathematics Standards of Learning for Virginia Public Schools — 2023 Grade 8](https://www.doe.virginia.gov/home/showpublisheddocument/48945/638741652670270000) | August 2023; Grade 8, printed page 1 | Standards authority |

The VDOE [2023 instructional-resources page](https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources) remains an **implementation-support reference only**. Every expectation row links to the corresponding official standards document and a grade-specific source ID; no 2016 SOL code or instructional guide is promoted to 2023 authority. Exact item-page locators beyond the grade-section start remain **not independently recorded**. All proposed Mihur mappings remain unaccepted.


## Post-merge #375 focused correction — Grade 7 histogram relation (2026-10-12)

The merged source inventory provisionally linked 2023 SOL `7.PS.2` (data cycle with histograms) to `VA7.PS.PROBABILITY`. Direct inspection of `scripts/seed_va_grade7.py` finds a bag-draw probability question and a sample-preference percentage question, **not** a histogram construction/interpretation or complete statistical data-cycle generator. This topical probability link is unsupported as a source-to-skill relation and is removed without altering the seed or creating a new canonical ID. Grade 7 repository-linked expectation rows fall from 11 to 10; the inventory total falls from 16 to 15, while unmatched rows increase from 30 to 31. These are **unverified repository-link counts**, not canonical coverage or mastery percentages. Independently verify the exact 2023 VDOE `7.PS.2` mathematical statement, page and lettered subparts before proposing any replacement mapping. Original merged PR #375 remains unchanged.
