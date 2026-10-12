# Grade 6 Comprehensive Gap Closure — Maryland Focus

**Status: DRAFT_UNVERIFIED · runtime_activation=false · no mastery writes**

This single Grade 6 PR covers all seven remaining high-value learning-package areas identified from the Maryland 2025 Grade 6 reconciliation, while reusing existing Mihur work instead of cloning it.

## Included topics

1. Fraction division reasoning
2. Expressions and early algebra
3. Contextual one-variable equations
4. Polygon decomposition and coordinate geometry
5. Prism and pyramid nets / surface area
6. Distribution, summary, and interpretation
7. Ratio and unit-rate strengthening

## Reuse-first boundary

This wave does **not** duplicate:

- `scripts/seed_grade6.py` Grade 6 identities;
- `W2-G6-RATIO-DOUBLE-LINE`;
- `W1-G6-FRACTIONAL-PRISM-VOLUME` and PR #345 deepening;
- histogram/IQR/box-plot work and PR #342;
- existing cube-net reasoning;
- existing M6.G.GEO area, volume, and coordinate-distance content.

Instead, it fills the remaining Grade 6 dimensions: conceptual fraction-division explanation, decomposed expression/equation evidence, irregular polygon decomposition, coordinate polygons, prism **and pyramid** nets, surface-area reasoning, distribution interpretation, and cross-representation ratio/rate reasoning.

## Mihur teaching design

Each package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

and a **Concrete/Context → Visual → Symbolic** progression.

Every package defines:

- at least four core reasoning goals;
- misconception-specific Socratic repair branches;
- fresh-seed repair exits;
- scaffold fading;
- deterministic guided practice;
- a disjoint unseen namespace for transfer;
- a hidden teacher oracle and answer-free learner payload;
- keyboard/screen-reader/reduced-motion/no-color-only accessibility requirements.

## Grade 6 concept depth

### Fraction division

Mihur does not teach “keep-change-flip” as an unexplained rule. Learners estimate quotient size, build measurement/sharing models, connect those models to an equation, and then explain why reciprocal multiplication gives the same result.

### Expressions

Learners distinguish coefficient, variable, exponent, and constant; evaluate with substitution and order of operations; and justify equivalence through the distributive property rather than merely simplifying.

### Equations

Learners model one-step Grade 6 contexts, solve with equality-preserving inverse operations, verify by substitution, and interpret the nonnegative rational solution in context and on a number line.

### Polygon / coordinate geometry

Learners decompose and recompose irregular figures, infer side lengths from coordinate differences, and distinguish perimeter from area.

### Nets / surface area

The package extends beyond cube nets to rectangular prisms and pyramids, requires face accounting, exact face areas, and a clear surface-area-versus-volume distinction.

### Statistics

Existing histogram/IQR/box-plot work is reused. This package focuses the remaining Grade 6 reasoning: five-number summaries, IQR, shape/center/spread/outliers, and choosing a useful summary for a contextual comparison.

### Ratios / rates

The existing ratio and double-number-line work is reused and strengthened across tables, double number lines, scaling, unit rates, and contextual interpretation.

## Standards

Maryland source candidates include:

- 6.NOS.A.1
- 6.AT.A.1–A.3
- 6.AT.B.5–B.7
- 6.AT.C.8
- 6.GR.A.1–A.4
- 6.DS.A.3–A.4
- 6.DS.B.5–B.6

These are **candidate mappings only**. This authoring agent does not self-approve Standards Mapping.

## Evidence files

- `package.json`: seven deep package contracts and review gates.
- `variants.py`: deterministic guided and independent variants for all seven concepts.
- `tests/test_grade6_gap_closure_wave1.py`: independent exact/structural oracle checks, public-answer isolation, mode separation, and hard runtime gates.

## Handoff

Independent Mathematical Review, Pedagogical Review, Standards Mapping, Architecture, Frontend/MVE, Assessment Backend, and Muse QA remain required.

This PR changes no canonical registry, production seed, learner route, assessment API, Attempt/DiagnosticAttempt/MasteryEvent history, or deployment state.

Suggested focused command:

`pytest -q tests/test_grade6_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and downstream browser/accessibility review before merge or activation.
