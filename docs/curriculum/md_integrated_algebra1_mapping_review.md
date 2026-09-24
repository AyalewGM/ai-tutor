# Maryland Integrated Algebra I mapping review

Status: reviewed architecture/PO input for F-012 mapping implementation.

Authority: Maryland State Department of Education (MSDE).

Adopted source: https://www.marylandpublicschools.org/about/Documents/DCAA/Math/revised/Integrated-Algebra-1-Crosswalk-A.pdf

Course/version: Integrated Algebra I, 2025 revised MCCRS, adopted July 2025, implementation SY 2027-2028.

## Mapping rule

The MSDE crosswalk is provenance evidence, not blanket permission to mark a new curriculum skill equivalent to an existing AI Tutor canonical skill. A mapping may use `EQUIVALENT` only when the AI Tutor skill grain matches the adopted Integrated Algebra I expectation. Curriculum-local prerequisites, problem eligibility, mastery, and learner evidence remain isolated even when canonical concepts are shared.

Integrated Algebra I intentionally blends algebraic thinking, geometric reasoning, and data/statistics. Canonical reuse must therefore be searched across the whole mathematics concept catalog, not only the traditional Maryland Algebra I pack.

## Representative review matrix

| IA1 standard | MSDE predecessor evidence | Review disposition |
| --- | --- | --- |
| IA1.AT.C.11 — average rate of change | F.IF.B.6 | Reuse an existing average-rate-of-change canonical concept only if its grain covers linear and exponential functions over an interval; otherwise create a new canonical concept. |
| IA1.AT.C.12 — compare function properties | F.IF.C.9 | Candidate for canonical reuse after grain review; do not infer mastery from traditional Algebra I. |
| IA1.GR.A.1 — rigid transformations/congruence | G.CO.A.2, G.CO.B.6 | Geometry-derived. Reuse a geometry canonical concept only when the concept includes transformation-as-function and congruence verification at the same grain. |
| IA1.DS.A.1 — correlation vs causation | S.ID.C.9 | Statistics-derived. Reuse an existing statistics concept if present at matching grain; otherwise create one. |
| IA1.DS.B.6 — two-way frequency tables | S.ID.B.5 | Statistics-derived candidate; preserve IA1-local skill/evidence identity. |
| IA1.AT.B.8 — optimize with systems of linear inequalities | New standard | Do not force-map to a traditional Algebra I concept. Create/review a new canonical concept. |
| IA1.AT.B.9 — linear/exponential systems with technology | New standard | Do not manufacture equivalence. Create/review a new canonical concept. |
| IA1.AT.D.17 — inverse of a linear function in context | New standard | Do not manufacture equivalence. Create/review a new canonical concept. |

## Implementation acceptance for the next slice

1. Seed a small representative set before bulk authoring: algebra/function, geometry, statistics, and at least one explicitly new IA1 expectation.
2. Persist mapping provenance containing the IA1 code, MSDE crosswalk source, predecessor code(s) where applicable, curriculum code, and curriculum version.
3. Re-running the seed is idempotent.
4. Shared canonical identity must not create cross-curriculum prerequisite edges or copy `StudentSkill` evidence/mastery.
5. A new IA1 expectation must not be silently attached to an unrelated traditional Algebra I canonical concept.
6. Problems and explanations remain original AI Tutor content. No state sample item or proprietary district/vendor instructional content is copied.
7. LLMs do not choose standards, equivalence, prerequisites, mastery, or jurisdiction mappings.

## Data-impact check

This mapping slice requires only curriculum standards metadata and mapping provenance. It requires no new student/parent data, profiling, authentication data, consent state, exports, or retention behavior. No learner data is sent to OpenAI, Gemini, or another third party. Tests must use synthetic/minimized data and must not contain secrets or real child data.
