# Maryland Grade 5 Comprehensive Gap Closure

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes**

This single PR deepens the existing Maryland Grade 5 curriculum pack across every Grade 5 strand without creating parallel canonical identities.

Maryland’s 2025 revised MCCRS Grade 5 standards are part of the state’s current revised mathematics program. MSDE states that the revised PreK–Grade 5 standards clarify expectations, emphasize strategies/representations, and strengthen foundational numeracy; the revised MCCRS were adopted July 29, 2025. This package uses the existing repository Maryland Grade 5 pack as the local source contract and keeps all standards mappings provisional.

## Included learning packages

1. Expressions and order of operations
2. Two-rule numerical patterns
3. Place value, powers of ten, multi-digit whole-number and decimal operations
4. Fraction addition/subtraction with unlike denominators
5. Fraction multiplication/division and scaling
6. Measurement conversion within a system
7. Volume and additive/composite volume reasoning
8. Coordinate-plane reasoning
9. Two-dimensional figure hierarchy and classification

## Why this wave is needed

The existing Maryland Grade 5 pack contains all major strand buckets, but several entries are still practice inventories rather than deep teaching experiences. For example, the current `MD5.OA.EXPRESSIONS` problem inventory is largely decimal-operations and powers-of-ten practice even though the stated skill concerns grouping symbols and expression writing. Similar depth issues exist around pattern relationships, fraction scaling, composite volume, coordinate interpretation, and inclusive shape hierarchies.

This PR strengthens those experiences rather than replacing the existing curriculum pack.

## Mihur learning architecture

Every package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

and a **Concrete/Context → Visual → Symbolic** progression.

Each package includes:
- at least four core reasoning goals;
- misconception-specific Socratic repair branches;
- fresh-number or contrast-case repair tasks;
- scaffold fading;
- deterministic guided variants;
- a distinct unseen independent namespace;
- hidden teacher-oracle data and answer-free learner projection;
- keyboard, screen-reader, reduced-motion, text-equivalent, focus, and no-color-only accessibility requirements.

## Reuse-first boundaries

This wave reuses, rather than duplicates:

- `docs/curriculum/packs/md-grade5-mccrs-2026_27.json`;
- existing decimal/place-value canonical families;
- whole-number multiplication/division families;
- `W1-G4-FRACTION-EQUIVALENCE`;
- `W2-G5-DECIMAL-PLACE-VALUE`;
- fraction multiply/divide families;
- measurement conversion and volume families;
- coordinate-plane and shape-classification families.

No canonical ID is created or broadened here. Architecture and independent reviewers own any later identity changes.

## Package depth by topic

### Expressions
Learners translate words to numerical expressions, use grouping symbols intentionally, predict before evaluating, and distinguish structural equivalence from coincidental equal value.

### Patterns
Learners generate two rules, compare corresponding terms, organize paired values, and justify a relationship from multiple pairs instead of guessing from one example.

### Number and decimal operations
Learners connect powers of ten to place value, estimate before operating, use place-value explanations for multi-digit multiplication/division and decimal operations, and reject algorithmic answers that fail magnitude checks.

### Fraction addition/subtraction
Learners construct equivalent fractions from the same whole, reason with a common unit, include mixed-number renaming, estimate, and interpret answers in context.

### Fraction multiplication/division
Learners reason about scaling before multiplying and distinguish “how many groups?” from “how much in each group?” division structures. Reciprocal procedures must be connected to a model.

### Measurement conversion
Learners reason from relative unit size and multiplicative conversion factors, preserve units, and solve multi-step contexts rather than memorizing directional arrows.

### Volume
Learners build layers of unit cubes, connect (l×w×h) to base-area-times-height, distinguish volume from surface area, and reason additively about composite rectangular-prism volumes.

### Coordinate plane
Learners interpret origin and axes, preserve ordered-pair meaning, graph/read first-quadrant points, and connect coordinates to paired contextual quantities.

### Shape hierarchy
Learners classify by defining attributes, reason with inclusive categories, and answer always/sometimes/never hierarchy questions instead of treating shapes as mutually exclusive labels.

## Standards and provenance

Repository standard candidates are the existing Maryland Grade 5 strands:
- 5.OA
- 5.NBT
- 5.NF
- 5.MD
- 5.G

The package does **not** claim independent expectation-level acceptance. Standards Mapping must review against the current MSDE Grade 5 crosswalk and companion guide.

External source used for scope/provenance:
- Maryland State Department of Education, 2025 Revised MCCRS Mathematics, Grade 5 resources: https://msde.maryland.gov/academics-0/curriculum-academic-standards/mathematics

All new questions, explanations, scenarios, diagnostics, and transfer structures are original Mihur-authored content. No released Maryland assessment item text, copyrighted worksheet, teacher PDF, or child identifying data is included.

## Evidence and gates

Files:
- `package.json`: nine deep learning-package contracts.
- `variants.py`: deterministic guided and unseen variants for all nine packages.
- `tests/test_grade5_gap_closure_wave1.py`: exact and structural oracle checks, mode isolation, answer isolation, and fail-closed runtime gates.

Current state:

- Authored: YES
- Draft deterministic variants/tests: YES
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

`pytest -q tests/test_grade5_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and independent Math → Pedagogy → Standards/Architecture → Frontend/MVE → Assessment Backend → Muse review before activation.
