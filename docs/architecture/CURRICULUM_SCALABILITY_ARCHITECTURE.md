# Curriculum Scalability Architecture

Status: Accepted direction. Implementation begins after the Math Visual Engine (MVE) reaches its agreed completion gate.

## Decision

**Implement mathematics once. Map curricula many times.**

Mihur must not build separate tutoring systems for each U.S. state or Canadian province. Jurisdictions are curriculum overlays on a canonical Mihur mathematical knowledge model.

**Deterministic first. Use AI only when it adds pedagogical value.**

## Architecture

The shared layer contains canonical concepts and skills, prerequisite relationships, misconception taxonomy, deterministic validators, reusable problem families, and Math Visual Engine capabilities.

The jurisdiction layer contains country/state/province, curriculum authority, grade/course, standard or expectation code, curriculum version, sequence and coverage metadata, and mappings to canonical Mihur skill IDs.

Every curriculum mapping retains provenance: source reference, standard code, effective version/year, review status, and audit/reviewer metadata. AI may propose mappings, but publication requires controlled validation.

## Boundary rule

Jurisdiction metadata must not leak into shared mathematical correctness, visualization, misconception detection, or mastery algorithms unless a documented jurisdiction requirement genuinely changes the evidence rule. Curriculum revisions should normally update/version mappings rather than fork the math engine.

## Core flow

Official curriculum -> CurriculumVersion -> Standard/Expectation -> StandardSkillMapping -> Canonical Skill -> Prerequisites/Misconceptions -> Problem Families/MVE -> Deterministic Validation -> Mastery Evidence.

## Post-MVE implementation sequence

1. Define canonical Skill, Concept, Prerequisite, Misconception, ProblemFamily, CurriculumVersion, Standard, and StandardSkillMapping contracts.
2. Reconcile existing Maryland/DMV and Ontario/MTH1W data into those contracts without changing learner behavior.
3. Add curriculum provenance, versioning, and mapping validation.
4. Prove the architecture with Maryland and Ontario as structurally different reference jurisdictions.
5. Build controlled ingestion: official source -> extracted draft -> proposed mappings -> consistency checks -> human review -> published version.
6. Expand jurisdictions incrementally.

## Scalability acceptance criteria

A new state or province should normally require curriculum data, mappings, review, and only genuinely missing canonical skills/problem families—not a new tutoring implementation.

The same canonical skill may map to many standards without duplicating its validator, misconception model, problem generator, or visual implementation.

Learner evidence does not silently transfer across jurisdictions merely because standards have similar wording. Reuse happens at the canonical mathematics layer; curriculum evidence remains explicitly scoped.

## Architecture review triggers

Require architecture review before forking a validator by jurisdiction, creating a jurisdiction-specific visualization framework, duplicating a problem family solely for a curriculum code, allowing AI to publish curriculum mappings without review, or changing mastery semantics because standards appear textually similar.

Related architecture: Math Visual Engine epic #175.
