"""Database-backed deterministic content audits for F-007.

Audits in this module are application-owned quality gates. They do not call an
LLM and never infer curriculum equivalence across jurisdictions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content_models import (
    CurriculumExpectation,
    ExpectationSkillMapping,
    ProblemContentMetadata,
)
from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_active_skill_traceability,
    validate_expectation_skill_mapping,
    validate_fresh_problem_sets,
    validate_learning_mode_inventory,
    validate_prerequisite_edge,
    validate_problem_scope,
)
from app.models import Curriculum, Problem, Skill, SkillPrerequisite


def _active_curriculum(session: Session, curriculum_id) -> Curriculum:
    curriculum = session.get(Curriculum, curriculum_id)
    if curriculum is None or not curriculum.active:
        raise ValueError("Active curriculum is required for content audit")
    return curriculum


def audit_curriculum_isolation(
    session: Session,
    *,
    curriculum_id,
) -> None:
    """Re-audit persisted records that could leak across curriculum boundaries.

    Normal ingestion validates these relationships before persistence. This
    audit intentionally reads the database back and fails closed if records were
    inserted or modified through another path. It provides an independent QA
    gate for the repository's strict jurisdiction-isolation requirement.
    """
    curriculum = _active_curriculum(session, curriculum_id)
    skills = session.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)).all()
    skill_by_id = {skill.id: skill for skill in skills}
    selected_skill_ids = set(skill_by_id)

    expectations = session.scalars(
        select(CurriculumExpectation).where(
            CurriculumExpectation.curriculum_id == curriculum.id
        )
    ).all()
    expectation_by_id = {expectation.id: expectation for expectation in expectations}
    selected_expectation_ids = set(expectation_by_id)

    # Mapping rows are deliberately inspected globally so a row with a forged
    # mapping.curriculum_id cannot hide a reference into this curriculum.
    for mapping in session.scalars(select(ExpectationSkillMapping)).all():
        if not (
            mapping.curriculum_id == curriculum.id
            or mapping.expectation_id in selected_expectation_ids
            or mapping.skill_id in selected_skill_ids
        ):
            continue
        expectation = session.get(CurriculumExpectation, mapping.expectation_id)
        skill = session.get(Skill, mapping.skill_id)
        if expectation is None or skill is None:
            raise ContentValidationError("Expectation mapping references missing persisted records")
        if mapping.curriculum_id != curriculum.id:
            raise ContentValidationError(
                "Expectation mapping touching audited curriculum uses another curriculum_id"
            )
        validate_expectation_skill_mapping(
            mapping_curriculum_id=mapping.curriculum_id,
            expectation=CurriculumScopedRef(
                id=expectation.id,
                curriculum_id=expectation.curriculum_id,
            ),
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
        )

    # A prerequisite edge has no curriculum_id column, so validate every edge
    # touching an audited skill from the curricula attached to both endpoints.
    for edge in session.scalars(select(SkillPrerequisite)).all():
        if (
            edge.skill_id not in selected_skill_ids
            and edge.prerequisite_skill_id not in selected_skill_ids
        ):
            continue
        skill = session.get(Skill, edge.skill_id)
        prerequisite = session.get(Skill, edge.prerequisite_skill_id)
        if skill is None or prerequisite is None:
            raise ContentValidationError("Prerequisite edge references missing persisted skills")
        validate_prerequisite_edge(
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
            prerequisite=CurriculumScopedRef(
                id=prerequisite.id,
                curriculum_id=prerequisite.curriculum_id,
            ),
        )
        if skill.curriculum_id != curriculum.id or prerequisite.curriculum_id != curriculum.id:
            raise ContentValidationError(
                "Prerequisite edge touching audited curriculum crosses curriculum boundaries"
            )

    # Metadata is also inspected globally so a forged metadata.curriculum_id
    # cannot disguise a problem whose primary skill belongs to this curriculum.
    for metadata in session.scalars(select(ProblemContentMetadata)).all():
        problem = session.get(Problem, metadata.problem_id)
        if problem is None:
            raise ContentValidationError("Problem metadata references a missing problem")
        if (
            metadata.curriculum_id != curriculum.id
            and problem.primary_skill_id not in selected_skill_ids
        ):
            continue
        primary_skill = session.get(Skill, problem.primary_skill_id)
        if primary_skill is None:
            raise ContentValidationError("Problem references a missing primary skill")
        if metadata.curriculum_id != curriculum.id:
            raise ContentValidationError(
                "Problem attached to audited curriculum skill uses another curriculum_id"
            )
        validate_problem_scope(
            pack_curriculum_id=metadata.curriculum_id,
            primary_skill=CurriculumScopedRef(
                id=primary_skill.id,
                curriculum_id=primary_skill.curriculum_id,
            ),
        )


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