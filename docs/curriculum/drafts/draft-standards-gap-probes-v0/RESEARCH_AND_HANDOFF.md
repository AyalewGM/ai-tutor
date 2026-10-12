# Ontario–Maryland mathematical concept gap intake (PROVISIONAL)

**Status:** DRAFT_UNVERIFIED. **Scope:** content production and candidate-gap identification only; **not** a completed standards-to-skill mapping or proof that any canonical skill is missing.

## Authoritative source set
- Ontario Ministry of Education, Mathematics Grades 1–8 (2020): https://www.ontario.ca/page/math-curriculum-grades-1-8
- Ontario official Grade 5 strand overview: https://www.dcp.edu.gov.on.ca/en/curriculum/elementary-mathematics/grades/g5-math/strand-overviews
- Maryland State Department of Education, mathematics standards and implementation timeline: https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics
- Maryland mathematical domain regulation: https://regs.maryland.gov/us/md/exec/comar/13A.04.12.01

## Repository evidence inspected
- `app/canonical_problem_families.py` on `main` imports domain generators for `statistics_probability`, `elementary_data_patterns`, `bivariate_sampling`, `geometry_measurement`, `geometry_reasoning_depth`, `measurement_spatial`, `financial_simple_interest`, `financial_budget_capacity`, `financial_percent_unit_depth`, and algebraic modules. **Thus none of these entire domains should be labelled absent from Mihur.**
- This is a *module-level inspection*, not an exhaustive concept-by-concept inventory. Generator existence does not prove canonical concept completeness, explanation quality, standards alignment, or assessed mastery.
- The 16 new original content probes in `content.draft.json` are exploratory draft content. They are **not** new canonical skill definitions.

## Candidate concepts requiring canonical taxonomy reconciliation

| Concept candidates | Ontario evidence | Maryland evidence | Current verdict |
|---|---|---|---|
| Representative sampling, misleading graph scales, outlier-sensitive mean | Data literacy strand | Measurement/data and statistics/probability domains | **CHECK DEPTH**; data generators already exist |
| Independent/dependent event probability, experimental probability | Data/probability strand | Statistics/probability | **CHECK DEPTH**; probability generator exists |
| Triangle/parallel-line angle relationships, area vs perimeter, volume | Spatial sense strand | Geometry and measurement | **CHECK DEPTH**; geometry generators already exist |
| Budget constraints, best-value unit price, simple interest | Financial literacy strand | Mathematical modelling/financial literacy connections in companion guidance | **CHECK DEPTH**; financial generators already exist |
| Repeated-loop numeric patterns, explicit modelling assumptions and constraints | Algebra coding/modelling strands | Mathematical practices: modelling, structure, reasoning | **CHECK DEPTH**; determine whether content is an application of existing skills rather than a distinct canonical concept |

## Review and handoff rules
1. Mapping agent: retrieve specific official grade expectation identifiers and document versions, then compare each candidate to the approved canonical taxonomy. **Do not infer expectation IDs from these broad strand summaries.**
2. Independent mathematical reviewer: distinguish genuinely missing mathematical concepts from different representations, pedagogical applications, and generator-depth gaps; review mathematical correctness of every probe.
3. Engineering Lead: deduplicate against active generator families and other draft PRs before accepting any content. Only independently approved work may proceed through integration.
4. Content Production: refine explanations, misconceptions and transfer tasks only; do not approve canonical definitions, claim verified coverage, modify student mastery, or activate runtime content.
5. Maryland version note: the state lists Algebra I for implementation in school year 2026–2027, with revised Integrated Algebra I in **future** school years. Do not conflate them.
