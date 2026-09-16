"""Synthetic F-007A learner-flow evidence for the Maryland Algebra I pilot.

The test deliberately keeps pedagogy application-owned: deterministic evaluation,
remediation selection, and mastery evidence remain in the tutor service. No real
learner data or external LLM call is used.
"""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession
from scripts.seed_algebra1 import seed

client = TestClient(app)


def _problem(problem_id: str, curriculum_id) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        skill = db.get(Skill, problem.primary_skill_id)
        assert skill is not None
        assert skill.curriculum_id == curriculum_id
        db.expunge(problem)
        return problem


def test_algebra1_pilot_remediation_requires_fresh_independent_evidence() -> None:
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_ALGEBRA_1_2026_27")
        )
        target = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "A1.LINEAR.EQ",
            )
        )
        prerequisite = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "A1.EXPR",
            )
        )
        assert curriculum is not None and target is not None and prerequisite is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Synthetic Algebra Learner",
            grade_level="Algebra 1",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()

        # Establish a prerequisite gap using synthetic, independent evidence.
        prerequisite_problems = db.scalars(
            select(Problem)
            .where(Problem.primary_skill_id == prerequisite.id)
            .order_by(Problem.id)
        ).all()
        evidence_session = TutorSession(
            student_id=student.id,
            primary_skill_id=prerequisite.id,
            active_skill_id=prerequisite.id,
            curriculum_id=curriculum.id,
        )
        db.add(evidence_session)
        db.flush()
        for problem in prerequisite_problems:
            db.add(
                Attempt(
                    session_id=evidence_session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="synthetic-incorrect",
                    normalized_answer="synthetic-incorrect",
                    is_correct=False,
                    attempt_number=1,
                    assistance_level=0,
                )
            )
        db.commit()
        student_id = student.id
        curriculum_id = curriculum.id
        target_id = target.id
        prerequisite_id = prerequisite.id

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(target_id)},
    )
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]
    problem_id = payload["problem"]["id"]

    # Repeated deterministic errors activate declared-prerequisite remediation.
    for _ in range(3):
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": "synthetic-incorrect",
                "assistance_level": 0,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["next_problem"] is not None
        problem_id = payload["next_problem"]["id"]

    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(prerequisite_id)
    _problem(problem_id, curriculum_id)

    # Assisted success cannot by itself release remediation.
    problem = _problem(problem_id, curriculum_id)
    assisted = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": problem.canonical_answer,
            "assistance_level": 3,
        },
    )
    assert assisted.status_code == 200
    payload = assisted.json()
    assert payload["focus"]["in_remediation"] is True
    problem_id = payload["next_problem"]["id"]

    # Only fresh, unassisted correct work can satisfy the return/mastery gate.
    for _ in range(6):
        problem = _problem(problem_id, curriculum_id)
        independent = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": problem.canonical_answer,
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
    _problem(payload["next_problem"]["id"], curriculum_id)
