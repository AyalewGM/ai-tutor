from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Skill, Student, TutorSession
from scripts.seed_md_grade3 import CURRICULUM_CODE, seed
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def test_md_grade3_equal_groups_session_preserves_curriculum_and_fresh_evidence():
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MD3.OA.MULTIPLICATION",
            )
        )
        learner = Student(
            curriculum_id=curriculum.id,
            first_name="Synthetic Elementary Learner",
            grade_level="3",
            school_system="TEST",
        )
        db.add(learner)
        db.flush()
        authenticate_parent_for_student(client, db, learner)
        db.refresh(learner)
        learner_id = learner.id
        skill_id = skill.id
        curriculum_id = curriculum.id

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner_id), "skill_id": str(skill_id)},
    )
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["state"] == "DIAGNOSE"
    assert payload["focus"]["active_skill_id"] == str(skill_id)

    with SessionLocal() as db:
        session = db.get(TutorSession, payload["session_id"])
        problem = db.get(Problem, payload["problem"]["id"])
        assert session.curriculum_id == curriculum_id
        assert problem.primary_skill_id == skill_id
        assert problem.problem_type in {"EQUAL_GROUPS", "MULTIPLICATION_WITHIN_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"}
        answer = problem.canonical_answer

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{payload['session_id']}/respond",
        json={
            "problem_id": payload["problem"]["id"],
            "answer": answer,
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["evaluation"]["correct"] is True
    assert result["next_problem"] is not None

    with SessionLocal() as db:
        next_problem = db.get(Problem, result["next_problem"]["id"])
        assert next_problem.primary_skill_id == skill_id
        next_skill = db.get(Skill, next_problem.primary_skill_id)
        assert next_skill.curriculum_id == curriculum_id
