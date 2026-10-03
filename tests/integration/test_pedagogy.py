import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Skill, Student, TutorSession
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _step_problem(db: Session, skill_id: uuid.UUID) -> Problem:
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type="SOLVE_EQUATION",
        difficulty=3,
        prompt="Solve 2(x + 3) = 14.",
        canonical_answer="x=4",
        answer_kind="FREE_TEXT",
        source_type="TEST",
    )
    db.add(problem)
    db.flush()
    return problem


def _fresh_learner() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        assert curriculum is not None and skill is not None
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Pedagogy Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.commit()
        return student.id, curriculum.id, skill.id


def _start_session(student_id: uuid.UUID, skill_id: uuid.UUID) -> str:
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert created.status_code == 200
    return created.json()["session_id"]


def _step(session_id: str, problem_id: uuid.UUID, line: str) -> dict:
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/work-step",
        json={"problem_id": str(problem_id), "line": line},
    )
    assert response.status_code == 200
    return response.json()


def _setup() -> tuple[str, uuid.UUID]:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        problem = _step_problem(db, skill_id)
        db.commit()
        problem_id = problem.id
    return session_id, problem_id


def test_two_failed_steps_downgrade_cpa_and_emit_step_visual() -> None:
    session_id, problem_id = _setup()
    first = _step(session_id, problem_id, "2x + 6 = 20")
    assert first["status"] == "invalid"
    assert first["cpa_level"] == "ABSTRACT"
    second = _step(session_id, problem_id, "2x = 20")
    assert second["status"] == "invalid"
    assert second["cpa_level"] == "PICTORIAL"
    assert second["step_visual"] is not None
    assert second["step_visual"]["type"] == "balance_scale"
    with SessionLocal() as db:
        session = db.get(TutorSession, uuid.UUID(session_id))
        assert session.cpa_level == "PICTORIAL"


def test_reverse_socratic_challenge_spotted() -> None:
    session_id, problem_id = _setup()
    # Three consecutive valid steps: expand, scale both sides by 2, isolate.
    assert _step(session_id, problem_id, "2x + 6 = 14")["status"] == "valid"
    assert _step(session_id, problem_id, "4x + 12 = 28")["status"] == "valid"
    third = _step(session_id, problem_id, "4x = 16")
    assert third["status"] == "valid"
    challenge = third["reverse_challenge"]
    assert challenge is not None
    assert challenge["line"] == "x = 64"  # 4x = 16 with a planted EQ_003
    spotted = _step(session_id, problem_id, "x = 4")
    assert spotted["status"] == "solved"
    assert spotted["challenge_outcome"] == "spotted"


def test_reverse_socratic_challenge_missed_when_copied() -> None:
    session_id, problem_id = _setup()
    _step(session_id, problem_id, "2x + 6 = 14")
    _step(session_id, problem_id, "4x + 12 = 28")
    third = _step(session_id, problem_id, "4x = 16")
    assert third["reverse_challenge"] is not None
    copied = _step(session_id, problem_id, third["reverse_challenge"]["line"])
    assert copied["status"] == "invalid"
    assert copied["challenge_outcome"] == "missed"
    # The planted error classifies under the authentic code, not a synthetic one.
    assert copied["misconception_code"] == "EQ_003"
