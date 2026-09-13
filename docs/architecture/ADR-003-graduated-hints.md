# ADR-003: Graduated Hint Ladder

## Status
Accepted for F-003 implementation.

## Context
The tutor already has deterministic learning states and assistance-aware mastery, but hint depth is not yet a first-class persisted policy. An LLM must not decide how much of a solution to reveal.

## Decision
Hint depth is selected by a deterministic `HintPolicy`; the `TutorEngine` only renders language within the selected level.

### Persisted HintEvent
Each delivered hint records:
- tutor session;
- problem and active skill;
- optional triggering attempt;
- optional tutor turn;
- hint level 1-4;
- trigger (`REQUESTED` or `JUST_IN_TIME`);
- misconception code when applicable;
- generation metadata;
- timestamp.

### Policy
- New problem starts at hint level 0.
- Explicit help advances by at most one level from the highest delivered hint for that problem.
- Confident misconception detection may issue a just-in-time Level 2 hint; otherwise automatic support is Level 1.
- Hint levels never decrease within one problem.
- Level 4 is the maximum and represents bottom-out/model support.
- `DIAGNOSE` and `MASTERY_CHECK` states reject hint delivery.
- Diagnostic placement remains a separate API and never invokes the hint policy.

### Hint information contract
- Level 1: directional cue only; do not name or perform the complete step.
- Level 2: explain the governing concept/misconception and ask one focused question; do not complete the step.
- Level 3: provide a partial scaffold/template with a meaningful blank or unresolved operation.
- Level 4: model the blocked step, but do not complete the remainder of the full problem when additional work remains; require retry/transfer afterward.

The selected constraint is sent to the `TutorEngine` as structured context and is also enforced by deterministic fallback language.

### Mastery evidence
Existing attempt `assistance_level` remains the source of truth for mastery weighting. The frontend should submit the highest hint level used when the learner answers that problem. The hint endpoint returns the current level so the client can do this reliably.

Future server-side attempt/hint linkage may infer assistance automatically, but V1 preserves the existing API contract while auditing every hint event.

## Consequences
- Help behavior is testable without an LLM.
- Provider swaps cannot change pedagogy or hint depth.
- We can later optimize when to intervene using HintEvent outcomes while retaining explainable policy in V1.
