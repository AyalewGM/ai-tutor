"""Versioned mathematical skill authority, independent of problem generators.

This module is deliberately read-only and not wired into runtime publication.
An explicit reviewed taxonomy must be populated before alias activation (#282).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class TaxonomyError(ValueError):
    """Invalid taxonomy definition."""


class SkillReviewState(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"


@dataclass(frozen=True)
class CanonicalSkillDefinition:
    code: str
    name: str
    description: str
    review_state: SkillReviewState
    reviewed_by: str | None = None


@dataclass(frozen=True)
class CanonicalTaxonomy:
    version: str
    skills: Mapping[str, CanonicalSkillDefinition]

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise TaxonomyError("taxonomy version is required")
        for key, skill in self.skills.items():
            if key != skill.code or not key.startswith("MATH."):
                raise TaxonomyError(f"invalid canonical skill key: {key}")
            if not skill.name.strip() or not skill.description.strip():
                raise TaxonomyError(f"{key}: name and description are required")
            if skill.review_state == SkillReviewState.REVIEWED and not skill.reviewed_by:
                raise TaxonomyError(f"{key}: reviewed skill requires reviewer identity")
            if skill.review_state != SkillReviewState.REVIEWED and skill.reviewed_by:
                raise TaxonomyError(f"{key}: draft skill cannot claim review")

    def contains(self, code: str, *, reviewed_only: bool = True) -> bool:
        skill = self.skills.get(code)
        return skill is not None and (
            not reviewed_only or skill.review_state == SkillReviewState.REVIEWED
        )

    def capability(self, code: str, family_skill_codes: set[str]) -> tuple[bool, bool]:
        """Return (reviewed mathematical existence, generator availability).

        Generator presence alone never establishes a reviewed skill.
        Neither value asserts practice, assessment, mastery, or jurisdiction coverage.
        """
        return self.contains(code), code in family_skill_codes


# Intentionally empty until definitions are independently authored and reviewed.
# Do NOT synthesize this registry from FAMILIES: that recreates the #282 defect.
TAXONOMY = CanonicalTaxonomy(version="0.1.0-draft", skills={})
