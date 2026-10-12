"""Isolated alias-to-canonical resolver (#286 Deliverable B groundwork).

Reads the versioned alias manifest
(``docs/curriculum/canonical_alias_map.v1.json``) and resolves pack
aliases to canonical skill targets under the merged #282 contract.

Hard rules:

- ``REVIEWED`` entries only: resolve deterministically, returning the
  mapping version, provenance evidence, and the full ``ALL_OF`` target
  set. A composite target is never silently reduced to one skill.
- ``UNMAPPED``/``PROPOSED`` and unknown aliases: return an explicit
  ``UNRESOLVED`` status. No fallback to a similar skill, no coverage
  credit, no learner-data mutation.
- Structurally invalid manifests raise ``AliasManifestError`` — the
  resolver fails closed rather than guessing.

This module is NOT wired into any production consumer. Runtime
activation requires independently approved mappings plus an explicit
Architecture/Product gate; see Board #278 and Issue #286.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/canonical_alias_map.v1.json"
)


class AliasManifestError(Exception):
    """Manifest violates the #282 contract; fail closed."""


class ResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class AliasResolution:
    """Immutable resolution outcome — never mutates learner evidence."""

    alias: str
    status: ResolutionStatus
    relation: str | None = None
    target_skill_codes: tuple[str, ...] = ()
    mapping_version: str | None = None
    evidence: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class AliasManifest:
    """Parsed, validated manifest. ``entries`` preserves ALL_OF targets."""

    mapping_version: str
    release_status: str
    entries: dict[str, dict] = field(default_factory=dict)


def load_manifest(path: Path = MANIFEST_PATH) -> AliasManifest:
    """Parse and structurally validate the manifest; fail closed on drift."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AliasManifestError(f"cannot read manifest: {exc}") from exc

    if raw.get("schema_version") != 1:
        raise AliasManifestError("unsupported schema_version")
    if not isinstance(raw.get("mapping_version"), str) or not raw["mapping_version"]:
        raise AliasManifestError("mapping_version must be a nonempty string")
    entries_raw = raw.get("aliases")
    if not isinstance(entries_raw, list):
        raise AliasManifestError("aliases must be a list")

    entries: dict[str, dict] = {}
    for index, item in enumerate(entries_raw):
        if not isinstance(item, dict) or not isinstance(item.get("alias"), str):
            raise AliasManifestError(f"aliases[{index}] has invalid alias")
        alias = item["alias"]
        if alias in entries:
            raise AliasManifestError(f"duplicate alias: {alias}")
        status = item.get("status")
        if status not in {"UNMAPPED", "PROPOSED", "REVIEWED"}:
            raise AliasManifestError(f"{alias}: invalid status")
        targets = item.get("target_skill_codes")
        if not isinstance(targets, list) or any(
            not isinstance(t, str) or not t for t in targets
        ):
            raise AliasManifestError(f"{alias}: targets must be skill ID strings")
        if len(targets) != len(set(targets)):
            raise AliasManifestError(f"{alias}: duplicate targets")
        if status == "REVIEWED":
            if item.get("relation") != "ALL_OF" or not targets:
                raise AliasManifestError(f"{alias}: REVIEWED requires ALL_OF targets")
            if not item.get("evidence"):
                raise AliasManifestError(f"{alias}: REVIEWED requires evidence")
            if not item.get("reviewed_by"):
                raise AliasManifestError(f"{alias}: REVIEWED requires reviewer")
        entries[alias] = item
    return AliasManifest(
        mapping_version=raw["mapping_version"],
        release_status=raw.get("release_status", ""),
        entries=entries,
    )


def resolve_alias(
    manifest: AliasManifest, alias: str
) -> AliasResolution:
    """Resolve one pack alias. Unresolved means zero credit — never guess."""
    item = manifest.entries.get(alias)
    if item is None:
        return AliasResolution(
            alias=alias,
            status=ResolutionStatus.UNRESOLVED,
            reason="unknown alias: not present in the reviewed manifest",
        )
    if item["status"] != "REVIEWED":
        return AliasResolution(
            alias=alias,
            status=ResolutionStatus.UNRESOLVED,
            mapping_version=manifest.mapping_version,
            reason=(
                f"mapping status is {item['status']}: not independently "
                "mathematically approved"
            ),
        )
    # REVIEWED: return the complete ALL_OF target set — consumers must not
    # pick a single target from a composite mapping.
    return AliasResolution(
        alias=alias,
        status=ResolutionStatus.RESOLVED,
        relation="ALL_OF",
        target_skill_codes=tuple(item["target_skill_codes"]),
        mapping_version=manifest.mapping_version,
        evidence=tuple(item["evidence"]),
    )
