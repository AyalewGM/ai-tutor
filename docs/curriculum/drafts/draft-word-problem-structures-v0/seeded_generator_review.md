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
