# Draft seeded word-problem generator wave

**Status:** `DRAFT_UNVERIFIED` — independent mathematical review and QA required.

This batch extends the existing 48 fixed, distinct word-problem structures and 48
diagnostic/remediation pathways in PR #319 with a **separate, draft-only**
deterministic generator experiment.

## What is implemented

- **18 generators** across six provisional domains (three per domain).
- **108 reproducible variants** at the default six variants per structure.
- Exact rational or integer answers, three progressive hints, worked solutions,
  a misconception-specific plausible wrong answer and corrective feedback.
- Concrete/visual representation prompts and a separate inverse/substitution
  check for each generated problem.
- Independent exact arithmetic oracles and mathematical boundary tests run
  across several seeds.

The generator is deliberately isolated in
`scripts/draft_word_problem_generators.py`. It does **not** change the canonical
taxonomy, generator registry, student session runtime, historical mastery,
curriculum packs, or any database.

### Preview / review

```bash
python -m scripts.draft_word_problem_generators --seed 20261009 --variants 6 > /tmp/mihur-draft-variants.json
pytest -q tests/test_draft_word_problem_generators.py
```

A new seed produces a new deterministic selection of parameters; a fixed seed
reproduces the same content. `--variants` supports 1–50 variants per
structure. These are *parameter variations*, not 108 distinct pedagogical
structures or 108 independently reviewed questions.

| Provisional domain | Structures |
| --- | --- |
| Additive reasoning | Start unknown, comparison difference, two changes |
| Multiplicative reasoning | Equal groups, capacity remainder, two-stage groups |
| Fractions | Fraction of set, unknown whole, like-denominator addition |
| Ratios and rates | Unit price, percent discount, fixed fee plus rate |
| Geometry and measurement | Rectangle perimeter, area, prism volume |
| Algebraic reasoning | Unknown count with fixed fee, linear sequence, two ticket types |

## Independent review checklist

1. Check each mathematical structure for semantic accuracy and grade suitability,
   including edge cases not exercised by the example seed.
2. Inspect distractors for mathematical plausibility **and** ensure they are
   never equal to the correct answer.
3. Evaluate all generated prompts for ambiguous units, inappropriate real-world
   assumptions, and repetitive contexts.
4. Review the hints for Socratic sequencing, not premature answer disclosure.
5. Validate whether proposed visual models can be implemented accessibly with
   manipulatives/animations and a text alternative.
6. Reconcile any accepted mathematical skill with the independently approved
   canonical taxonomy. Do not invent or infer skill IDs.
7. Review official curriculum expectations separately; generator existence is
   not evidence of standards alignment.
8. Only after mathematical review, curriculum review as applicable, Muse QA,
   and explicit engineering approval should any generator be considered for
   runtime integration. Student mastery remains untouched.

**Important:** Passing tests validates specified arithmetic invariants, not
pedagogical effectiveness, originality clearance of external sources, curriculum
coverage, or mastery-assessment validity.

## Conceptual depth added in the same PR

`seeded_teaching_depth.draft.json` now defines **18 original teaching
blueprints**, one per generator structure. Each contains:

- a mathematical invariant that the learner must understand;
- concrete, visual and symbolic representations;
- an alternative strategy that is not simply a repeated solution;
- a misconception-specific teaching intervention;
- three Socratic prompts and differentiated support after repeated errors;
- an independently authored transfer problem, answer and explanation rubric;
- a textual alternative to proposed animations.

`tests/test_draft_seeded_teaching_depth.py` verifies complete structural
linkage, unique teaching concepts, independent transfer questions and exact
transfer answer keys. These are **lesson specifications**, not live
interactive animations or proof of student mastery.

### Production acceptance criteria (per approved skill)

| Dimension | Minimum evidence before claiming deep coverage |
| --- | --- |
| Mathematical identity | Independently approved canonical skill definition and prerequisites |
| Practice | Multiple distinct reasoning structures, bounded seeded generators, exact oracles |
| Diagnostics | Meaningful misconception distractors with mathematically accurate feedback |
| Instruction | Concrete, visual, symbolic and alternative methods, with accessible text |
| Adaptation | Distinct response to repeated mistakes; avoid disclosing answers prematurely |
| Assessment | Unseen transfer with explanation and independent verification |
| Quality | Independent mathematical review, curriculum review where claimed, Muse QA |
| Release | Explicit owner/engineering approval, isolation and no historical mastery rewrite |

No row should be marked verified solely because a generator exists or tests pass.

## Conceptual expansion wave: 12 more structures

The isolated `scripts/draft_conceptual_depth_generators.py` adds
12 **new reasoning structures** across four high-value domains:

| Domain | Distinct conceptual structures |
| --- | --- |
| Fractions | Equivalence by scaling, comparing unlike fractions, adding unlike fractions |
| Signed numbers | Temperature change below zero, subtracting a negative, distance on a number line |
| Proportional reasoning | Recipe scaling, partitioning by ratio, recovering original price after a discount |
| Algebra | Two-sided linear equations, signed slope from two points, linear function evaluation |

At the default six seeded variations each, this wave yields 72 additional
parameterized draft items. Unlike merely increasing the variant count,
these 12 structures require **12 different conceptual invariants, visual
models, Socratic sequences and misconception responses**.

Each item provides a deterministic exact answer, plausible wrong answer
with feedback, three non-answer-revealing teaching hints, alternate
solution strategy, independent arithmetic check and explicit mastery
requirements. The adaptive responses are *specifications*, not a live
adaptive tutoring engine. The generator does not grant mastery.

```bash
python -m scripts.draft_conceptual_depth_generators --seed 20261009 --variants 6 > /tmp/mihur-concept-wave.json
pytest -q tests/test_draft_conceptual_depth_generators.py
```

The independent tests recompute answers from operands for all 12
structures over multiple seeds, reject diagnostic collisions and verify
structural support. Mathematical reviewers must still evaluate whether
the distractors, contexts, explanations and conceptual boundaries are
pedagogically correct; automated arithmetic tests are not approval.

**CI caveat:** The preceding PR head had passing code/security checks,
but its latest CI failed because GitHub Actions hit Docker Hub
unauthenticated pull limits (HTTP 429) while initializing Postgres and
building base images. This is an infrastructure dependency failure,
not evidence that the new mathematics is invalid. The new exact-head
CI must be checked separately.
