from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Attempt,
    InterventionRecord,
    MasteryEvent,
    Problem,
    Skill,
    SkillPrerequisite,
    TutorSession,
)
from app.services.intervention_policy import (
    DeclaredPrerequisiteEdge,
    IndependentAttemptEvidence,
    InterventionDecision,
    InterventionPolicy,
    decide_intervention,
)


def _declared_prerequisite(
    db: Session,
    *,
    curriculum_id: uuid.UUID,
    target_skill_id: uuid.UUID,
) -> DeclaredPrerequisiteEdge | None:
    target = db.get(Skill, target_skill_id)
    if target is None or target.curriculum_id != curriculum_id:
        raise ValueError("target skill must belong to the selected curriculum")

    prerequisites = db.scalars(
        select(SkillPrerequisite)
        .where(SkillPrerequisite.skill_id == target_skill_id)
        .order_by(SkillPrerequisite.importance_weight.desc())
    ).all()
    if not prerequisites:
        return None

    # Validate all direct edges before choosing the highest-priority one so a corrupt
    # cross-curriculum edge cannot remain hidden behind an earlier valid row.
    for prerequisite in prerequisites:
        prerequisite_skill = db.get(Skill, prerequisite.prerequisite_skill_id)
        if prerequisite_skill is None or prerequisite_skill.curriculum_id != curriculum_id:
            raise ValueError("declared prerequisite must remain inside the selected curriculum")

    selected = prerequisites[0]
    return DeclaredPrerequisiteEdge(
        curriculum_id=curriculum_id,
        skill_id=target_skill_id,
        prerequisite_skill_id=selected.prerequisite_skill_id,
    )


def _attempt_evidence(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    skill_ids: set[uuid.UUID],
    evidence_window_start: datetime,
) -> list[IndependentAttemptEvidence]:
    if not skill_ids:
        return []

    rows = db.execute(
        select(Attempt, Problem)
        .join(Problem, Problem.id == Attempt.problem_id)
        .join(TutorSession, TutorSession.id == Attempt.session_id)
        .where(
            Attempt.student_id == student_id,
            Attempt.created_at > evidence_window_start,
            Attempt.is_correct.is_not(None),
            Problem.primary_skill_id.in_(skill_ids),
            TutorSession.curriculum_id == curriculum_id,
        )
        .order_by(Attempt.created_at.asc(), Attempt.id.asc())
    ).all()

    evidence: list[IndependentAttemptEvidence] = []
    for attempt, problem in rows:
        evidence.append(
            IndependentAttemptEvidence(
                evidence_id=attempt.id,
                curriculum_id=curriculum_id,
                skill_id=problem.primary_skill_id,
                problem_id=problem.id,
                correct=bool(attempt.is_correct),
                assistance_level=attempt.assistance_level,
                occurred_at=attempt.created_at,
            )
        )
    return evidence


def _latest_independent_mastery(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> datetime | None:
    events = db.scalars(
        select(MasteryEvent)
        .where(
            MasteryEvent.student_id == student_id,
            MasteryEvent.skill_id == skill_id,
            MasteryEvent.reason == "MASTERY_CHECK_RESULT",
        )
        .order_by(MasteryEvent.created_at.desc())
    ).all()
    for event in events:
        metadata = event.metadata_json or {}
        if metadata.get("curriculum_id") != str(curriculum_id):
            continue
        if metadata.get("passed") is True and metadata.get("assistance_level") == 0:
            return event.created_at
    return None


def evaluate_persisted_intervention(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    evidence_window_start: datetime,
    policy: InterventionPolicy | None = None,
) -> InterventionDecision:
    """Project persisted, curriculum-local evidence into the pure F-010 policy.

    This adapter is read-only: it does not mutate tutor state, mastery state, or routing.
    """

    selected_policy = policy or InterventionPolicy()
    prerequisite = _declared_prerequisite(
        db,
        curriculum_id=curriculum_id,
        target_skill_id=target_skill_id,
    )
    skill_ids = {target_skill_id}
    if prerequisite is not None:
        skill_ids.add(prerequisite.prerequisite_skill_id)

    evidence = _attempt_evidence(
        db,
        student_id=student_id,
        curriculum_id=curriculum_id,
        skill_ids=skill_ids,
        evidence_window_start=evidence_window_start,
    )
    prerequisite_mastery_at = None
    if prerequisite is not None:
        prerequisite_mastery_at = _latest_independent_mastery(
            db,
            student_id=student_id,
            curriculum_id=curriculum_id,
            skill_id=prerequisite.prerequisite_skill_id,
        )

    return decide_intervention(
        policy=selected_policy,
        curriculum_id=curriculum_id,
        target_skill_id=target_skill_id,
        prerequisite_edge=prerequisite,
        evidence=evidence,
        evidence_window_start=evidence_window_start,
        prerequisite_mastery_at=prerequisite_mastery_at,
    )


def record_intervention_decision(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    decision: InterventionDecision,
) -> InterventionRecord:
    """Persist an auditable decision without applying it to learner routing."""

    record = InterventionRecord(
        student_id=student_id,
        curriculum_id=curriculum_id,
        target_skill_id=target_skill_id,
        prerequisite_skill_id=decision.selected_prerequisite_skill_id,
        policy_version=decision.policy_version,
        state=decision.state.value,
        reason_code=decision.reason_code,
        evidence_ids_json=[str(evidence_id) for evidence_id in decision.evidence_ids],
        return_condition=decision.return_condition,
        status="RECOMMENDED",
    )
    db.add(record)
    db.flush()
    return record
