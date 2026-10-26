# Ontario Grade 9 signed and exact-fraction equation depth — author candidates v5

**Status: DRAFT_UNVERIFIED; NOT learner-visible; NOT approved for runtime registration or seeding.**

Refs: #488, #337, #446, #313. Compare draft #484 before considering integration. This draft addresses materially different **non-integer exact solutions and negative-sign reasoning**, without replacing an accepted generator. Existing canonical targets are `MATH.EE.EQUATION.TWO` and `MATH.EE.EQUATION.MULTISTEP`; these are authoring hints, not proof of an approved Ontario mapping.

Run `python -m scripts.author_ontario_linear_depth --count-per-family-mode 25 --output /tmp/ontario_signed_fractional_draft.json` for 400 original candidate instances across **four reasoning families**, three presentation layouts and four separate modes. The 400 instances are not represented as 400 pedagogical families. Coefficients and values use exact `Fraction` arithmetic. Tests independently parse each displayed equation and use SymPy to recompute its unique real solution.

No teacher-handout wording, protected assessment item, school data or learner PII is copied.

| Proposed family | Core reasoning target | Presentation layouts | Primary misconception target |
|---|---|---|---|
| Signed two-step, non-integer solution | Preserve equality under inverse operations and signed division | variable term first; constant term first; sides reversed | additive constant omitted |
| Fractional coefficient, non-integer solution | Isolate the product and multiply by the reciprocal | variable term first; constant term first; sides reversed | coefficient multiplied instead of inverted |
| Negative-bracket distribution | Apply the negative factor to every grouped term | product first; constant first; sides reversed | bracket constant dropped |
| Variables on both sides | Collect variable terms with equal operations before division | variable term first; constant term first; sides reversed | right-side variable ignored |

## Bounded diagnosis and repair contract

This authoring package no longer treats one wrong answer as a diagnosis.

- Every generated task contains at least two distinct, non-colliding misconception response signatures.
- A response signature must be followed by a neutral reasoning probe. The contract requires two corroborating signals before a misconception label may be selected.
- Ambiguous evidence must trigger another neutral probe and withhold the label.
- Each confirmed route defines two targeted Socratic questions; it does not reveal a worked answer.
- The routing and repair metadata is author/reviewer evidence only. It is excluded from the learner projection and is not a runtime classifier or scorer.

Backend and MVE remain responsible for authenticated response observations, route implementation, accessible controls and rendering. Muse remains responsible for browser and assistive-technology evidence.

## Authored response-routing journey (v5)

The draft now includes a machine-checkable, author-review-only journey simulator.
It is not a production route or trusted scorer. It demonstrates the intended
content contract with original structured reasoning choices and regression
transcripts:

1. consume the learner's actual exact `PRACTICE` response;
2. match a possible misconception response without assigning a label;
3. present a neutral follow-up question with three learner-operable reasoning
   choices;
4. confirm a route only when the selected reasoning choice corroborates the
   original wrong answer;
5. withhold the label and return a neutral retry for an unparseable, unmatched
   or inconsistent answer/reasoning pair;
6. select a fresh same-family guided task that still contains the confirmed
   misconception probe, but has a new fingerprint and exact answer;
7. require an exact successful guided re-test, then an explicit readiness
   confirmation;
8. hand off to a different-family, hint-free independent exit under the same
   canonical skill.

The stage-specific learner projection never includes diagnostic labels,
confirmation evidence keys, exact oracles or private transcripts. Guided
success remains ineligible for independent credit. Backend still owns trusted
response normalization and persistence; Frontend/MVE owns the learner controls;
Muse owns real interaction and accessibility evidence.

## Independent and mastery isolation

The bounded transfer selector keeps the same canonical skill but changes the
reasoning family:

1. `INDEPENDENT` or `MASTERY` mode;
2. a different semantic/reasoning family under that same canonical skill;
3. a new mathematical task fingerprint;
4. a different exact answer;
5. no learner-visible hint, diagnosis or oracle.

Hinted success is explicitly ineligible as independent evidence. Even a successful unhinted transfer remains `runtime_credit_authorized=false` in this draft; the trusted Assessment Backend contract and independent review gates are separate.

## Remaining gates

Independent Math must confirm that the new journey layer preserves the accepted
displayed-equation layouts, exact oracles, diagnostic response collisions and
transfer search at the changed head. Independent Pedagogy must execute the new
multi-probe, ambiguity, target-preserving re-test and independent-exit paths.
Standards, trusted scoring/API, accessible Frontend/MVE, Muse QA, Security and
Engineering remain separate.

No candidate is registered, seeded, routed or activated. Historical attempts, diagnostic results, variants and mastery events remain unchanged.

Presentation layout may also change, but it is recorded separately and is not
used as evidence of structural transfer. Current same-skill transfer pairs are
signed two-step ↔ fractional-coefficient and negative distribution ↔ variables
on both sides.

## Cross-mode mathematical task identity (v4)

Previously the contract called the three layouts `structure_id`, so a
constant-first or sides-reversed rendering could be misreported as structural
transfer. Draft v4 records them accurately as `presentation_id` and adds a
separate `reasoning_structure_id`. The fingerprint remains the unordered pair
of exact affine sides **within the same reasoning family**. Reordering or
swapping the two sides does not create a fresh mathematical-task identity.
Root-only matching is deliberately avoided: many distinct reasoning tasks
share the same solution. The fingerprint version remains
`AFFINE_SIDE_SYMMETRY_V1`, and the draft pack schema is
`MIHUR_DRAFT_RATIONAL_EQUATION_CANDIDATES_V5`. Earlier v2/v3/v4 generated exports
are superseded for novelty and transfer accounting; none is authorized for
learner use.
