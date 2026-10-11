# Fraction equivalence reasoning revision (DRAFT_UNVERIFIED)

This is a depth revision of the existing `W1-G4-FRACTION-EQUIVALENCE`
package from draft PR #327. It does not create a package count, canonical
identity, standards mapping, runtime route, assessment API, or mastery write.

## Reuse-first audit

| Existing work | Actual gap | Planned improvement | Verification |
| --- | --- | --- | --- |
| PR #327 already authors `W1-G4-FRACTION-EQUIVALENCE`; its pedagogy-only review accepted the equal-whole, bar, number-line and misconception design | The batch record has no machine-readable source/version evidence for this package and no seedable reasoning variants | Preserve the package ID and add a complete fail-closed provenance record plus deterministic guided/independent namespaces | Contract, oracle, invalid-input and non-disclosure tests in `tests/test_foundations_fraction_equivalence_v2.py` |
| Main already has canonical family `MATH.FRAC.EQUIV.FIND`, legacy `FRACTION_EQUIVALENCE` generation, the `fraction_bar` renderer, and `InteractiveFractionBars` | The existing interactive component shades one fixed-denominator bar; it cannot compare paired equal wholes or repartition each piece | Reuse the renderer/component contract, but record integration as `PARTIAL_REUSE_NOT_WIRED` and hand paired-bar/repartition behavior to the MVE owner | Tests assert the reuse boundary and forbid claims of working runtime integration |
| PR #325 records broad curriculum-gap evidence but no independently accepted exact mapping for this Grades 3–5 package | A grade band and generator do not establish an official expectation | Record source URL, publication/version and exact IDs as `UNKNOWN_PENDING_STANDARDS_MAPPING`, with zero mapping or coverage credit | Provenance tests require empty expectation IDs, `UNKNOWN` fields and approval `NONE` |
| The original transfer compares equal-size ribbons with two names for one half | That confirms equivalence but does not test whether the learner distinguishes equal fractions from equal quantities when wholes differ | Add a two-part transfer: identify equivalent fraction values, then determine that colored quantities differ when whole lengths differ | Exact `Fraction` oracle tests recompute both statements independently |

## Ownership and limits

- Foundations Content owns only this draft package revision and its local
  deterministic review generator.
- Standards Mapping owns authoritative source selection and expectation IDs.
- Mathematical Review owns correctness and scope.
- Pedagogical Review must review this revision independently; the acceptance
  of PR #327 applies only to the earlier authored revision.
- The MVE owner controls paired-bar/repartition implementation; Muse owns
  accessibility and end-to-end assessment verification.
- Engineering and Assessment Backend own routing and trusted scoring.

`runtime_activation` remains `false`. The draft generator is not imported by
production code and performs no learner, attempt, diagnostic, or mastery write.
