# Grade 9 Algebra — Draft Reuse Audit

This branch is draft-only and does not activate runtime content, change canonical IDs, or write learner evidence. Existing Grade 9 packages are owned by PRs #327 and #328; this branch is reserved for independent provenance and pedagogy evidence.

| Existing work | Actual gap | R4 improvement | Verification |
| --- | --- | --- | --- |
| `W1-G9-LINEAR-MODELING`, main linear generators, and `InteractiveLinearExplorer` candidate reuse | Independent review found scope drift, an unrelated equation drill, and no independent table↔graph translation or physical-domain justification | Bound the arc to one linear model across context/table/graph/equation/domain; add a deterministic six-field delivery-log transfer | Exact reconstruction and public-payload non-disclosure tests; pedagogy re-review, math review, standards, Muse, and wiring still pending |
| `W2-G9-QUADRATIC-PATTERNS`, main quadratic generators, and tile/rectangle specification | Independent review found a shift from pattern growth into factoring/roots and no unseen prediction or explanation of quadratic growth | Bound the arc to tile tables, first/second differences, stage prediction, rule, and explanation; add a deterministic five-field transfer | Exact finite-difference reconstruction and public-payload non-disclosure tests; all independent gates still pending |

## R5 measured quadratic-depth supplement

The PR #447 synthetic full-seed audit reports only two stored distinct tasks in one
family for both `MTH1W.C.QUAD` and `A1.QUAD.FN`. R5 therefore deepens the existing
`W2-G9-QUADRATIC-PATTERNS` package ID rather than opening a jurisdiction-specific
bank. It preserves the R4 tile/area work and adds seven structurally different
draft families: exact rational substitution, factored roots with substituted
totals, vertex symmetry, complete plus/minus branches, no-real classification,
equal-step table-to-rule evidence, and reconciliation of standard/factored/vertex
forms. Fresh transfer must change mathematical family, not just coefficients.

R5 is implemented only in `quadratic_depth_r5.py` with machine-readable evidence
in `quadratic_depth_r5.package.json`. It is not imported by runtime code, registered,
seeded, routed, scored, or mapped. Canonical authority remains
`UNKNOWN_NOT_AUTHORITATIVE`; standards mappings remain provisional; independent
Math, Pedagogy, Muse, backend, frontend/accessibility, and Engineering gates are
all pending.

`W4-G9-EXPO-MODELING` is deliberately unchanged: its source remains `UNKNOWN_UNLOCATED`, so it is not counted as coverage or advanced by this revision.
