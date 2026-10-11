# Mihur Learning Package Factory — Wave 2 (DRAFT)

This wave expands Grade 1–9 **instructional depth**, not approved curriculum coverage. It builds on Wave 1 draft PR #327 and Standards Mapping's ranked gap register PR #325.

## Deliverables

Six packages, each with five worked examples, three misconception-specific Socratic remediation pathways, four guided practice items, three independent assessment/transfer items, diagnostic probes, five-stage concrete→visual→symbolic lessons, and MVE interaction/accessibility specifications.

- **Grades 1–2:** addition/subtraction unknown position and equality.
- **Grades 4–5:** decimals, fraction conversion and place-value comparisons.
- **Grades 6–7:** unit rates and equivalent ratios using double number lines.
- **Grades 6–8:** five-number summaries, IQR, box plots and comparison of distributions.
- **Grades 6–8:** cube-net foldability and surface area.
- **Grade 9 / Algebra I:** quadratic patterns, area models, factorization and two real roots.

**Draft totals:** 30 worked examples, 18 remediation pathways, 24 guided practice items, 18 independent assessment items. Combined with PR #327 if both are accepted: 11 draft packages, 55 examples, 33 misconception pathways, 44 guided practice items, 33 assessment items. **Not deduplicated against existing content and not verified.**

## Handoff and boundaries

- Standards Mapping: assign exact, source-versioned Ontario and Maryland expectation IDs, confirm appropriate grade placements; no invented alignment.
- Mathematical Review: independently verify every mathematical claim, worked step, error probe and transfer item. For quartiles, approve or adjust the specified median-of-halves convention before assessment use; for cube nets, verify hinge geometry with a fold simulator; for quadratic roots, distinguish solving equations from principal square root notation.
- Engineering: deduplicate against existing families and draft PRs #309, #315, #316, #317, #319 and #327; avoid new canonical identifiers. Add deterministic seedable generators only after independent acceptance of item contracts.
- MVE: implement keyboard-operable representations and equivalent accessible text; ensure assessments do not expose lesson scaffolds.
- Muse QA: check independent assessment isolation, content correctness, accessibility, mobile behavior, deterministic variants, and historical learner-evidence preservation.

**Review gates:** DRAFT_UNVERIFIED, runtime_activation=false, mastery_writes=false, standards mapping provisional, independent math review pending, QA pending. No activation, merge, production taxonomy, or student data changes.

## Checks

`pytest -q tests/test_learning_packages_wave2.py`

Tests check draft metadata, package depth, and a subset of independently calculated arithmetic. They are not evidence of full lesson correctness or a passed CI run until executed.
