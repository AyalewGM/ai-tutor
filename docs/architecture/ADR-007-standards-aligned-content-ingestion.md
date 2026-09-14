# ADR-007: Standards-Aligned Curriculum Content Ingestion

## Status
Accepted for F-007 implementation. Pilot curriculum identity remains subject to the Product Owner research gate recorded on issue #15.

## Context
F-006 established curriculum authority, versioning, jurisdiction isolation, enrollment scoping and local implementation overlays. F-007 needs a repeatable way to ingest official standards/expectation metadata and map that metadata to AI Tutor-owned pedagogical skills without allowing source records, proprietary curriculum material, or an LLM to become the tutoring policy.

The same ingestion architecture must support the Ontario MTH1W pilot and the final authorized Maryland pilot course without creating jurisdiction-specific application forks.

## Decision
1. `CurriculumExpectation` is a provenance-bearing source record scoped by `curriculum_id`, curriculum version and source identifier. Official expectation metadata is not itself the tutor skill graph.
2. `ExpectationSkillMapping` is an explicit application-owned mapping from a source expectation to one or more tutor `Skill` records. Both ends must belong to the same curriculum.
3. Ingestion uses stable curriculum/version/source keys and idempotent upsert semantics. It requires a pre-existing active curriculum registry entry and never creates curriculum authority records implicitly.
4. Prerequisite edges are persisted separately from expectation mappings. Both skills in a prerequisite edge must resolve inside the selected curriculum; duplicate and self-referential edges are rejected.
5. Content validation fails closed on cross-curriculum mappings, missing traceability for active skills, duplicate source identifiers, invalid source/version metadata and inadequate or overlapping assessment/practice problem pools.
6. Diagnostic, guided-practice, independent-practice and mastery-check inventories are distinct application-owned modes. Mastery evidence cannot reuse a problem already used for independent or assisted practice when freshness is required.
7. Official-source provenance and AI Tutor-authored instructional content remain distinct. Commercial curriculum lesson text, worksheets, answer keys and protected sequencing artifacts are not ingested.
8. The LLM may only render constrained language after application code selects curriculum, skill, objective, difficulty, problem mode and hint policy. It may not create standards, curriculum mappings, prerequisite edges, mastery implications or cross-curriculum equivalencies.

## Runtime boundaries
F-007 does not introduce a new AI runtime dependency. Existing learner/session APIs continue to resolve the learner's active curriculum before diagnostic, remediation or tutoring operations. Historical evidence remains attached to the curriculum/enrollment snapshot that produced it.

The ingestion layer is an administrative/content-build path, not an unrestricted learner-facing endpoint. Invalid packs must fail before they can influence tutoring state.

## Data and migration impact
Alembic migration `0008_curriculum_content_expectations` introduces the expectation/mapping persistence model using the repository's idempotent migration pattern. Existing curriculum, skill, enrollment and prerequisite records remain authoritative and are not destructively rewritten.

## Failure behavior
- Unknown or inactive curriculum/version: reject ingestion.
- Duplicate expectation identity inside one curriculum/version: deterministic upsert or validation failure according to pack semantics; never duplicate rows silently.
- Cross-curriculum expectation mapping or prerequisite: reject.
- Active skill without source traceability: fail content audit.
- Missing/overlapping required problem modes: reject pack validation.
- LLM/provider unavailable: no effect on curriculum identity, mapping, prerequisite topology, mastery eligibility or assessment policy.

## QA implications
Acceptance must include idempotent double ingestion, cross-curriculum rejection, curriculum-local prerequisite validation, source-traceability audit, distinct problem-mode validation, migration/regression CI, and an end-to-end learner flow showing that a learner cannot receive a foreign-jurisdiction skill or problem.

## Consequences
The design adds explicit source-to-pedagogy mapping work, but keeps provenance auditable and prevents standards metadata from becoming an accidental tutoring engine. New jurisdictions can be added primarily as versioned content/configuration rather than application forks, while jurisdiction-specific authority rules stay in the curriculum registry.
