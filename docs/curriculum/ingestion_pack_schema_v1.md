# Curriculum ingestion pack schema v1

The ingestion pack is the portable boundary between source extraction and Mihur's curriculum database.

A pack contains one authoritative curriculum identity and version, its official source URI, standards/expectations, and optional **proposed** mappings to canonical mathematical skills. Ingestion packs never publish mappings and never carry learner evidence.

## Required identity

- `schema_version`: currently `1.0`
- `curriculum_code`
- `curriculum_version`
- `authority_code`
- `source_uri`: absolute HTTP(S) URI for the authoritative curriculum source
- one or more standards

Each standard carries its official code, title, and the same authoritative source URI. Optional description, strand, and sequence fields preserve jurisdiction presentation without changing canonical mathematics.

## Proposed mappings

A proposed mapping references a standard code and canonical skill code. Supported mapping types are `ALIGNS_TO`, `EQUIVALENT`, and `PARTIAL`. Rationale and coverage may be carried for review.

All mappings entering through this contract are proposals. The contract has no `PUBLISHED` field and no reviewer field. Publication is a separate privileged workflow governed by the validation/review gate introduced in #216.

## Deterministic validation

Before persistence Mihur rejects unsupported schema versions, missing identity fields, non-absolute source URIs, standards citing a different source, invalid effective windows, duplicate standards, mappings to unknown standards, unsupported mapping types, and duplicate proposed mappings.

Stable persistence identity is `(curriculum_code, curriculum_version, standard_code)`.

## Trust boundary

The pack contains curriculum metadata only. It must not contain StudentSkill, mastery scores, attempts, learner identifiers, or other learner evidence. Canonical mathematics remains reusable; learner evidence remains curriculum-local.

Parent epic: #220. Initial contract issue: #221.
