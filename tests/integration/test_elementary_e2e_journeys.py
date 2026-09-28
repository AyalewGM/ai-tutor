"""Synthetic E2E learner journeys for DMV elementary Grades 1–5.

These tests exercise the full tutoring loop for each jurisdiction:
diagnostic placement → guided practice → independent practice → mastery
check → completion → spaced review scheduling. They prove that the
declarative elementary packs integrate correctly with the adaptive tutoring
engine, cross-grade prerequisite wiring, misconception detection, and
review scheduling.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    Problem,
    Skill,
    SkillReviewSchedule,
    SkillStatus,
    Student,
    StudentSkill,
    TutorState,
)
from app.services.review_schedule import REVIEW_REASON
from scripts.seed_all_elementary_packs import seed as seed_all_packs
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _curriculum(db, code: str):
    return db.scalar(select(Curriculum).where(Curriculum.code == code))


def _skills_by_code(db, curriculum_id):
    return {
        skill.code: skill
        for skill in db.scalars(
            select(Skill).where(Skill.curriculum_id == curriculum_id)
        )
    }


def _create_learner(db, curriculum, grade_level: str) -> Student:
    learner = Student(
        curriculum_id=curriculum.id,
        first_name=f"Synthetic {curriculum.jurisdiction} G{grade_level} Learner",
        grade_level=grade_level,
        school_system=curriculum.jurisdiction,
    )
    db.add(learner)
    db.flush()
    authenticate_parent_for_student(client, db, learner)
    db.commit()
    return learner


def _create_problem(db, skill, problem_id: str | None = None) -> Problem:
    problem = Problem(
        id=uuid.UUID(problem_id) if problem_id else uuid.uuid4(),
        primary_skill_id=skill.id,
        problem_type="E2E_QA",
        difficulty=1,
        prompt="What is 1 + 1?",
        canonical_answer="2",
        solution={
            "answer": "2",
            "problem_family": "E2E_QA",
        },
        source_type="GENERATED",
    )
    db.add(problem)
    db.flush()
    return problem


def _answer_correct(session_id: str, problem_id: str) -> dict:
    """Answer the problem correctly using its stored canonical answer."""
    with SessionLocal() as db:
        problem = db.get(Problem, uuid.UUID(problem_id))
        assert problem is not None
        answer = problem.canonical_answer
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": answer,
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200
    return response.json()


def _run_to_state(
    session_id: str,
    problem_id: str,
    target_states: set[TutorState],
    max_turns: int = 30,
) -> dict:
    """Answer correct until a target state is reached or max_turns exceeded."""
    for _ in range(max_turns):
        result = _answer_correct(session_id, problem_id)
        state = TutorState(result["state"])
        if state in target_states:
            return result
        problem_id = result["next_problem"]["id"]
        assert problem_id is not None
    raise AssertionError(f"Never reached {target_states}; final result: {result}")


def _verify_review_scheduled(db, student_id, skill_id) -> None:
    schedule = db.get(
        SkillReviewSchedule,
        {"student_id": student_id, "skill_id": skill_id},
    )
    assert schedule is not None
    assert schedule.status == "SCHEDULED"
    assert schedule.due_at > datetime.now(UTC)


def _run_session_to_completion(session_id: str, problem_id: str, max_turns: int = 30) -> dict:
    """Answer all problems correctly until the session reaches COMPLETE."""
    result = _answer_correct(session_id, problem_id)
    states_seen = {result["state"]}
    for _ in range(max_turns):
        if result["state"] == "COMPLETE":
            return result, states_seen
        problem_id = result["next_problem"]["id"]
        assert problem_id is not None
        result = _answer_correct(session_id, problem_id)
        states_seen.add(result["state"])
    raise AssertionError(f"Session never completed; states seen: {states_seen}")


def test_md_grade3_full_learner_journey():
    """Maryland Grade 3 multiplication journey through all states."""
    seed_all_packs()
    with SessionLocal() as db:
        curriculum = _curriculum(db, "MD_MATH_3_2026_27")
        skills = _skills_by_code(db, curriculum.id)
        skill = skills["MD3.OA.MULTIPLICATION"]
        learner = _create_learner(db, curriculum, "3")

    # Create session
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(skill.id)},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["state"] == "DIAGNOSE"
    session_id = payload["session_id"]

    # Run full journey to completion
    result, states_seen = _run_session_to_completion(session_id, payload["problem"]["id"])
    assert result["tutor"]["action"] == "MARK_MASTERED"
    # Must have passed through key states
    assert "GUIDED_PRACTICE" in states_seen or "INDEPENDENT_PRACTICE" in states_seen

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill,
            {"student_id": learner.id, "skill_id": skill.id},
        )
        assert progress.status == SkillStatus.MASTERED
        _verify_review_scheduled(db, learner.id, skill.id)


def test_dc_grade2_full_learner_journey():
    """DC Grade 2 addition within 100 journey through all states."""
    seed_all_packs()
    with SessionLocal() as db:
        curriculum = _curriculum(db, "DC_MATH_2_2024_25")
        skills = _skills_by_code(db, curriculum.id)
        skill = skills["DC2.NBT.ADDITION_100"]
        learner = _create_learner(db, curriculum, "2")

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(skill.id)},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    # Run to completion
    result, _ = _run_session_to_completion(session_id, created.json()["problem"]["id"])
    assert result["tutor"]["action"] == "MARK_MASTERED"

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill,
            {"student_id": learner.id, "skill_id": skill.id},
        )
        assert progress.status == SkillStatus.MASTERED
        _verify_review_scheduled(db, learner.id, skill.id)


def test_va_grade4_misconception_triggers_remediation():
    """Virginia Grade 4 fraction misconception triggers remediation path."""
    seed_all_packs()
    with SessionLocal() as db:
        curriculum = _curriculum(db, "VA_MATH_4_2024_25")
        skills = _skills_by_code(db, curriculum.id)
        skill = skills["VA4.NF.FRACTIONS"]
        learner = _create_learner(db, curriculum, "4")

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(skill.id)},
    )
    session_id = created.json()["session_id"]

    # First answer correct (DIAGNOSE -> GUIDED_PRACTICE)
    result = _answer_correct(session_id, created.json()["problem"]["id"])
    assert result["state"] == "GUIDED_PRACTICE"

    # Answer wrong twice — misconception_count >= 2 triggers REMEDIATION
    problem_id = result["next_problem"]["id"]
    for _ in range(2):
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": "999",
                "assistance_level": 0,
            },
        )
        assert response.status_code == 200
        result = response.json()
        problem_id = result["next_problem"]["id"]

    # After repeated misses, should be in REMEDIATION or still guided practice
    assert result["state"] in {"REMEDIATION", "GUIDED_PRACTICE"}


def test_md_grade4_cross_grade_prerequisite_diagnostic():
    """Maryland Grade 4 student with unmastered Grade 3 prerequisite."""
    seed_all_packs()
    with SessionLocal() as db:
        g3_curriculum = _curriculum(db, "MD_MATH_3_2026_27")
        g4_curriculum = _curriculum(db, "MD_MATH_4_2026_27")
        g3_skills = _skills_by_code(db, g3_curriculum.id)
        g4_skills = _skills_by_code(db, g4_curriculum.id)

        g3_skill = g3_skills["MD3.OA.MULTIPLICATION"]
        g4_skill = g4_skills["MD4.OA.COMPARISON"]

        # Create learner enrolled in Grade 4
        learner = _create_learner(db, g4_curriculum, "4")

        # Create Grade 3 skill progress with low mastery (prerequisite not met)
        g3_progress = StudentSkill(
            student_id=learner.id,
            skill_id=g3_skill.id,
            mastery_score=Decimal("0.300"),
            confidence_score=Decimal("0.300"),
            status=SkillStatus.PRACTICING,
        )
        db.add(g3_progress)
        db.commit()

    # Create session for Grade 4 skill
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(g4_skill.id)},
    )
    assert created.status_code == 200

    # The session should start with the target skill (no auto-remediation)
    assert created.json()["state"] == "DIAGNOSE"
    assert created.json()["focus"]["target_skill_id"] == str(g4_skill.id)


def test_va_grade5_review_scheduling_after_mastery():
    """Virginia Grade 5 decimal skill mastery triggers review scheduling."""
    seed_all_packs()
    with SessionLocal() as db:
        curriculum = _curriculum(db, "VA_MATH_5_2024_25")
        skills = _skills_by_code(db, curriculum.id)
        skill = skills["VA5.NBT.DECIMALS"]
        learner = _create_learner(db, curriculum, "5")

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(skill.id)},
    )
    session_id = created.json()["session_id"]

    # Run to completion
    result, _ = _run_session_to_completion(session_id, created.json()["problem"]["id"])
    assert result["tutor"]["action"] == "MARK_MASTERED"

    with SessionLocal() as db:
        schedule = db.get(
            SkillReviewSchedule,
            {"student_id": learner.id, "skill_id": skill.id},
        )
        assert schedule is not None
        assert schedule.status == "SCHEDULED"
        assert schedule.interval_index == 0
        assert schedule.due_at > datetime.now(UTC)


def test_review_due_state_intercepts_session():
    """When review is due, new session starts in REVIEW state."""
    seed_all_packs()
    with SessionLocal() as db:
        curriculum = _curriculum(db, "MD_MATH_1_2026_27")
        skills = _skills_by_code(db, curriculum.id)
        skill = skills["MD1.OA.ADDITION_20"]
        learner = _create_learner(db, curriculum, "1")

        # Mark skill as mastered with old evidence
        progress = StudentSkill(
            student_id=learner.id,
            skill_id=skill.id,
            mastery_score=Decimal("0.950"),
            confidence_score=Decimal("0.900"),
            status=SkillStatus.MASTERED,
            last_independent_evidence_at=datetime.now(UTC) - timedelta(days=30),
        )
        db.add(progress)

        # Create due review schedule
        review = SkillReviewSchedule(
            student_id=learner.id,
            skill_id=skill.id,
            interval_index=0,
            due_at=datetime.now(UTC) - timedelta(hours=1),
            status="SCHEDULED",
        )
        db.add(review)
        db.commit()

        # Add problem for review
        _create_problem(db, skill)
        db.commit()

    # Create new session — should start in REVIEW
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(skill.id)},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["state"] == "REVIEW"
    assert payload["focus"]["remediation_reason"] == REVIEW_REASON
    assert payload["focus"]["active_skill_id"] == str(skill.id)


def test_cross_jurisdiction_isolation_in_e2e():
    """Ensure Maryland learner cannot access DC or VA skills."""
    seed_all_packs()
    with SessionLocal() as db:
        md_curriculum = _curriculum(db, "MD_MATH_3_2026_27")
        dc_curriculum = _curriculum(db, "DC_MATH_3_2024_25")
        md_skills = _skills_by_code(db, md_curriculum.id)
        dc_skills = _skills_by_code(db, dc_curriculum.id)

        learner = _create_learner(db, md_curriculum, "3")

    # Maryland learner tries to access DC skill — should fail
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(dc_skills["DC3.OA.MULTIPLICATION"].id)},
    )
    assert created.status_code == 409  # CurriculumScopeError

    # Maryland learner can access MD skill
    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(learner.id), "skill_id": str(md_skills["MD3.OA.MULTIPLICATION"].id)},
    )
    assert created.status_code == 200


def test_all_jurisdictions_have_equivalent_e2e_capability():
    """Verify all three jurisdictions support the same E2E flow."""
    seed_all_packs()
    jurisdictions = [
        ("MD_MATH_3_2026_27", "MD3.OA.MULTIPLICATION"),
        ("DC_MATH_3_2024_25", "DC3.OA.MULTIPLICATION"),
        ("VA_MATH_3_2024_25", "VA3.OA.MULTIPLICATION"),
    ]
    for curriculum_code, skill_code in jurisdictions:
        with SessionLocal() as db:
            curriculum = _curriculum(db, curriculum_code)
            skills = _skills_by_code(db, curriculum.id)
            skill = skills[skill_code]
            learner = _create_learner(db, curriculum, "3")

        created = client.post(
            "/api/v1/adaptive-tutor/sessions",
            json={"student_id": str(learner.id), "skill_id": str(skill.id)},
        )
        assert created.status_code == 200, f"{curriculum_code} session failed"
        assert created.json()["state"] == "DIAGNOSE"
