# Maryland Grade 1 Comprehensive Learning-Depth Wave

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes**

This single PR deepens the complete Maryland Grade 1 strand set while preserving the already-separated Grade 1 Gate-5 mathematical identity boundaries.

## Included learning packages

1. Counting, numeral representation, comparison, and ordering to 120
2. Tens-and-ones place value
3. Addition within 20
4. Subtraction within 20
5. Addition/subtraction word problems within 20
6. Equality meaning and unknowns
7. Hour and half-hour time
8. Shape attributes, construction, composition, and equal shares

## Reuse-first design

This wave reuses:
- `docs/curriculum/packs/md-grade1-mccrs-2026_27.json`
- `docs/curriculum/taxonomy_candidate_scope.grade1_gate5.v1.json`
- PR #335 Grade 1 Gate-5 bounded scope cards
- G1–5 place-value foundation drafts
- Grades 1–2 unknown-position arithmetic package
- shared addition, subtraction, time, and geometry families

It creates no new canonical IDs and does not broaden any independently separated Gate-5 atom.

## Atomic evidence boundaries preserved

This package explicitly preserves the following separations:

- numeral representation is not automatically counting mastery;
- ordering a list is not automatically pairwise-comparison mastery;
- equality truth is not unknown-solving mastery;
- addition and subtraction unknown positions require distinct evidence;
- reading a time and producing its representation require distinct evidence;
- shape identification, construction, and composition are not interchangeable.

Those boundaries are documented in `package.json` and asserted in tests.

## Mihur teaching architecture

Each package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

with **Concrete/Context → Visual → Symbolic** progression.

Every package includes:
- at least four reasoning goals;
- misconception-specific Socratic repair;
- fresh-number or contrast-case exits;
- scaffold fading;
- deterministic guided variants;
- a distinct unseen independent namespace;
- hidden teacher-oracle data and answer-free learner projection;
- keyboard, screen-reader, reduced-motion, text-equivalent visual state, focus, and no-color-only accessibility requirements.

## Topic depth

### Counting / representation / ordering
Learners connect quantities, numerals, and number names through 120, including the 99→100 transition, then compare and order values without conflating these as one evidence dimension.

### Place value
Learners build two-digit numbers with tens/ones, reason explicitly about teen numbers and multiples of ten, and exchange ten ones for one ten without changing value.

### Addition
Learners count on, make ten, use ten-frames, and explain strategies rather than relying only on memorized facts.

### Subtraction
Learners use take-away, difference, counting-up, and through-ten strategies and connect subtraction to addition as an inverse relation.

### Word problems
Learners solve result-, change-, start-, part-, and comparison-unknown structures. Operation choice comes from story structure rather than keywords.

### Equality and unknowns
The equal sign is treated as “same value,” with equation-truth/symmetry evidence separated from solving for missing numbers in addition/subtraction equations.

### Time
Learners read and represent hours and half-hours on analog and digital clocks and explain that a half-hour is 30 minutes past the hour.

### Shapes
Learners distinguish defining from non-defining attributes, construct/draw shapes from attributes, compose larger shapes, and partition circles/rectangles into equal shares using equal-area reasoning.

## Standards and provenance

The current Maryland Grade 1 repository pack groups expectations under:
- 1.OA
- 1.NBT
- 1.MD
- 1.G

These remain candidate scope references pending independent Standards Mapping.

All new prompts, contexts, explanations, diagnostics, and transfer structures are original Mihur-authored content. No released Maryland assessment items, proprietary worksheets, teacher PDFs, or child-identifying data are included.

## Evidence and review gates

Files:
- `package.json`: eight deep learning-package contracts and Gate-5 boundary notes
- `variants.py`: deterministic guided/independent variants
- `tests/test_grade1_gap_closure_wave1.py`: exact/structural checks, atomic-boundary assertions, namespace isolation, answer isolation, and hard runtime gates

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

`pytest -q tests/test_grade1_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and independent Math → Pedagogy → Standards/Architecture → Frontend/MVE → Assessment Backend → Muse review before activation.
