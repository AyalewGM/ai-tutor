"""XP/level derivation from authoritative attempt + award rows."""
import uuid

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
from app.services.awards import attempt_xp, learner_progress
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def test_attempt_xp_weights_independence_and_difficulty() -> None:
    assert attempt_xp(True, 0, 3) > attempt_xp(True, 2, 3)
    assert attempt_xp(True, 0, 5) > attempt_xp(True, 0, 1)
    assert attempt_xp(False, 0, 5) == 0


def test_learner_progress_aggregates_attempts_and_badges() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).limit(1))
        assert curriculum
        # Dedicated throwaway skill — borrowing a real curriculum skill would
        # leak test problems into its bank and disturb other tests.
        skill = Skill(
            curriculum_id=curriculum.id,
            code=f"TEST.XP.{uuid.uuid4().hex[:8]}",
            name="XP test skill",
            description="dedicated skill for XP aggregation test",
            difficulty_level=1,
        )
        db.add(skill)
        db.flush()

        student = Student(
            curriculum_id=curriculum.id,
            first_name="XP Learner",
            grade_level="7",
        )
        session = None
        db.add(student)
        db.flush()
        session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            curriculum_id=curriculum.id,
        )
        db.add(session)
        db.flush()

        expected = 0
        for i in range(4):
            problem = Problem(
                primary_skill_id=skill.id,
                problem_type="SOLVE_EQUATION",
                difficulty=3,
                prompt=f"xp-test {uuid.uuid4()}",
                canonical_answer="x=1",
                source_type="TEST",
            )
            db.add(problem)
            db.flush()
            db.add(
                Attempt(
                    session_id=session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="x=1",
                    is_correct=True,
                    assistance_level=0,
                )
            )
            expected += attempt_xp(True, 0, 3)

        db.add(
            LearnerAward(
                student_id=student.id,
                badge_code="SKILL_MASTERED",
                skill_id=skill.id,
                session_id=session.id,
            )
        )
        expected += 50  # SKILL_MASTERED badge bonus
        db.commit()

        progress = learner_progress(db, student.id)
        assert progress["xp"] == expected
        assert progress["xp_in_level"] < progress["xp_for_next"]
        assert progress["level"] >= 1


def _xp_student(db, *, prior_correct: int) -> tuple[str, str, str]:
    """Student with `prior_correct` independent d=3 corrects on a dedicated skill.

    7 × 14 XP = 98 — just under the 100 XP level-1 boundary — so one more
    independent correct answer crosses into level 2.
    """
    curriculum = db.scalar(select(Curriculum).limit(1))
    assert curriculum
    skill = Skill(
        curriculum_id=curriculum.id,
        code=f"TEST.LVL.{uuid.uuid4().hex[:8]}",
        name="Level-up test skill",
        description="dedicated skill for level-up test",
        difficulty_level=1,
    )
    student = Student(curriculum_id=curriculum.id, first_name="Level Learner", grade_level="7")
    db.add_all([skill, student])
    db.flush()
    problems = [
        Problem(
            primary_skill_id=skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=3,
            prompt=f"lvl-test {uuid.uuid4()}",
            canonical_answer="x=1",
            source_type="TEST",
        )
        for _ in range(prior_correct + 1)
    ]
    db.add_all(problems)
    db.flush()
    session = TutorSession(
        student_id=student.id,
        primary_skill_id=skill.id,
        active_skill_id=skill.id,
        curriculum_id=curriculum.id,
    )
    db.add(session)
    db.flush()
    for problem in problems[:-1]:
        db.add(
            Attempt(
                session_id=session.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="x=1",
                is_correct=True,
                assistance_level=0,
            )
        )
    authenticate_parent_for_student(client, db, student)
    ids = (str(student.id), str(skill.id), str(problems[-1].id))
    db.commit()
    return ids


def test_respond_reports_level_up_on_threshold_crossing() -> None:
    with SessionLocal() as db:
        student_id, skill_id, problem_id = _xp_student(db, prior_correct=7)

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": student_id, "skill_id": skill_id},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    # The session-served problem is whatever the bank holds; the level-up check
    # is about the learner's XP, so answer our dedicated problem correctly.
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "x=1", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is True
    assert payload["xp_earned"] > 0
    assert payload["growth"]["leveled_up"] is True
    assert payload["growth"]["level"] == 2
    assert payload["growth"]["level_title"] == "Explorer"
    assert payload["growth"]["xp_in_level"] < payload["growth"]["xp_for_next"]


def test_respond_does_not_level_up_below_threshold() -> None:
    with SessionLocal() as db:
        student_id, skill_id, problem_id = _xp_student(db, prior_correct=0)

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": student_id, "skill_id": skill_id},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "x=1", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["growth"]["leveled_up"] is False
    assert payload["growth"]["level"] == 1
