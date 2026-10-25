# Canonical Grade 8 inverse-operations depth R1

This draft-only sidecar responds to Issue #446 and PR #447's measured finding
that the populated `M8.ALG.INVERSE.ADD` and `M8.ALG.INVERSE.MULT` skills each
have only two distinct stored tasks. It deepens those existing identities once;
it does not create a Maryland-, DC-, or Virginia-specific question engine.

The twelve families cover additive and multiplicative balance, missing-addend
and quotient meanings, equality symmetry, signed and rational cases, unknown
start/per-group contexts, and error analysis. Coefficient changes are seeded
variants inside a family, not new families. Each generated item carries its
prerequisite, difficulty rationale, exact oracle, equivalence/domain boundary,
misconception signatures, targeted representation move, and concrete → visual
→ symbolic contract.

Guided practice retains the learner's first parseable exact response, whether
correct or incorrect. Diagnose uses that authentic practice response with a
learner-visible labelled strategy choice and exact substitution values; it does
not ask the learner to invent a replacement wrong answer. A single wrong answer
never earns a misconception label. The public probe contract—not a
reviewer-only token—drives classification. Ambiguous, inconsistent, or
unparseable evidence fails closed to neutral questions. After agreeing
evidence, guided repair adds two Socratic questions, a representation move, and
an explanation of why the observed strategy breaks equality without revealing
the correct answer. The corrected repair-exit answer is then retained for final
verification.

The guided path is an enforced pure state machine: Observe → Predict →
Manipulate → Explain → Practice → Diagnose → Transfer → Verify. The actual
prediction is retained; an incorrect inverse choice stays in Predict with a
task-specific Socratic retry before manipulation is revealed. Manipulation
requires the exact inverse on both complete sides. Explain requires a correct
public equality-preservation choice plus a learner explanation naming both
sides. Diagnose is bound to the retained practice response plus public
strategy/substitution probes: arbitrary evidence cannot advance, and a uniquely
matched misconception remains in Diagnose until the learner completes its
answer-free targeted repair and exactly resolves the original equation. A
correct practice response receives no remediation and only requires readiness
confirmation before transfer. Transfer must identify a fresh
different-family `independent` item with no support, and verification
reconstructs both original equation sides from the practiced exact answer.
Diagnostic, independent, and mastery modes cannot obtain guided repair.
Diagnostic exposes only one exact unhinted answer field, retains an accepted
answer for final original-equation verification, and never requests guided
strategy or substitution probes. Independent and mastery paths contain only
unhinted Practice and Verify stages.

## Standards and local-source boundary

Maryland's current Grade 8 MCCRS Companion Guide (Version 1, February 2026;
standards adopted July 29, 2025), standard 8.AT.B.3b on page 24, supports
one-variable linear equations with rational coefficients. This package claims
only a PARTIAL_NON_EXHAUSTIVE correspondence for its one-step inverse-operation
subset. It excludes 8.AT.B.3a and the remaining 8.AT.B.3b work, including
equations requiring the distributive property and combining like terms, from
coverage credit. The correspondence remains PROVISIONAL_NOT_ACCEPTED. MCPS's
current middle-school mathematics page identifies
Amplify Desmos Math as its Grades 6-8 core curriculum but publishes no
unit-to-standard mapping there. The separate, undated Math 8 Unit 4
family-support page reproduces 2017-2019 IM/Open Up Resources material and is
used only as historical, openly licensed mathematical-structure research for
balanced equations—not as proof of current MCPS sequence or alignment. The
Math 7 Unit 5 page is likewise prerequisite-only evidence for opposites and
reciprocals, not proof of Grade 8 alignment.

No source task, wording, diagram, or protected expression is copied. The
prompts, contexts, parameterization, representations, distractors, and repairs
are original. Full publisher, URL, version/date, page, standard ID, access date,
and adaptation rationale are recorded in `package.json`.

## Gate boundary

`DRAFT_UNVERIFIED`, `runtime_activation=false`, and no seed or learner-history
writes. Independent Mathematical and Pedagogical reviewers must assess the
exact head. Source/mapping review remains separate. Assessment Backend owns
trusted selection, mode eligibility, scoring, persistence, nonrepetition, and
history isolation. Frontend/MVE and Muse own rendering, keyboard/AT behaviour,
learner visibility, and browser isolation. No DC or Virginia mapping is added
or activated here.



