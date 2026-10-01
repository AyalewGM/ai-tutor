"""XP/level derivation from authoritative attempt + award rows."""
import uuid

from sqlalchemy import select

from app.core.database import SessionLocal
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


def test_attempt_xp_weights_independence_and_difficulty() -> None:
    assert attempt_xp(True, 0, 3) > attempt_xp(True, 2, 3)
    assert attempt_xp(True, 0, 5) > attempt_xp(True, 0, 1)
    assert attempt_xp(False, 0, 5) == 0


def test_learner_progress_aggregates_attempts_and_badges() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).limit(1))
        skill = db.scalar(select(Skill).limit(1))
        assert curriculum and skill

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
                source_type="GENERATED",
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
