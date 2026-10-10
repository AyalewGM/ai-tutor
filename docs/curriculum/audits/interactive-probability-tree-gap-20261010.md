# Interactive Probability Tree Gap Audit

Existing probability content includes deterministic generators, simple probability,
complements, compound outcomes, spinner visuals and marble-bag visuals. The missing
piece was a guided manipulable probability tree where students can change event
counts and observe exact products, complements and sample-space size immediately.

This implementation adds a bounded two-stage independent-event explorer for guided
practice and remediation only. It uses synthetic counts, emits only mathematical
state, and unmounts during independent assessment and mastery verification.

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
