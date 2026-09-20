import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Skill, SkillStatus, StudentSkill
from app.services.prerequisite_readiness import find_unready_prerequisite

RESUME_IN_PROGRESS = "RESUME_IN_PROGRESS"
READY_TO_START = "READY_TO_START"
PREREQUISITE_GAP = "PREREQUISITE_GAP"


@dataclass(frozen=True)
class PlacementRecommendation:
    skill: Skill
    reason: str


def recommend_next_skill(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
) -> PlacementRecommendation | None:
    """Recompute placement from live mastery instead of a one-time diagnostic.

    The lowest-difficulty non-mastered skill is the candidate. If its
    prerequisites are ready it is recommended directly (resuming in-progress
    work or starting fresh); otherwise the recommendation descends the
    prerequisite chain to the first unready skill so placement stays current
    as evidence accumulates.
    """
    skills = list(
        db.scalars(
            select(Skill)
            .where(Skill.curriculum_id == curriculum_id)
            .order_by(Skill.difficulty_level, Skill.code)
        ).all()
    )
    if not skills:
        return None
    progress_rows = list(
        db.scalars(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id.in_([skill.id for skill in skills]),
            )
        ).all()
    )
    progress_by_skill = {row.skill_id: row for row in progress_rows}

    candidate = None
    for skill in skills:
        progress = progress_by_skill.get(skill.id)
        if progress is not None and progress.status == SkillStatus.MASTERED:
            continue
        candidate = skill
        break
    if candidate is None:
        return None

    target = candidate
    visited = {target.id}
    while True:
        unready = find_unready_prerequisite(
            db, student_id=student_id, target_skill_id=target.id
        )
        if (
            unready.prerequisite_skill_id is None
            or unready.prerequisite_skill_id in visited
        ):
            break
        next_skill = db.get(Skill, unready.prerequisite_skill_id)
        if next_skill is None:
            break
        target = next_skill
        visited.add(target.id)

    if target.id != candidate.id:
        return PlacementRecommendation(skill=target, reason=PREREQUISITE_GAP)

    progress = progress_by_skill.get(candidate.id)
    if progress is not None and progress.attempt_count > 0:
        return PlacementRecommendation(skill=candidate, reason=RESUME_IN_PROGRESS)
    return PlacementRecommendation(skill=candidate, reason=READY_TO_START)
