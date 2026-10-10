# Maryland cross-grade canonical scope candidates — r1

**Status:** DRAFT / not authoritative / not for runtime  
**Architecture basis:** [Issue #282 decision 6093222041](https://github.com/AyalewGM/ai-tutor/issues/282#issuecomment-6093222041)  
**Source-mapping context:** draft PR #325; all expectation relations remain `PROVISIONAL_NOT_ACCEPTED`.

## Purpose

The existing local seeds `M7.G.GEO` and `M7.SP.PROB` combine independently assessable mathematics now placed across Maryland Grades 7 and 8. Architecture determined that neither local seed may become one canonical atom or an equivalence alias. This artifact supplies eight bounded, machine-readable candidate cards for independent mathematical review.

| Proposed candidate | Boundary |
|---|---|
| `MATH.GEO.CIRCLE.CIRCUMFERENCE` | Linear measure around a circle via (C=2\pi r=\pi d) |
| `MATH.GEO.CIRCLE.AREA` | Square measure via (A=\pi r^2) |
| `MATH.GEO.ANGLE.RELATIONSHIPS` | Complementary, supplementary, vertical, adjacent and linear-pair reasoning |
| `MATH.GEO.TRIANGLE.ANGLE_RELATIONSHIPS` | Triangle interior-sum and exterior-angle reasoning |
| `MATH.PROB.EVENT.LIKELIHOOD_0_TO_1` | Interpret and compare likelihood on the inclusive probability scale |
| `MATH.PROB.EXPERIMENTAL.FREQUENCY` | Experimental probability, long-run relative frequency and expected-count uncertainty |
| `MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT` | Compare theoretical models with finite experimental evidence |
| `MATH.PROB.COMPOUND.SAMPLE_SPACE` | Two-stage sample spaces and bounded compound-event probabilities |

Each card includes inclusions, exclusions, prerequisite concepts, boundary examples, misconception probes and independent assessment criteria. Circle area and circumference are separate because they use different measures, formulas, units and misconception evidence. The three Grade 7 probability operations are separated from Grade 8 compound-event/sample-space evidence.

## Existing-code overlap

Repository generators already include circle circumference, circle area, complementary/supplementary angle, triangle missing-angle, experimental-probability, expected-count and theory-versus-experiment families. Those are recorded only as possible overlaps. A generator or passing test does not prove that a proposed canonical identity is mathematically complete, independently assessed or standards-aligned.

## Deliberate deferral

`M8.G.TRANS` and `M8.G.SIM` are not re-authored here. Architecture preserves them as legacy placement identifiers with no current Maryland Grade 8 equivalence. New placement-neutral transformation, congruence, dilation and similarity candidates require authoritative Integrated Algebra I/II scope reconciliation before Content authors definitions.

## Required review sequence

1. Independent Mathematical Review checks every card's correctness, boundaries, decomposition, prerequisites, examples, misconceptions and assessment evidence.
2. Architecture confirms or revises proposed code identity where overlap with historical broad identities remains.
3. Standards Mapping independently reviews expectation-to-skill relations; no relation is accepted from this artifact.
4. Muse evaluates implemented assessment and persistence behavior only after accepted contracts exist.
5. Devin/integration remains blocked from runtime activation.

Production `TAXONOMY`, historical UUIDs, variants and learner evidence are unchanged. This bundle is separate from PR #308 so its already-approved r5 definitions and Gate-4 validation head are not disturbed.
