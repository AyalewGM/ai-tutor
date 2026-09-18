import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.hint_models import HintEvent
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, StudentSkill, TutorSession, TutorState
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _partial_distribution_answer(prompt: str) -> str:
    compact = prompt.replace(" ", "")
    match = re.search(r"(-?\d+)\(x([+-]\d+)\)", compact)
    assert match is not None
    replacement = f"{match.group(1)}x{int(match.group(2)):+d}"
    return compact[: match.start()] + replacement + compact[match.end() :]


def _create_guided_session() -> tuple[str, str, str]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        assert curriculum is not None
        assert skill is not None
        student = Student(curriculum_id=curriculum.id, first_name="Hint QA Learner", grade_level="8", school_system="MCPS")
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.refresh(student)
        student_id = student.id
        skill_id = skill.id

    created = client.post("/api/v1/adaptive-tutor/sessions", json={"student_id": str(student_id), "skill_id": str(skill_id)})
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]
    problem_id = payload["problem"]["id"]

    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        session.current_state = TutorState.GUIDED_PRACTICE
        db.commit()
    return session_id, problem_id, str(student_id)


def _problem(problem_id: str) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        db.expunge(problem)
        return problem


def test_confident_misconception_emits_and_persists_jit_hint() -> None:
    session_id, problem_id, _ = _create_guided_session()
    problem = _problem(problem_id)
    response = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": problem_id, "answer": _partial_distribution_answer(problem.prompt), "assistance_level": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["misconception_code"] == "DIST_001"
    assert payload["tutor"]["action"] == "GIVE_HINT"
    assert payload["tutor"]["hint_level"] in (1, 2)
    assert payload["next_problem"]["id"] == problem_id
    with SessionLocal() as db:
        event = db.scalar(select(HintEvent).where(HintEvent.session_id == session_id, HintEvent.problem_id == problem_id, HintEvent.trigger == "MISCONCEPTION_JIT").order_by(HintEvent.created_at.desc()))
        assert event is not None
        assert event.attempt_id is not None
        assert event.tutor_turn_id is not None
        assert event.level in (1, 2)


def test_level_three_hint_forces_assisted_success_until_new_problem() -> None:
    session_id, problem_id, student_id = _create_guided_session()
    for expected_level in (1, 2, 3):
        hint = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/hint", json={"problem_id": problem_id})
        assert hint.status_code == 200
        hint_payload = hint.json()
        assert hint_payload["allowed"] is True
        assert hint_payload["level"] == expected_level
    problem = _problem(problem_id)
    assisted = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": problem_id, "answer": problem.canonical_answer, "assistance_level": 0})
    assert assisted.status_code == 200
    assisted_payload = assisted.json()
    next_problem_id = assisted_payload["next_problem"]["id"]
    assert next_problem_id != problem_id
    with SessionLocal() as db:
        assisted_attempt = db.scalar(select(Attempt).where(Attempt.session_id == session_id, Attempt.problem_id == problem_id, Attempt.is_correct.is_(True)).order_by(Attempt.attempt_number.desc()))
        assert assisted_attempt is not None
        assert assisted_attempt.assistance_level == 2
        session = db.get(TutorSession, session_id)
        assert session is not None
        skill_id = session.active_skill_id or session.primary_skill_id
        progress = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
        assert progress is not None
        independent_correct_before = progress.independent_correct_count
    next_problem = _problem(next_problem_id)
    independent = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": next_problem_id, "answer": next_problem.canonical_answer, "assistance_level": 0})
    assert independent.status_code == 200
    with SessionLocal() as db:
        independent_attempt = db.scalar(select(Attempt).where(Attempt.session_id == session_id, Attempt.problem_id == next_problem_id, Attempt.is_correct.is_(True)).order_by(Attempt.attempt_number.desc()))
        assert independent_attempt is not None
        assert independent_attempt.assistance_level == 0
        session = db.get(TutorSession, session_id)
        assert session is not None
        skill_id = session.active_skill_id or session.primary_skill_id
        progress = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
        assert progress is not None
        assert progress.independent_correct_count == independent_correct_before + 1
