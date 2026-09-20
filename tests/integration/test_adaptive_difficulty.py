from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    Misconception,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
    TutorState,
)
from tests.auth_helpers import authenticate_parent_for_student
from tests.fixtures import TEST_PROVENANCE

client = TestClient(app)


def _seed() -> tuple[Curriculum, Skill]:
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None
        return curriculum, skill
    finally:
        db.close()


def _setup_session(*, state: TutorState, current_difficulty: int = 1) -> tuple[str, str, str]:
    curriculum, skill = _seed()
    with SessionLocal() as db:
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Adaptive Difficulty QA Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)

        db.add(
            StudentSkill(
                student_id=student.id,
                skill_id=skill.id,
                mastery_score=Decimal("0.500"),
                confidence_score=Decimal("0.500"),
                status=SkillStatus.PRACTICING,
                current_difficulty=current_difficulty,
            )
        )
        session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            current_state=state,
            status="ACTIVE",
        )
        db.add(session)
        db.commit()
        return str(session.id), str(student.id), str(skill.id)


def _add_problem(prompt: str, answer: str, difficulty: int) -> str:
    _, skill = _seed()
    with SessionLocal() as db:
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="F0XX_QA",
            difficulty=difficulty,
            prompt=prompt,
            canonical_answer=answer,
            solution={"answer": answer, "provenance": TEST_PROVENANCE},
            source_type="CURATED",
        )
        db.add(problem)
        db.commit()
        return str(problem.id)


def _progress_difficulty(student_id: str, skill_id: str) -> int:
    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        return progress.current_difficulty


def test_independent_successes_raise_current_difficulty() -> None:
    session_id, student_id, skill_id = _setup_session(state=TutorState.GUIDED_PRACTICE)
    problems = [
        (_add_problem("Expand 3(x+9).", "3x+27", 2), "3x+27"),
        (_add_problem("Expand 4(x+8).", "4x+32", 2), "4x+32"),
    ]

    for problem_id, answer in problems:
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={"problem_id": problem_id, "answer": answer, "assistance_level": 0},
        )
        assert response.status_code == 200

    assert _progress_difficulty(student_id, skill_id) == 2


def test_remediation_lowers_current_difficulty() -> None:
    session_id, student_id, skill_id = _setup_session(
        state=TutorState.GUIDED_PRACTICE, current_difficulty=3
    )
    problem_id = _add_problem("Expand 3(x+9).", "3x+27", 2)

    with SessionLocal() as db:
        misconception = db.scalar(
            select(Misconception)
            .join(Skill, Skill.id == Misconception.skill_id)
            .where(Skill.code == "M8.ALG.DIST", Misconception.code == "DIST_001")
        )
        assert misconception is not None
        db.add(
            StudentMisconception(
                student_id=student_id,
                misconception_id=misconception.id,
                occurrence_count=1,
            )
        )
        db.commit()

    # Second partial-distribution occurrence pushes misconception_count to 2 -> REMEDIATE.
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "3x+9", "assistance_level": 0},
    )
    assert response.status_code == 200

    assert _progress_difficulty(student_id, skill_id) == 2
