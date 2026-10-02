import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student
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
            first_name="Step Learner",
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


def test_work_step_flow_accepts_equivalent_routes() -> None:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        problem = _step_problem(db, skill_id)
        db.commit()
        problem_id = problem.id

    assert _step(session_id, problem_id, "2x + 6 = 14")["status"] == "valid"
    assert _step(session_id, problem_id, "2x = 8")["status"] == "valid"
    solved = _step(session_id, problem_id, "x = 4")
    assert solved["status"] == "solved"
    assert solved["normalized_line"] == "x = 4"

    # The solved line then flows through the normal grading path.
    result = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": str(problem_id), "answer": "x = 4", "assistance_level": 0},
    )
    assert result.status_code == 200
    assert result.json()["evaluation"]["correct"] is True


def test_work_step_invalid_steps_escalate_to_reveal() -> None:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        problem = _step_problem(db, skill_id)
        db.commit()
        problem_id = problem.id

    first = _step(session_id, problem_id, "2x = 20")  # added instead of subtracted
    assert first["status"] == "invalid"
    assert first["misconception_code"] == "EQ_001"
    assert first["invalid_count"] == 1
    assert first["revealed_line"] is None

    second = _step(session_id, problem_id, "2x = 22")
    assert second["status"] == "invalid" and second["invalid_count"] == 2

    third = _step(session_id, problem_id, "2x = 26")
    assert third["status"] == "invalid"
    assert third["revealed_line"] is not None
    assert third["invalid_count"] == 3

    # A wrong final answer after a revealed step is still graded wrong, and the
    # recorded step errors raise the attempt's assistance level.
    result = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": str(problem_id), "answer": "x = 4", "assistance_level": 0},
    )
    assert result.status_code == 200
    assert result.json()["evaluation"]["correct"] is True
    with SessionLocal() as db:
        attempt = db.scalar(
            select(Attempt)
            .where(Attempt.session_id == uuid.UUID(session_id))
            .order_by(Attempt.attempt_number.desc())
        )
        assert attempt is not None
        assert attempt.assistance_level >= 2  # errors + reveal


def test_step_misconception_counts_as_evidence_on_correct_final_answer() -> None:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        problem = _step_problem(db, skill_id)
        db.commit()
        problem_id = problem.id

    # Two inverse-direction errors mid-work, then a correct final answer.
    assert _step(session_id, problem_id, "2x = 20")["misconception_code"] == "EQ_001"
    assert _step(session_id, problem_id, "2x = 22")["status"] == "invalid"

    result = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": str(problem_id), "answer": "x = 4", "assistance_level": 0},
    )
    assert result.status_code == 200
    assert result.json()["evaluation"]["correct"] is True
    # The recovered answer still records the step-level misconception.
    assert result.json()["evaluation"]["misconception_code"] == "EQ_001"

    with SessionLocal() as db:
        attempt = db.scalar(
            select(Attempt)
            .where(Attempt.session_id == uuid.UUID(session_id))
            .order_by(Attempt.attempt_number.desc())
        )
        assert attempt is not None
        assert attempt.misconception_id is not None


def test_work_step_rejects_unsupported_and_foreign_problems() -> None:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        arithmetic = Problem(
            primary_skill_id=skill_id,
            problem_type="ARITHMETIC_20",
            difficulty=1,
            prompt="7 + 8",
            canonical_answer="15",
            answer_kind="FREE_TEXT",
            source_type="TEST",
        )
        foreign_skill = db.scalar(
            select(Skill).where(
                Skill.code != "M8.ALG.MULTI_STEP",
                Skill.curriculum_id == select(Skill.curriculum_id).where(
                    Skill.code == "M8.ALG.MULTI_STEP"
                ).scalar_subquery(),
            )
        )
        assert foreign_skill is not None
        foreign = Problem(
            primary_skill_id=foreign_skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=1,
            prompt="x + 1 = 2",
            canonical_answer="x=1",
            source_type="TEST",
        )
        db.add_all([arithmetic, foreign])
        db.commit()
        arithmetic_id, foreign_id = arithmetic.id, foreign.id

    for pid in (arithmetic_id, foreign_id):
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/work-step",
            json={"problem_id": str(pid), "line": "x = 1"},
        )
        assert response.status_code == 400


def test_work_step_requires_auth() -> None:
    client.cookies.clear()
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{uuid.uuid4()}/work-step",
        json={"problem_id": str(uuid.uuid4()), "line": "x = 1"},
    )
    assert response.status_code in (401, 403)


def test_work_step_word_problem_model_then_answer() -> None:
    student_id, _, skill_id = _fresh_learner()
    session_id = _start_session(student_id, skill_id)
    with SessionLocal() as db:
        problem = Problem(
            primary_skill_id=skill_id,
            problem_type="WORD_PROBLEM",
            difficulty=2,
            prompt="A $80 purchase has 13% tax. What is the tax amount?",
            canonical_answer="10.40",
            answer_kind="FREE_TEXT",
            source_type="TEST",
        )
        db.add(problem)
        db.commit()
        problem_id = problem.id

    # A wrong-value model is caught deterministically.
    bad = _step(session_id, problem_id, "0.13 * 50")
    assert bad["status"] == "invalid"
    # A model whose value matches the canonical answer is accepted.
    assert _step(session_id, problem_id, "0.13 * 80")["status"] == "valid"
    # The answer with a unit word solves; normalized to the authored answer.
    solved = _step(session_id, problem_id, "10.40 dollars")
    assert solved["status"] == "solved"
    assert solved["normalized_line"] == "10.40"
