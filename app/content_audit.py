"""Database-backed deterministic content audits for F-007.

Audits in this module are application-owned quality gates. They do not call an
LLM and never infer curriculum equivalence across jurisdictions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content_models import ExpectationSkillMapping
from app.content_validation import CurriculumScopedRef, validate_active_skill_traceability
from app.models import Curriculum, Skill


def audit_curriculum_skill_traceability(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Require every skill in one curriculum to have source expectation traceability.

    The current schema does not expose a per-skill active flag, so the pilot
    completeness rule applies to every skill registered under the selected
    curriculum. Mapping counts are constrained by both mapping.curriculum_id and
    skill_id so a mapping from another jurisdiction cannot satisfy this audit.
    """
    curriculum = session.get(Curriculum, curriculum_id)
    if curriculum is None or not curriculum.active:
        raise ValueError("Active curriculum is required for traceability audit")

    skills = session.scalars(
        select(Skill).where(Skill.curriculum_id == curriculum.id).order_by(Skill.code)
    ).all()

    for skill in skills:
        mapped_expectation_count = session.scalar(
            select(func.count())
            .select_from(ExpectationSkillMapping)
            .where(
                ExpectationSkillMapping.curriculum_id == curriculum.id,
                ExpectationSkillMapping.skill_id == skill.id,
            )
        )
        validate_active_skill_traceability(
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
            mapped_expectation_count=int(mapped_expectation_count or 0),
        )
