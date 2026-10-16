# TX regular Grade 2 — independent source-fidelity handoff (2026-10-15)

Author-side source tree SHA before this handoff commit: `b60c081d1daef0706b4aec2ee61a13b447adf54a`.
Reviewer MUST fetch the current PR #384 head and record its exact SHA before deciding.

## Official source and new author evidence

- Official Texas Education Agency Chapter 111 Subchapter A (December 2014 update), §111.4, printed page 9, zero-based PDF page index 8:
  https://tea.texas.gov/laws-and-rules/sboe-rules-tac/sboe-tac-currently-effect/ch111a.pdf
- Existing 10 provisional §111.4(b)(2)(A–F), (3)(A–D) rows:
  `tx_regular_grade2_number_fraction_author.v1.json`.
- Added 8 provisional §111.4(b)(4)(A–D), (5)(A–B), (6)(A–B) rows:
  `tx_regular_grade2_operations_4_6_author.v1.json`.
- Author metadata and regression enforce 18 distinct IDs, publisher page 9 and PENDING/UNVERIFIED/FORBIDDEN gates. The original publisher bytes/hash are not authenticated in repository evidence.

## Independent verifier's checklist

1. Verify all 18 exact expectation IDs, parent stems, scope paraphrases and any mandatory qualifiers against the original TEA edition and printed page 9. `including` is mandatory; `such as` is illustrative.
2. Check mathematical non-equivalences: automaticity within 20 versus operations on two-digit numbers; one- and multi-step problems within 1,000 versus generating situations from number sentences; coin-value limit one dollar versus symbols/decimal notation; joining equal sets for multiplication versus partition into equal sets for division.
3. Re-review corrected Texas Grade 1 §§111.3(b)(4)–(9) 30 author rows on printed pages 6–7. Five absent identifiers were added; corrected total 50. Verify source fidelity before approval.
4. Check fresh exact-head CI and AppSec. The earlier run 38782036489 failed outdated tests (Grade 1 45 versus 50, and a Grade 6 assertion that forbade Grade 2 partial status). Both assertions were amended. Do not presume fresh green.
5. Issue bounded exact-SHA ACCEPTED or CHANGES_REQUIRED with row-level findings. No independent acceptance may be inferred from tests or author readback.

Grade 2 §111.4(b)(1), (7)–(11), Texas regular Grades 3–5, California remaining verification and Washington OSPI publisher authentication are still open. This author-side handoff does not create canonical mappings or authorize curriculum activation. PR is draft/unmerged; do not modify learner data.
