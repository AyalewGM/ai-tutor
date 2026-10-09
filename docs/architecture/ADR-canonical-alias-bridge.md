# ADR: Canonical curriculum alias bridge (#282)

Status: **PROPOSED — NOT RUNTIME-APPROVED**. Owner: Curriculum/Architecture. Independent QA: Muse. Engineering Board: #278.

## Decision

Application canonical skill IDs are authoritative. Existing jurisdiction-pack `MATH.ELEMENTARY.*` identifiers are retained as compatibility aliases; do not mass-rename existing packs, learner evidence, mastery records or assessment identifiers. Introduce a versioned, reviewable alias mapping. An alias may map to several authoritative skills only with explicit `ALL_OF` semantics: all targets are required. Alternative mapping is not automatically equivalent and requires separate architectural and curriculum review. Unmapped, ambiguous, unreviewed, duplicate, stale or invalid targets **fail closed**; no automatic coverage credit.

## Implementation sequence

1. Inventory all published pack aliases and application canonical IDs, with counts independently checked by Muse. Current investigation found 42 distinct pack aliases and 488 application IDs; treat these as baseline observations, not immutable requirements.
2. Define a versioned schema with alias, mapping status (UNMAPPED/PROPOSED/REVIEWED), relation (ALL_OF), target skill codes, evidence, reviewer, and version.
3. Validate every published pack alias and target against the application registry, reject duplicates and unreviewed mappings at the publication gate, and add deterministic CI tests. Existing published packs remain incomplete until mappings are reviewed.
4. Have Curriculum review mathematical equivalence for each alias. Broad aliases may require several targets. Do not guess mappings from name similarity.
5. Once the schema is approved, coordinate consumer integration with Devin #286. Coverage reconciliation belongs to #283 and must preserve all eight evidence predicates.

## Safety invariants

Bridge lookups must not mutate historical mastery, assessment IDs, problem evidence, or jurisdiction/source-version attribution. No real child PII. Do not claim curriculum coverage based solely on ingestion, aliases, or seed content. Muse independently reviews mapping completeness and regressions.

This ADR documents a proposed contract only. It does not assert that runtime resolution or coverage reconciliation is implemented.
