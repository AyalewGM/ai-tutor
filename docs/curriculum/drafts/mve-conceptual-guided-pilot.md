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

**Unconditionally DEFAULT OFF at Workspace integration.** The guided
fraction/ratio components are draft illustrations and are not mounted from the
learner Workspace. A build-time flag or mutable `skill_name` match cannot
authorize either journey, including broad siblings or grade/jurisdiction
labels. There is no accepted server-owned exact capability identity for either
pilot; do not invent one from draft taxonomy.

The component itself returns null for independent assessment. Before changing
this default-off boundary, obtain independently approved mathematical scope,
pedagogical eight-stage readiness, an exact server-owned capability contract,
and a fresh Muse accessibility/browser review. Nothing in this PR enables
learner/mastery/scoring/history/persistence changes or a deployment.

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
