from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, MasteryEvent, Problem, Skill, Student, TutorTurn


client = TestClient(app)


def test_tutor_session_persists_learning_evidence() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Integration Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        student_id = student.id
        skill_id = skill.id

    session_response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert session_payload["state"] == "DIAGNOSE"
    assert session_payload["message"]

    problem_id = session_payload["problem"]["id"]
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        assert problem.canonical_answer is not None
        answer = problem.canonical_answer

    response = client.post(
        f"/api/v1/tutor/sessions/{session_payload['session_id']}/respond",
        json={
            "problem_id": problem_id,
            "answer": answer,
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is True
    assert payload["tutor"]["message"]
    assert payload["mastery"]["score"] > 0

    with SessionLocal() as db:
        attempt_count = db.scalar(
            select(func.count(Attempt.id)).where(Attempt.student_id == student_id)
        )
        mastery_event_count = db.scalar(
            select(func.count(MasteryEvent.id)).where(MasteryEvent.student_id == student_id)
        )
        tutor_turn_count = db.scalar(
            select(func.count(TutorTurn.id)).join(
                Attempt,
                TutorTurn.attempt_id == Attempt.id,
                isouter=True,
            ).where(
                (Attempt.student_id == student_id) | (TutorTurn.attempt_id.is_(None))
            )
        )

        assert attempt_count == 1
        assert mastery_event_count == 1
        assert tutor_turn_count >= 2
