"""Read-only preflight for preserving canonical skill UUID identities."""
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from app.canonical_skill_taxonomy import CanonicalTaxonomy, TaxonomyError


@dataclass(frozen=True)
class PersistedSkillIdentity:
    code: str
    skill_id: UUID


def validate_identity_revision(
    previous: Mapping[str, PersistedSkillIdentity],
    proposed: Mapping[str, PersistedSkillIdentity],
    taxonomy: CanonicalTaxonomy,
) -> None:
    """Reject identity rewrites and unreviewed new mathematical codes."""
    if len({row.skill_id for row in previous.values()}) != len(previous):
        raise TaxonomyError("duplicate previous UUID")
    if len({row.skill_id for row in proposed.values()}) != len(proposed):
        raise TaxonomyError("duplicate proposed UUID")
    for code, old in previous.items():
        if old.code != code or proposed.get(code) != old:
            raise TaxonomyError(f"historical identity changed: {code}")
    for code, row in proposed.items():
        if row.code != code:
            raise TaxonomyError(f"invalid identity key: {code}")
        if code not in previous and not taxonomy.contains(code):
            raise TaxonomyError(f"new skill lacks review: {code}")
