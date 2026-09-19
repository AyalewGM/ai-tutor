from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
    TutorState,
)
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _setup_mastery_session(*, state: TutorState) -> tuple[str, str, str, str]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Mastery Gate QA Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)

        progress = StudentSkill(
            student_id=student.id,
            skill_id=skill.id,
            mastery_score=skill.mastery_threshold,
            confidence_score=Decimal("0.900"),
            status=SkillStatus.PRACTICING,
        )
        db.add(progress)

        session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            current_state=state,
            status="ACTIVE",
        )
        db.add(session)
        db.flush()

        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="F004_QA",
            difficulty=2,
            prompt="What is 1 + 1?",
            canonical_answer="2",
            solution={"answer": "2"},
            source_type="CURATED",
        )
        db.add(problem)
        db.commit()
        return str(session.id), str(problem.id), str(student.id), str(skill.id)


def test_mastery_check_rejects_hint_and_pass_marks_mastered() -> None:
    session_id, problem_id, student_id, skill_id = _setup_mastery_session(
        state=TutorState.MASTERY_CHECK
    )

    hint = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/hint",
        json={"problem_id": problem_id},
    )
    assert hint.status_code == 200
    assert hint.json()["allowed"] is False

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "2", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is True
    assert payload["state"] == "COMPLETE"
    assert payload["tutor"]["action"] == "MARK_MASTERED"

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill,
            {"student_id": student_id, "skill_id": skill_id},
        )
        assert progress is not None
        assert progress.status == SkillStatus.MASTERED

        result = db.scalar(
            select(MasteryEvent)
            .where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "MASTERY_CHECK_RESULT",
            )
            .order_by(MasteryEvent.created_at.desc())
        )
        assert result is not None
        assert result.metadata_json["passed"] is True


def test_failed_mastery_check_without_confirmed_gap_returns_to_guided_practice() -> None:
    session_id, problem_id, student_id, skill_id = _setup_mastery_session(
        state=TutorState.MASTERY_CHECK
    )

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "999", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is False
    assert payload["state"] == "GUIDED_PRACTICE"
    assert payload["tutor"]["action"] == "ASK_RETRY"

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill,
            {"student_id": student_id, "skill_id": skill_id},
        )
        assert progress is not None
        assert progress.status != SkillStatus.MASTERED

        session = db.get(TutorSession, session_id)
        assert session is not None
        assert session.active_skill_id == session.primary_skill_id

        result = db.scalar(
            select(MasteryEvent)
            .where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "MASTERY_CHECK_RESULT",
            )
            .order_by(MasteryEvent.created_at.desc())
        )
        assert result is not None
        assert result.metadata_json["passed"] is False


def test_strong_help_requires_new_independent_problem_before_mastery_check() -> None:
    session_id, problem_id, student_id, skill_id = _setup_mastery_session(
        state=TutorState.INDEPENDENT_PRACTICE
    )

    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None

        strong_help_problem = Problem(
            primary_skill_id=session.active_skill_id,
            problem_type="F004_QA",
            difficulty=2,
            prompt="What is 2 + 2?",
            canonical_answer="4",
            solution={"answer": "4"},
            source_type="CURATED",
        )
        independent_problem = Problem(
            primary_skill_id=session.active_skill_id,
            problem_type="F004_QA",
            difficulty=2,
            prompt="What is 3 + 3?",
            canonical_answer="6",
            solution={"answer": "6"},
            source_type="CURATED",
        )
        db.add_all([strong_help_problem, independent_problem])
        db.flush()

        db.add_all(
            [
                Attempt(
                    session_id=session.id,
                    student_id=session.student_id,
                    problem_id=strong_help_problem.id,
                    student_answer="4",
                    normalized_answer="4",
                    is_correct=True,
                    attempt_number=1,
                    assistance_level=2,
                    state_at_attempt=TutorState.GUIDED_PRACTICE,
                ),
                Attempt(
                    session_id=session.id,
                    student_id=session.student_id,
                    problem_id=independent_problem.id,
                    student_answer="6",
                    normalized_answer="6",
                    is_correct=True,
                    attempt_number=1,
                    assistance_level=0,
                    state_at_attempt=TutorState.INDEPENDENT_PRACTICE,
                ),
            ]
        )
        db.commit()

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": problem_id, "answer": "2", "assistance_level": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["correct"] is True
    assert payload["state"] == "MASTERY_CHECK"
    assert payload["tutor"]["action"] == "START_MASTERY_CHECK"

    with SessionLocal() as db:
        gate = db.scalar(
            select(MasteryEvent)
            .where(
                MasteryEvent.student_id == student_id,
                MasteryEvent.skill_id == skill_id,
                MasteryEvent.reason == "MASTERY_GATE_DECISION",
            )
            .order_by(MasteryEvent.created_at.desc())
        )
        assert gate is not None
        assert gate.metadata_json["eligible"] is True
        assert gate.metadata_json["strong_help_seen"] is True
        assert gate.metadata_json["independent_successes_after_strong_help"] >= 1
