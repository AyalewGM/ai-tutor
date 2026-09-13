# ruff: noqa: I001

import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Skill, Student, TutorSession

client = TestClient(app)


def _partial_distribution_answer(prompt: str) -> str:
    compact = prompt.replace(" ", "")
    match = re.search(r"(-?\d+)\(x([+-]\d+)\)", compact)
    assert match is not None
    replacement = f"{match.group(1)}x{int(match.group(2)):+d}"
    return compact[: match.start()] + replacement + compact[match.end() :]


def _problem(problem_id: str) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        db.expunge(problem)
        return problem


def test_adaptive_tutor_remediates_prerequisite_and_resumes_target() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        target = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        distributive = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert target is not None
        assert distributive is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Adaptive Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        student_id = student.id
        target_id = target.id
        distributive_id = distributive.id

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(target_id)},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["focus"]["in_remediation"] is False
    assert payload["focus"]["active_skill_id"] == str(target_id)

    session_id = payload["session_id"]
    problem_id = payload["problem"]["id"]

    for _ in range(3):
        problem = _problem(problem_id)
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": _partial_distribution_answer(problem.prompt),
                "assistance_level": 0,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["evaluation"]["misconception_code"] == "DIST_001"
        assert payload["next_problem"] is not None
        problem_id = payload["next_problem"]["id"]

    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(distributive_id)
    assert payload["tutor"]["action"] == "REMEDIATE"

    remediation_problem = _problem(problem_id)
    assisted = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": remediation_problem.canonical_answer,
            "assistance_level": 3,
        },
    )
    assert assisted.status_code == 200
    payload = assisted.json()
    assert payload["focus"]["in_remediation"] is True
    problem_id = payload["next_problem"]["id"]

    for _ in range(5):
        remediation_problem = _problem(problem_id)
        independent = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": remediation_problem.canonical_answer,
                "assistance_level": 0,
            },
        )
        assert independent.status_code == 200
        payload = independent.json()
        if not payload["focus"]["in_remediation"]:
            break
        problem_id = payload["next_problem"]["id"]

    assert payload["focus"]["in_remediation"] is False
    assert payload["focus"]["active_skill_id"] == str(target_id)
    assert payload["tutor"]["action"] == "RESUME_TARGET"
    assert payload["next_problem"] is not None

    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        assert session.active_skill_id == target_id
        assert session.remediation_reason is None
