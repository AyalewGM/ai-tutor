# ADR-017: CPA presentation layer + reverse-Socratic challenges

Status: accepted
Date: 2026-10-08

## Context

The step ladder (ADR-013) decides *what to say* about a wrong line; the
escalation audit (ADR-015) kept its thresholds. What it could not express is
*how to present* the problem space when symbolic work is not landing — and it
had no mechanism to probe whether a fluent learner actually understands the
moves they are making versus pattern-matching them.

## Decisions

1. **Session-level CPA state.** `TutorSession.cpa_level` ∈
   {ABSTRACT, PICTORIAL, CONCRETE}, defaulting to ABSTRACT. Two consecutive
   invalid WORK_STEP turns move down one rung (never two); two consecutive
   valid turns — or a solved line — move back up one. The engine
   (`app/services/pedagogy_engine.py`) is a pure function over persisted turn
   metadata; transitions are audited as `CPA_TRANSITION` TutorTurns.

2. **Step-context visuals, not problem-level.** At PICTORIAL/CONCRETE the
   `/work-step` response carries `step_visual`: a declarative spec anchored
   at the learner's *latest accepted line* (a balance scale of `3x = 18`,
   not of the original problem) so the picture tracks their position.
   Rendering reuses the ADR-014 spec types via `CPAVisualizer`.

3. **Misconception taxonomy as a service.** `app/services/misconceptions.py`
   maps every checker-emitted code to {name, Socratic hint, preferred visual
   cue}. Socratic hints must surface the error as a question — never name the
   correct move.

4. **Reverse-Socratic challenges are crafted, not generated.** After 3
   consecutive valid steps, `craft_flawed_step` corrupts the last accepted
   line with a *real* catalogued misconception (EQ_001 sign-flip family,
   EQ_003 multiply-instead-of-divide) and persists a `REVERSE_CHALLENGE`
   turn. Resolution is closed on the challenge turn's
   `resolved_outcome` — `spotted` / `missed` (learner copied the flaw) /
   `unresolved` — never by timestamp comparison.

## Consequences

- A learner who copies the planted line verbatim gets the *authentic*
  misconception code (verified in tests) — metacognitive failure and
  procedural failure share one classifier, one evidence trail.
- Challenge feedback is metacognitive by construction: "spotted" confirms the
  learner caught a seeded error; "missed" reframes the wrong line as "that
  repeats the slip in my attempt," which is more face-saving than a plain
  rejection.
- CPA state flows to the explainer via `TutorContext.cpa_level` →
  llm-gateway payload, so constrained language can describe the picture
  without the gateway deciding anything.
- All decisions remain deterministic; the LLM is never in the loop.
- Not done: CONCRETE manipulatives beyond the declarative specs (needs
  interactive widgets — a real feature), challenge variety beyond the two
  equation transforms, cross-problem CPA carry-over tuning.

## Compliance

`cpa_level`, misconception codes, and challenge turns store math-work state
only — no PII beyond the learner's own work lines, unchanged from ADR-013.
