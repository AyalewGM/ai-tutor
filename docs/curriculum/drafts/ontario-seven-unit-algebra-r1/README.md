# Issue #337 — seven-unit algebra R2

This draft is the first cohesive, jurisdiction-neutral content slice for the
owner-approved seven-unit classroom milestone. The private worksheets are not
stored, transcribed, or linked in learner content. All prompts, values, contexts,
diagnostics, and transfer tasks are original Mihur material.

## Existing work → actual gap → planned improvement → verification

| Existing work | Actual gap | R1 improvement | Verification |
| --- | --- | --- | --- |
| `MATH.EQ.TWO.DIRECT` and the runtime `SOLVE_EQUATION` generator | Mostly integer solutions; no cohesive evidence for negative coefficients, exact rationals, or substitution checks | Deterministic exact-rational two-step variants with guided/independent namespaces | Independent `Fraction` reconstruction and substitution tests |
| Multistep distribute/both-sides families and exact step checker | Existing family builders generate positive integral solutions and do not compare equivalent equations | Negative-distribution, rational both-sides and equation-equivalence structures | Exact linear oracle, scale-equivalence and invalid-input tests |
| Balance visual and guided distributive MVE | R1 described manipulation but did not point to an implemented negative/fractional both-side interaction | Reuse PR #340 exact-head equation-equivalence MVE contract while keeping routing explicitly unclaimed | Component head and remaining Frontend/Muse ownership are pinned |
| R1 static diagnostic descriptions | No executable response-evidence selection, fresh exits or fading rule | Structured evidence classifier, misconception-specific seeded exits and three-stage scaffold fading | Correct/no-route, misconception, invalid-evidence and fresh-exit tests |
| R1 prose transfer | No generated unfamiliar context or multi-field oracle | Seeded perimeter/rate transfer with model, quantities, units, exact verification and explanation fields | Deterministic replay, non-disclosure and independent reconstruction tests |
| Advanced-number, polynomial and geometry families | Seven-unit depth is partial or absent for roots, polynomial division, power laws/geometry, and scientific notation division | Machine-readable row-per-question-type audit ranks real extensions and proposed gaps | Fail-closed status assertions; no inferred coverage |

## Scope and gates

R2 deepens content evidence only for the first connected equation slice:

- exact rational two-step equations;
- negative distribution;
- variables on both sides;
- equivalent-equation comparison;
- exact substitution verification;
- five response-evidence misconception routes;
- seeded unseen contextual transfer and assessment-isolation contracts;
- response-evidence diagnosis, fresh repair exits, and explicit scaffold fading;
- a multi-field reasoning rubric aligned to the independent-assessment claim.

Polynomial/monomial division, exponent/geometry, scientific notation, and full
root-equation solution sets remain explicit later-stage gaps. No new canonical
identity is asserted. Official Ontario source/version/expectation IDs remain
`UNKNOWN_PENDING_STANDARDS_MAPPING`.

The entire directory is `DRAFT_UNVERIFIED`, runtime inactive, unwired, not
independently accepted, and incapable of learner/mastery writes.

`original_question_type_design_taxonomy.json` adds the owner-requested ranked
design taxonomy: 12 genuinely missing or weak structures, reuse evidence,
variation boundaries, cognitive transitions, Mihur scenarios, accessible model
requirements, independent-oracle contracts, transfer cases, acceptance checks,
owners, and source-rights restrictions. It stores no worksheet questions and
does not put external worksheet or video links in student lessons.
