# Middle Grades rational scale and inverse reasoning (DRAFT_UNVERIFIED)

This package deepens an existing Grade 7 rational-operations family. It does not create or approve a canonical identity, alter runtime routing, change scoring, or award learner credit.

## Reuse-first audit

| Existing work | Actual gap | Planned improvement | Verification |
| --- | --- | --- | --- |
| Main has `MATH.RAT.MUL`, `MATH.RAT.DIV`, `MATH.RAT.NUMBER_LINE`, and exact `Fraction` generator tests | Existing prompts emphasize procedures; they do not establish direction-and-scale meaning, division as a missing scale, or reasoning transfer | Add one draft package that connects oriented fraction strips, a reflection/scale model, symbolic products, and inverse equations | Exact rational oracle and deterministic namespace tests in `tests/test_middle_grades_rational_scale_v1.py`; independent reviews remain pending |
| PR #315 and PR #328 already own ratio/double-number-line content; PR #328 separately owns signed-integer addition and data/spatial depth | New work could duplicate active packages or imply that integer-addition evidence transfers to rational multiplication/division | Reuse only the exact-rational helper contract and explicitly exclude addition/subtraction, ratio lessons, IQR, cube nets, and assessment-backend changes | Scope-boundary assertions prevent overlap; Issue #278 coordination is required before integration |
| PR #325 traces local `M7.NS.RAT` to Maryland `7.NOS.A.1`–`7.NOS.A.3` but accepts no mapping | A local seed and a canonical generator do not prove expectation-level coverage | Record `7.NOS.A.2` and `7.NOS.A.3` only as provisional candidate targets for independent Standards Mapping review | Provenance remains `PROVISIONAL_NOT_ACCEPTED`; no coverage or mastery claim |

Ownership is separated: Middle Grades Content owns this draft package; Standards Mapping owns expectation approval; Mathematical Review owns correctness; Pedagogical Review owns learning-design acceptance; the assessment backend owner controls scoring contracts; Muse owns accessibility and assessment QA; Engineering Lead approval is required before integration or any scoring-contract change.

The independent-assessment section is a content contract only. It requires server-controlled unseen variants and no hints, but this draft does not modify an API, persist an attempt, or activate mastery writes.
