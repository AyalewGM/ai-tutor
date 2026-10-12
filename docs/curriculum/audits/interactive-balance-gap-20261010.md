# Equation-balance exploration

The existing BalanceScale renderer and equation generators provide static views,
but the inspected guided MVE components lacked equal-operation manipulation.
This implementation reuses the scale and the exact rational helper from the linear
explorer. It does not activate any draft curriculum package or taxonomy mapping.

## Scope and boundaries

Three whole-tile examples include variables on both sides. Learners add/remove one
unit on both sides, remove x from both sides, or divide both sides by 2 or 3 when
all tile counts divide exactly. Undo, reset, example switching and a visible history
support experimentation. Every allowed transformation preserves the exact solution.

The physical model is bounded to 0–3 x-boxes and 0–12 units per pan, positive net
x coefficient and nonnegative solution. Disabled operations may be algebraically
valid but outside this concrete model; the UI explicitly states this distinction.
No division by zero, fractional physical tiles, negative weights, or inferred mastery.
Separate practice includes a fractional solution checked by exact rational equality.
The activity unmounts outside guided/remediation; the component itself fails closed
unless independentAssessment is explicitly false. Semantic events contain only the
bounded pre-operation equation and action, with an allowlist rejecting extra fields.

## Verification

- Local full MVE suite: 30 tests PASS; production TypeScript/Vite build PASS.
- Exhaustive bounded equation/action checks: solution preservation, substitution,
  immutability and event-validator agreement; invalid states/actions rejected.
- Real component SSR and handlers: accessible SVG/controls/history, disabled states,
  assessment exclusion, undo/reset and answer feedback.
- Browser harness extended to exercise equal subtraction, keyboard division, undo,
  assessment removal and fresh remount. New-head browser CI pending publication.
- Previous head 636b188 passed CI 38054813765, including the guided integer/linear
  browser harness, and AppSec 38054813784. That evidence does not cover this addition.

Independent mathematical/pedagogical review and screen-reader evaluation remain
outstanding. Do not infer curriculum coverage or production approval from test results.
