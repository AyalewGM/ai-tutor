# Mihur Grades 1–9 gap mapping — Wave 1 triage

**Status: DRAFT, source-linked, NOT verified curriculum coverage.** This is a cross-PR coordination snapshot, not a new production curriculum pack. Independent standards, architecture and mathematical review remain required.

## Evidence examined

- [Ontario Grade 9 MTH1W 2021](https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w) — 43 specific expectations in draft PR #310.
- [Maryland Integrated Algebra I 2025](https://msde.maryland.gov/media/17822) — 30 top-level expectations in draft PR #322.
- [Maryland traditional Algebra I](https://msde.maryland.gov/media/17798) — 40 top-level standards and a 15-skill seed reconciliation in draft PR #323.
- The versioned `docs/curriculum/canonical_alias_map.v1.json` on current `main` — 42 pack aliases; independent mathematical acceptance remains subject to #282/#293.

### Baseline — no verified coverage claimed

| Evidence source | Official expectations inventoried | Existing / provisional relation found | No candidate found | Accepted mapping |
|---|---:|---:|---:|---:|
| Ontario MTH1W | 43 | 4 repository rows, not reviewed | 39 | 0 evidenced by these draft inventories |
| Maryland Integrated Algebra I | 30 | 13 repository rows, not reviewed | 17 | 0 evidenced by these draft inventories |
| Maryland traditional Algebra I | 40 | 17 parent standards with provisional topic links from 15 local skills | 23 | 0 evidenced by these draft inventories |
| **Grade 9 snapshot** | **113** | **34**, of differing and unverified relationship types | **79** | **0 evidenced here** |

**Do not interpret 34/113 as actual curriculum coverage.** Traditional Maryland links are only candidate topic overlaps, while Ontario/Integrated Maryland links are existing seed rows without independent review. The 113 are course-specific standards, **not 113 distinct mathematical concepts**. Cross-jurisdiction reuse must be proven at the canonical skill level, not assumed.

The elementary alias registry has **42 entries**: **38 UNMAPPED** and **4 PROPOSED** at the snapshot. These aliases are not 42 official grade-specific expectations. The 4 proposals are not accepted by the independent review gate. This is a critical Grade 1–5 readiness risk, not a verified count of missing mathematical concepts.

**Grades 6–8:** No authoritative Grade 6–8 expectation inventory was integrated into this cross-PR register. This is an **evidence acquisition gap**, not proof that Mihur has zero content or zero standards mappings in those grades. The next mapping task must inventory official Maryland/major-state Grades 6–8 and relevant Ontario Grades 6–8 expectations before calculating grade-by-grade coverage.

## Ranked workstreams for complete learning packages

| Rank | Batch | Why first | Exit evidence |
|---:|---|---|---|
| 1 | **Grades 1–5 number foundations**: place value, operations, fractions, word-problem structures | Foundational prerequisites, 42 unresolved/proposed elementary aliases, existing fractions content work | Source/versioned grade-level expectations; independently reviewed atomic skills and alias relations; validated complete package |
| 2 | **Grades 6–8 rational numbers and prealgebra**: ratios, proportions, signed arithmetic, exponents, equations | Critical transition into Algebra I; Grade 6–8 authoritative mapping is not yet present in this register | Source inventories and ranked missing concepts before accepted content package |
| 3 | **Grade 9 linear relationships and modeling**: rates, equations, systems, inequalities, graph/representation transitions | Source-linked overlaps across three separate courses and multiple clear candidate gaps | Independent scope decomposition, exact-target generators, worked examples, remediation, independent assessment |
| 4 | **Grade 9 data, geometry, financial literacy** | Algebra-only coverage would leave broad curriculum omissions, especially Ontario MTH1W | Standards-to-atomic-skill and modeling evidence, visual pedagogy, independently validated practice |

The machine-readable [Wave 1 register](grades1_9_gap_triage.wave1.v1.json) records 17 exact Grade 9 source IDs for Batch 3 and 16 for Batch 4 as **illustrative high-priority expectations**, not a complete list or approved equivalences. Grade 1–8 batches intentionally do **not** invent expectation IDs where authoritative grade-level inventories are not yet included.

## Definition of a complete learning package

A bundle can be proposed when it has (1) source-linked expectation and prerequisite rationale, (2) an independently reviewed mathematical skill definition, (3) progressive explanations and worked examples, (4) deterministic parameterized practice and answer contracts, (5) common misconception detection, tiered hints and remediation, (6) an independent assessment design, and (7) an MVE animation/interactive spec where the concept benefits from it. **Production readiness requires Engineering integration and independent QA.**

All seven are separately tracked. A generator does not prove a skill is reviewed; a curated question does not prove generator availability; neither proves mastery. The app-owned deterministic verifier alone decides independent assessment, with historical student records unchanged.

## Immediate handoffs

1. **Curriculum Mapping:** Extend this register with authoritative Grades 1–8 official expectation IDs and existing pack-to-standard reconciliation. Prioritize Grade 1–5 foundational aliases and Grade 6–8 prerequisites. Flag overlaps and missing generator/explanation/assessment evidence separately.
2. **Architecture #282:** Resolve the authoritative canonical registry and alias relation semantics, including composites and `ALL_OF`; no automatic acceptance of legacy `EQUIVALENT` labels.
3. **Independent Math Review #293:** Finish the existing Grade 1 alias gate; explicitly assign additional review scopes for other grades. Never self-approve.
4. **Content Production #311/#312/#306:** Draft substantial prerequisite-connected learning packages, maintaining unverified status until review; do not duplicate the separate fractions pilot intake.
5. **Engineering + MVE + Muse QA:** Integrate accepted packages in substantial batches; validate exact-head CI/AppSec, mathematical determinism, independent mastery separation, accessibility, and child privacy.

**Ownership:** This PR contains only coordination data, no production mappings, canonical ID changes, learner evidence changes, deployment, or approval to merge the existing draft PRs.

## Wave 1 extension — actual Grade 6–8 seed evidence

The initial Wave 1 register identified an official-standards *inventory gap* for Grades 6–8. I have now inspected five existing seed scripts and added [a separate machine-readable local-skill audit](grades6_8_existing_seed_evidence.wave1.v1.json), with a test that checks the exact codes against the scripts on `main`.

| Repository seed | Grade | Local skill rows directly identified |
|---|---:|---:|
| `scripts/seed_grade6.py` (Maryland) | 6 | 7 |
| `scripts/seed_dc_grade6.py` (DC) | 6 | 5 |
| `scripts/seed_va_grade6.py` (Virginia) | 6 | 5 |
| `scripts/seed_grade7.py` (Maryland) | 7 | 15 |
| `scripts/seed_grade8.py` (Maryland) | 8 | 6 |
| **Total in these five scripts** | | **38 local rows** |

**Important:** These 38 are curriculum-local seed entries, not 38 independently verified mathematical skills, and not 38 mapped official expectations. The Grade 8 script extends a pre-existing Grade 8 curriculum; its six rows are explicitly a **partial** inventory, not a complete Grade 8 count. Source-authority URLs in the seeders do not themselves provide expectation-level alignment. The machine-readable audit deliberately records **zero independently accepted mappings in this evidence layer**, not zero actual product content.

**Prioritized Grade 6–8 mapping questions:** (1) ratio/rate/proportional reasoning, (2) signed and rational arithmetic, (3) expression/equation/inequality scope, (4) geometry/transformations/Pythagorean reasoning, (5) data/statistics/probability/functions. All five have *some existing local seed evidence*; none can be marked curriculum-complete until official expectation IDs, reviewed canonical definitions, generators, validated practice and assessment contracts are checked independently.

**Next source acquisition:** identify authoritative expectation identifiers and versions for Maryland Grades 6–8, DC Grade 6 and Virginia Grade 6; then compare those official requirements with the 38 local rows and all other seed/pack sources. Grade 1–5 standards inventory and Grade 8's additional legacy seed remain separate unresolved tasks.

## Wave 1 extension — Ontario Grades 1–8 strand-level source acquisition

Added [Ontario Grades 1–8 source acquisition matrix](on_grades1_8_2020.strand_acquisition.wave1.v1.json) based on the [Ontario Ministry's 2020 curriculum overview](https://www.ontario.ca/page/math-curriculum-grades-1-8) and [official curriculum portal](https://www.dcp.edu.gov.on.ca/en/curriculum/elementary-mathematics?grades=n7). This covers **8 grades × 6 official strands = 48 grade-strand audit cells**: A Social-Emotional Learning and Mathematical Processes, B Number, C Algebra (including coding/modelling), D Data, E Spatial Sense, F Financial Literacy. **These 48 cells are neither 48 expectations nor 48 missing concepts**; official *specific expectation IDs* have not yet been transcribed or independently reviewed. Government overview examples are included only when directly described by that source; blanks do not mean the strand is absent.

**High-impact potential alignment gaps to investigate (not confirmed missing content):**

1. **Number progression and fractions, Grades 1–5:** equal-sharing fraction foundations in Grade 1, array multiplication and fraction equivalence in Grade 3, decimals and multi-digit division in Grade 4, percentage and fraction operations in Grade 5. Verify exact B1/B2 expectation IDs and Mihur's content depth.
2. **Coding and mathematical modelling, Grades 1–8:** Ontario includes these in Algebra across elementary grades. A U.S. equation-solving seed does not prove Ontario coding/modeling readiness. Verify grade-specific C-strand IDs and whether deterministic interactive coding pedagogy exists.
3. **Financial literacy, Grades 1–8:** explicit F-strand progressions include Canadian coins, transactions, value comparisons, budgeting and credit/debt. Grade 9 financial content does not establish elementary-grade coverage.
4. **Grade 6–8 transitions:** integer/rational operations, scientific notation, algebraic relationships, data, spatial reasoning and modeling require expectation-specific comparisons with existing Maryland/DC/Virginia seeds.

**Assessment caveat:** The [official Grade 6 Ontario curriculum page](https://www.dcp.edu.gov.on.ca/en/curriculum/elementary-mathematics/grades/g6-math/strands) states that schools were asked from 2021–22 not to assess/evaluate/report on overall social-emotional learning expectations, while continuing instruction. Strand A must not be automatically converted to deterministic mastery requirements; confirm the policy for the relevant grade and year.

**Next gate:** retrieve each grade's official specific-expectation IDs and exact scope, then reconcile Mihur's actual Ontario elementary packs. The machine-readable 48-cell grid deliberately gives **zero accepted mappings**, rather than falsely equating strand presence with curriculum completeness.
