# State Curriculum Addition Runbook

This runbook describes how to add a new U.S. state or district curriculum to AI Tutor without modifying runtime code or breaking jurisdiction isolation. The process has been validated with Maryland (MCCRS), District of Columbia (OSSE/CCSS-aligned), and Virginia (VDOE 2023 SOL) elementary mathematics.

## Prerequisites

Before adding a new state, confirm the repository contains:

- `app/elementary_pack.py` — the declarative `ElementaryPack` loader/validator.
- `app/services/problem_generation.py` — deterministic problem-family generators.
- `app/services/visualization.py` — deterministic visual specs.
- `app/services/elementary_cross_grade_prerequisites.py` — cross-grade prerequisite wiring (optional).
- `app/services/elementary_misconception_loader.py` — misconception catalog loader (optional).
- `scripts/seed_all_elementary_packs.py` — idempotent loader for all packs.
- A working test database and `pytest` environment.

## Step 1 — Gather authoritative sources

Identify the state education agency and the exact standards document for the target grade band.

| Field | Example | Where to record |
|---|---|---|
| Country code | `US` | Pack `jurisdiction.country_code` |
| State/territory code | `TX`, `FL`, `CA` | Pack `jurisdiction.code` |
| State/territory name | `Texas` | Pack `jurisdiction.name` |
| Agency code | `TEA`, `FLDOE`, `CDE` | Pack `authority.code` |
| Agency name | `Texas Education Agency` | Pack `authority.name` |
| Standards source URI | Link to PDF or web page | Pack `curriculum.source_uri`, `expectations[*].source_uri` |
| Authority URI | Link to agency standards page | Pack `authority.source_uri` |
| Curriculum version | `TEKS-2024-25` | Pack `curriculum.version` |

Use only government/official sources for standards text and identifiers. Do not copy problem text, diagrams, explanations, or assessment items from commercial products or unlicensed open resources.

## Step 2 — Map local standards to canonical concepts

For each state standard at the target grade, decide:

1. **What mathematical idea** does the standard represent?
2. **Does a canonical concept already cover it?**
   - Browse existing canonical codes in generated packs, e.g.:
     - `MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20`
     - `MATH.ELEMENTARY.PLACE_VALUE.TENS_ONES`
     - `MATH.ELEMENTARY.FRACTIONS.FRACTIONS_AS_NUMBERS`
     - `MATH.ELEMENTARY.GEOMETRY.COORDINATE_PLANE`
   - If yes, reuse the canonical code.
   - If no, propose a new canonical code under `MATH.ELEMENTARY.{domain}.{concept}`.
3. **Does the standard need more than one local skill?**
   - Decompose a broad standard into distinct mathematical ideas when the prerequisite graph, problem families, or remediation paths differ.

Keep a mapping document or spreadsheet during this step. It becomes the provenance justification for each `CurriculumSkillMapping`.

## Step 3 — Design curriculum-local skills

For each local skill in the new pack, specify:

- `code` — jurisdiction-prefixed, e.g. `TX3.NBT.PLACE_VALUE`.
- `name` and `description` — learner-facing but specific to the local scope.
- `difficulty_level` — grade level or pedagogical difficulty.
- `canonical` — code, name, and description from Step 2.
- `standard_refs` — list the state standard identifiers declared in the pack’s `expectations`.
- `prerequisite_codes` — within-grade prerequisites only; cross-grade prerequisites are wired separately.
- `problem_families` — subset of registered families in `app/services/problem_generation.py`.

## Step 4 — Author original problems

Do not transcribe problems from published worksheets or assessments. Instead:

1. Pick an eligible `problem_family` for the skill.
2. Provide an original prompt, canonical answer, difficulty, objective, and modes (`diagnostic`, `guided`, `independent`, `mastery`).
3. Include `parameters` that the generator and visualizer can consume.

Aim for at least 8 curated problems per skill, with all four modes represented.

## Step 5 — Build or extend generators and visuals

If the new state introduces a mathematical representation not yet covered:

1. Add a deterministic generator function in `app/services/problem_generation.py`.
2. Register it in the generator registry.
3. Add a matching deterministic visual spec in `app/services/visualization.py` if a diagram helps the learner.
4. Include an `aria_label` and avoid color-only encoding.

Generators must produce a deterministic canonical answer from parameters. They must not use an LLM to compute mathematical truth.

## Step 6 — Add the declarative pack

Create a JSON file under `docs/curriculum/packs/` using the `ElementaryPack` schema:

```text
docs/curriculum/packs/{state-code}-grade{grade}-{standards-tag}-{version}.json
```

Example: `tx-grade3-teks-2024_25.json`.

Validate the pack locally before committing:

```bash
python - <<'PY'
from app.elementary_pack import parse_pack, validate_pack
path = "docs/curriculum/packs/tx-grade3-teks-2024_25.json"
pack = parse_pack(path)
validate_pack(pack)
print("valid")
PY
```

## Step 7 — Wire cross-grade prerequisites (optional)

If the new state spans multiple grades, add cross-grade edges to `app/services/elementary_cross_grade_prerequisites.py` using grade and skill suffixes. The wiring service reuses the same edge declarations across jurisdictions, so add only state-specific differences if they exist.

Edges must stay within the same jurisdiction. The content audit rejects cross-jurisdiction prerequisite edges.

## Step 8 — Add misconception and remediation content (optional)

For each canonical concept with known common errors:

1. Add entries to the appropriate JSON catalog in `docs/curriculum/misconceptions/`.
2. Include deterministic `diagnostic_pattern` and `remediation` text.
3. If the error can be detected from a wrong answer, add an evaluation rule in `app/services/evaluation.py`.

The `elementary_misconception_loader.py` service will attach the catalog entries to every curriculum-local skill that maps to the canonical concept.

## Step 9 — Register the pack in the loader

Add the new pack filename to `scripts/seed_all_elementary_packs.py::_PACK_ORDER` in grade order. Keep all packs for a jurisdiction contiguous.

## Step 10 — Validate with tests

Run these checks locally before opening a PR:

```bash
python scripts/seed_all_elementary_packs.py
python -m pytest tests/test_all_elementary_packs.py -q
python -m pytest tests/test_elementary_visualization.py -q
python -m pytest tests -q
```

Add tests that prove:

- The new pack parses and validates.
- The pack loads idempotently.
- Local skill codes are unique per curriculum.
- Canonical concepts are reused where appropriate.
- Prerequisite edges stay within the new jurisdiction.
- Learner evidence is not shared with other jurisdictions.

## Step 11 — Document and submit

Update this runbook if the new state required any new pattern. In the PR description, include:

- Authoritative source URIs.
- Grade/standard coverage summary.
- New problem families or visuals added.
- Cross-grade prerequisite decisions.
- Misconception catalog additions.
- Test results and any deviations from this runbook.

## Isolation checklist

- [ ] No learner evidence tables reference canonical concepts directly.
- [ ] Local skill IDs are unique per curriculum.
- [ ] Prerequisite edges do not cross jurisdictions.
- [ ] Expectation mappings stay within the pack’s curriculum.
- [ ] Generated answers are computed deterministically.
- [ ] No Ontario/F-025 files were modified unless a shared architectural defect required a generic, backward-compatible fix.
