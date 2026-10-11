# Mihur Learning Package Factory — Wave 1 (DRAFT)

**Status:** DRAFT_UNVERIFIED. **Runtime:** OFF. **Standards alignment:** PROVISIONAL_NOT_ACCEPTED. **Math review and Muse QA:** PENDING.

## Purpose and inventory

First cross-grade teaching-depth batch based on ranked gap register PR #325 and existing Mihur generators. This is **not** a claim of complete Grades 1–9 coverage. These five exemplar packages are a foundation for systematic expansion.

| Package | Grade band | Existing concept reused / depth strengthened |
|---|---|---|
| W1-G2-PLACE-VALUE-REGROUP | 1–3 | place value; regrouping models and comparison |
| W1-G4-FRACTION-EQUIVALENCE | 3–5 | fraction equivalence; fraction-bar and number-line explanation |
| W1-G6-FRACTIONAL-PRISM-VOLUME | 6–7 | prism volume; fractional edge lengths and exact cubic units |
| W1-G7-PERCENT-COMMISSION-ERROR | 7–8 | percent applications; commission, fees, reference-based error |
| W1-G9-LINEAR-MODELING | Grade 9 / Algebra I | linear functions; rate/intercept/domain contextual modeling |

Each package has five worked examples, three misconception-specific Socratic pathways, four guided practice items, three separate independent assessment/transfer items, a five-phase teaching sequence, a diagnostic prompt, and keyboard/screen-reader/reduced-motion MVE specifications. In total: **25 worked examples, 15 remediation pathways, 20 guided practice items and 15 independent assessment items.** These counts represent draft authored content, not verified coverage or readiness.

## Review and acceptance handoff

1. **Curriculum Mapping:** link each package to exact expectation identifiers and publication versions; do not assume grade placement is authoritative. PR #325 is source for prioritization only.
2. **Mathematical Review:** independently inspect every worked solution, diagnostic, misconception, answer contract, unit, and assessment. Particularly examine Grade 2 place-value exchange language, Grade 4 equal-whole requirement, Grade 6 fractional unit partitions, Grade 7 reference base for percent error, and Grade 9 physical domain constraints.
3. **Engineering:** deduplicate against existing packages/PRs #309, #315, #316, #317, #319, and the generator registry. These are teaching-depth proposals, not new canonical skills or new active generator identities. Attach approved content to existing families only after review.
4. **Muse QA:** test independence of assessment from teaching hints and MVE scaffolds, deterministic exact oracles, accessibility, mobile interactions, and rollback/learner-history isolation.
5. **Release:** only after independent approval, accepted standards mapping where claimed, CI/AppSec, and QA may content be considered for activation. No activation performed here.

## Execution

`pytest -q tests/test_learning_packages_wave1.py`

The included tests validate structural draft gates and a subset of independent arithmetic oracles. **They do not prove complete mathematical correctness, exhaustive generator coverage, mastery readiness, or curriculum alignment.** No test execution is claimed by the authoring agent until CI produces evidence.

## Next coherent batches

- **Wave 2 (Grades 1–5):** full-number operations and unknown-position word problems, fractions and decimals, measurement/geometry; deduplicate PRs #309/#316/#319 first.
- **Wave 3 (Grades 6–8):** histogram/box-plot interpretation, IQR comparisons, valid solid nets, ratios and rational operations; preserve existing generators.
- **Wave 4 (Grade 9):** Ontario MTH1W and Maryland Algebra I linear/quadratic/data/geometry/financial modeling, only with verified expectation IDs and independent review.
- **Factory gate:** record for each canonical skill separately: mapped expectation, mathematical approval, generator, diagnostic, examples, misconception repair, independent assessment, interactive implementation, QA, runtime activation, and observed learner mastery. Do not collapse these into a single 'covered' flag.
