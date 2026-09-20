import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, LearnerAward, Problem, Skill, Student
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _create_session() -> tuple[str, uuid.UUID]:
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None and skill is not None
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Award Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        student_id = student.id
        skill_id = skill.id

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert created.status_code == 200
    return created.json()["session_id"], student_id


def _canonical_answer(problem_id: str) -> str:
    with SessionLocal() as db:
        problem = db.get(Problem, uuid.UUID(problem_id))
        assert problem is not None and problem.canonical_answer is not None
        return problem.canonical_answer


def _respond_correct(session_id: str, problem_id: str) -> dict:
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": _canonical_answer(problem_id),
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_first_correct_answer_awards_badge() -> None:
    session_id, _ = _create_session()
    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    problem_id = workspace.json()["problem"]["id"]

    payload = _respond_correct(session_id, problem_id)
    codes = {award["code"] for award in payload["new_awards"]}
    assert "FIRST_CORRECT" in codes

    payload = _respond_correct(session_id, payload["next_problem"]["id"])
    assert "FIRST_CORRECT" not in {
        award["code"] for award in payload["new_awards"]
    }


def test_streak_badges_and_workspace_shelf() -> None:
    session_id, student_id = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]

    seen: set[str] = set()
    for _ in range(5):
        payload = _respond_correct(session_id, problem_id)
        seen.update(award["code"] for award in payload["new_awards"])
        if payload["next_problem"] is None:
            break
        problem_id = payload["next_problem"]["id"]

    assert {"FIRST_CORRECT", "STREAK_3", "STREAK_5"} <= seen

    with SessionLocal() as db:
        rows = db.scalars(
            select(LearnerAward).where(LearnerAward.student_id == student_id)
        ).all()
        codes = {row.badge_code for row in rows}
    assert {"FIRST_CORRECT", "STREAK_3", "STREAK_5"} <= codes

    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    assert workspace.status_code == 200
    shelf_codes = {award["code"] for award in workspace.json()["awards"]}
    assert "FIRST_CORRECT" in shelf_codes
    assert "STREAK_5" in shelf_codes


def test_badge_collection_shows_earned_and_progress() -> None:
    session_id, _ = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]

    payload = _respond_correct(session_id, problem_id)
    assert payload["next_problem"] is not None
    _respond_correct(session_id, payload["next_problem"]["id"])

    collection = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}/badges"
    )
    assert collection.status_code == 200
    badges = {badge["code"]: badge for badge in collection.json()}

    assert badges["FIRST_CORRECT"]["earned"] is True
    assert badges["STREAK_5"]["earned"] is False
    assert badges["STREAK_5"]["progress"] == {"current": 2, "target": 5}
    assert badges["SKILL_MASTERED"]["earned"] is False


def test_wrong_answer_breaks_streak_and_awards_nothing() -> None:
    session_id, _ = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]

    payload = _respond_correct(session_id, problem_id)
    problem_id = payload["next_problem"]["id"]

    wrong = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": "definitely wrong",
            "assistance_level": 0,
        },
    )
    assert wrong.status_code == 200
    assert wrong.json()["new_awards"] == []
