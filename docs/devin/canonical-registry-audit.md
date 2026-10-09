# Canonical Registry Audit — #282 Phase A

**Reproducible:** `python scripts/audit_canonical_registry.py` (add `--json` for the machine-readable report). Pinned invariants live in `tests/test_canonical_registry_audit.py`.

## Measured counts

| Quantity | Count | Meaning |
|---|---|---|
| Merged runtime families (`FAMILIES`) | **390** | Problem generators, keyed by family ID |
| Domain-module family definitions | **384** | `FAMILIES` in `app/domains/*.py` |
| Locally defined families | **6** | `MATH.EQ.*` entries in `canonical_problem_families.py` itself |
| Distinct canonical skill codes | **107** | `canonical_skill_code` values — the mapping-target vocabulary |
| Skills with multiple families | **86** | One skill can have many generators (max 14) |
| MATH.* literals in `app/` source | **500** | Union of family IDs, skill codes, and other constants — **not** a skill count |

## The "107 vs 488" discrepancy

Muse's two numbers measure different things. **107** is the count of distinct canonical *skill* codes. **488** is the count of distinct `MATH.*` string literals inside `app/domains/` — it counts *family IDs and skill codes and miscellaneous constants together*. A family ID names a generator; a skill code names a mathematical skill. Neither raw literal count is a taxonomy.

Additional finding: **5 orphan literals** — `MATH.RP.PERCENT.APPLICATION`, `MATH.RP.PERCENT.MULTI`, `MATH.RP.PROPORTION`, `MATH.RP.RATIO.CONCEPT`, `MATH.RP.UNIT_RATE` — appear only in `app/content_audit.py`. They are neither family IDs nor skill codes: legacy or aspirational references, not valid targets.

## Identifier vocabularies (not interchangeable)

| Vocabulary | Example | Authority |
|---|---|---|
| Family ID | `MATH.ADD.WORD.MULTI_STEP` | `FAMILIES` keys |
| Canonical skill ID | `MATH.NS.WORD_PROBLEMS` | `canonical_skill_code` / `CanonicalSkill.code` |
| Pack alias | `MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20` | pack `skills[].canonical.code` |
| Jurisdiction skill ID | `MD1.NS.COUNT_COMPARE` | pack `skills[].code` |
| Standard ID | `1.NBT` | pack `skills[].standard_refs` |
| Legacy pack generator | `NUMBER_SEQUENCE` | pack `skills[].problem_families` (49 codes, 0 overlap with family IDs) |

## Registry authority

`register_problem_families` seeds `CanonicalSkill` rows from `FAMILIES[*].canonical_skill_code`. **The canonical skill registry is therefore generator-derived, not a complete mathematical taxonomy** — a curriculum-valid skill with no implemented generator is absent, not nonexistent. Mapping review needs a separate *content-availability* signal: a skill can be a valid target mathematically while still lacking generated problems.

## Alias status

All **42** `MATH.ELEMENTARY.*` aliases (15 packs, 135 jurisdiction skills) have **zero intersection** with the 107 implemented skill codes. No alias auto-matches; every one requires a reviewed mapping or a documented gap. Family IDs and skill codes share only two self-referential names (`MATH.PROB.SIMPLE`, `MATH.PROB.EXPERIMENTAL`) — bounded and pinned by test.

## Gate posture (unchanged)

All 42 aliases remain `UNMAPPED`; publication stays blocked. This audit is read-only evidence for #282; it approves nothing and unblocks nothing on #283.
