# Grade 9 Gap Closure Wave 1

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes · no self-approval**

This is the owner's consolidated Grade 9 gap-closure batch. It deliberately avoids another wave of tiny PRs and does not duplicate concepts already present in Mihur's established linear-equation, systems-equation, polynomial, quadratic, exponential, exponent/scientific-notation, or polynomial-division work.

## Scope

Twenty deep reusable concept packages are authored:

1. Absolute-value equations
2. Linear inequalities in two variables
3. Systems of linear inequalities
4. Optimization over feasible regions
5. Linear–exponential intersections
6. Domain, range, and function notation
7. Inverse linear functions
8. Piecewise and absolute-value functions
9. Average rate of change
10. Arithmetic and geometric sequences
11. Function transformations
12. Parallel/perpendicular slope geometry
13. Triangle congruence reasoning
14. Random sampling and population inference
15. Statistical investigation design and claim evaluation
16. Bivariate quantitative modeling
17. Correlation coefficient and causation
18. Units, quantities, scale, and measurement precision
19. Formula rearrangement
20. Two-variable equations as solution sets

These correspond to genuine gaps or insufficient evidence identified in the current Maryland Algebra I / Integrated Algebra I inventories, plus traditional Algebra I concepts that remain underdeveloped.

## Mihur learning contract

Every package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

Each package contains:

- a Concrete/Context → Visual → Symbolic progression;
- at least three explicit core reasoning goals;
- misconception-specific Socratic repair routes;
- fresh-number repair exits rather than generic "try again";
- guided practice with fading support;
- a separate unseen namespace for independent transfer;
- hidden teacher oracle / answer-free public projection;
- accessibility/MVE requirements for keyboard, screen reader, reduced motion, graph/visual text equivalence, focus preservation, and no color-only meaning.

`variants.py` provides deterministic draft variants for every one of the twenty concepts. These are review/test contracts only, not runtime question generators.

`tests/test_grade9_gap_closure_wave1.py` verifies deterministic replay, public-answer isolation, guided/independent namespace separation, and concept-specific mathematical invariants such as:

- complete two-branch absolute-value solution sets;
- solid/dashed inequality boundaries and half-planes;
- feasible-region intersection semantics;
- optimization candidate membership;
- linear–exponential intersection verification;
- domain/range/function-value consistency;
- inverse composition requirements;
- absolute-value graph vertices;
- average-rate-of-change ratio;
- arithmetic/geometric sequence distinctions;
- function-transform vertices;
- exact negative reciprocal slopes;
- rejection of AAA and generic SSA as congruence proofs;
- no causal inference from observational association;
- formula-domain restrictions;
- graphs as sets of ordered-pair solutions.

## Jurisdiction separation

### Maryland

The current Maryland Grade 9 / Integrated Algebra I source candidates include IA1.AT.B.2–B.9, IA1.AT.C.10–C.12, IA1.AT.D.13–D.17, IA1.GR.A.1–A.2, IA1.GR.B.3–B.5, IA1.DS.A.1–A.4 and IA1.DS.B.5–B.8, plus traditional Algebra I N.Q/A.CED/A.REI/F.IF/F.BF/F.LE/S.ID targets where applicable.

This PR **does not accept those mappings**. Standards Mapping must review each concept independently.

### Ontario

Ontario MTH1W concepts not reducible to the above reusable mathematics remain explicitly separate extensions:

- coding/computational algebra and modelling (C2.1–C2.3);
- large-data investigation and modelling-process limitations (D1.1, D2.1–D2.5);
- geometry/design/measurement relationships (E1.1–E1.6);
- financial literacy (F1.1–F1.4);
- cultural/historical investigations in number, algebra, and geometry (B1.1, C1.1, E1.1).

Those are recorded in `package.json` as separate Ontario extensions so they are not falsely merged with Maryland Algebra I concepts. A later Ontario-specific batch can implement them without duplicating the shared mathematics here.

## Existing content that must NOT be duplicated

Current main already contains or has accepted/merged work for:

- one-, two-, and multi-step linear equations;
- systems of linear equations;
- polynomial addition/subtraction/multiplication and GCF factoring;
- quadratic evaluation/roots/vertex reasoning;
- exponential functions;
- linear vs exponential comparison;
- slope and linear modeling;
- exponent laws and scientific notation;
- monomial and polynomial-by-monomial division.

This wave supplements those areas; it does not replace them.

## Ownership and review handoff

- **Algebra Content:** verify reuse boundaries and any canonical-family extension, but do not silently broaden an existing atom.
- **Independent Mathematical Review:** verify all exact oracles, branches, geometry claims, statistics logic, and counterexamples.
- **Independent Pedagogical Review:** verify Mihur flow, misconception specificity, scaffold fading, and genuine transfer.
- **Standards Mapping:** accept/reject Maryland and Ontario mappings separately.
- **Architecture:** approve atomic identity boundaries before any new canonical registration.
- **Frontend/MVE:** implement accessible interactions after package acceptance.
- **Assessment Backend:** implement trusted unseen scoring, authenticated task state, idempotency, and no support-atom back-credit.
- **Muse QA:** adversarial browser, accessibility, privacy, answer-leakage, and learner-history isolation.

No agent that authors this batch may self-approve any of those gates.

## Current state

Authored: **YES**

Draft deterministic variants/tests: **YES**

Production wired: **NO**

MVE wired: **NO**

Assessment backend wired: **NO**

Standards accepted: **NO**

Math accepted: **NO**

Pedagogy accepted: **NO**

Muse QA accepted: **NO**

Runtime activated: **NO**

Deployed/pilot-ready: **NO**

Suggested focused command:

`pytest -q tests/test_grade9_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and downstream independent review before merge or activation.
