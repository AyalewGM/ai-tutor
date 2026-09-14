"""Deterministic, curriculum-scoped prerequisite ingestion for F-007.

The application owns prerequisite topology. This module contains no LLM calls
and never infers or transfers prerequisite relationships across curricula.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_prerequisite_edge,
)
from app.models import Curriculum, Skill, SkillPrerequisite


@dataclass(frozen=True)
class PrerequisiteEdgeInput:
    skill_code: str
    prerequisite_skill_code: str
    importance_weight: Decimal = Decimal("1.0")


def persist_prerequisite_edges(
    session: Session,
    *,
    curriculum_code: str,
    curriculum_version: str,
    edges: tuple[PrerequisiteEdgeInput, ...],
) -> tuple[SkillPrerequisite, ...]:
    """Persist prerequisite edges idempotently inside one exact curriculum version."""
    curriculum = session.scalar(
        select(Curriculum).where(
            Curriculum.code == curriculum_code.strip(),
            Curriculum.version == curriculum_version.strip(),
            Curriculum.active.is_(True),
        )
    )
    if curriculum is None:
        raise ContentValidationError(
            "Active curriculum registry entry not found for prerequisite pack"
        )

    persisted: list[SkillPrerequisite] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        skill_code = edge.skill_code.strip()
        prerequisite_code = edge.prerequisite_skill_code.strip()
        key = (skill_code, prerequisite_code)
        if key in seen:
            raise ContentValidationError(
                f"Duplicate prerequisite edge in content pack: {skill_code} -> {prerequisite_code}"
            )
        seen.add(key)

        skill = session.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == skill_code,
            )
        )
        prerequisite = session.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == prerequisite_code,
            )
        )
        if skill is None:
            raise ContentValidationError(
                f"Prerequisite edge references skill not found in content-pack curriculum: {skill_code}"
            )
        if prerequisite is None:
            raise ContentValidationError(
                "Prerequisite edge references prerequisite skill not found in "
                f"content-pack curriculum: {prerequisite_code}"
            )

        validate_prerequisite_edge(
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
            prerequisite=CurriculumScopedRef(
                id=prerequisite.id,
                curriculum_id=prerequisite.curriculum_id,
            ),
        )

        row = session.scalar(
            select(SkillPrerequisite).where(
                SkillPrerequisite.skill_id == skill.id,
                SkillPrerequisite.prerequisite_skill_id == prerequisite.id,
            )
        )
        if row is None:
            row = SkillPrerequisite(
                skill_id=skill.id,
                prerequisite_skill_id=prerequisite.id,
                importance_weight=edge.importance_weight,
            )
            session.add(row)
        else:
            row.importance_weight = edge.importance_weight
        persisted.append(row)

    session.flush()
    return tuple(persisted)
