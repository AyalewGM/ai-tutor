"""Database-backed deterministic content audits for F-007.

Audits in this module are application-owned quality gates. They do not call an
LLM and never infer curriculum equivalence across jurisdictions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content_models import ExpectationSkillMapping, ProblemContentMetadata
from app.content_validation import (
    CurriculumScopedRef,
    validate_active_skill_traceability,
    validate_fresh_problem_sets,
    validate_learning_mode_inventory,
)
from app.models import Curriculum, Problem, Skill


def _active_curriculum(session: Session, curriculum_id) -> Curriculum:
    curriculum = session.get(Curriculum, curriculum_id)
    if curriculum is None or not curriculum.active:
        raise ValueError("Active curriculum is required for content audit")
    return curriculum


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
    curriculum = _active_curriculum(session, curriculum_id)

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


def audit_curriculum_problem_inventory(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Audit persisted pilot problems for complete, fresh application-owned pools.

    Every skill in an accepted pilot pack must have at least one persisted
    problem reserved for each deterministic learning mode. Problem IDs may not
    be shared across mode pools, which guarantees that post-help independent and
    mastery evidence can be selected from genuinely fresh content without asking
    an LLM to decide whether reuse is pedagogically acceptable.

    Both metadata.curriculum_id and the problem's primary skill are constrained
    to the selected curriculum. Cross-jurisdiction records therefore cannot make
    an incomplete pack pass this audit.
    """
    curriculum = _active_curriculum(session, curriculum_id)
    skills = session.scalars(
        select(Skill).where(Skill.curriculum_id == curriculum.id).order_by(Skill.code)
    ).all()

    for skill in skills:
        rows = session.execute(
            select(Problem.id, ProblemContentMetadata)
            .join(
                ProblemContentMetadata,
                ProblemContentMetadata.problem_id == Problem.id,
            )
            .where(
                Problem.primary_skill_id == skill.id,
                ProblemContentMetadata.curriculum_id == curriculum.id,
            )
        ).all()

        pools = {
            "diagnostic": [],
            "guided": [],
            "independent": [],
            "mastery": [],
        }
        for problem_id, metadata in rows:
            if metadata.diagnostic_eligible:
                pools["diagnostic"].append(problem_id)
            if metadata.guided_eligible:
                pools["guided"].append(problem_id)
            if metadata.independent_eligible:
                pools["independent"].append(problem_id)
            if metadata.mastery_eligible:
                pools["mastery"].append(problem_id)

        skill_ref = CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id)
        validate_learning_mode_inventory(
            skill=skill_ref,
            diagnostic_count=len(pools["diagnostic"]),
            guided_count=len(pools["guided"]),
            independent_count=len(pools["independent"]),
            mastery_count=len(pools["mastery"]),
        )
        validate_fresh_problem_sets(
            skill=skill_ref,
            diagnostic_problem_ids=pools["diagnostic"],
            guided_problem_ids=pools["guided"],
            independent_problem_ids=pools["independent"],
            mastery_problem_ids=pools["mastery"],
        )
