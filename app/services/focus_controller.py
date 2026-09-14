from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Attempt, InterventionRecord, Problem, StudentSkill, TutorSession, TutorState
from app.services.intervention_evidence import (
    evaluate_persisted_intervention,
    record_intervention_decision,
)
from app.services.intervention_policy import InterventionState
from app.services.state_machine import Transition

INTERVENTION_EVIDENCE_WINDOW_DAYS = 30
FRESH_RETURN_SUCCESSES_REQUIRED = 2


def _active_intervention(db: Session, session: TutorSession) -> InterventionRecord | None:
    return db.scalar(
        select(InterventionRecord)
        .where(
            InterventionRecord.student_id == session.student_id,
            InterventionRecord.curriculum_id == session.curriculum_id,
            InterventionRecord.target_skill_id == session.primary_skill_id,
            InterventionRecord.prerequisite_skill_id == session.active_skill_id,
            InterventionRecord.status == "STARTED",
        )
        .order_by(InterventionRecord.started_at.desc(), InterventionRecord.created_at.desc())
        .limit(1)
    )


def _fresh_independent_return_ready(
    db: Session,
    *,
    session: TutorSession,
    intervention: InterventionRecord,
) -> bool:
    if intervention.started_at is None or intervention.prerequisite_skill_id is None:
        return False

    distinct_correct = db.scalar(
        select(func.count(func.distinct(Attempt.problem_id)))
        .join(Problem, Problem.id == Attempt.problem_id)
        .join(TutorSession, TutorSession.id == Attempt.session_id)
        .where(
            Attempt.student_id == session.student_id,
            Attempt.created_at > intervention.started_at,
            Attempt.is_correct.is_(True),
            Attempt.assistance_level == 0,
            Problem.primary_skill_id == intervention.prerequisite_skill_id,
            TutorSession.curriculum_id == intervention.curriculum_id,
        )
    ) or 0
    return int(distinct_correct) >= FRESH_RETURN_SUCCESSES_REQUIRED


def apply_focus_policy(
    db: Session,
    *,
    session: TutorSession,
    progress: StudentSkill,
    transition: Transition,
    correct: bool,
    assistance_level: int,
) -> Transition:
    active_skill_id = session.active_skill_id or session.primary_skill_id
    in_remediation = active_skill_id != session.primary_skill_id

    if in_remediation:
        intervention = _active_intervention(db, session)
        if (
            intervention is not None
            and correct
            and assistance_level == 0
            and _fresh_independent_return_ready(db, session=session, intervention=intervention)
        ):
            intervention.status = "COMPLETED"
            intervention.outcome_code = "RETURN_CONDITION_MET"
            intervention.completed_at = datetime.utcnow()
            session.active_skill_id = session.primary_skill_id
            session.remediation_reason = None
            return Transition(TutorState.GUIDED_PRACTICE, "RESUME_TARGET")
        return Transition(
            TutorState.REMEDIATION,
            "ASK_RETRY" if correct else "GIVE_HINT",
            None if correct else 1,
        )

    if transition.action != "REMEDIATE":
        return transition

    if session.curriculum_id is None:
        return Transition(TutorState.GUIDED_PRACTICE, "ASK_RETRY")

    decision = evaluate_persisted_intervention(
        db,
        student_id=session.student_id,
        curriculum_id=session.curriculum_id,
        target_skill_id=session.primary_skill_id,
        evidence_window_start=datetime.utcnow()
        - timedelta(days=INTERVENTION_EVIDENCE_WINDOW_DAYS),
    )
    record = record_intervention_decision(
        db,
        student_id=session.student_id,
        curriculum_id=session.curriculum_id,
        target_skill_id=session.primary_skill_id,
        decision=decision,
    )

    if (
        decision.state != InterventionState.PREREQUISITE_GAP_CONFIRMED
        or decision.selected_prerequisite_skill_id is None
    ):
        record.status = "NOT_STARTED"
        record.outcome_code = decision.reason_code
        return Transition(TutorState.GUIDED_PRACTICE, "ASK_RETRY")

    record.status = "STARTED"
    record.started_at = datetime.utcnow()
    session.active_skill_id = decision.selected_prerequisite_skill_id
    session.remediation_reason = decision.reason_code
    return Transition(TutorState.REMEDIATION, "REMEDIATE", hint_level=2)
