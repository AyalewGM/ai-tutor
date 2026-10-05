import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    LearnerAward,
    Problem,
    Skill,
    Student,
    TutorSession,
)
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
    assert badges["STREAK_5"]["progress"] == {
        "current": 2,
        "target": 5,
        "unit": "in a row",
    }
    assert badges["SKILL_MASTERED"]["earned"] is False


def test_skill_map_lists_curriculum_skills_with_mastery() -> None:
    session_id, _ = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]
    _respond_correct(session_id, problem_id)

    response = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}/skill-map"
    )
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 9  # MCPS_MATH_8 anchors + subskills
    active = [entry for entry in entries if entry["is_active"]]
    assert len(active) == 1
    assert active[0]["code"].startswith("M8.ALG.DIST")
    assert active[0]["mastery_score"] > 0
    untouched = [e for e in entries if e["status"] == "NOT_STARTED"]
    assert untouched  # skills the session never touched stay unstarted


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


def _backdate_session(student_id: uuid.UUID, skill_id: uuid.UUID, days_ago: int) -> None:
    with SessionLocal() as db:
        db.add(
            TutorSession(
                student_id=student_id,
                primary_skill_id=skill_id,
                started_at=datetime.now(UTC) - timedelta(days=days_ago),
            )
        )
        db.commit()


def _seed_old_attempt(
    student_id: uuid.UUID, session_id: uuid.UUID, days_ago: int
) -> None:
    with SessionLocal() as db:
        problem = db.scalar(select(Problem).limit(1))
        assert problem is not None
        db.add(
            Attempt(
                session_id=session_id,
                student_id=student_id,
                problem_id=problem.id,
                student_answer="?",
                is_correct=False,
                created_at=datetime.now(UTC) - timedelta(days=days_ago),
            )
        )
        db.commit()


def test_question_milestone_and_progress_meters() -> None:
    session_id, student_id = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]

    seen: set[str] = set()
    for _ in range(10):
        payload = _respond_correct(session_id, problem_id)
        seen.update(award["code"] for award in payload["new_awards"])
        if payload["next_problem"] is None:
            break
        problem_id = payload["next_problem"]["id"]

    assert "QUESTIONS_10" in seen
    assert "PERFECT_SESSION" in seen  # 10 straight correct clears the 5-answer bar

    with SessionLocal() as db:
        codes = {
            row.badge_code
            for row in db.scalars(
                select(LearnerAward).where(LearnerAward.student_id == student_id)
            )
        }
    assert "QUESTIONS_10" in codes and "QUESTIONS_50" not in codes

    collection = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}/badges"
    ).json()
    badges = {badge["code"]: badge for badge in collection}
    assert badges["QUESTIONS_10"]["earned"] is True
    assert badges["QUESTIONS_50"]["earned"] is False
    assert badges["QUESTIONS_50"]["progress"] == {
        "current": 10,
        "target": 50,
        "unit": "answered",
    }
    assert badges["DAY_STREAK_3"]["progress"] == {
        "current": 1,
        "target": 3,
        "unit": "days",
    }
    assert badges["PERFECT_SESSION"]["earned"] is True
    assert badges["EXPLORER_10"]["progress"]["target"] == 10


def test_perfect_session_not_awarded_after_a_miss() -> None:
    session_id, _ = _create_session()
    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]

    _respond_correct(session_id, problem_id)
    wrong = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": "definitely wrong",
            "assistance_level": 0,
        },
    )
    problem_id = wrong.json()["next_problem"]["id"]
    seen: set[str] = set()
    for _ in range(6):
        payload = _respond_correct(session_id, problem_id)
        seen.update(award["code"] for award in payload["new_awards"])
        if payload["next_problem"] is None:
            break
        problem_id = payload["next_problem"]["id"]
    assert "PERFECT_SESSION" not in seen

    collection = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}/badges"
    ).json()
    perfect = {b["code"]: b for b in collection}["PERFECT_SESSION"]
    assert perfect["earned"] is False
    assert perfect["progress"]["target"] == 5


def test_day_streak_badge() -> None:
    session_id, student_id = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, uuid.UUID(session_id))
        assert session is not None
        skill_id = session.primary_skill_id
    _backdate_session(student_id, skill_id, days_ago=1)
    _backdate_session(student_id, skill_id, days_ago=2)

    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]
    payload = _respond_correct(session_id, problem_id)
    codes = {award["code"] for award in payload["new_awards"]}
    assert "DAY_STREAK_3" in codes


def test_comeback_badge() -> None:
    session_id, student_id = _create_session()
    _seed_old_attempt(student_id, uuid.UUID(session_id), days_ago=8)

    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]
    payload = _respond_correct(session_id, problem_id)
    codes = {award["code"] for award in payload["new_awards"]}
    assert "COMEBACK" in codes


def test_explorer_badge_for_ten_distinct_skills() -> None:
    session_id, student_id = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, uuid.UUID(session_id))
        assert session is not None
        seen_skills: set[uuid.UUID] = {session.primary_skill_id}
        rows: list[uuid.UUID] = []
        for problem_id, skill_id in db.execute(
            select(Problem.id, Problem.primary_skill_id)
        ):
            if skill_id not in seen_skills:
                seen_skills.add(skill_id)
                rows.append(problem_id)
            if len(rows) == 9:
                break
        for index, problem_id in enumerate(rows):
            db.add(
                Attempt(
                    session_id=uuid.UUID(session_id),
                    student_id=student_id,
                    problem_id=problem_id,
                    student_answer="?",
                    is_correct=True,
                    attempt_number=index + 2,
                )
            )
        db.commit()

    problem_id = client.get(
        f"/api/v1/learner-workspace/sessions/{session_id}"
    ).json()["problem"]["id"]
    payload = _respond_correct(session_id, problem_id)
    assert "EXPLORER_10" in {award["code"] for award in payload["new_awards"]}
