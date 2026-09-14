# ADR-010: Deterministic Intervention Policy

## Status
Accepted for the F-010 engineering slice; owner-gated choices remain explicit at final PO acceptance.

## Context
F-010 must turn persisted learning evidence into explainable intervention recommendations without allowing an LLM or an opaque statistical model to take ownership of pedagogy. F-009 already introduced an evidence-sufficiency seam for parent reporting; F-010 now owns the shared deterministic intervention policy semantics.

Research found no credible universal wrong-answer count that proves a prerequisite gap. The pilot therefore uses a conservative, versioned product-policy hypothesis that can be recalibrated from F-011 telemetry without rewriting historical evidence.

## Decision
1. Intervention decisions are deterministic application logic. LLMs may verbalize a completed structured decision only.
2. The policy separates two gates:
   - **target struggle:** enough fresh independent failures on distinct target problems to justify checking a declared prerequisite;
   - **prerequisite confirmation:** enough fresh independent failures on distinct problems for a declared prerequisite to justify remediation.
3. The initial replaceable `pilot-v1` hypothesis is 2 target independent failures + 2 prerequisite independent failures. These counts are policy configuration, not learner-facing pedagogical truth.
4. Evidence-window boundaries are supplied explicitly by the caller. This ADR intentionally does not invent a universal number of days for "fresh" evidence.
5. Repeated retries on one problem count once toward evidence breadth. Assisted/hinted attempts cannot independently satisfy either threshold.
6. A more-recent independent mastery timestamp supersedes older prerequisite failures. After remediation, a fresh independent success condition is required before returning upward.
7. A remediation target must be a declared prerequisite edge inside the learner's selected curriculum. Cross-curriculum evidence is excluded; a mismatched prerequisite edge fails closed.
8. The decision output is auditable: policy version, reason code, evidence IDs, selected prerequisite skill, and return condition are explicit.
9. The policy service is pure and does not mutate mastery, tutor state, curriculum topology, or parent reporting state.

## Decision states
- `NO_INTERVENTION`: target struggle threshold is not met.
- `INSUFFICIENT_EVIDENCE`: target struggle exists but no declared prerequisite edge or insufficient fresh prerequisite evidence exists.
- `PREREQUISITE_GAP_CONFIRMED`: both deterministic gates pass on the same curriculum-local evidence scope.

## Integration plan
The first slice implements the pure policy and replay tests. A subsequent F-010 slice will add a DB adapter that projects persisted `Attempt`/`Problem`/`SkillPrerequisite` records into the policy input, then persist intervention start/outcome records for F-011 measurement. The adapter must resolve the learner's curriculum scope before loading either evidence or prerequisite edges.

F-009 may consume a shared F-010 evidence-sufficiency adapter later, but F-010 must not redefine existing F-003/F-004 mastery or strong-help semantics.

## Owner gates retained
The following are not silently decided by this ADR:
- granting a probabilistic/BKT model production routing authority;
- aggressive remediation across multiple prerequisite levels.

The current implementation remains deterministic and one-edge-compatible so neither owner choice is pre-empted.

## Consequences
### Positive
- Replayable and testable decisions.
- Clear curriculum-jurisdiction isolation.
- Sparse evidence remains uncertainty instead of a weakness label.
- Policy can be calibrated later without giving an LLM control.

### Tradeoffs
- The pilot thresholds are hypotheses and may be conservative.
- Explicit evidence windows and mastery supersession require careful DB projection.
- A deterministic policy may miss subtler patterns that a future shadow knowledge-tracing model could identify; that is intentionally deferred until adequate pilot data exists.

## QA requirements
- same evidence + same policy version => identical decision;
- one target failure cannot trigger remediation;
- assisted attempts cannot satisfy independent thresholds;
- duplicate attempts on one problem do not create false breadth;
- recent mastery supersedes older prerequisite failures;
- cross-curriculum evidence/edges cannot confirm a gap;
- removing or failing an LLM cannot change the structured decision.
