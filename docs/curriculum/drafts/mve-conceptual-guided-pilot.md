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


## Learning Package Production handoff — depth-before-breadth task contracts

These contracts are **DRAFT_UNVERIFIED content inputs** for the Interactive MVE
Agent. They do not authorize routing, scoring, mastery, or learner-history writes.
The existing bounded mathematical helpers remain unchanged.

### Fraction equivalence — required learner evidence

**Prediction before reveal**

Present `2/3 = ?/9` without showing the completed second bar. Capture one of:

- `SAME_VALUE`
- `SECOND_IS_LARGER`
- `SECOND_IS_SMALLER`

Then ask for a one-sentence reason referring to the **same whole** and equal
partition size. The prediction is practice evidence only.

**Structured explanation after manipulation**

Require all three fields before considering the guided explanation complete:

1. scale factor from 3 to 9;
2. numerator operation using the **same** scale factor;
3. equality statement that both fractions name the same amount of one whole.

For the pilot item, the deterministic target is scale factor `3`, numerator
`6`, and an equality claim equivalent to `2/3 = 6/9`.

**Misconception-specific repair exits**

- `DENOMINATOR_ONLY_SCALE`: learner gives `2/9`.
  - Socratic prompt: "If each third is split into 3 equal pieces, how many ninths
    come from each of the 2 shaded thirds?"
  - Different repair item: `3/4 = ?/8`.
  - Verified exit: learner supplies scale factor `2`, numerator `6`, and
    explains that numerator and denominator are multiplied by the same factor.
- `ADDITIVE_SCALE`: learner gives `8/9` or describes adding rather than scaling.
  - Socratic prompt: "Did the number of equal pieces grow by adding the same
    amount, or by splitting every old piece into the same number of new pieces?"
  - Different repair item: `1/2 = ?/6`.
  - Verified exit: scale factor `3`, numerator `3`, multiplicative explanation.
- `SAME_NUMERATOR_MEANS_EQUIVALENT`: learner treats `2/3` and `2/9` as equal.
  - Socratic prompt: "If the same whole is cut into more equal pieces, is one
    piece larger or smaller?"
  - Different repair item: compare `2/5` and `2/10`.
  - Verified exit: identifies `2/5 > 2/10` and explains why equal numerators
    do not imply equal fraction values when denominators differ.

**Unseen transfer**

Use a new representation and numbers: "A strip has 12 equal cells. Shade a
fraction equivalent to `3/4`, then write the fraction and justify the scaling."
Expected evidence: `9/12`, scale factor `3`, same-whole explanation. Do not
pre-fill the target numerator or display a completed fraction bar before response.

### Fraction modeling-versus-independent-evidence boundary

The completed `6/9` fraction bar may be shown during **guided modeling** after
the learner has locked a prediction. It must not count as independent solution
evidence for the missing numerator or for transfer. Any response collected while
that completed bar is visible is guided/manipulative evidence only.

For independent-like repair or transfer within this guided pilot, hide the
completed target bar and require the learner to reconstruct the scale factor,
target numerator, and same-whole justification before verification. Do not award
mastery from either state.

### Ratio partition — required learner evidence

**Prediction before reveal**

Before counters are grouped, ask: "If 20 counters are shared in the ratio
`2:3`, will the first share be less than, equal to, or greater than half of the
whole?" Capture the choice plus a brief parts-based reason.

**Structured explanation after manipulation**

Require:

1. total ratio parts `2+3=5`;
2. common unit value `20/5=4`;
3. first share `2×4=8`;
4. recomposition `8+12=20`.

**Misconception-specific repair exits**

Learner-facing repair prompts must state only the **new whole and ratio**. They
must **not** include the expected common unit, shares, recomposition, or any
answer-formatted example. Expected values below are server/test-side verification
targets only.

Every repair response must independently provide:

1. total ratio parts;
2. common unit value;
3. first share;
4. second share;
5. recomposition of both shares to the stated whole.

- `WHOLE_AS_UNIT_VALUE`: learner treats 20 as one ratio part.
  - Socratic prompt: "How many equal ratio parts make the whole before any share
    is assigned?"
  - Learner-facing repair item: "Share 24 in the ratio 1:3. Find both shares and
    show how they recombine to 24."
  - Hidden verification target: `4` total parts, common unit `6`, shares
    `6` and `18`, recomposition `6+18=24`.
- `PART_COUNT_AS_SHARE`: learner answers `2` or `3` instead of a quantity.
  - Socratic prompt: "Does the ratio tell the number of counters directly, or the
    number of equal-sized parts each person receives?"
  - Learner-facing repair item: "Share 30 in the ratio 2:3. Find both shares and
    show how they recombine to 30."
  - Hidden verification target: `5` total parts, common unit `6`, shares
    `12` and `18`, recomposition `12+18=30`.
- `UNEQUAL_UNIT_PARTS`: learner assigns different values to ratio parts.
  - Socratic prompt: "What must be true about the size of every ratio part?"
  - Learner-facing repair item: "Share 28 in the ratio 3:4. Find both shares and
    show how they recombine to 28."
  - Hidden verification target: `7` total parts, common unit `4`, shares
    `12` and `16`, recomposition `12+16=28`.

A repair is not verified by matching the two final shares alone. The common-unit
reasoning and exact recomposition must also agree with the hidden contract.

**Unseen transfer**

"A 35-minute practice session is split between warm-up and drills in ratio
`2:5`. Determine both times and justify the partition." Expected evidence:
`7` equal parts, unit `5` minutes, `10` minutes warm-up, `25` minutes
drills, recomposition `35`. This changes context and quantities and must not
reuse the original counter grouping.

### Scaffold-fading contract for MVE implementation

After a verified structured explanation, the next guided item should hide the
completed visual and computed intermediate values until the learner responds.
Any diagnosed error may restore the relevant scaffold. This content contract
does not prescribe React state mechanics; MVE/Frontend owns that implementation.

No item in this section may award mastery. A future trusted Assessment Backend
must independently authorize any unseen scoring contract.
