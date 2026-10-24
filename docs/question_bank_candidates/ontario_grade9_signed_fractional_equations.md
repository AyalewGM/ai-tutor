# Ontario Grade 9 signed and exact-fraction equation depth — author candidates v1

**Status: DRAFT_UNVERIFIED; NOT learner-visible; NOT approved for runtime registration or seeding.**

Refs: #488, #337, #446, #313. Compare draft #484 (independent quality factory for existing integer multi-step canonical families) before considering integration. This draft addresses materially different **non-integer exact solutions and negative-sign reasoning**, without replacing an already accepted generator. Existing canonical targets are `MATH.EE.EQUATION.TWO` and `MATH.EE.EQUATION.MULTISTEP`; these are authoring hints, **not** proof that official Ontario expectation mappings are approved.

Run `python -m scripts.author_ontario_linear_depth --count-per-family-mode 25 --output /tmp/ontario_signed_fractional_draft.json` for 400 original candidate instances across four reasoning structures and four separate modes (25 each). Coefficients and values are exact `Fraction` representations, and the independent test oracle uses SymPy to solve reconstructed equations from structured coefficients. No teacher handout wording, copyright-protected assessments, school data, or learner PII is copied.

| Proposed structure | Mathematical evidence | Misconception probe |
|---|---|---|
| Signed two-step, non-integer solution | Preserve equality under inverse operations and signed division | Omitting the additive constant |
| Fractional coefficient, non-integer solution | Multiply by the reciprocal after isolating term | Multiplying by the coefficient instead of its reciprocal |
| Negative-bracket distribution | Expand every term and retain sign | Dropping constant from negative distribution |
| Variables on both sides | Collect terms then isolate; handle a-c<0 | Ignoring the variable on the right |

Learner projection intentionally omits answers, explanations, hints, and misconception answers in all modes. Future guided delivery needs approved staged hints and accessibility behavior; independent/mastery must never receive them. Nothing in this draft grants a curriculum or mode authorization.

**Integration checklist (blocked until independent approvals)**: independent mathematical verdict on exact SHA and unseen seeds; independent pedagogy review on realistic prompts and remediations; authoritative Ontario source mapping when changing local skill mapping; backend typed rational-value scoring contract and deterministic non-repetition; frontend fraction-entry keyboard and screen-reader tests; synthetic PostgreSQL and browser E2E; security/QA/release gate; then an explicitly authorized staged student activation and rollback. Historical attempts, diagnostic results, and mastery events must remain unchanged.
