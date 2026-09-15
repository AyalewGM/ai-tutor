import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession, TutorState
from app.telemetry import (
    RetentionPolicy,
    TelemetryEnvelope,
    append_telemetry_event,
    expire_disposable_telemetry,
)
from app.telemetry_models import TelemetryEventRecord


def test_expiry_deletes_only_disposable_telemetry_and_preserves_authoritative_attempt() -> None:
    db = SessionLocal()
    now = datetime(2026, 9, 15, tzinfo=UTC)
    try:
        curriculum = Curriculum(
            code=f"F011_RET_{uuid.uuid4().hex[:8]}",
            name="F011 Retention Scope",
            jurisdiction="Retention Test",
            grade_level="8",
            version="1",
        )
        db.add(curriculum)
        db.flush()
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Retention Learner",
            grade_level="8",
            school_system="Pilot",
        )
        skill = Skill(
            curriculum_id=curriculum.id,
            code=f"F011.RET.{uuid.uuid4().hex[:8]}",
            name="Retention skill",
            difficulty_level=1,
        )
        db.add_all([student, skill])
        db.flush()
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="ARITHMETIC",
            prompt="2 + 2",
            canonical_answer="4",
            difficulty=1,
        )
        db.add(problem)
        db.flush()
        session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            curriculum_id=curriculum.id,
            current_state=TutorState.PRACTICE,
        )
        db.add(session)
        db.flush()
        attempt = Attempt(
            session_id=session.id,
            student_id=student.id,
            problem_id=problem.id,
            student_answer="4",
            normalized_answer="4",
            is_correct=True,
            attempt_number=1,
            assistance_level=0,
            evaluation_confidence=1,
            state_at_attempt=TutorState.PRACTICE,
        )
        db.add(attempt)
        db.flush()
        append_telemetry_event(
            db,
            TelemetryEnvelope(
                event_type="attempt.observed",
                learner_pseudonymous_id="retention-learner",
                curriculum_id=curriculum.id,
                session_id=session.id,
                skill_id=skill.id,
                occurred_at=now - timedelta(days=91),
                payload={"assistance_class": "INDEPENDENT", "correct": True},
            ),
        )
        db.commit()
        attempt_id = attempt.id

        result = expire_disposable_telemetry(db, RetentionPolicy(days=90), now=now)
        db.commit()

        assert result.deleted_count == 1
        assert result.policy_version == "pilot-retention-v1"
        assert db.get(Attempt, attempt_id) is not None
        remaining = db.scalar(
            select(func.count(TelemetryEventRecord.id)).where(
                TelemetryEventRecord.curriculum_id == curriculum.id
            )
        )
        assert remaining == 0
    finally:
        db.rollback()
        db.close()
