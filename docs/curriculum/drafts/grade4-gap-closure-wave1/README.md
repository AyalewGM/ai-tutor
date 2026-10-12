# Maryland Grade 4 Comprehensive Gap Closure

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes**

This single PR deepens every current Maryland Grade 4 strand while preserving the existing Grade 4 curriculum pack and shared canonical mathematics.

## Included learning packages

1. Multiplicative comparison
2. Multi-step four-operation word problems and remainder interpretation
3. Factors, multiples, and patterns
4. Multi-digit place value and rounding
5. Multi-digit multiplication
6. Whole-number division with remainders
7. Fraction equivalence, comparison, and operations
8. Decimal notation for fractions
9. Measurement and conversion
10. Angles, lines, and shape classification

## Reuse-first design

This wave reuses:
- `docs/curriculum/packs/md-grade4-mccrs-2026_27.json`
- PR #336 deep fraction-equivalence reasoning
- `draft-g45-fractions-pilot-v0`
- shared whole-number, factor/multiple, fraction, decimal, measurement, angle, line, and shape families.

It does not create new canonical IDs, broaden existing atoms, or rewrite historical curriculum mappings.

## Mihur teaching architecture

Each package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

and a **Concrete/Context → Visual → Symbolic** progression.

Every package includes:
- at least four reasoning goals;
- misconception-specific Socratic repair branches;
- fresh-number or contrast-case repair exits;
- scaffold fading;
- deterministic guided practice;
- a separate unseen independent namespace;
- hidden teacher-oracle data and answer-free learner projection;
- accessibility requirements for keyboard, screen reader, text-equivalent diagrams, reduced motion, focus preservation, and no color-only meaning.

## Topic depth

### Multiplicative comparison
Learners distinguish “times as many” from “more than,” connect tape/array models to multiplication equations, and solve both product and unknown-factor comparison structures.

### Multi-step word problems
Learners choose operations from situation structure rather than keywords, track intermediate quantities and units, estimate before calculating, and interpret remainders according to context.

### Factors, multiples, and patterns
Learners find factor pairs systematically, distinguish factors from multiples, identify prime/composite structure, and generalize numeric or shape patterns.

### Place value
Learners read/write/compare large whole numbers, reason about ten-times relationships, and round using magnitude and number-line position rather than a memorized digit rule.

### Multiplication
Learners connect area models and partial products to the distributive property and standard algorithm, including 4-digit×1-digit and 2-digit×2-digit cases.

### Division
Learners use place-value/area/partial-quotient reasoning, produce quotient and remainder, verify by multiplication, and interpret the remainder in context.

### Fractions
Existing Grade 4–5 fraction-equivalence work is reused. This package adds benchmark comparison, like-denominator operations including mixed-number reasoning, and fraction-by-whole multiplication with explanation.

### Decimal fractions
Learners connect tenths/hundredths to fractions, place decimals on a number line, compare by place value, and translate between fractions with denominator 10/100 and decimal notation.

### Measurement
Learners reason from relative unit size, convert multiplicatively, preserve units, and solve contextual measurement problems.

### Angles, lines, and shapes
Learners measure/sketch angles, compose/decompose angle measures additively, recognize parallel/perpendicular relationships and symmetry, and classify shapes using defining properties rather than appearance.

## Standards and provenance

The current Maryland Grade 4 repository pack groups expectations under:
- 4.OA
- 4.NBT
- 4.NF
- 4.MD
- 4.G

These remain **candidate scope references**, not independently approved mapping claims.

All new examples, explanations, diagnostics, and transfer tasks are original Mihur-authored material. No released assessment items, proprietary worksheets, teacher PDFs, or child-identifying data are included.

## Evidence and review gates

Files:
- `package.json`: ten deep package contracts
- `variants.py`: deterministic guided/independent variants
- `tests/test_grade4_gap_closure_wave1.py`: exact/structural checks, answer isolation, namespace isolation, and hard runtime gates

Current state:
- Authored: YES
- Draft variants/tests: YES
- Production wired: NO
- Standards accepted: NO
- Math accepted: NO
- Pedagogy accepted: NO
- Architecture accepted: NO
- MVE implemented: NO
- Assessment backend wired: NO
- Muse QA: NO
- Runtime activated: NO
- Deployed/pilot-ready: NO

Suggested focused command:

`pytest -q tests/test_grade4_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and independent Math → Pedagogy → Standards/Architecture → Frontend/MVE → Assessment Backend → Muse review before activation.
