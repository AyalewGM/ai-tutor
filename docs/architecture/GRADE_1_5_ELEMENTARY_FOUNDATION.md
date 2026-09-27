# Grade 1–5 Elementary Mathematics Expansion Foundation

Status: ACTIVE FOUNDATION SLICE after F-023.

## Scope
Build one reusable elementary mathematics foundation before activating Maryland Grade 1 content. Later grades are gated: Grade 2 starts only after Grade 1 satisfies the repository Definition of Done, and so on through Grade 5.

## Architectural invariants
- Application code owns pedagogy, prerequisites, eligibility, progression, assessment, answers, and mastery.
- LLM use is constrained to language generation after deterministic application decisions.
- Curriculum identity, standards, skills, prerequisites, attempts, mastery, and evidence remain jurisdiction/version local.
- Canonical mathematical concepts may be reused for authoring and rendering but never imply cross-curriculum mastery equivalence.
- Original instructional content only; proprietary commercial/district problem banks are not ingested or copied.

## Problem-family contract
A parameterized family must declare:
1. curriculum-local skill/objective;
2. canonical mathematical concept;
3. parameter domains and constraints;
4. deterministic answer/evaluation function;
5. difficulty and representation metadata;
6. misconception/distractor rules where applicable;
7. guided versus independent/mastery eligibility;
8. deterministic validation invariants;
9. semantic visual specification when the representation requires one;
10. accessible text/math alternative.

Families should support conceptual understanding, fluency, application/word problems, multiple representations, misconception probes, fresh independent mastery checks, and increasing difficulty without storing thousands of duplicated questions.

## Visual contract
Pipeline: validated mathematical state -> declarative semantic visual spec -> accessible renderer.

Initial elementary primitives: number line, ten-frame/counters, arrays, place value, fraction bars/circles, clocks, money, measurement, geometry, coordinate grids, pictographs, bar graphs, line plots, and tables. Render programmatically (SVG/DOM where practical), not as a static image bank. Visual truth is deterministic and must match the answer model.

## Required automated checks
- generated parameter constraints and answer correctness;
- deterministic/reproducible seeded generation where applicable;
- valid distractors and no duplicate answer choices;
- difficulty bounds and fresh-variant behavior;
- answer-to-visual semantic consistency;
- accessible alternatives and keyboard/reduced-motion behavior;
- curriculum/jurisdiction isolation and no evidence leakage;
- regression/E2E checks required by docs/qa/DEFINITION_OF_DONE.md.

## Grade activation sequence
Foundation -> Maryland Grade 1 -> Grade 2 -> Grade 3 -> Grade 4 -> Grade 5 -> cross-grade prerequisite/content audit -> family-pilot readiness.

Research alone does not activate a later grade.

## Data-impact baseline
No new child/parent PII is required for this foundation. Use synthetic/minimized fixtures only. Do not add telemetry, session replay, advertising SDKs, or new third-party learner-data flows. Any boundary change requires Security & Compliance review covering purpose, storage, retention/deletion, access, third-party/LLM flow, and a less-data alternative.

## Parallel boundaries
F-012 Integrated Algebra I remains bounded and must not delay this work. Business Model/Pilot Economics remains a nonblocking research track. Reuse and extend F-020 visualization architecture rather than creating a competing renderer.
