"""Fail-closed, read-only validator for the proposed canonical alias inventory (#282).

Run: python scripts/validate_canonical_alias_map.py
Publication gate: python scripts/validate_canonical_alias_map.py --publication-gate
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/curriculum/canonical_alias_map.v1.json"
PACKS = ROOT / "docs/curriculum/packs"


def validate_manifest(
    manifest: dict,
    pack_aliases: set[str],
    known_skills: set[str],
    *,
    publication_gate: bool = False,
) -> list[str]:
    """Check alias integrity; only REVIEWED mappings may pass publication."""
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(manifest.get("mapping_version"), str) or not manifest["mapping_version"]:
        errors.append("mapping_version must be a nonempty string")
    entries = manifest.get("aliases")
    if not isinstance(entries, list):
        return errors + ["aliases must be a list"]
    seen: set[str] = set()
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"aliases[{index}] must be an object")
            continue
        alias = item.get("alias")
        if not isinstance(alias, str) or not alias.startswith("MATH.ELEMENTARY."):
            errors.append(f"aliases[{index}] has invalid alias")
            continue
        if alias in seen:
            errors.append(f"duplicate alias: {alias}")
        seen.add(alias)
        status = item.get("status")
        targets = item.get("target_skill_codes")
        relation = item.get("relation")
        if status not in {"UNMAPPED", "PROPOSED", "REVIEWED"}:
            errors.append(f"{alias}: invalid status")
            continue
        if not isinstance(targets, list) or any(not isinstance(x, str) for x in targets):
            errors.append(f"{alias}: targets must be a list of skill IDs")
            continue
        if len(targets) != len(set(targets)):
            errors.append(f"{alias}: duplicate target IDs")
        unknown = set(targets) - known_skills
        if unknown:
            errors.append(f"{alias}: unknown application skill IDs: {sorted(unknown)}")
        if status == "UNMAPPED" and (targets or relation is not None):
            errors.append(f"{alias}: UNMAPPED must have no targets or relation")
        if status in {"PROPOSED", "REVIEWED"}:
            if relation != "ALL_OF" or not targets:
                errors.append(f"{alias}: mapping requires ALL_OF and targets")
            if not isinstance(item.get("evidence"), list) or not item["evidence"]:
                errors.append(f"{alias}: mapping requires evidence")
        if status == "REVIEWED" and not item.get("reviewed_by"):
            errors.append(f"{alias}: REVIEWED requires reviewer identity")
        if status != "REVIEWED" and item.get("reviewed_by"):
            errors.append(f"{alias}: only REVIEWED may specify reviewer")
        if publication_gate and status != "REVIEWED":
            errors.append(f"{alias}: publication blocked until REVIEWED")
    errors.extend(f"missing pack alias: {alias}" for alias in sorted(pack_aliases - seen))
    errors.extend(f"alias not present in packs: {alias}" for alias in sorted(seen - pack_aliases))
    return errors


def pack_aliases() -> tuple[set[str], int, int]:
    aliases: set[str] = set()
    count = 0
    files = sorted(PACKS.glob("*.json"))
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for skill in data["skills"]:
            aliases.add(skill["canonical"]["code"])
            count += 1
    return aliases, count, len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publication-gate", action="store_true")
    args = parser.parse_args()
    from app.canonical_problem_families import FAMILIES

    known_skills = {family.canonical_skill_code for family in FAMILIES.values()}
    aliases, skill_count, pack_count = pack_aliases()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = validate_manifest(
        manifest, aliases, known_skills, publication_gate=args.publication_gate
    )
    print(
        f"packs={pack_count} jurisdiction_skills={skill_count} "
        f"aliases={len(aliases)} application_skills={len(known_skills)}"
    )
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Inventory valid; does NOT certify mapping approval or coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
