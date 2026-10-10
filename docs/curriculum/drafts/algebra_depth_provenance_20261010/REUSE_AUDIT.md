# Grade 9 algebra reuse-first audit

Status: DRAFT_UNVERIFIED. No runtime activation or learner evidence changes.

Existing work: PR #327 covers linear modeling, PR #328 covers quadratic patterns and exponential comparisons, and PR #317 covers algebraic equations. Existing generators are in app/domains/algebra_functions.py and app/domains/advanced_algebra_highschool.py. InteractiveLinearExplorer and InteractiveEquationBalance already exist.

Actual gaps: The drafts do not establish verified misconception-specific response branching, independent transfer scoring, or accessible student-journey integration. The quadratic and exponential manipulatives have not been verified. Generated question counts are not verified learning coverage.

Proposed improvement: Extend these existing packages instead of producing competing package IDs. Add source-versioned records, prediction-before-manipulation, diagnostic probes that react to actual errors, context-sensitive domains, unseen transfer, deterministic practice with independently calculated answers, and separate QA evidence.

Verification: Independent source mapping, mathematical review, pedagogical review, exact-head CI, Muse browser/assessment QA and engineering acceptance are pending. Do not activate or credit mastery.

Coordinate with the owners of PRs #327 and #328 before modifying any original package files.
