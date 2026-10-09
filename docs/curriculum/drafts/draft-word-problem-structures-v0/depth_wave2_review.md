# Wave 2 — draft depth generators for foundational mathematics through algebra

**Review status:** `DRAFT_UNVERIFIED / PENDING`; no canonical IDs,
curriculum mappings, publication, mastery evidence, or student activation.

This batch adds 16 mathematically distinct **problem structures** to the
draft-only generator experiment in PR #319. The default preview produces
8 deterministic parameter variations of each structure (**128 variants**).

| Provisional area | Structures | Intended depth |
| --- | --- | --- |
| Foundational number sense | Place-value composition; value of a digit; missing addend; regrouping subtraction | Base-ten manipulatives, inverse operations, regrouping |
| Fractions | Equivalent fractions; same-denominator comparison; unlike-denominator addition; fraction of a remaining collection | Fraction strips, common partitions, part/whole reasoning |
| Ratios and proportional reasoning | Equivalent ratios; proportional table; percent increase; scale drawing | Batch models, double number lines, proportional tables |
| Algebra | Distributive property; two-step equation; budget inequality; slope between two points | Split arrays, balance diagrams, inequality number lines, coordinate grids |

Every generated item includes three progressive hints, a concrete-to-visual-to-symbolic
teaching sequence, an exact answer, a misconception-specific distractor and
corrective feedback, and a transfer/inverse-check prompt.

```bash
python -m scripts.draft_depth_generators_wave2 --seed 20261009 --variants 8 > /tmp/mihur-depth-wave2.json
pytest -q tests/test_draft_depth_generators_wave2.py
```

## Evidence boundaries

- The generator file is **not** imported by the production family registry.
- Exact-answer oracle tests validate arithmetic contracts, not grade suitability,
  effectiveness of scaffolding, accessibility of proposed visual models, or
  standards alignment.
- The visual-model text is a storyboard/specification, **not** a rendered
  interactive animation.
- Generated variants are not independently reviewed teaching items, and a
  variation count must not be represented as a canonical skill count.
- Reviewers must examine mathematical semantics, ambiguity, distractor
  plausibility, representation accuracy, misconception feedback, age
  appropriateness, and accessibility.
- Accepted content may only be mapped to **independently reviewed** canonical
  skills. Historical student mastery remains unchanged.

## Review handoff

Mathematical Review (#293): validate mathematical structure and edge cases.
Curriculum Standards Mapping: independently align to official expectations,
recording verified source identifiers rather than inferring from grade labels.
Muse QA: review pedagogy and verify exact oracle tests and safety boundaries.
Engineering Lead (#278): coordinate activation only after all independent gates.
