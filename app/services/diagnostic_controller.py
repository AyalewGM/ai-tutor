import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.models import Misconception, SkillPrerequisite


@dataclass(frozen=True)
class DiagnosticDecision:
    complete: bool
    next_skill_id: uuid.UUID | None = None
    recommended_skill_id: uuid.UUID | None = None
    reason: str | None = None


def _direct_prerequisites(db: Session, skill_id: uuid.UUID) -> list[SkillPrerequisite]:
    return list(
        db.scalars(
            select(SkillPrerequisite)
            .where(SkillPrerequisite.skill_id == skill_id)
            .order_by(SkillPrerequisite.importance_weight.desc())
        ).all()
    )


def _misconception_prerequisite(
    db: Session,
    skill_id: uuid.UUID,
    misconception: Misconception | None,
) -> uuid.UUID | None:
    if misconception is None:
        return None
    for prerequisite in _direct_prerequisites(db, skill_id):
        if prerequisite.prerequisite_skill_id == misconception.skill_id:
            return prerequisite.prerequisite_skill_id
    return None


def _recent_attempts(
    db: Session,
    diagnostic_session_id: uuid.UUID,
    skill_id: uuid.UUID,
    limit: int = 2,
) -> list[DiagnosticAttempt]:
    return list(
        db.scalars(
            select(DiagnosticAttempt)
            .where(
                DiagnosticAttempt.diagnostic_session_id == diagnostic_session_id,
                DiagnosticAttempt.skill_id == skill_id,
            )
            .order_by(DiagnosticAttempt.sequence_number.desc())
            .limit(limit)
        ).all()
    )


def decide_next_probe(
    db: Session,
    *,
    session: DiagnosticSession,
    misconception: Misconception | None,
) -> DiagnosticDecision:
    current_skill_id = session.current_skill_id
    attempts = _recent_attempts(db, session.id, current_skill_id)

    if session.question_count >= session.max_questions:
        recommended = session.blocked_skill_id or current_skill_id
        return DiagnosticDecision(
            complete=True,
            recommended_skill_id=recommended,
            reason="max_questions_reached",
        )

    ready = len(attempts) >= 2 and all(attempt.is_correct for attempt in attempts)
    if ready:
        recommended = session.blocked_skill_id or current_skill_id
        reason = "target_ready" if session.blocked_skill_id is None else "prerequisite_ready"
        return DiagnosticDecision(
            complete=True,
            recommended_skill_id=recommended,
            reason=reason,
        )

    latest = attempts[0] if attempts else None
    misconception_skill_id = None
    if latest is not None and not latest.is_correct:
        misconception_skill_id = _misconception_prerequisite(
            db,
            current_skill_id,
            misconception,
        )

    incorrect_count = sum(not attempt.is_correct for attempt in attempts)
    should_descend = misconception_skill_id is not None or incorrect_count >= 2
    if not should_descend:
        return DiagnosticDecision(complete=False, next_skill_id=current_skill_id)

    prerequisites = _direct_prerequisites(db, current_skill_id)
    next_skill_id = misconception_skill_id
    if next_skill_id is None and prerequisites:
        next_skill_id = prerequisites[0].prerequisite_skill_id

    if next_skill_id is None:
        return DiagnosticDecision(
            complete=True,
            recommended_skill_id=current_skill_id,
            reason="graph_boundary_gap",
        )

    return DiagnosticDecision(
        complete=False,
        next_skill_id=next_skill_id,
        reason="probe_prerequisite",
    )
