# Grade 7 inequalities: full-set reasoning, not one-answer drills

**Status: DRAFT_UNVERIFIED · runtime_activation: false · no mastery writes.**
Owner-directed *Grade 7* follow-on, separate from Issue #337's seven **Grade 9** Ontario algebra units. No school handout is reproduced.

## Reuse-first audit (2026-10-11)

Source \`main@cfda3f7301502c712c29f22ae5e4948cfa1ebc75\`:

| Existing source | What is actually present | What's not demonstrated | Boundary |
| --- | --- | --- | --- |
| \`scripts/seed_grade7.py\` | \`M7.EE.EQUATION\` Grade 7 curriculum-local grouping explicitly describes equations **and inequalities**; \`M7.EE.EQUATION.ONE/TWO\` specialize equations. | A learner-facing deep multi-term inequality/graph/counterexample journey with trusted unseen transfer. | Reuse existing identity as **provisional reference** only. Do **not** create or bind a new canonical atom. |
| \`app/canonical_problem_families.py\`, \`app/domains/algebra_functions.py\` | Canonical direct and multi-step **equation** families; generic equation/expressions solving. | A separately audited atomic inequality-assessment contract. | No family registry or generator changes. Algebra Content and Architecture own scope/atom choice. |
| Merged PRs #327 and #328, Waves 1–4 | Grade 7 percent/commission; ratio double number lines; IQR, signed addition, transformations, prisms/nets/histograms. | They do not establish this **inequality truth-set** journey. | No overlapping modifications or repeated draft batch. |
| Issue #337; \`ontario-seven-unit-algebra-r1\` | Two-sided negative/fractional **equations** and unseen equation transfer. | An inequality is not an equality and must not earn Grade 9 equation atom credit. | Distinct Grade 7 scope; no #337 files modified. |
| Open PR #330 | Probability tree MVE. | Unrelated. | No MVE code edited. |

## Intended learner experience

Start with two competing activity-pass costs built from fixed-fee and per-visit tiles. Predict where one plan will overtake the other. On a two-sided inequality ledger, remove matching variable bundles and fixed amounts, then justify the equivalence-preserving change. Compare positive and negative coefficient differences: multiplying/dividing by a negative **reverses** ordering, unlike adding/subtracting a common quantity. Move through number-line OPEN/CLOSED endpoints, accessible textual interval descriptions, and original-expression substitution proofs. Transfer to an unfamiliar pass-plan story in which the learner must **write the mathematical model**, not receive it.

\`package.json\` carries Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify, five fully computed original examples, seven evidence-triggered Socratic repair loops, keyboard/screen-reader/reduced-motion MVE requirements and independent-assessment isolation. Each repair asks new numbers or a contrasting reasoning check, not a canned "try again". No learner demonstration or actual UI wiring is claimed.

\`variants.py\` creates deterministic seed-diverse whole-number inequalities with positive or negative difference coefficient, four strict/non-strict relations, both algebra-first and context-first phrasing. Guided and independent modes use **different integer boundary ranges** and namespace IDs; assessment responses require an inequality boundary, relation, included endpoint, direction, satisfied and rejected original-example checks, contextual domain and written justification. \`public_payload()\` omits hidden parameters and answers. \`teacher_oracle()\` is only draft test data and MUST NOT be shipped to a browser. \`diagnose_guided()\` never calls any mastery or persistence code and never independently verifies the semantics of free-text reasoning.

**Important limitation:** The draft generator does not create a production/API scoring flow. Even a correct structured guided submission is \`GUIDED_STRUCTURED_FIELDS_MATCH_REASONING_UNREVIEWED\`, not a mastery grade. Draft independent variants are a *specification*; the Assessment Backend agent must separately design authenticated server-owned task state, correct canonical atom binding, exact scoring, independent reasoning rubric, idempotency, non-disclosure and no support-atom back-credit.

## Standards and provenance (no self-approval)

- **Ontario Grade 7 C2.4 is a source-linked candidate only**: Grade 7, 2020 elementary mathematics curriculum, corrected January 2021, Strand C2 "Equations and Inequalities". Ministry source: https://www.dcp.edu.gov.on.ca/en/curriculum/elementary-mathematics/grades/g7-math/strand-c/c2 . Original sample wording/examples were **not** copied. Standards Mapping must verify latest official text and approve the atom-to-expectation relation; this README does not assert accepted Ontario coverage.
- Existing local Grade 7 seed: \`scripts/seed_grade7.py\`, and local canonical registry: \`app/canonical_problem_families.py\`.
- Original scenarios/examples, arithmetic and pedagogy authored for Mihur without proprietary worksheets, video links, personal data or external question-bank replication.

## Review, integration, and evidence gates

| Axis | Status |
| --- | --- |
| Authored explanatory package, seeded test oracle and guided diagnosis | **Authored**, implementation confined to draft/test modules |
| Production content registry, learner route, MVE and assessment API | **NOT WIRED** |
| Independent Mathematical Review, Pedagogical Review, Standards Mapping, Engineering, Muse QA | **PENDING** |
| Exact-head CI/AppSec, browser keyboard/screen-reader/phone and learner-history isolation | **PENDING: do not represent author tests as independent sign-off** |
| Runtime, scoring, historical Attempt/DiagnosticAttempt/MasteryEvent and learner history | **UNCHANGED / runtime OFF** |
| Independently accepted, deployed or pilot-ready | **NO** |

Suggested local review command: \`pytest -q tests/test_grade7_inequality_reasoning_v1.py\`. Run Ruff, JSON parse, diff check and full repo CI at the exact PR head and link actual pass/fail outcomes in Issue #337 / #278; never invent execution results.

**Reviewer ownership:** Algebra Content validates/or authors reusable inequality family extensions **without editing this draft**; Independent Mathematical Review checks every relation/strictness/oracle and domain; Standards Mapping confirms Ontario C2.4 and atom; Pedagogical Review reviews learner reasoning and misconception routes; Frontend/MVE owns inequality balance/number-line interactions; Assessment Backend owns hidden scoring and authentication; Muse tests unseen paths, accessibility and privacy; Engineering Lead integrates only after independent gates.
