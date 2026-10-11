# Interactive Polynomial Division Gap Audit

Issue #337 and PR #348 identified a reviewed draft package for polynomial by
monomial division, but the actual learner-facing grouped-term MVE was absent.
This implementation adds a guided/remediation-only frontend journey that mirrors
the accepted `poly-division-evidence-v1` dimensions without claiming backend
scoring, mastery credit, standards acceptance, or runtime activation.

Evidence added in this branch:

- `polynomialDivision.ts`: exact rational term arithmetic, quotient and
  reconstruction helpers, deterministic misconception diagnosis, fresh negative
  exponent transfer case, and route gating.
- `InteractivePolynomialDivision.tsx`: Observe -> Manipulate -> Explain ->
  Practice -> Transfer component with keyboard-accessible buttons/radios/checks,
  live diagnosis, multiplication reconstruction, domain restrictions, and
  fail-closed independent assessment isolation.
- `interactions.ts`: strict `POLYNOMIAL_DIVISION_MANIPULATED` semantic event with
  only bounded mathematical state.
- `polynomialDivision.test.mjs`: exact helper tests, evidence-diagnosis tests,
  event validation, SSR/accessibility assertions, assessment guard, and handler
  coverage.
- `Workspace.tsx` and `e2e/mve-guided-browser.mjs`: guarded guided/remediation
  mounting and browser harness coverage.

Limits: this is an accessible guided MVE and review route only. Backend-trusted
scoring, independent mastery, external Muse QA, standards mapping, and merge or
deployment approval remain separate gates.
