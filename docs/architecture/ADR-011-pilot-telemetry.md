# ADR-011: First-party pilot telemetry boundary

## Status
Accepted for the F-011 implementation slice.

## Decision
Pilot telemetry is a first-party, append-only observability stream that is strictly non-authoritative for pedagogy. Authoritative learning evidence remains in the existing tutoring, mastery, curriculum, and intervention stores.

The event envelope is versioned and metadata-minimized. It carries pseudonymous learner identity, curriculum/course identity, optional session/skill references, policy/version metadata, purpose, retention class, and bounded metrics. Standard telemetry rejects raw prompts, learner answers, transcripts, names, email addresses, authentication tokens, precise location, and session-replay content.

The initial disposable retention class is `DISPOSABLE_90D`. This is a configurable/versioned pilot product policy, not a claim that COPPA requires 90 days. Shorter purpose-specific periods may be introduced later. Authoritative learning evidence has a separate lifecycle.

## Pedagogy boundary
Telemetry may measure tutoring decisions but may not choose or alter curriculum, skill progression, prerequisites, hints, mastery, assessment restrictions, or F-010 interventions. Analytics loss or deletion must not change those outcomes. LLMs may only verbalize already-computed application decisions and never derive pedagogical authority from telemetry.

## Curriculum boundary
Every learning-related telemetry event includes its curriculum/course identity. Analytics may aggregate by curriculum but telemetry never becomes cross-curriculum learning evidence and never establishes curriculum equivalence.

## Failure behavior
Telemetry publication is intended to fail open relative to tutoring correctness. This first slice establishes the append-only persistence seam and validation boundary; later F-011 slices will add non-blocking publication, retention jobs, KPI read models, cost events, and fail-open integration tests.

## Consequences
- Event IDs provide deduplication/audit identity for retry-prone transitions.
- Privacy-schema validation happens before persistence.
- Deleting disposable telemetry cannot erase or mutate mastery/intervention evidence.
- External analytics SaaS is outside the initial private-pilot slice.
