"""Session resume: re-entering a skill must not restart from DIAGNOSE."""

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
)
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _student_and_skill(skill_status=None, mastery=Decimal("0.5")):
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "M8.ALG.MULTI_STEP",
            )
        )
        assert skill is not None
        student = Student(
            curriculum_id=curriculum.id,
            first_name=f"Resume QA {uuid.uuid4().hex[:6]}",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        if skill_status is not None:
            db.add(
                StudentSkill(
                    student_id=student.id,
                    skill_id=skill.id,
                    status=skill_status,
                    mastery_score=mastery,
                )
            )
            db.flush()
        authenticate_parent_for_student(client, db, student)
        db.refresh(student)
        return student.id, skill.id


def _create_session(student_id, skill_id):
    response = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_fresh_learner_starts_at_diagnose():
    student_id, skill_id = _student_and_skill()
    payload = _create_session(student_id, skill_id)
    assert payload["state"] == "DIAGNOSE"


def test_restart_resumes_active_session_not_new_session():
    student_id, skill_id = _student_and_skill()
    first = _create_session(student_id, skill_id)
    with SessionLocal() as db:
        session = db.get(TutorSession, first["session_id"])
        from app.models import TutorState

        session.current_state = TutorState.INDEPENDENT_PRACTICE
        db.commit()

    second = _create_session(student_id, skill_id)
    assert second["session_id"] == first["session_id"]
    assert second["state"] == "INDEPENDENT_PRACTICE"
    assert second["problem"]["id"] == first["problem"]["id"]


def test_new_session_for_practicing_skill_skips_diagnose():
    student_id, skill_id = _student_and_skill(
        skill_status=SkillStatus.PRACTICING, mastery=Decimal("0.6")
    )
    payload = _create_session(student_id, skill_id)
    assert payload["state"] == "INDEPENDENT_PRACTICE"


def test_mastered_skill_reopens_in_mastery_check():
    student_id, skill_id = _student_and_skill(
        skill_status=SkillStatus.MASTERED, mastery=Decimal("0.95")
    )
    payload = _create_session(student_id, skill_id)
    assert payload["state"] == "MASTERY_CHECK"
