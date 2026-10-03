# ADR-016: Photo intake — OCR suggests, the learner confirms, the checker grades

## Status

Accepted (pilot scope).

## Context

Learners frequently work problems on paper first. Letting them photograph
written work and have each line checked closes the gap between paper practice
and the deterministic step checker (ADR-013) — the Photomath/Khanmigo-shaped
feature families expect.

Two hard constraints shaped the design:

1. **OCR of handwriting is imperfect.** If an OCR misread were graded
   directly, a learner could be told they hold a misconception they never
   expressed — the worst possible tutoring experience, and it would poison
   `Attempt.misconception_id` and parent-facing `recent_patterns` with
   phantom evidence.
2. **Data minimization.** Photographs of a child's work are a new data
   category. We do not want a corpus of learner images.

## Decision

**OCR is a suggestion layer, never a grader.**

- `POST /adaptive-tutor/sessions/{id}/work-photo/scan` accepts an image
  (JPEG/PNG/WebP, ≤ 8 MB), sends it to a pluggable OCR provider
  (`app/services/photo_ocr.py`), and returns the extracted work lines as
  *editable* text. No step is graded by this endpoint and nothing about the
  image or its contents is persisted.
- The client renders the lines in a review panel — each editable, each
  deletable, `needs_review` flagged when OCR confidence was low or the line
  uses constructs the checker cannot grade (exponents, radicals). The learner
  fixes misreads, then submits.
- Confirmed lines are submitted one at a time through the existing
  `/work-step` endpoint. The deterministic checker, escalation ladder,
  misconception classification, and persistence path are unchanged — a
  photographed line is indistinguishable from a typed one after confirmation.

**Normalization is conservative.** Mathpix `asciimath`/`text` output is
rewritten to the checker's syntax (`\frac{a}{b}` → `(a)/(b)`, `xx` → `*`,
`÷` → `/`). Lines that resist conversion surface raw with `needs_review`
rather than being guessed at; prose/caption lines are dropped.

**Provider is pluggable and off by default.** `photo_ocr_provider=auto` uses
Mathpix when `MATHPIX_APP_ID`/`MATHPIX_APP_KEY` are set, else the endpoint
returns 503 and the UI stays usable. A `stub` provider exercises the full
flow in dev/tests. `improve_mathpix: false` is sent so images are not
retained by the provider for training.

## Consequences

- First-line duplicates are expected (a photographed first line usually
  restates the problem) — `duplicate` renders neutral in the step list, not
  as a red error.
- Misconception evidence stays truthful: every graded line was confirmed by
  the learner and checked deterministically.
- OCR cost and latency sit behind one optional endpoint; disabling the
  provider removes the feature without touching grading.
- Not in scope: persisting worksheets, multi-problem page detection,
  stroke-level feedback, or server-side line editing history.
