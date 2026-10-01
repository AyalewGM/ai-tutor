from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Skill, Student
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _seeded_context() -> tuple[Curriculum, Skill, Skill]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        target = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        distributive = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert target is not None
        assert distributive is not None
        db.expunge(curriculum)
        db.expunge(target)
        db.expunge(distributive)
        return curriculum, target, distributive


def _student(curriculum_id) -> str:
    with SessionLocal() as db:
        student = Student(
            curriculum_id=curriculum_id,
            first_name="Diagnostic Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.commit()
        db.refresh(student)
        return str(student.id)


def _problem(problem_id: str) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        db.expunge(problem)
        return problem


def _display_answer(problem: Problem) -> str:
    """The answer text that must never leak into diagnostic coaching."""
    if problem.choices:
        for choice in problem.choices:
            if choice["id"] == problem.canonical_answer:
                return choice["text"]
    return problem.canonical_answer or ""


def _wrong_answer(problem: Problem) -> str:
    """A definitely-wrong answer for any item kind."""
    if problem.choices:
        for choice in problem.choices:
            if choice["id"] != problem.canonical_answer:
                return choice["id"]
    return "I do not know"


def test_diagnostic_requires_authenticated_parent() -> None:
    curriculum, target, _ = _seeded_context()
    student_id = _student(curriculum.id)
    client.cookies.clear()
    unauthenticated = TestClient(app)

    start = unauthenticated.post(
        "/api/v1/diagnostics/sessions",
        json={"student_id": student_id, "target_skill_id": str(target.id)},
    )
    assert start.status_code == 401


def test_diagnostic_stops_early_when_target_is_ready() -> None:
    curriculum, target, _ = _seeded_context()
    student_id = _student(curriculum.id)

    created = client.post(
        "/api/v1/diagnostics/sessions",
        json={"student_id": student_id, "target_skill_id": str(target.id)},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "ACTIVE"

    seen_problem_ids: list[str] = []
    for _ in range(2):
        problem_id = payload["problem"]["id"]
        seen_problem_ids.append(problem_id)
        problem = _problem(problem_id)
        response = client.post(
            f"/api/v1/diagnostics/sessions/{payload['session_id']}/respond",
            json={"problem_id": problem_id, "answer": problem.canonical_answer},
        )
        assert response.status_code == 200
        payload = response.json()

    assert len(set(seen_problem_ids)) == 2
    assert payload["status"] == "COMPLETED"
    assert payload["recommended_skill_id"] == str(target.id)
    assert payload["placement_reason"] == "target_ready"
    assert payload["problem"] is None
    assert payload["question_count"] == 2

    result = client.get(f"/api/v1/diagnostics/sessions/{payload['session_id']}/result")
    assert result.status_code == 200
    result_payload = result.json()
    assert result_payload["recommended_skill_id"] == str(target.id)
    assert result_payload["evidence"][0]["correct_count"] == 2
    assert result_payload["evidence"][0]["incorrect_count"] == 0


def test_diagnostic_descends_to_relevant_prerequisite_without_teaching() -> None:
    curriculum, target, distributive = _seeded_context()
    student_id = _student(curriculum.id)

    created = client.post(
        "/api/v1/diagnostics/sessions",
        json={"student_id": student_id, "target_skill_id": str(target.id)},
    )
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]

    # Answer wrong until the diagnostic descends to the distributive
    # prerequisite — incorrect_count >= 2 triggers graph-boundary descent
    # even when no misconception maps; a misconception-coded answer descends
    # sooner. Either way it must land on the same declared prerequisite.
    descended_payload = None
    problem_id = payload["problem"]["id"]
    for _ in range(3):
        problem = _problem(problem_id)
        response = client.post(
            f"/api/v1/diagnostics/sessions/{session_id}/respond",
            json={
                "problem_id": str(problem.id),
                "answer": _wrong_answer(problem),
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert _display_answer(problem) not in payload["message"]
        if payload["current_skill_id"] == str(distributive.id):
            descended_payload = payload
            break
        problem_id = payload["problem"]["id"] if payload.get("problem") else None
        if problem_id is None:
            break
    assert descended_payload is not None
    payload = descended_payload
    assert payload["status"] == "ACTIVE"
    assert payload["current_skill_id"] == str(distributive.id)

    for _ in range(2):
        problem_id = payload["problem"]["id"]
        problem = _problem(problem_id)
        response = client.post(
            f"/api/v1/diagnostics/sessions/{session_id}/respond",
            json={"problem_id": problem_id, "answer": "I do not know"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert _display_answer(problem) not in payload["message"]

    assert payload["status"] == "COMPLETED"
    assert payload["recommended_skill_id"] == str(distributive.id)
    assert payload["placement_reason"] == "graph_boundary_gap"

    result = client.get(f"/api/v1/diagnostics/sessions/{session_id}/result")
    assert result.status_code == 200
    evidence = {row["skill_id"]: row for row in result.json()["evidence"]}
    assert evidence[str(target.id)]["incorrect_count"] >= 1
    assert evidence[str(distributive.id)]["incorrect_count"] == 2
