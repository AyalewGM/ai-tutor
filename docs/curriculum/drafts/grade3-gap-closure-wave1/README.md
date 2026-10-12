# Maryland Grade 3 Comprehensive Gap Closure

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes**

This single PR deepens the complete Maryland Grade 3 strand set while preserving the existing F-024 Grade 3 vertical slice.

## Included learning packages

1. Multiplication as equal groups and arrays
2. Division as sharing and grouping
3. Multiplication/division properties and fact families
4. Place value, rounding, and addition/subtraction within 1000
5. Fractions as numbers
6. Time and elapsed time
7. Scaled picture and bar graphs
8. Area and perimeter
9. Shape attributes and quadrilateral reasoning

## Reuse-first design

The following existing work is preserved and reused rather than reauthored:

- PR #92 / F-024 Maryland Grade 3 vertical slice
- equal-groups multiplication
- equal-sharing division
- unit-fraction foundations
- rectangle-area foundations
- docs/curriculum/packs/md-grade3-mccrs-2026_27.json
- shared canonical place-value, time, graph/data, area/perimeter, and geometry families

This PR creates no new canonical IDs and does not reinterpret historical learner evidence.

## Mihur teaching architecture

Each package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

with a **Concrete/Context → Visual → Symbolic** progression.

Every package includes:
- at least four reasoning goals;
- misconception-specific Socratic repair routes;
- fresh-number or contrast-case repair;
- scaffold fading;
- deterministic guided variants;
- a distinct unseen independent namespace;
- hidden teacher-oracle data and answer-free learner projection;
- keyboard, screen-reader, reduced-motion, text-equivalent visual state, focus, and no-color-only accessibility requirements.

## Topic depth

### Multiplication
Learners connect equal groups, repeated addition, arrays, and equations and reason about unknown-factor as well as unknown-product contexts.

### Division
Learners distinguish sharing from grouping/measurement division, connect division to arrays and multiplication fact families, and verify quotients by multiplication.

### Fact families and properties
Learners use commutative, associative, and distributive reasoning to derive facts rather than memorize disconnected products/quotients.

### Place value
Learners represent hundreds/tens/ones flexibly, round using benchmark numbers, regroup without changing value, and estimate/check addition and subtraction within 1000.

### Fractions
Learners treat fractions as numbers, not just shaded pieces: same-whole area models, number-line locations, equivalent fractions, and benchmark comparisons are all required.

### Time
Learners tell/write time to the minute, model elapsed time, cross hour boundaries, and explain addition/subtraction strategies.

### Data
Learners read and construct scaled picture/bar graphs, use legends/scales, and solve comparison questions rather than reading bar height as raw count.

### Area and perimeter
Learners distinguish square units from linear units, connect arrays to rectangle area, find perimeter, and reason about missing sides and same-area/different-perimeter situations.

### Shapes
Learners classify by defining attributes, recognize inclusive quadrilateral categories, and partition shapes into equal-area parts.

## Standards and provenance

The current Maryland Grade 3 repository pack groups expectations under:
- 3.OA
- 3.NBT
- 3.NF
- 3.MD
- 3.G

These remain candidate scope references pending independent Standards Mapping. This authoring PR does not claim that all expectation-level mappings are accepted.

All new prompts, contexts, explanations, diagnostics, and transfer structures are original Mihur-authored content. No released Maryland assessment items, proprietary worksheets, teacher PDFs, or child-identifying data are included.

## Evidence and review gates

Files:
- `package.json`: nine deep package contracts
- `variants.py`: deterministic guided/independent variants
- `tests/test_grade3_gap_closure_wave1.py`: mathematical/structural checks, namespace isolation, answer isolation, and fail-closed runtime gates

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

`pytest -q tests/test_grade3_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and independent Math → Pedagogy → Standards/Architecture → Frontend/MVE → Assessment Backend → Muse review before activation.
