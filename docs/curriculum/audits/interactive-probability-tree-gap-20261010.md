# Interactive Probability Tree Gap Audit

Existing probability content includes deterministic generators, simple probability,
complements, compound outcomes, spinner visuals and marble-bag visuals. The missing
piece was a guided manipulable probability tree where students can change event
counts and observe exact products, complements and sample-space size immediately.

This implementation adds a bounded two-stage independent-event explorer for guided
practice and remediation only. The learner-facing flow explicitly states that the
second-stage probabilities stay the same on every first-stage branch, and contrasts
that with dependent situations that require conditional branch probabilities. It
uses synthetic counts, emits only mathematical state, and unmounts during
independent assessment and mastery verification.

Evidence added in this branch:

- `probabilityTree.ts`: exact rational helper, bounded validation, immutable state
  updates and local practice checks.
- `InteractiveProbabilityTree.tsx`: Observe -> Manipulate -> Explain -> Practice
  React activity with labeled keyboard sliders, live status and assessment guard.
- `ProblemVisual.tsx`: deterministic SVG probability-tree renderer.
- `interactions.ts`: strict `PROBABILITY_TREE_CHANGED` semantic event validation.
- `probabilityTree.test.mjs`: exact math, boundary, event, SSR/accessibility and
  handler tests.
- `e2e/mve-guided-browser.mjs`: browser harness coverage for the fifth guided
  MVE activity.

Limits: the current model covers two independent stages with whole-number counts
from 2 to 12 and at least one favorable and non-favorable outcome per stage. It
does not claim replacement sampling, conditional probability, or curriculum
approval.


## Learning Package Production handoff — repair and transfer contracts

The following is **DRAFT_UNVERIFIED guided content** for MVE implementation.
It preserves the mathematically approved two-stage **independent-event** scope
and does not broaden the helper into conditional-probability computation.

### Prediction-to-observation evidence

Before revealing the recomputed path table, capture a directional prediction
for a named change, for example:

> Event A changes from 2 favorable outcomes out of 5 to 3 out of 5 while Event B
> stays 1 out of 4. Will `P(A and B)` increase, decrease, or stay the same?

Deterministic expected prediction: `INCREASE`.

After manipulation, require the learner to compare the old and new exact path
probabilities:

- before: `(2/5)(1/4)=1/10`;
- after: `(3/5)(1/4)=3/20`;
- observed relation: `3/20 > 1/10`.

The guided flow should record whether the prediction matched the observed
relation. This remains zero-mastery practice evidence.

### Misconception-specific repair exits

**ADD_BRANCH_PROBABILITIES**

Trigger evidence: learner treats an intersection such as `1/2 and 1/3` as
`1/2+1/3`.

- Socratic prompt: "A single path must pass through both stages. What fraction
  of the first-stage favorable branch continues through the favorable branch
  of stage two?"
- Different repair item: fair coin followed by a fair 4-section spinner with
  exactly one target section.
- Verified exit: `P(head and target)=1/2×1/4=1/8`, with learner selecting
  multiplication because both conditions must occur on one path.

**AT_LEAST_ONE_AS_BOTH**

Trigger evidence: learner answers the both-success path for an "at least one"
question.

- Socratic prompt: "Does 'at least one' include outcomes where only the first
  event succeeds or only the second succeeds?"
- Different repair item: independent events with `P(A)=1/2`, `P(B)=1/4`.
- Verified exit: learner uses the complement of neither:
  `1-(1/2)(3/4)=5/8`, and identifies that this includes A-only, B-only, and
  both-success paths.

**BRANCH_COMPLEMENT_CONFUSION**

Trigger evidence: learner uses `P(B)` where `1-P(B)` is required for a
not-B branch.

- Socratic prompt: "Do the B and not-B branches together account for the whole
  second stage?"
- Different repair item: `P(A)=2/3`, `P(B)=1/5`; ask for
  `P(A and not B)`.
- Verified exit: complement `4/5`, path probability `(2/3)(4/5)=8/15`.

Each repair must be response-verified before returning to the normal guided
sequence. Merely showing the worked correction is not an exit.

### Independent-versus-dependent contextual transfer

Present two new situations **without** a computed tree and require
classification plus justification.

**Transfer A — independent**

> A fair coin is tossed, then a fair six-sided die is rolled. Does the coin
> result change the die probabilities?

Expected evidence:
- classification: `INDEPENDENT`;
- reason: second-stage probabilities remain the same after either first-stage
  branch;
- product rule is permitted for a joint path.

**Transfer B — dependent**

> A bag contains 3 red and 2 blue counters. One counter is drawn and kept out,
> then a second counter is drawn. Can the same second-stage probabilities be
> reused after every first draw?

Expected evidence:
- classification: `DEPENDENT`;
- reason: removing the first counter changes both the total and possibly the
  favorable count for the second draw;
- learner must state that the current fixed-marginal probability-tree helper is
  **not** the right model for computing this case.

This transfer checks recognition of the approved model boundary; it does not
ask the learner to calculate conditional probabilities.

### Scaffold-fading content boundary

Once explanation evidence is verified, subsequent guided repair/transfer items
should not expose the computed path-probability table or rule statement before
the response. A diagnosed error may restore only the needed support. MVE owns
the actual visual hide/restore mechanics.

No task above is mastery evidence. Trusted Assessment Backend authorization and
Muse browser/accessibility verification remain separate gates.
