# Maryland cross-grade canonical scope candidates — r2

**Status:** DRAFT / not authoritative / not for runtime  
**Architecture basis:** [Issue #282 decision 6094147290](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6094147290)  
**Independent review basis:** [PR #326 review 6094115259](https://github.com/AyalewGM/ai-tutor/pull/326#issuecomment-6094115259)  
**Source-mapping context:** draft PR #325; all expectation relations remain `PROVISIONAL_NOT_ACCEPTED`.

## Purpose and r2 disposition

The local seeds `M7.G.GEO` and `M7.SP.PROB` combine independently assessable mathematics now placed across Maryland Grades 7 and 8. They remain preserved local composites, never canonical atoms or equivalence aliases.

Independent Mathematical Review approved five r1 cards for mathematical scope and requested changes to three. Architecture then directed Content to replace the broad angle candidate with four bounded components, correct likelihood-scale semantics, and remove expected-count mastery from experimental frequency. This r2 implements only that handoff.

The five unchanged, mathematically approved cards remain DRAFT:

- `MATH.GEO.CIRCLE.CIRCUMFERENCE`
- `MATH.GEO.CIRCLE.AREA`
- `MATH.GEO.TRIANGLE.ANGLE_RELATIONSHIPS`
- `MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT`
- `MATH.PROB.COMPOUND.SAMPLE_SPACE`

The six changed or new cards require limited independent re-review:

| Draft candidate | r2 boundary |
|---|---|
| `MATH.GEO.ANGLE.COMPLEMENT` | Complementary-angle reasoning from an explicit 90° total |
| `MATH.GEO.ANGLE.SUPPLEMENT` | Supplementary reasoning from an explicit 180° total; linear pair is an evidence context |
| `MATH.GEO.ANGLE.VERTICAL_EQUALITY` | Equality of opposite, nonadjacent angles at an intersection |
| `MATH.GEO.ANGLE.ADJACENT_ADDITION` | Angle addition only with a supplied whole, total, or partition |
| `MATH.PROB.EVENT.LIKELIHOOD_0_TO_1` | Fraction/decimal bounds [0,1], percent bounds 0%–100%, and precise equal-likelihood semantics |
| `MATH.PROB.EXPERIMENTAL.FREQUENCY` | Successes/trials and long-run stabilization; expected count is excluded from mastery |

## Angle composition and identity safety

`MATH.GEO.ANGLE.RELATIONSHIPS` is removed as a proposed atom. The Maryland angle-relationships outcome is represented only as a fail-closed reporting `ALL_OF` over the four bounded members. The profile receives no row, UUID, variant, attempt, diagnostic attempt, mastery event, evidence propagation, or duplicate credit.

The existing reviewed candidate registry in PR #308 and its inactive production taxonomy do not confirm persisted/reviewed complement or supplement identities. Accordingly, the familiar complement/supplement spellings in this artifact remain DRAFT candidates; generator-family literals are overlap evidence only and confer no identity or alias authority.

## Probability separation

Likelihood representations are now explicit: fractions and decimals lie in [0,1], while percent notation lies from 0% through 100%. For one event and its complement, probability 0.5 means equal likelihood; two distinct events may be equally likely at probabilities other than 0.5.

Experimental frequency remains successes divided by trials plus qualitative long-run stabilization. Expected-count reasoning `n × p` is a distinct competency. The expectation-versus-guarantee example remains only as a non-credit misconception contrast and cannot establish expected-count mastery.

## Deliberate deferral

`M8.G.TRANS` and `M8.G.SIM` are not re-authored here. Architecture preserves them as legacy placement identifiers with no current Maryland Grade 8 equivalence. New placement-neutral transformation, congruence, dilation and similarity candidates require authoritative Integrated Algebra I/II reconciliation before Content authors definitions.

## Required review sequence

1. Independent Mathematical Review re-reviews only the six changed/new r2 cards at the exact new head.
2. Architecture identity decisions remain binding; no generator literal becomes alias authority.
3. Standards Mapping independently reviews expectation-to-skill relations; no relation is accepted here.
4. Muse evaluates implemented assessment and persistence behavior only after accepted contracts exist.
5. Devin/integration remains blocked from runtime activation.

Production `TAXONOMY`, historical UUIDs, local-seed meanings, variants and learner evidence remain unchanged. PR #308 is untouched.
