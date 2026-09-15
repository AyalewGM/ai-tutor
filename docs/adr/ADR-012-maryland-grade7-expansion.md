# ADR-012: Maryland Grade 7 curriculum expansion

## Status
Accepted for F-012 implementation following owner approval on 2026-09-15.

## Context
The AI Tutor already supports curriculum-scoped learning evidence and an MCPS Grade 8 content pack. F-012 validates that Maryland grade expansion can occur through curriculum/content configuration rather than an application fork.

## Decision
Maryland Grade 7 Mathematics is implemented as a separately versioned curriculum pack under the existing curriculum authority/provenance model.

- Curriculum code: `MCPS_MATH_7`.
- Authority: reuse the existing `MCPS` education authority.
- Grade 7 skills, prerequisite edges, misconceptions, and problems are curriculum-local.
- Prerequisite edges may never cross curriculum IDs.
- Grade 7 content does not inherit Grade 8 mastery, attempts, diagnostics, interventions, or other learner evidence.
- Historical evidence remains bound to the curriculum/version under which it was generated.
- Adding Grade 7 requires no separate application deployment or pedagogical code path.
- Source/provenance metadata identifies the public curriculum/standards authority; tutoring problems and pedagogical decomposition remain original/permitted content.

## Pedagogical authority
Application code remains authoritative for curriculum selection, prerequisites, mastery, remediation, assessment, and intervention routing. LLMs may only generate constrained language from application-computed decisions and cannot infer cross-curriculum equivalence or transfer mastery.

## Validation
F-012 QA must prove:
1. Grade 7 and Grade 8 curriculum records coexist independently.
2. Grade 7 prerequisite edges remain within Grade 7.
3. Grade 7 problem inventories reference only Grade 7 skills.
4. Existing Grade 8 behavior and tests remain unchanged.
5. Learner evidence cannot be reused as Grade 7 evidence merely because a skill appears conceptually related in another curriculum.
