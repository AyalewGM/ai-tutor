# Mihur Learning Package Factory — Wave 3 expansion on PR #328

**Status: DRAFT_UNVERIFIED** · Runtime: off · No student-data or mastery writes · Standards mappings: provisional · Independent math review: pending · QA: pending.

## Five additional packages

| Package | Band | Model emphasis |
|---|---|---|
| W3-G3-MULTIPLICATIVE-ARRAYS | Grades 2–4 | Rotatable tile arrays, equal groups, inverse division |
| W3-G5-FRACTION-ADDITION | Grades 4–6 | Common-unit fraction bars and number lines |
| W3-G7-SIGNED-NUMBERS | Grades 6–8 | Directional number line and signed counters |
| W3-G8-COORDINATE-TRANSFORM | Grades 7–9 | Rigid transformations on a coordinate grid |
| W3-G9-SYSTEMS-LINEAR | Grade 9 | Linked equations and graph with no/one/infinite solutions |

Each package includes 2 diagnostics, 5 worked examples, 3 misconception-specific Socratic pathways, 4 guided practice problems, 3 independent assessment/transfer problems, five concrete-to-visual-to-symbolic teaching phases and interactive/a11y specifications. Wave 3 contains **25 worked examples, 15 misconception pathways, 20 guided practice and 15 independent assessments**. These items are authored draft content, not implemented interactive components or production question generators.

This expansion is committed **to the existing Wave 2 PR #328** instead of creating a third small PR. Across the original draft Wave 1 PR #327 and Waves 2–3 contained in #328, authored totals are 16 draft packages, 80 worked examples, 48 remediation pathways, 64 guided practice problems and 48 independent assessments. Counts are not deduplicated or independently approved.

## Independent review gates

1. **Mapping**: link exact source-versioned Ontario/Maryland expectation IDs or mark a concept unmapped. No unsupported grade-placement claims.
2. **Math**: independently verify worked steps, assessment keys, notation, whole-size assumptions and solution cardinality. Special checks: missing-number language, fraction equal wholes, integer negative products, reflection versus translation, coincident versus parallel linear systems.
3. **Engineering**: reuse existing canonical identity and generators. Review overlap with PRs #309, #315, #316, #317, #319, #327, plus Wave 2 contents already on #328.
4. **MVE**: keyboard operability and screen-reader mathematical state descriptions; hide teaching scaffolds in independent assessment.
5. **QA**: require stronger exact-answer oracle coverage and separate unseen deterministic generator seeds before production; verify historical mastery remains unchanged.

Run `pytest -q tests/test_learning_packages_wave3.py`; draft tests check safety and selected arithmetic only, not comprehensive mathematical correctness. **No passing CI or independent approval is claimed.**

## Next content depth priorities

Improve statistics distribution-shape interpretation and contextual comparisons, non-cube prism and pyramid nets, Grade 9 functions and modeling, and Grade 1–5 measurement and division strategies. Prefer deeper reviewable batch updates over new small PRs.
