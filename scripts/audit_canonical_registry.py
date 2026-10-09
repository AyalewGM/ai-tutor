"""Deterministic, read-only audit of the canonical skill registry (#282 Phase A).

Reconciles the reported discrepancy between "registered families" and
"domain-level codes" by distinguishing five identifier vocabularies that
share the ``MATH.*`` shape but are NOT interchangeable:

- Family ID: key in ``FAMILIES`` — identifies a problem generator.
- Canonical skill ID: ``ProblemFamilySpec.canonical_skill_code`` — the
  eligible mapping-target vocabulary.
- Pack alias: ``skills[].canonical.code`` in jurisdiction packs —
  the ``MATH.ELEMENTARY.*`` identifiers awaiting mapping.
- Jurisdiction skill ID: ``skills[].code`` (e.g. ``MD1.NS.COUNT_COMPARE``).
- Standard identifier: ``skills[].standard_refs`` (e.g. ``1.NBT``).

Also surfaces the legacy pack ``problem_families`` codes (e.g.
``NUMBER_SEQUENCE``), a generator namespace disjoint from canonical
family IDs.

Run: python scripts/audit_canonical_registry.py
Deterministic output; exits nonzero only on unexpected structural drift.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "docs/curriculum/packs"
MANIFEST = ROOT / "docs/curriculum/canonical_alias_map.v1.json"
MATH_CODE = re.compile(r'"(MATH\.[A-Z0-9_.]+)"')


def audit() -> dict:
    from app.canonical_problem_families import _DOMAIN_MODULES, FAMILIES

    family_ids = set(FAMILIES)
    domain_defs: dict[str, int] = {}
    domain_family_ids: set[str] = set()
    for module in _DOMAIN_MODULES:
        domain_defs[module.__name__.rsplit(".", 1)[-1]] = len(module.FAMILIES)
        domain_family_ids.update(module.FAMILIES)

    skill_counts = Counter(
        family.canonical_skill_code for family in FAMILIES.values()
    )
    skill_ids = set(skill_counts)
    multi_family = {s: n for s, n in skill_counts.items() if n > 1}

    # Every MATH.* string literal in source — NOT a single concept.
    literals: dict[str, set[str]] = {}
    for path in sorted((ROOT / "app").rglob("*.py")):
        for code in MATH_CODE.findall(path.read_text()):
            literals.setdefault(str(path.relative_to(ROOT)), set()).add(code)
    all_literals = set().union(*literals.values(), set())
    orphan_literals = all_literals - family_ids - skill_ids

    # Curriculum packs and the alias manifest.
    pack_aliases: set[str] = set()
    jurisdiction_skills = 0
    pack_family_codes: set[str] = set()
    pack_files = sorted(PACKS.glob("*.json"))
    for path in pack_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for skill in data["skills"]:
            jurisdiction_skills += 1
            pack_aliases.add(skill["canonical"]["code"])
            pack_family_codes.update(skill.get("problem_families", []))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_aliases = {a["alias"] for a in manifest["aliases"]}

    return {
        "families": {
            "merged_total": len(FAMILIES),
            "domain_module_total": len(domain_family_ids),
            "domain_modules": domain_defs,
            "locally_defined": sorted(family_ids - domain_family_ids),
            "all_domain_families_merged": domain_family_ids <= family_ids,
        },
        "canonical_skills": {
            "distinct_codes": len(skill_ids),
            "skills_with_multiple_families": len(multi_family),
            "max_families_per_skill": (
                max(skill_counts.values()) if skill_counts else 0
            ),
            "family_ids_reused_as_skill_codes": sorted(
                family_ids & skill_ids
            ),
            "registry_is_generator_derived": True,
        },
        "source_literals": {
            "math_code_literals": len(all_literals),
            "orphan_literals": {
                code: sorted(
                    path
                    for path, codes in literals.items()
                    if code in codes
                )
                for code in sorted(orphan_literals)
            },
        },
        "curriculum": {
            "pack_files": len(pack_files),
            "jurisdiction_skills": jurisdiction_skills,
            "distinct_aliases": len(pack_aliases),
            "aliases_match_manifest": pack_aliases == manifest_aliases,
            "aliases_present_as_skill_codes": sorted(
                pack_aliases & skill_ids
            ),
            "legacy_pack_family_codes": len(pack_family_codes),
            "legacy_pack_codes_in_families": sorted(
                pack_family_codes & family_ids
            ),
        },
    }


def _print(report: dict) -> None:
    f, s, l, c = (
        report["families"],
        report["canonical_skills"],
        report["source_literals"],
        report["curriculum"],
    )
    print("== Canonical registry audit ==")
    print(
        f"families: merged={f['merged_total']} "
        f"domain={f['domain_module_total']} "
        f"local={len(f['locally_defined'])}"
    )
    print(
        f"canonical skill codes: distinct={s['distinct_codes']} "
        f"shared-by-multiple-families={s['skills_with_multiple_families']} "
        f"max-families={s['max_families_per_skill']}"
    )
    print(
        f"source MATH.* literals={l['math_code_literals']} "
        f"orphans={len(l['orphan_literals'])}"
    )
    for code, paths in l["orphan_literals"].items():
        print(f"  orphan: {code} <- {paths}")
    print(
        f"packs={c['pack_files']} jurisdiction_skills={c['jurisdiction_skills']} "
        f"aliases={c['distinct_aliases']} "
        f"legacy_pack_family_codes={c['legacy_pack_family_codes']}"
    )
    print(
        f"aliases ∩ skill codes: {c['aliases_present_as_skill_codes']} "
        "(empty = no alias auto-matches an implemented skill)"
    )
    print(
        "NOTE: the registry is generator-derived — a canonical skill "
        "without a generator is absent, not mathematically nonexistent."
    )


def main() -> int:
    report = audit()
    _print(report)
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, sort_keys=True))
    ok = (
        report["families"]["all_domain_families_merged"]
        and report["curriculum"]["aliases_match_manifest"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
