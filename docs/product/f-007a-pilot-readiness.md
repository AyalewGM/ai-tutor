# F-007A — Authoritative Pilot Content Packs & Maryland Course Decision

## Problem statement

The pilot must demonstrate deterministic tutoring against the learner's actual curriculum without silently reusing Grade 8, another jurisdiction, or a future course sequence. The existing Maryland seed is `MCPS_MATH_8`; that identity must not be relabeled or have its evidence migrated into Algebra 1.

## Accepted pilot identities

### Maryland

For the current SY2026–27 pilot, use a separately versioned traditional **MCPS/Maryland Algebra 1** curriculum pack when enrollment evidence confirms Algebra 1. MCPS currently identifies Algebra 1 as part of its 2026–27 mathematics pathway and states that the transition to Integrated Algebra I begins in fall 2027. Integrated Algebra I is therefore a separate future pack and must not share evidence implicitly with this pilot pack.

Authoritative/current references:

- MCPS mathematics curriculum: https://www.montgomeryschoolsmd.org/curriculum/math/ms/
- MCPS SY2026–27 family curriculum update: https://ww2.montgomeryschoolsmd.org/departments/publicinfo/community/thingstoknow/2026/Community-Update-2026-09-03.html
- MCPS/MSDE pathway transition explanation: https://www.montgomeryschoolsmd.org/news/mcps-news/2026/02/math-update/
- MCPS MCAP assessment information: https://pprd.montgomeryschoolsmd.org/curriculum/mcap

Do not copy Amplify Desmos proprietary tasks, wording, lesson sequences, screenshots, or answer keys. Repository problems must be original/non-proprietary expressions of public course/standards outcomes.

### Ontario

Consume the canonical F-015 Ontario Grade 9 `MTH1W / 2021` pack. F-007A must not create a second Ontario mapping or migrate evidence between Ontario and Maryland.

## Application-owned pedagogy

Application code remains authoritative for curriculum mapping, prerequisite topology, problem-mode eligibility, hint/remediation selection, intervention, mastery eligibility, and progression. LLM services may render constrained language only after those decisions. LLM availability or output must never change a mastery or progression decision.

## Minimum engineering slice

1. Add a separately versioned Maryland Algebra 1/SY2026–27 curriculum pack; do not mutate `MCPS_MATH_8`.
2. Add a bounded set of original skills, local prerequisite edges, misconceptions, and enough original problems for diagnostic, guided/remediation, independent practice, and fresh mastery evidence.
3. Validate every prerequisite edge is curriculum-local.
4. Add synthetic Maryland E2E evidence for diagnostic → targeted remediation/hints → fresh independent mastery.
5. Add/reuse synthetic Ontario E2E evidence against the canonical F-015 MTH1W pack.
6. Prove assisted evidence cannot satisfy independent mastery and cross-curriculum evidence cannot affect mastery, prerequisites, remediation, or intervention.
7. Run the complete regression suite and `docs/qa/DEFINITION_OF_DONE.md` before acceptance.

## Acceptance criteria

- Maryland Algebra 1 has an explicit jurisdiction/course/effective-version identity and provenance.
- Existing Grade 8 evidence is unchanged and is not treated as Algebra 1 evidence.
- Future Integrated Algebra I is not treated as equivalent to traditional Algebra 1.
- Ontario MTH1W and Maryland Algebra 1 remain strictly isolated.
- Diagnostic and remediation operate only on skills/prerequisites in the selected pack.
- Hinted/assisted success remains distinguishable from independent evidence.
- Mastery requires the existing deterministic fresh-independent evidence rules.
- LLM failure/fallback does not alter the pedagogical decision.
- Seed/problem/test content is original and synthetic; no proprietary vendor content or real child data is committed.

## Lightweight data-impact check

F-007A should not introduce a new category of personal data. Curriculum metadata, skill topology and original problem content are first-party application content. E2E learner identities and attempts must be synthetic. No real child name, schedule, answer history, screenshot, identifier, email, authentication token, prompt transcript, or secret belongs in repository fixtures or GitHub issues.

Existing runtime learner evidence remains subject to existing authorization, retention and telemetry controls. F-007A does not require additional identity data to be sent to OpenAI, Gemini, or the LLM Gateway. The less-data design is the required design: synthetic/minimized test identities and constrained generation inputs only.

## Product and growth implication

The defensible product claim is curriculum-specific, explainable progression with independently demonstrated mastery—not reproduction of a district/vendor curriculum. Pilot commercialization evidence should emphasize jurisdiction isolation, independent mastery evidence, parent trust, and deterministic fallback behavior.

## Risks

- Course identity drift as Maryland transitions to Integrated Algebra I: mitigate with explicit effective school year/version and separate pack IDs.
- Proprietary-content contamination: mitigate by authoring original problems from public standards/outcomes only.
- False equivalence across courses/jurisdictions: mitigate by curriculum IDs, local prerequisite validation and regression tests.
- Child-data leakage during pilot development: mitigate with synthetic fixtures and existing privacy-safe telemetry boundaries.
