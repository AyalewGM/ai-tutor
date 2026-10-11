# Grade 9 Algebra — Draft Reuse Audit

This branch is draft-only and does not activate runtime content, change canonical IDs, or write learner evidence. Existing Grade 9 packages are owned by PRs #327 and #328; this branch is reserved for independent provenance and pedagogy evidence.

| Existing work | Actual gap | R4 improvement | Verification |
| --- | --- | --- | --- |
| `W1-G9-LINEAR-MODELING`, main linear generators, and `InteractiveLinearExplorer` candidate reuse | Independent review found scope drift, an unrelated equation drill, and no independent table↔graph translation or physical-domain justification | Bound the arc to one linear model across context/table/graph/equation/domain; add a deterministic six-field delivery-log transfer | Exact reconstruction and public-payload non-disclosure tests; pedagogy re-review, math review, standards, Muse, and wiring still pending |
| `W2-G9-QUADRATIC-PATTERNS`, main quadratic generators, and tile/rectangle specification | Independent review found a shift from pattern growth into factoring/roots and no unseen prediction or explanation of quadratic growth | Bound the arc to tile tables, first/second differences, stage prediction, rule, and explanation; add a deterministic five-field transfer | Exact finite-difference reconstruction and public-payload non-disclosure tests; all independent gates still pending |

`W4-G9-EXPO-MODELING` is deliberately unchanged: its source remains `UNKNOWN_UNLOCATED`, so it is not counted as coverage or advanced by this revision.
