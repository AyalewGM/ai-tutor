# ADR-002: Adaptive Diagnostic Placement

## Status
Accepted for F-002 implementation.

## Context
The tutor needs a fast way to determine where a learner should begin relative to a selected target skill. The diagnostic must use the prerequisite graph, remain auditable, avoid teaching during assessment, and stay independent of the LLM.

## Decision
Diagnostic placement is a separate bounded workflow rather than another `TutorState`.

### Persisted model
`DiagnosticSession` stores:
- learner;
- target skill;
- current probe skill;
- lowest skill currently known to be unready (`blocked_skill_id`);
- final recommended starting skill;
- status and placement reason;
- timestamps.

`DiagnosticAttempt` stores each unassisted probe response and evaluation evidence.

Normal `StudentSkill` evidence is updated from valid diagnostic responses so tutoring and diagnosis share one learner model, while the diagnostic's raw attempts remain separately auditable.

### Probe policy
1. Start at the target skill.
2. Require unassisted responses.
3. Two consecutive correct probes classify the current skill as ready for placement purposes.
4. A prerequisite-specific misconception may trigger immediate descent to that prerequisite.
5. Otherwise, two incorrect probes classify the current skill as not ready and descend to its highest-priority prerequisite.
6. When a prerequisite is shown ready, recommend the lowest blocked parent skill.
7. If an unready skill has no prerequisite, recommend that skill.
8. Cap the V1 diagnostic at eight responses and return the best supported placement if uncertainty remains.

This readiness rule is a placement heuristic, not a declaration of curriculum mastery. Normal mastery thresholds remain separate.

### No tutoring during diagnosis
The diagnostic API returns neutral assessment text only. It does not call `TutorEngine`, reveal correctness explanations, provide hints, or expose solutions before placement is complete.

## Consequences
- Placement is deterministic and testable.
- Diagnostic evidence can be audited independently from tutor dialogue.
- The algorithm can later be replaced by IRT/BKT without changing the API concept.
- The V1 graph is narrow enough that deterministic prerequisite traversal is preferable to a probabilistic model.
