# Canonical middle-grades ratio, rate, and percent depth R2

This is a shared, draft-only question-depth sidecar. It responds to Issue #446
and PR #447's synthetic finding that Grade 6 ratio/unit-rate and Grade 7
percent/proportion rows are among the two-task persisted pools. That evidence
does **not** prove learner-visible availability, approved mode eligibility, or
production counts.

The package reuses ten family-to-skill relationships already declared in
`app/domains/ratios.py` and `app/domains/percent.py`. It creates no canonical
identity, curriculum mapping, jurisdiction bank, seed row, runtime import, or
mastery authority. In particular, it does not activate proposed DC or Virginia
Grade 8 mappings.

## Authored depth

- ten distinct mathematical structures rather than coefficient-only variants;
- exact `fractions.Fraction` teacher oracles and family-specific verification;
- concrete → visual → symbolic representation contracts;
- observed-answer-specific Socratic repair in guided mode only;
- diagnostic and guided sources exit to a different family in independent,
  hint-free mode;
- answer-free public payloads and keyboard/screen-reader/reduced-motion rules.

## Review boundary

`DRAFT_UNVERIFIED`, `runtime_activation=false`, and no learner or history writes.
Independent Mathematical and Pedagogical review must assess this exact head.
Assessment Backend owns trusted mode selection, scoring, persistence,
cross-session non-repetition, and history preservation. Frontend/MVE and Muse
own learner-visible interaction, rendering, browser accessibility, and
independent-assessment isolation. Standards and local mapping remain separate.
