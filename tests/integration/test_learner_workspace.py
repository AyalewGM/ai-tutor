import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Skill,
    Student,
    TutorSession,
    TutorState,
    TutorTurn,
)

client = TestClient(app)


def _create_session() -> tuple[uuid.UUID, uuid.UUID]:
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Workspace Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        student_id = student.id
        skill_id = skill.id

    response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert response.status_code == 200
    payload = response.json()
    return uuid.UUID(payload["session_id"]), student_id


def _evidence_counts(
    session_id: uuid.UUID,
    student_id: uuid.UUID,
) -> tuple[int, int, int]:
    with SessionLocal() as db:
        attempts = db.scalar(
            select(func.count(Attempt.id)).where(Attempt.session_id == session_id)
        ) or 0
        mastery_events = db.scalar(
            select(func.count(MasteryEvent.id)).where(MasteryEvent.student_id == student_id)
        ) or 0
        turns = db.scalar(
            select(func.count(TutorTurn.id)).where(TutorTurn.session_id == session_id)
        ) or 0
    return int(attempts), int(mastery_events), int(turns)


def test_workspace_refresh_is_read_only_and_assessment_safe() -> None:
    session_id, student_id = _create_session()
    before = _evidence_counts(session_id, student_id)

    first = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    second = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["state"] == "DIAGNOSE"
    assert payload["allowed_actions"] == ["SUBMIT_ANSWER"]
    assert payload["problem"] is not None
    assert payload["curriculum"]["id"]
    assert payload["focus"]["in_remediation"] is False
    assert _evidence_counts(session_id, student_id) == before


def test_workspace_derives_help_actions_from_backend_state() -> None:
    session_id, _ = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        session.current_state = TutorState.GUIDED_PRACTICE
        db.commit()

    response = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["allowed_actions"] == [
        "SUBMIT_ANSWER",
        "REQUEST_HINT",
        "I_DONT_UNDERSTAND",
    ]
