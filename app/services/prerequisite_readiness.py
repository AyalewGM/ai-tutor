import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SkillPrerequisite, StudentSkill
from app.services.curriculum_scope import require_prerequisite_same_curriculum


@dataclass(frozen=True)
class PrerequisiteDecision:
    prerequisite_skill_id: uuid.UUID | None
    reason: str | None


def find_unready_prerequisite(
    db: Session,
    *,
    student_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    readiness_threshold: Decimal = Decimal("0.700"),
    minimum_confidence: Decimal = Decimal("0.350"),
) -> PrerequisiteDecision:
    prerequisites = db.scalars(
        select(SkillPrerequisite)
        .where(SkillPrerequisite.skill_id == target_skill_id)
        .order_by(SkillPrerequisite.importance_weight.desc())
    ).all()

    # Validate the complete direct graph boundary before returning a readiness
    # decision. Otherwise an earlier unready prerequisite could mask a corrupt
    # cross-curriculum edge later in the ordered list.
    for prerequisite in prerequisites:
        require_prerequisite_same_curriculum(
            db,
            target_skill_id=target_skill_id,
            prerequisite_skill_id=prerequisite.prerequisite_skill_id,
        )

    for prerequisite in prerequisites:
        progress = db.get(
            StudentSkill,
            {
                "student_id": student_id,
                "skill_id": prerequisite.prerequisite_skill_id,
            },
        )
        if progress is None:
            return PrerequisiteDecision(
                prerequisite_skill_id=prerequisite.prerequisite_skill_id,
                reason="prerequisite_not_assessed",
            )
        if progress.mastery_score < readiness_threshold:
            return PrerequisiteDecision(
                prerequisite_skill_id=prerequisite.prerequisite_skill_id,
                reason="prerequisite_mastery_below_threshold",
            )
        if progress.confidence_score < minimum_confidence:
            return PrerequisiteDecision(
                prerequisite_skill_id=prerequisite.prerequisite_skill_id,
                reason="prerequisite_confidence_below_threshold",
            )

    return PrerequisiteDecision(prerequisite_skill_id=None, reason=None)
