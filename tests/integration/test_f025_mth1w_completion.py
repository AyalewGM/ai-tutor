import random

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Skill, Student
from app.services.problem_generation import GENERATORS
from scripts.seed_md_integrated_algebra1 import seed as seed_maryland
from scripts.seed_mth1w import seed as seed_ontario
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def test_f025_generators_produce_fresh_original_variation():
    for problem_type in ("COMBINE_LIKE_TERMS", "POLYNOMIAL_ADD_SUBTRACT"):
        generated = {
            GENERATORS[problem_type](random.Random(seed), 3).prompt
            for seed in range(20)
        }
        assert len(generated) >= 12, problem_type
        assert all(prompt.startswith("Simplify ") for prompt in generated)


def test_ontario_session_rejects_maryland_algebra_skill():
    seed_ontario()
    seed_maryland()
    with SessionLocal() as db:
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        maryland = db.scalar(
            select(Curriculum).where(
                Curriculum.code == "MD_INTEGRATED_ALGEBRA_1_2027_28"
            )
        )
        assert ontario is not None and maryland is not None
        ontario_skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == ontario.id,
                Skill.code == "MTH1W.C.ALG.LIKE",
            )
        )
        maryland_skill = db.scalar(
            select(Skill).where(Skill.curriculum_id == maryland.id)
        )
        assert ontario_skill is not None and maryland_skill is not None
        learner = Student(
            curriculum_id=ontario.id,
            first_name="Synthetic F025 Learner",
            grade_level="9",
            school_system="Ontario",
        )
        db.add(learner)
        db.flush()
        authenticate_parent_for_student(client, db, learner)
        db.commit()
        learner_id = learner.id
        maryland_skill_id = maryland_skill.id

    response = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner_id), "skill_id": str(maryland_skill_id)},
    )
    assert response.status_code == 409
    assert "active curriculum" in response.json()["detail"]
