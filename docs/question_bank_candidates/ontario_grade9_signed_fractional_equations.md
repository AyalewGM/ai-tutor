# Ontario Grade 9 signed and exact-fraction equation depth — author candidates v2

**Status: DRAFT_UNVERIFIED; NOT learner-visible; NOT approved for runtime registration or seeding.**

Refs: #488, #337, #446, #313. Compare draft #484 before considering integration. This draft addresses materially different **non-integer exact solutions and negative-sign reasoning**, without replacing an accepted generator. Existing canonical targets are `MATH.EE.EQUATION.TWO` and `MATH.EE.EQUATION.MULTISTEP`; these are authoring hints, not proof of an approved Ontario mapping.

Run `python -m scripts.author_ontario_linear_depth --count-per-family-mode 25 --output /tmp/ontario_signed_fractional_draft.json` for 400 original candidate instances across **four reasoning families**, three presentation structures and four separate modes. The 400 instances are not represented as 400 pedagogical families. Coefficients and values use exact `Fraction` arithmetic. Tests independently parse each displayed equation and use SymPy to recompute its unique real solution.

No teacher-handout wording, protected assessment item, school data or learner PII is copied.

| Proposed family | Core reasoning target | Presentation structures | Primary misconception target |
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

## Independent and mastery isolation

The bounded transfer selector keeps the same mathematical family but requires:

1. `INDEPENDENT` or `MASTERY` mode;
2. a different presentation structure;
3. a new mathematical task fingerprint;
4. a different exact answer;
5. no learner-visible hint, diagnosis or oracle.

Hinted success is explicitly ineligible as independent evidence. Even a successful unhinted transfer remains `runtime_credit_authorized=false` in this draft; the trusted Assessment Backend contract and independent review gates are separate.

## Remaining gates

Independent Math must recheck the changed displayed-equation structures, exact oracles, diagnostic response collisions and transfer search at the exact head. Independent Pedagogy must evaluate whether the multi-probe and target-preserving repair contract resolves its prior concern. Standards, trusted scoring/API, accessible Frontend/MVE, Muse QA, Security and Engineering remain separate.

No candidate is registered, seeded, routed or activated. Historical attempts, diagnostic results, variants and mastery events remain unchanged.
