# F-018 Deletion Dependency Audit

## Purpose
Prevent an unsafe `DELETE parent` / blind cascade implementation. This is an engineering and privacy lifecycle contract, not legal advice.

## Repository findings

### Account/session layer
- `auth_sessions.user_id -> users.id` uses `ON DELETE CASCADE`.
- `user_credentials.user_id -> users.id` uses `ON DELETE CASCADE`.
- `parent_profiles.user_id -> users.id` currently has no database `ON DELETE` action.

Therefore deleting a `users` row first is not a safe family-deletion algorithm: the parent profile can block deletion and downstream family records require explicit handling.

### Parent/family layer
- `parent_student_relationships.parent_profile_id -> parent_profiles.id` has no cascade.
- `parent_student_relationships.student_id -> students.id` has no cascade.
- `parent_student_relationship_events.relationship_id -> parent_student_relationships.id` has no cascade.
- `child_link_claims.student_id -> students.id` has no cascade.

Relationship/audit records must have an explicit lifecycle decision rather than inheriting an accidental FK behavior.

### Learner authoritative evidence
The following learner records are authoritative educational state and are linked by non-cascading FKs: `student_skills`, `student_misconceptions`, `tutor_sessions`, `attempts`, `mastery_events`, and `intervention_records`. `tutor_turns` and attempts also depend on sessions/attempts. Curriculum enrollments/diagnostics/hints/content-linked evidence in their dedicated model modules must be included in the implementation transaction as well.

A learner deletion must therefore be a deliberately ordered service operation. Do not add broad database cascades merely to make deletion convenient.

## Safe implementation direction

1. **Separate unlink from erase.** Unlinking a parent/learner relationship is not deletion of learner evidence.
2. **Authorize before mutation.** Only the authenticated parent/family authority may request deletion for an owned learner. Identifier substitution must fail closed and non-enumerating.
3. **Revoke access early.** For account deletion, revoke/delete active auth sessions in the same transaction before final account removal.
4. **Delete disposable/security artifacts deliberately.** Expired/link claims and disposable telemetry associated with the learner/account should follow their documented lifecycle and must never be treated as mastery evidence.
5. **Delete learner evidence in dependency order** inside one database transaction, after every dependent table has explicit test coverage. If any dependency is unknown, rollback rather than partially erase.
6. **Do not delete shared curriculum/content.** Curriculum, skills, problems, standards and provenance are shared reference data and are outside a family deletion.
7. **Minimal audit outcome.** If an operational deletion receipt is retained, it must not contain learner name/email/free-form answers or reconstructable tutoring content. Prefer opaque request ID, action type, policy version, timestamps and outcome.
8. **No third-party deletion call is currently required by this slice.** The browser has no direct OpenAI/Gemini flow and standard pilot telemetry is first-party. If provider data flows change, vendor deletion obligations must be re-audited.

## Required tests before enabling destructive UI
- unrelated parent cannot delete/unlink another family's learner;
- deleting/unlinking one learner cannot affect a sibling or another curriculum;
- unlink does not erase authoritative learner evidence;
- full learner erase removes all learner-scoped authoritative and disposable records without touching shared curriculum/content;
- parent account erase revokes sessions/credentials and handles parent profile/relationships explicitly;
- transaction failure rolls back completely;
- post-deletion API access is denied;
- deletion/expiry of telemetry cannot change mastery/intervention outcomes;
- synthetic/minimized identities only.

## Release gate
Do not expose a destructive browser control until the deletion service has a complete dependency map, transactional implementation, authorization/isolation tests, and Security + QA acceptance. Notice acknowledgement may proceed independently because it is additive, minimized metadata and does not require destructive lifecycle behavior.
