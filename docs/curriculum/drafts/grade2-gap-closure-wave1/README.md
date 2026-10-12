# Maryland Grade 2 Comprehensive Gap Closure

**Status: DRAFT_UNVERIFIED · runtime off · no mastery writes**

This single PR deepens the complete Maryland Grade 2 strand set while preserving existing place-value regrouping and unknown-position arithmetic work.

## Included learning packages

1. Hundreds, tens, ones and number representation
2. Skip counting and number patterns
3. Addition within 100
4. Subtraction within 100
5. One- and two-step addition/subtraction word problems
6. Money value and equivalence
7. Length measurement, estimation, and comparison
8. Time to five minutes
9. Shape attributes and equal shares

## Reuse-first design

The following existing work is reused rather than duplicated:

- `docs/curriculum/packs/md-grade2-mccrs-2026_27.json`
- the existing Grade 2 place-value regrouping learning package
- the existing Grades 1–2 unknown-position arithmetic package
- shared place-value, addition, subtraction, money, measurement, time, and geometry canonical families

No new canonical IDs are created, and this PR does not rewrite historical curriculum mappings or learner evidence.

## Mihur teaching architecture

Each package follows:

**Observe → Predict → Manipulate → Explain → Practice → Diagnose → Transfer → Verify**

with a **Concrete/Context → Visual → Symbolic** progression.

Every package includes:
- at least four reasoning goals;
- misconception-specific Socratic repair;
- fresh-number or contrast-case exits;
- scaffold fading;
- deterministic guided variants;
- a separate unseen independent namespace;
- hidden teacher-oracle data and answer-free learner projection;
- keyboard, screen-reader, reduced-motion, text-equivalent visual state, focus, and no-color-only accessibility requirements.

## Topic depth

### Place value
Learners compose/decompose three-digit numbers, exchange 10 ones for 1 ten and 10 tens for 1 hundred without changing value, and move among standard, word, and expanded forms.

### Skip counting
Learners skip-count by 5s, 10s, and 100s, identify the invariant step, move forward/backward, and connect skip counting to place value and early multiplicative structure.

### Addition
Learners use tens-and-ones models, make-a-ten/place-value strategies, regroup 10 ones as a ten, and check with subtraction or estimation.

### Subtraction
Learners decompose a ten when needed, connect subtraction to missing-addend reasoning, and explain why regrouping does not change total value.

### Word problems
Learners solve result-unknown, change-unknown, start-unknown, comparison, and two-step structures. Operation choice comes from story structure, not keywords.

### Money
Learners identify coin/bill values, compose the same total in multiple ways, count mixed collections strategically, and use cent/dollar notation correctly.

### Length
Learners choose appropriate tools and units, align measurement with zero, estimate before measuring, and solve comparison/difference problems.

### Time
Learners distinguish hour/minute hands, count minutes by fives, translate analog↔digital time, and reason through simple hour-boundary situations.

### Shapes and equal shares
Learners identify/draw shapes from attributes and partition circles/rectangles into halves, thirds, and fourths, with equality based on area rather than visual count alone.

## Standards and provenance

The current Maryland Grade 2 repository pack groups expectations under:
- 2.OA
- 2.NBT
- 2.MD
- 2.G

These remain candidate scope references pending independent Standards Mapping.

All new prompts, contexts, explanations, diagnostics, and transfer structures are original Mihur-authored content. No released Maryland assessment items, proprietary worksheets, teacher PDFs, or child-identifying data are included.

## Evidence and review gates

Files:
- `package.json`: nine deep package contracts
- `variants.py`: deterministic guided/independent variants
- `tests/test_grade2_gap_closure_wave1.py`: exact/structural checks, namespace isolation, answer isolation, and fail-closed runtime gates

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

`pytest -q tests/test_grade2_gap_closure_wave1.py`

Also run Ruff, JSON validation, exact-head CI/AppSec, and independent Math → Pedagogy → Standards/Architecture → Frontend/MVE → Assessment Backend → Muse review before activation.
