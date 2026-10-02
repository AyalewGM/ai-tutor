# ADR-013: Stepwise work checking and in-problem intervention

## Status
Accepted. Implemented on `feature/f-026-math-notation-scratch-pad` (PR #128). The escalation thresholds are a provisional `pilot-v1`-style policy pending owner research, mirroring the ADR-010 pattern of versioned, replaceable hypotheses.

## Context
Pre-stepwise adaptivity operated only *between* problems: an attempt was graded as a whole, and the next problem was selected from that evidence. This cannot detect *where* in a solution a learner went wrong, and a learner who made a recognizable error mid-solution but recovered produced no misconception evidence at all. Competing products (IXL and beyond) adapt *inside* a problem. The gap decomposes into: (1) gradeable intermediate representations per problem family, (2) an intervention policy, (3) a UI that is honest about what can actually be verified.

## Decision
1. **A work line is a mathematical state, not a solution step.** For equations, a submitted line is legal iff it preserves the solution set of the previous line — normalized polynomial coefficients proportional in exact `Fraction` arithmetic. This deliberately permits multiple valid routes (distribute-first vs. divide-first) rather than enforcing one canonical path.
2. **Expression families use value equality plus a simplified-form check.** A line is a valid step iff its value equals the previous line's; it is the final answer only if also fully simplified (no expandable parens, ≤1 term per degree, lone fractions in lowest terms — `10/12` is a valid step but not the answer).
3. **Parsing is deterministic and narrow.** A small recursive-descent parser handles integer/fraction coefficients, implicit multiplication (`3x`, `2(x+4)`), division (`x/2`), and signed terms. Each line must use a single consistent variable (`x`, `y`, `n`, …). Unparseable or multi-variable input returns honest "I can't read that" feedback rather than a wrong guess.
4. **Step checking is only offered where it is honest.** `supports_steps` requires `answer_kind == "FREE_TEXT"`, a supported `problem_type`, and a prompt the parser can decompose. Multiple-choice variants of the same `problem_type` are excluded.
5. **Supported families (v1):** `SOLVE_EQUATION`, `SIMPLIFY_EXPRESSION`, `COMBINE_LIKE_TERMS`, `FRACTION_OPERATIONS`, `FRACTION_SUBTRACT`.
6. **Misconception classification fires on transitions, not states.** Recognizable wrong *transitions* map to existing codes: `3x+12=30 → 3x=42` → EQ_001 (wrong-direction move), `3(x+4)=30 → x+4=30` → EQ_002 (one-sided operation), `3(x+4) → 3x+4` → DIST_001 (partial distribution), `1/2+1/3 → 2/5` → NUM_003 (added across). Unrecognized wrong lines are invalid but unclassified.
7. **Intervention is immediate but graduated, and server-derived.** Invalid-line count is computed from persisted `WORK_STEP` tutor turns — the client cannot fabricate it. `pilot-v1` escalation: 1st invalid → generic retry; 2nd → targeted misconception feedback when classified; 3rd → reveal one legal next line computed from the learner's *current* state (`_canonical_next_line` works from any position). The policy boundary is one function so research can retune it without touching the checker or UI.
8. **Step evidence joins existing evidence flow, not a parallel system.** Work lines persist in `TutorTurn.metadata_json` (no new tables). Step errors raise the effective `assistance_level` used by `respond`, so a solved-by-steps answer is graded honestly as assisted (reduced XP, not independent mastery evidence). The latest classified step error is fed to `record_evidence` as a *fallback* misconception when the final answer carries none, at reduced confidence — closing the recovered-answer blind spot without letting step evidence dominate.
9. **UI separates rough work from checked work.** The scratch pad remains freeform and ungraded; `StepWork` renders accepted/rejected lines, misconception feedback, and reveals. Reaching solved form (`x = 6`, `5/6`) auto-submits through the normal `respond` path so XP, awards, and celebrations flow unchanged.
10. **MathText renders KaTeX to DOM nodes via `katex.render`** — no `dangerouslySetInnerHTML` anywhere; learner-typed lines cannot become an XSS sink.

## API
`POST /api/v1/adaptive-tutor/sessions/{session_id}/work-step` with `{problem_id, line}` returns `{status: valid|invalid|solved|unparseable, normalized_line, feedback, revealed_line?, misconception_code?}`. Problem payloads expose `problem_type` and `supports_steps`.

## Consequences
### Positive
- In-problem struggle becomes auditable evidence feeding the same remediation loop as answer-level evidence.
- Multiple solution routes accepted; checker semantics match how math is actually worked.
- No new tables; step trails are already queryable for future parent-facing "where they stumbled" reporting.
- The provisional policy is isolated and versionable.

### Tradeoffs / deferred
- Linear equations and single-variable expressions only; rational expressions, systems, and word problems are not honestly checkable yet.
- Escalation thresholds are hypotheses pending pedagogical research and pilot telemetry.
- Step trails are not yet surfaced on the parent dashboard.
- Expression "fully simplified" is a heuristic for the v1 families, not a general canonical-form proof.

## QA requirements
- Same previous line + same new line ⇒ identical verdict, and equivalent rewrites of a legal step (`3x+12=30` vs `30=3x+12`) are both valid.
- `x = const` / fully-simplified-expression is the only solved form.
- Invalid count is server-derived; a client-supplied count cannot change escalation.
- Step-mode problems keep MC and non-step families on the classic answer path.
- A solved line's auto-submit produces the same `respond` outcome as typing the answer directly.
