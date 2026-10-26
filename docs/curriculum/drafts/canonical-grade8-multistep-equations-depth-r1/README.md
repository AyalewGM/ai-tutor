# Grade 8 multistep equations — draft depth package

This bounded package implements the highest-ranked reusable equation gap in
`dmv_original_task_structure_crosswalk.v1.json`: multistep linear equations,
solution-class reasoning, error analysis, contexts, and unseen transfer.

It provides twelve mathematical families, not twelve coefficient templates:
positive and negative distribution, like terms, variables on both sides,
fractional coefficients, nested groups, identity, contradiction, perimeter
modeling, competing plans, first-error critique, and three-class comparison.

Every generated variant carries exact private evidence, multiple diagnostic
signals, guided-only Socratic repair, concrete→visual→symbolic representation
requirements, and keyboard/AT requirements. Independent transfer is always a
different family in the same proposed canonical skill. Diagnostic,
independent, and mastery variants expose no guided repair.

The source ledger is deliberately fail-closed. Maryland `8.AT.B.3a` and
`8.AT.B.3b` are recorded as separate `PARTIAL_NON_EXHAUSTIVE` /
`PROVISIONAL_NOT_ACCEPTED` relations. The three identity, contradiction, and
solution-class comparison families carry only bounded `8.AT.B.3a` recognition,
comparison, and justification evidence; learner construction of examples and
complete rewriting to the publisher-specified forms are excluded from coverage
credit. The other nine families carry the bounded `8.AT.B.3b` solving,
distribution, like-term, modeling, and error-analysis relation. DC `8.EE.C.7a` and `8.EE.C.7b` are likewise separate, disjoint
`PARTIAL_NON_EXHAUSTIVE` / `DC_PROVISIONAL_NOT_ACCEPTED` relations, sourced to
the controlling 2010 CCSS publication on printed page 54 and DC's July 28,
2010 State Board adoption. The same three/nine family boundary applies;
learner construction of examples and complete successive transformation to
`x = a`, `a = a`, or `a = b` are expressly excluded from `8.EE.C.7a` coverage
credit. Virginia `8.PFA.4(a–g)` is sourced to the Board-approved 2023 Grade 8
standards on printed page 64 and remains `VIRGINIA_PROVISIONAL_NOT_ACCEPTED`.
Clauses (b), (e), and (g) have bounded `PARTIAL_NON_EXHAUSTIVE` family evidence;
clauses (a), (c), (d), and (f) explicitly receive `NO_COVERAGE_CLAIM`. Declarative
representation metadata is not credited as concrete/pictorial learner work; solving
a provided context is not credited as writing an equation or creating a context;
and an exact x-value alone is not credited as contextual interpretation. The three
solution-class families are outside this Grade 8 Virginia clause, while
`NESTED_GROUPS` is withheld pending independent proof that its transformations stay
within Virginia's up-to-four-step boundary. The MCPS
support page is legacy/open-resource structure research, not proof of current
local sequence. No full-standard coverage, source task, diagram, wording, or
answer key is claimed or copied.

The package is not imported by `app`, registered, seeded, routed, scored, or
rendered. It changes no learner, Attempt, DiagnosticAttempt, MasteryEvent, or
variant-history record and cannot award mastery.

The first-invalid-step critique has a two-part answer contract:
the step identifier must match exactly (case-insensitive), while the `x=value`
component accepts mathematically equivalent exact rational forms, including
unreduced fractions. Missing or extra delimiters, wrong step codes, invalid
fractions, and non-equivalent values fail closed. Guided misconception-signature
comparison follows the same equivalence rule without revealing the oracle.

Context families use separate mathematical domain guards rather than the
unrestricted rational targets used by symbolic families. Rectangle variants
require strictly positive length, width, and perimeter. Competing-plan variants
require a nonnegative integer use count and nonnegative fixed charges. The same
guards apply when either family is selected for independent transfer.


## Enforced learner-flow and mode boundary

The guided draft now exposes only the evidence needed at the current stage and enforces:
Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify.

- Prediction selects the reviewed family-specific next move.
- Manipulation must submit the exact task-bound equivalent next step: affine coefficients for distribution, like-term, balance, fraction, modeling, and error-analysis families, or equation-specific invariants for the three-way solution-class comparison. Generic equality tokens alone fail closed.
- Explanation requires the family-specific justification plus exact coefficient, term-correspondence, model-structure, or solution-class evidence from the current task. Generic claims, incomplete evidence, and memorized labels fail closed.
- A genuine wrong practice response plus a corroborating reasoning choice is required before misconception-specific repair appears.
- Every misconception code has its own answer-free Socratic questions and explanation; diagnosis labels do not route to shared generic guidance.
- Repair is a separately observable DIAGNOSE state. A corrected answer submitted with the initial diagnosis cannot skip that state.
- Repair never reveals the worked answer and must end with an exact corrected response on a later action.
- Transfer is a generated different-family independent variant; both its server-generated ID and exact response must match.
- Final verification re-solves the original task and, for exact-rational families, reconstructs both substitution values.
- Diagnostic, independent, and mastery payloads expose no guided choices, representations, misconception routes, or repair.

This remains authoring evidence only: DRAFT_UNVERIFIED, unregistered, and runtime-disabled.
