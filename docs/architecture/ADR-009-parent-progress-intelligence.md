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
7. Parent-facing next steps use deterministic `reason_code` + bounded `action_code` values. These actions are communication guidance only (for example recognize independent progress, encourage a fresh independent attempt, or follow an already-existing review plan). They are **not** intervention decisions and cannot change tutoring state.
8. Any LLM layer may only verbalize already-computed facts/reasons/actions; disabling or removing the LLM cannot change the projection or recommended bounded action.
9. All database queries that feed the projection must be scoped to the authenticated linked child and the child’s resolved curriculum. Cross-child and cross-curriculum evidence is invalid input.
10. F-009 does **not** infer a new prerequisite gap while F-010's shared sufficiency/intervention policy is unresolved. Existing misconception/support evidence may be displayed curriculum-locally, but a prerequisite relationship becomes a parent-facing confirmed gap only after F-010 provides the deterministic evidence rule. This prevents F-009 from creating a second intervention threshold.

## Consequences
- F-009 can progress without prematurely fixing F-010’s intervention thresholds.
- Sparse evidence remains safe and non-shaming.
- The dashboard can clearly distinguish assistance from independent success without changing mastery semantics.
- Parents can receive concrete but bounded next-step guidance without delegating pedagogy to either the dashboard or an LLM.
- F-010 can later replace the display-only sufficiency policy and enable confirmed prerequisite-gap projections through a tested contract.
- QA must test authorization, curriculum isolation, sparse evidence, assisted-vs-independent classification, deterministic action mapping, and invariance when any optional LLM summary is unavailable.

## UI direction
The parent dashboard should remain summary-first and calm. Visual design should use Goozam-derived blue/purple brand tokens while preserving WCAG-oriented contrast and never communicating learning state by color alone. Brand styling is presentation-only and cannot influence learning classification.
