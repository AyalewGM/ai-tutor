# Grade 9 algebra reuse-first audit

Status: DRAFT_UNVERIFIED. No runtime activation or learner evidence changes.

Existing work: PR #327 covers linear modeling, PR #328 covers quadratic patterns and exponential comparisons, and PR #317 covers algebraic equations. Existing generators are in app/domains/algebra_functions.py and app/domains/advanced_algebra_highschool.py. InteractiveLinearExplorer and InteractiveEquationBalance already exist.

Actual gaps: Independent review found that linear modeling drifted across several objectives and omitted table↔graph/domain evidence, while quadratic patterns shifted from growth/second differences into factoring and roots. The drafts still do not establish verified misconception-specific response branching, independent transfer scoring, or accessible student-journey integration. The quadratic and exponential manipulatives have not been verified. Generated question counts are not verified learning coverage.

Proposed improvement: Extend these existing packages instead of producing competing package IDs. R4 narrows linear work to one context/table/graph/equation/domain arc and quadratic work to tile-table prediction through constant second differences. It adds mode-separated, deterministic multi-field transfer oracles while leaving runtime, scoring, and MVE integration to their owners.

Verification: Independent source mapping, mathematical review, pedagogical review, exact-head CI, Muse browser/assessment QA and engineering acceptance are pending. Do not activate or credit mastery.

Coordinate with the owners of PRs #327 and #328 before modifying any original package files.
