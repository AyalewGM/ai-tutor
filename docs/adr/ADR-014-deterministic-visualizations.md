# ADR-014: Deterministic, declarative math visualizations

- Status: accepted
- Date: 2026-10-02

## Context

Pilot learners work problems ranging from integer arithmetic to linear
equations. Industry practice (DreamBox, Khan) shows a diagram beside symbolic
work materially helps at this level. The naive option — asking an LLM to
describe or draw a diagram — violates the architecture boundary: the model
would decide what the math *looks like*, and could draw a wrong or misleading
picture with high confidence.

## Decision

1. **Visuals are declarative specs computed by the application.**
   `app/services/visualization.py` exposes `visualization_for(problem)` which
   returns a plain dict (`type` plus typed fields and a required
   `aria_label`) built from problem parameters or a bounded prompt parse.
   The LLM is never in the render path.

2. **`None` over a misleading picture.** Every visualizer checks honest
   bounds — non-negative pans and ≤6 x-blocks for the balance scale, common
   denominators ≤24 for fraction bars, supported templates only for tape
   diagrams — and returns `None` when the shape cannot be derived safely. The
   workspace simply renders nothing; absence is never an error.

3. **The diagram must not leak the answer.** Tape-diagram segments whose
   length encodes an unknown are drawn at fixed span (`$2 × ?`, `x` parts),
   so the visual cannot substitute for doing the math.

4. **One renderer per spec type, SVG only.** `ProblemVisual.tsx` maps spec
   types to inline SVG with `role="img"` + `aria-label`. No canvas, no
   `dangerouslySetInnerHTML`, no animation that would need reduced-motion
   handling yet.

5. **Server-rendered learner/parent pages are removed** (PR #129). The React
   app is the only learner surface, so visuals have exactly one render path.

## Consequences

- Adding a visual means teaching `visualization_for` a new spec type and
  adding one React renderer — no endpoint or schema changes; the spec rides
  the existing `WorkspaceProblemOut.visual` field.
- Coverage follows problem parameters, not problem count: curated rows
  without parameters still get visuals via prompt-parse fallbacks
  (`_linear_side`, `_FRACTION_OP`), but only when the parse is unambiguous.
- Screen-reader parity is mandatory: every spec carries `aria_label`, tested
  in `tests/test_visualization.py`.
