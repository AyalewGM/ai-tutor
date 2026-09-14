# ADR-009: Parent Progress Intelligence Read Model

## Status
Accepted for F-009 implementation.

## Context
F-009 extends the parent dashboard from raw progress fields into trustworthy learning intelligence. Parent-facing conclusions must be derived from persisted application evidence, remain curriculum-local and child-authorized, and must not let an LLM invent proficiency, weakness, remediation, or mastery conclusions.

F-010 will own the shared evidence-sufficiency/intervention threshold policy. F-009 therefore needs an explicit seam rather than a competing hard-coded threshold.

## Decision
1. Parent intelligence is a **read-model projection** over persisted tutoring evidence. It never mutates tutoring state, mastery, prerequisite routing, hint policy, or intervention decisions.
2. `INSUFFICIENT_EVIDENCE` is first-class. No observations are never presented as weakness.
3. Assisted success, independent progress, and independently mastered status remain separate.
4. F-009 may use a conservative observation-only display policy while F-010 is unfinished. That policy may distinguish “no evidence” from “evidence observed” but may not infer weakness or trigger remediation.
5. Evidence sufficiency is injected through an `EvidenceSufficiencyPolicy` contract. When F-010 finalizes the shared policy, F-009 consumes it through this seam rather than duplicating thresholds.
6. Existing application-owned states remain authoritative. In particular, parent intelligence may report `NEEDS_PRACTICE` from an existing `REVIEW_DUE` state, but it does not create that state.
7. Parent-facing recommendations use deterministic reason codes. Any LLM layer may only verbalize those already-computed facts/reasons; disabling the LLM cannot change the result.
8. All database queries that feed the projection must be scoped to the authenticated linked child and the child’s resolved curriculum. Cross-child and cross-curriculum evidence is invalid input.

## Consequences
- F-009 can progress without prematurely fixing F-010’s intervention thresholds.
- Sparse evidence remains safe and non-shaming.
- The dashboard can clearly distinguish assistance from independent success without changing mastery semantics.
- F-010 can later replace the display-only sufficiency policy through a tested contract.
- QA must test authorization, curriculum isolation, sparse evidence, assisted-vs-independent classification, and invariance when any optional LLM summary is unavailable.

## UI direction
The parent dashboard should remain summary-first and calm. Visual design should use Goozam-derived blue/purple brand tokens while preserving WCAG-oriented contrast and never communicating learning state by color alone. Brand styling is presentation-only and cannot influence learning classification.
