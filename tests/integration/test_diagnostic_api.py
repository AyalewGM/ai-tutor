import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Skill, Student

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
        db.commit()
        db.refresh(student)
        return str(student.id)


def _problem(problem_id: str) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        db.expunge(problem)
        return problem


def _partial_distribution_answer(prompt: str) -> str:
    compact = prompt.replace(" ", "")
    match = re.search(r"(-?\d+)\(x([+-]\d+)\)", compact)
    assert match is not None
    replacement = f"{match.group(1)}x{int(match.group(2)):+d}"
    return compact[: match.start()] + replacement + compact[match.end() :]


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

    target_problem = _problem(payload["problem"]["id"])
    descended = client.post(
        f"/api/v1/diagnostics/sessions/{session_id}/respond",
        json={
            "problem_id": str(target_problem.id),
            "answer": _partial_distribution_answer(target_problem.prompt),
        },
    )
    assert descended.status_code == 200
    payload = descended.json()
    assert payload["status"] == "ACTIVE"
    assert payload["current_skill_id"] == str(distributive.id)
    assert target_problem.canonical_answer not in payload["message"]

    for _ in range(2):
        problem_id = payload["problem"]["id"]
        problem = _problem(problem_id)
        response = client.post(
            f"/api/v1/diagnostics/sessions/{session_id}/respond",
            json={"problem_id": problem_id, "answer": "I do not know"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert problem.canonical_answer not in payload["message"]

    assert payload["status"] == "COMPLETED"
    assert payload["recommended_skill_id"] == str(distributive.id)
    assert payload["placement_reason"] == "graph_boundary_gap"

    result = client.get(f"/api/v1/diagnostics/sessions/{session_id}/result")
    assert result.status_code == 200
    evidence = {row["skill_id"]: row for row in result.json()["evidence"]}
    assert evidence[str(target.id)]["incorrect_count"] == 1
    assert evidence[str(distributive.id)]["incorrect_count"] == 2
