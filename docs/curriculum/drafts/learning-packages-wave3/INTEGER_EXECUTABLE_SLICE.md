# Guided integer addition: executable vertical slice

This implementation strengthens the existing **W3-G7-SIGNED-NUMBERS** draft family and reuses existing canonical `MATH.INT.ADD` concept semantics; it **does not** create a canonical identifier.

Files:
- `frontend/src/mve/integerPractice.ts`: a pure bounded seed→problem builder (same seed produces the same task), independent exact arithmetic oracle, response validation, error-code classification and Socratic questioning prompts.
- `frontend/src/mve/GuidedIntegerNumberLine.tsx`: keyboard-operable signed number line with reset, directional movement, progressive learner questions, controlled input, screen-reader position announcements and feedback.
- `frontend/src/components/LearnPanel.tsx`: optional integration via `integerPracticeSeed`; renders the guided experience **only when explicitly requested** and when `independentAssessment=false`. It is not yet enabled by any topic routing or parent/student flow. It does **not** claim to be a deployed UI.
- `frontend/src/mve/integerPractice.test.mjs`: executable deterministic variant, independent oracle, misconception, input-validation and assessment-isolation tests (compatible with the repo's Node test runner).

**Validation to run:** `cd frontend && npm run build && npm run test:mve`. Check exact-head CI/AppSec separately. The feature must be wired by Engineering only after acceptance and scoped to the existing integer lesson. Do not use this guided client-side checker as an authoritative independent mastery scorer. A backend-sealed or server-verified assessment with novel variants and separately implemented oracle is still required. No learner data, telemetry, or mastery writes are implemented.

**Review checkpoints:** Math Reviewer verify negative movement and answer diagnosis; Muse test keyboard functionality and screen reader, zero handling and assessment bypass; Engineering enable explicit `integerPracticeSeed` only from accepted lesson configuration, ensure no hint leak into mastery assessment; Curriculum Mapping link correct exact skill and expectation IDs.

**Limitations:** This is a working, manually opt-in React component built on repo contracts, not complete interactive integration for all 21 draft packages. It must not be represented as Grades 1–9 completion.
