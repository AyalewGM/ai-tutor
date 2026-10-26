# Grade 8 distributive-expression depth r1

This is a **DRAFT_UNVERIFIED**, runtime-disabled sidecar for the existing
`MATH.EE.EXPR` canonical skill. It does not add a state-specific engine,
activate a mapping, register content, modify scoring, or write learner,
attempt, diagnostic, mastery, or variant-history data.

## Why this bounded package exists

The read-only full-seed audit from PR #447 (head
`195806169943268a5d2d7878a34834c39d92f7a7`, artifact digest
`sha256:33bede1875efe5f70649c97c6158ddc233795d70c584926d8a79a5a138a86978`)
measured only one stored family for each of `M8.ALG.DIST.POS`,
`M8.ALG.DIST.NEG`, and `M8.ALG.DIST`; learner visibility was not verified.
This package deepens that single mathematical prerequisite instead of creating
new jurisdiction identities.

## Twelve genuinely different task families

1. Positive distribution over a sum using area decomposition.
2. Positive distribution over a difference using a signed tape.
3. Negative-factor sign tracking over a sum.
4. A bare negative interpreted as multiplication by negative one.
5. Exact rational-factor distribution without decimal approximation.
6. Distribution followed by combining only like terms.
7. Reverse distribution using the greatest positive integer common factor.
8. All-input equivalence decisions from normalized affine structure.
9. Exact counterexamples to false equivalence claims.
10. First-invalid-step error analysis and repair.
11. Missing distributed-term completion.
12. Rectangle-perimeter modeling and normalization.

Coefficient changes within a family are variants, not additional families.
Every family records prerequisites, a difficulty rationale, exact response
fields and boundaries, two misconception routes, a concrete-to-visual-to-
symbolic representation sequence, and an unseen partner-family transfer.

## Determinism, modes, and evidence isolation

The 32 primary seeds are generated independently for diagnostic, guided,
independent, and mastery modes. Mode and seed are part of the deterministic
parameter slice, yielding 1,536 distinct primary mathematical fingerprints.
Transfer uses a separate fixed seed band and changes both family and structure.

Only guided variants expose the eight-stage learning sequence and
representation support. A targeted repair requires two corroborating probes:
the observed wrong response and its matching reasoning choice. A mismatch
receives a neutral retry; the worked answer is not revealed and guided success
does not earn mastery credit. Diagnostic, independent, mastery, and transfer
payloads are unhinted.

Answers are normalized as exact signed integers or fractions. Family-specific
contracts additionally enforce greatest-factor form, all-input equivalence,
required exact counterexamples, the first invalid step, and complete missing
terms. The accessibility contract requires keyboard operation, ordered screen-
reader math, non-colour cues, reduced-motion equivalence, exact-input support,
and predictable focus.

## Source and copyright boundary

`package.json` records publisher, URL, document title, version/date, page,
standard identifier, access date, and adaptation rationale. Maryland
`8.AT.B.3b`, DC/CCSS `8.EE.C.7b`, and Virginia `8.PFA.4(b)` are cited
only as prerequisite or boundary evidence. Every jurisdiction row has an empty
family mapping and explicitly claims no standard coverage or canonical
correspondence. The DC row records the July 28, 2010 State Board adoption. The
Virginia row remains source-authentication-pending because the controlling VDOE
binary and later first-party clause reproductions returned HTTP 403 to the
independent reviewer; no Virginia clause credit is inferred. The current MCPS
listing identifies Amplify Desmos Math as the Grades 6–8 and Algebra 1 core
curriculum, while the undated legacy Math 8 support page is explicitly not
treated as current alignment evidence. All tasks, contexts,
representation descriptions, distractors, and repairs are original; no public
worksheet or protected expression is copied.

## Required independent gates

The package remains runtime-disabled until separate Mathematical, Pedagogical,
Source/Mapping, Assessment Backend, Frontend/MVE, Muse QA, and Engineering
Release decisions accept the same exact head. The author makes no approval,
merge, deployment, or activation claim.
