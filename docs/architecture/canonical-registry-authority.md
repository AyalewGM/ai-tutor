# Canonical registry authority — #282 follow-up

## Which identifiers are authoritative?

`app.canonical_problem_families.FAMILIES` is the **merged runtime registry** of problem families. It contains both the locally defined families and the entries merged from every module in `_DOMAIN_MODULES`. The number of families, the number of distinct canonical skill codes, and the number of family definitions across domain source files are **different quantities**.

- **Family ID**: dictionary key in `FAMILIES`; identifies a problem generator, not a curriculum skill.
- **Canonical skill ID**: `ProblemFamilySpec.canonical_skill_code` on each registered family; the current validator uses the set of these IDs as eligible targets.
- **Pack alias**: `skills[].canonical.code` in jurisdiction packs, currently all `UNMAPPED`.

A count obtained by searching domain source files is not necessarily the count of distinct skill IDs: several families can share a skill, and source-level identifiers can refer to families, skills, or other constants. Do not approve mapping targets on the basis of raw source counts.

## Verification and decision gates

1. Execute `tests/test_canonical_registry_authority.py` to confirm every domain family is merged into `FAMILIES`.
2. Independently enumerate **distinct** `canonical_skill_code` values from the runtime `FAMILIES.values()`, and compare against the domain-module union. Record family count and distinct skill count separately.
3. Confirm that the target vocabulary represents the intended canonical *skill* taxonomy, rather than merely the skills that currently have generators. A valid curriculum skill without a generator must not be silently considered mathematically nonexistent; document a separate content-availability gate if necessary.
4. Only then review the 42 alias mappings individually, with explicit mathematical evidence, `ALL_OF` semantics, and reviewer identity.
5. Keep all 42 `UNMAPPED` and publication blocked until this review is complete. No coverage or learner-mastery migration is authorized.

This change is a registry clarification and test contract only; it does not approve mappings or unblock #283.
