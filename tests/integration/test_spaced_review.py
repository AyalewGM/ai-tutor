import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    SkillReviewSchedule,
    SkillStatus,
    Student,
    StudentSkill,
)
from app.telemetry_models import TelemetryEventRecord
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _setup_review_due() -> tuple[str, str, str, str]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Spaced Review QA Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)

        now = datetime.now(UTC)
        progress = StudentSkill(
            student_id=student.id,
            skill_id=skill.id,
            mastery_score=Decimal("0.900"),
            confidence_score=Decimal("0.900"),
            status=SkillStatus.MASTERED,
            last_independent_evidence_at=now - timedelta(days=30),
        )
        db.add(progress)
        db.add(
            SkillReviewSchedule(
                student_id=student.id,
                skill_id=skill.id,
                interval_index=0,
                due_at=now - timedelta(hours=1),
                status="SCHEDULED",
            )
        )
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="F007_QA",
            difficulty=2,
            prompt="What is 1 + 1?",
            canonical_answer="2",
            solution={"answer": "2"},
            source_type="CURATED",
        )
        db.add(problem)
        db.commit()
        return str(problem.id), str(student.id), str(skill.id), str(curriculum.id)


def _start_session(student_id: str, skill_id: str) -> dict:
    response = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": student_id, "skill_id": skill_id},
    )
    assert response.status_code == 200
    return response.json()


def test_due_review_intercepts_new_session_and_decays_mastery() -> None:
    _, student_id, skill_id, _ = _setup_review_due()

    session = _start_session(student_id, skill_id)
    assert session["state"] == "REVIEW"
    assert session["focus"]["remediation_reason"] == "SPACED_REVIEW"
    assert session["focus"]["active_skill_id"] == skill_id
    assert session["problem"]["id"] is not None

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        assert progress.status == SkillStatus.REVIEW_DUE
        assert float(progress.mastery_score) < 0.9

        decay = db.scalar(
            select(MasteryEvent).where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "MASTERY_DECAY",
            )
        )
        assert decay is not None
        assert decay.metadata_json["days_since_evidence"] >= 29


def test_passed_review_reschedules_and_restores_mastery() -> None:
    problem_id, student_id, skill_id, _ = _setup_review_due()
    session = _start_session(student_id, skill_id)

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session['session_id']}/respond",
        json={"problem_id": problem_id, "answer": "2", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is True
    assert payload["state"] == "COMPLETE"
    assert payload["tutor"]["action"] == "MARK_MASTERED"

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        assert progress.status == SkillStatus.MASTERED
        assert progress.last_independent_evidence_at is not None

        schedule = db.get(
            SkillReviewSchedule,
            {"student_id": student_id, "skill_id": skill_id},
        )
        assert schedule is not None
        assert schedule.status == "SCHEDULED"
        assert schedule.interval_index == 1
        assert schedule.due_at > datetime.now(UTC)
        assert schedule.last_outcome == "REVIEW_PASSED"

        outcome = db.scalar(
            select(MasteryEvent).where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "REVIEW_OUTCOME",
            )
        )
        assert outcome is not None
        assert outcome.metadata_json["passed"] is True

        telemetry = db.scalar(
            select(TelemetryEventRecord).where(
                TelemetryEventRecord.event_type == "review.outcome_recorded",
                TelemetryEventRecord.skill_id == skill_id,
            )
        )
        assert telemetry is not None
        assert telemetry.payload_json["passed"] is True


def test_failed_review_demotes_mastery_and_enters_relearning() -> None:
    problem_id, student_id, skill_id, _ = _setup_review_due()
    session = _start_session(student_id, skill_id)

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session['session_id']}/respond",
        json={"problem_id": problem_id, "answer": "999", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is False
    assert payload["state"] == "REMEDIATION"
    assert payload["tutor"]["action"] == "REMEDIATE"

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        assert progress.status == SkillStatus.PRACTICING

        schedule = db.get(
            SkillReviewSchedule,
            {"student_id": student_id, "skill_id": skill_id},
        )
        assert schedule is not None
        assert schedule.status == "RELEARNING"
        assert schedule.last_outcome == "REVIEW_FAILED"

        outcome = db.scalar(
            select(MasteryEvent).where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "REVIEW_OUTCOME",
            )
        )
        assert outcome is not None
        assert outcome.metadata_json["passed"] is False


def test_due_review_detours_before_new_skill_and_resumes() -> None:
    problem_id, student_id, review_skill_id, curriculum_id = _setup_review_due()

    with SessionLocal() as db:
        new_skill = Skill(
            curriculum_id=curriculum_id,
            code=f"M8.ALG.NEWQA-{uuid.uuid4().hex[:8]}",
            name="New QA Skill",
            difficulty_level=1,
        )
        db.add(new_skill)
        db.flush()
        new_problem = Problem(
            primary_skill_id=new_skill.id,
            problem_type="F007_QA",
            difficulty=1,
            prompt="What is 2 + 2?",
            canonical_answer="4",
            solution={"answer": "4"},
            source_type="CURATED",
        )
        db.add(new_problem)
        db.commit()
        new_skill_id = str(new_skill.id)
        new_problem_id = str(new_problem.id)

    session = _start_session(student_id, new_skill_id)
    assert session["state"] == "REVIEW"
    assert session["focus"]["target_skill_id"] == new_skill_id
    assert session["focus"]["active_skill_id"] == review_skill_id
    assert session["focus"]["in_remediation"] is True

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session['session_id']}/respond",
        json={"problem_id": problem_id, "answer": "2", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tutor"]["action"] == "RESUME_TARGET"
    assert payload["focus"]["active_skill_id"] == new_skill_id
    assert payload["focus"]["in_remediation"] is False
    assert payload["next_problem"]["id"] == new_problem_id
