# ADR-010: Deterministic Intervention Policy

## Status
Accepted. Owner approved deterministic pilot routing and one-prerequisite-at-a-time remediation on 2026-09-14.

## Context
F-010 turns persisted learning evidence into explainable intervention decisions without allowing an LLM or an opaque statistical model to own pedagogy. F-009 already introduced an evidence-sufficiency seam for parent reporting; F-010 owns the shared deterministic intervention policy semantics.

Research found no credible universal wrong-answer count that proves a prerequisite gap. The pilot therefore uses a conservative, versioned product-policy hypothesis that can be recalibrated from F-011 telemetry without rewriting historical evidence.

## Decision
1. Intervention decisions and production pilot routing are deterministic application logic. LLMs may verbalize a completed structured decision only.
2. The policy separates two gates:
   - **target struggle:** enough fresh independent failures on distinct target problems to justify checking a declared prerequisite;
   - **prerequisite confirmation:** enough fresh independent failures on distinct problems for a declared prerequisite to justify remediation.
3. The initial replaceable `pilot-v1` hypothesis is 2 target independent failures + 2 prerequisite independent failures. These counts are policy configuration, not learner-facing pedagogical truth.
4. The persisted-routing adapter uses an explicit 30-day pilot evidence window. This duration is an application policy hypothesis for the private pilot and must be calibrated from F-011 telemetry rather than treated as universal pedagogy.
5. Repeated retries on one problem count once toward evidence breadth. Assisted/hinted attempts cannot independently satisfy either threshold.
6. A more-recent independent mastery timestamp supersedes older prerequisite failures.
7. Remediation descends exactly one verified curriculum-local prerequisite edge at a time.
8. Return to the target requires fresh independent evidence collected after the intervention starts; `pilot-v1` requires successful work on two distinct prerequisite problems before returning upward.
9. A remediation target must be a declared prerequisite edge inside the learner's selected curriculum. Cross-curriculum evidence is excluded; a mismatched prerequisite edge fails closed.
10. Every decision and intervention is auditable through policy version, reason code, evidence IDs, selected prerequisite skill, return condition, start state and outcome state.
11. Probabilistic/BKT/ML approaches may be evaluated later only in offline/shadow/advisory mode until separately accepted for any production authority.

## Decision states
- `NO_INTERVENTION`: target struggle threshold is not met.
- `INSUFFICIENT_EVIDENCE`: target struggle exists but no declared prerequisite edge or insufficient fresh prerequisite evidence exists.
- `PREREQUISITE_GAP_CONFIRMED`: both deterministic gates pass on the same curriculum-local evidence scope.

## Routing behavior
When the existing tutor state machine requests remediation, the focus controller evaluates persisted evidence through the versioned F-010 policy. `NO_INTERVENTION` and `INSUFFICIENT_EVIDENCE` do not move the learner to a prerequisite skill. Only `PREREQUISITE_GAP_CONFIRMED` may start a remediation intervention and change `active_skill_id` to the single selected prerequisite.

The intervention record is marked `STARTED` when routing begins. The learner remains on that prerequisite until fresh, independent post-start evidence satisfies the versioned return rule, after which the record is marked `COMPLETED`, the outcome is recorded, and the learner returns to the original target. Analytics records never mutate mastery scores and are not themselves authoritative learning evidence.

## Consequences
### Positive
- Replayable and testable routing decisions.
- Clear curriculum-jurisdiction isolation.
- Sparse evidence remains uncertainty instead of a weakness label.
- Parent reporting and future telemetry can reference the same auditable intervention record.
- Policy can be calibrated later without giving an LLM control.

### Tradeoffs
- The pilot thresholds, 30-day evidence window and two-distinct-problem return rule are hypotheses and may be conservative.
- Historical prerequisite evidence must be recent enough to enter the configured evidence window.
- A deterministic policy may miss subtler patterns that a future shadow knowledge-tracing model could identify; that is intentionally deferred until adequate pilot data exists.

## QA requirements
- same evidence + same policy version => identical decision;
- one target failure cannot trigger remediation;
- target struggle without prerequisite evidence cannot start remediation;
- assisted attempts cannot satisfy independent thresholds;
- duplicate attempts on one problem do not create false breadth;
- recent mastery supersedes older prerequisite failures;
- cross-curriculum evidence/edges cannot confirm a gap;
- only one prerequisite edge is entered per intervention;
- assisted remediation success cannot satisfy the return condition;
- return requires fresh independent post-intervention evidence on distinct problems;
- intervention start and outcome are persisted for F-011 analysis;
- removing or failing an LLM cannot change the structured classification or routing decision.
