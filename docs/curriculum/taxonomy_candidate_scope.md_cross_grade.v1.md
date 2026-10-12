# Maryland cross-grade canonical scope candidates — r3

**Status:** DRAFT / not authoritative / not for runtime  
**Architecture basis:** [Issue #282 decision 6094147290](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6094147290)  
**Independent review basis:** [PR #326 r2 review 6094993405](https://github.com/AyalewGM/ai-tutor/pull/326#issuecomment-6094993405)  
**Source-mapping context:** draft PR #325; all expectation relations remain `PROVISIONAL_NOT_ACCEPTED`.

## Purpose and r3 disposition

The local seeds `M7.G.GEO` and `M7.SP.PROB` combine independently assessable mathematics now placed across Maryland Grades 7 and 8. They remain preserved local composites, never canonical atoms or equivalence aliases.

Independent Mathematical Review approved five r1 cards, then approved complement, supplement, and vertical-angle equality in r2. It requested three bounded corrections: distinguish missing-part from missing-whole adjacent-angle evidence, make the probability 0/1 converses valid only within an explicit model class, and state the stable repeated-trial assumptions behind long-run relative-frequency stabilization. This r3 changes only those three cards.

The eight unchanged mathematically approved cards remain DRAFT:

- `MATH.GEO.CIRCLE.CIRCUMFERENCE`
- `MATH.GEO.CIRCLE.AREA`
- `MATH.GEO.ANGLE.COMPLEMENT`
- `MATH.GEO.ANGLE.SUPPLEMENT`
- `MATH.GEO.ANGLE.VERTICAL_EQUALITY`
- `MATH.GEO.TRIANGLE.ANGLE_RELATIONSHIPS`
- `MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT`
- `MATH.PROB.COMPOUND.SAMPLE_SPACE`

The three corrected r3 cards require limited independent re-review:

| Draft candidate | r3 boundary |
|---|---|
| `MATH.GEO.ANGLE.ADJACENT_ADDITION` | Missing part requires a supplied whole; missing whole requires every nonoverlapping constituent part |
| `MATH.PROB.EVENT.LIKELIHOOD_0_TO_1` | The 0/impossible and 1/certain converses are bounded to finite discrete models whose elementary outcomes all have positive probability |
| `MATH.PROB.EXPERIMENTAL.FREQUENCY` | Long-run stabilization is stated only for independent repeated trials under unchanged conditions with constant event probability |

## Angle composition and identity safety

`MATH.GEO.ANGLE.RELATIONSHIPS` remains absent as a proposed atom. The Maryland angle-relationships outcome is only a fail-closed reporting `ALL_OF` over the four bounded members. The profile receives no row, UUID, variant, attempt, diagnostic attempt, mastery event, evidence propagation, or duplicate credit.

The adjacent-addition card now has two explicit part-whole structures:

1. the whole/total is supplied and one constituent part is missing;
2. every nonoverlapping constituent part is supplied and the whole is missing.

Adjacency alone supplies no 90°, 180°, or 360° total.

## Probability boundaries

The likelihood card is explicitly limited to finite discrete models in which every elementary outcome has positive probability. Within that boundary, probability 0 is equivalent to impossibility and probability 1 is equivalent to certainty. Continuous/general spaces where probability-zero events may still occur are excluded. Fraction and decimal probabilities remain in [0,1], while percent probabilities remain in 0%–100%.

Experimental frequency remains successes divided by trials. Qualitative stabilization applies only to independent repeated trials conducted under unchanged conditions with constant event probability. A changed spinner, adaptive process, or dependent sequence cannot be treated as evidence for stabilization to one unchanged probability without a different model. Expected-count reasoning `n × p` remains excluded from mastery and appears only as a non-credit misconception contrast.

## Deliberate deferral

`M8.G.TRANS` and `M8.G.SIM` are not re-authored here. Architecture preserves them as legacy placement identifiers with no current Maryland Grade 8 equivalence. New placement-neutral transformation, congruence, dilation and similarity candidates require authoritative Integrated Algebra I/II reconciliation before Content authors definitions.

## Required review sequence

1. Independent Mathematical Review re-reviews only the three corrected r3 cards at the exact new head.
2. Architecture identity decisions remain binding; no generator literal becomes alias authority.
3. Standards Mapping independently reviews expectation-to-skill relations; no relation is accepted here.
4. Muse evaluates implemented assessment and persistence behavior only after accepted contracts exist.
5. Devin/integration remains blocked from runtime activation.

Production `TAXONOMY`, historical UUIDs, local-seed meanings, variants and learner evidence remain unchanged. PR #308 is untouched.
