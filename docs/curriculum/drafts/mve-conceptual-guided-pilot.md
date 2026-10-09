# Conceptual guided MVE pilot — review gated

This PR adds two **working React guided teaching activities**, not a
curriculum-wide activation. Both reuse the existing workspace and visual
renderer, provide deterministic misconception feedback, and never award
mastery.

- Fraction equivalence: `2/3 = ?/9`, with two fraction bars and progressive
  conceptual prompts.
- Ratio partition: share 20 counters in ratio 2:3, with equal-group
  manipulatives and guided unit reasoning.

## Release safety

**Disabled by default.** The workspace mounts neither activity unless the
build-time environment variable `VITE_ENABLE_CONCEPT_GUIDED_PILOT=true` is
explicitly set. This flag must remain unset for production until the owner
authorizes a reviewed pilot. Even with the flag, lessons only mount in
`GUIDED_PRACTICE` or `REMEDIATION` when the skill label matches, and the
component itself returns null for `independentAssessment=true`.

Skill-name matching is a **temporary pilot adapter**, not a validated
canonical skill mapping. Before wider activation, replace it with a reviewed
canonical skill ID mapping and server-authorized lesson assignment.

## Verification

```bash
cd frontend
npm run test:mve
npm run check:mve
```

The mathematical helpers are pure and tested across their bounded inputs.
No personal data is recorded, no student mastery is modified, and guided
checks do not count as independent mastery evidence.

Independent mathematical review, accessibility QA, child-usability testing,
curriculum mapping where claimed, and explicit owner release authorization
remain required. The UI does not automatically ingest draft content from
PR #319.
