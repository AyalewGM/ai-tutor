# External fractions intake — draft-g45-fractions-pilot-v0

**DRAFT_UNVERIFIED / PENDING review / not executable or published**

Source: owner-provided Grok-generated Grades 4–5 package in ChatGPT, 2026-10-09. These are **editorially normalized** artifacts, not an exact byte-for-byte archival copy. The original owner transcript remains the source for checking editorial fidelity. Do not infer originality, jurisdiction alignment, canonical identity, or independent mathematical approval from the import.

## Inventory

| Component | Count | Location |
|---|---:|---|
| Practice questions | 25 | `practice.normalized.json` |
| Worked examples | 5 | `supporting.normalized.json` |
| Misconception/remediation entries | 5 | `supporting.normalized.json` |
| Interactive specifications | 1 | `supporting.normalized.json` (design only) |

## Corrections applied

1. **Numerical domain:** Explicitly list 7 and 9 as operational denominator exceptions for the original practice set. Equivalence problems legitimately produce 9, 15, 20 and 25; these are recorded as derived denominators, not silently treated as original practice denominator choices. Other denominator appearances (e.g. 3 in representation/comparison) are context-specific, not a global generator limit.
2. **Single mathematical expected values:** Normalize `3/9 or 1/3` to `1/3`, `6/12 or 1/2` to `1/2`, `4/10 or 2/5` to `2/5`. Retain unsimplified calculation in `intermediate_form` for instruction. Numeric equivalence is checked by exact `fractions.Fraction` arithmetic; **do not** automatically grant full credit when the prompt explicitly requires simplest form.
3. **Fixed denominator:** `q-eq-01` expects `3/9` because the prompt specifies denominator 9, even though its value equals 1/3.
4. **Two-answer question:** `q-eq-03` uses two distinct answer slots, with distinct multipliers from 2–5. A single accepted answer is insufficient. The pair is represented as semicolon-delimited normalized expected values pending a future structured answer interface; this is **not** a runtime parser.
5. **Mixed-number scope:** `q-add-04` now explicitly requests an improper fraction only (`7/5`). The original mixed-number answer `1 2/5` is mathematically valid but excluded by the stated package scope.
6. **Reasoning rubrics:** `q-rep-06`, `q-eq-02`, `q-eq-05`, and `q-eq-06` require **human reasoning review**. Exact numeric or choice validation alone cannot assess the requested explanation. No keyword-match auto-mastery.
7. **Misconception fidelity:** `misc-04` now shows a genuinely incorrect tick/interval count; `misc-05` explicitly states an invalid gap-to-one comparison. They remain pending pedagogical review.
8. **Visual model:** The combined result may exceed one whole; render an additional unit bar rather than exceeding a single unit bar. Interactive implementation belongs to the MVE lane, not this draft PR.

## Validation

`tests/test_draft_g45_fraction_intake.py` contains deterministic exact-rational oracles for all 25 items, checks intermediate forms, comparison/equivalence relations, item uniqueness, inventory, draft-only metadata, disallowed ambiguous answer formats, strict parser behavior, and exhaustive bounded state invariants for the proposed fraction bar.

**Execution evidence:** The test suite has not been executed in this ChatGPT environment against a checked-out repository. CI results must be examined on the draft PR; a passing test suite is necessary but insufficient for mathematical/pedagogical approval.

## Review gates and limitations

- No authoritative canonical skill IDs, official curriculum mappings, generator registrations, runtime activation, historical mastery changes, or claims of published Grade 4/5 coverage.
- Independent mathematical review requested through #293; Muse QA independently checks test execution and fidelity against original owner-provided package.
- Some original step-by-step hints, alternative phrasings, and detailed pedagogical rationale have been condensed in the normalized intake. Compare with original transcript before accepting a publishable source-of-truth conversion.
- Exact arithmetic tests do **not** prove contextual wording, explanatory adequacy, accessibility, originality, or source-curriculum alignment.
- Avoid overlap with taxonomy foundation #282 / PR #308 and MVE fraction arithmetic PR #303.
- On review approval only, propose a coherent **separate** expansion to 100 practice questions, 15 worked examples, 15 misconceptions and 5 interactive specifications; no automatic publication.
