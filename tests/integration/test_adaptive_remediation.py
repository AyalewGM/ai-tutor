# ruff: noqa: I001

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, InterventionRecord, Problem, Skill, Student, TutorSession
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _distractor_problem(db: Session, skill_id: uuid.UUID) -> Problem:
    """Create a deterministic multiple-choice problem on `skill_id` whose distractor
    'a' maps to DIST_001. This avoids relying on random bank selection."""
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type="SOLVE_EQUATION",
        difficulty=3,
        prompt="Solve 2(x + 3) = 14. Choose the correct answer.",
        canonical_answer="b",
        answer_kind="MULTIPLE_CHOICE",
        choices=[
            {"id": "a", "text": "x = 2", "misconception_code": "DIST_001"},
            {"id": "b", "text": "x = 4"},
            {"id": "c", "text": "x = 7"},
            {"id": "d", "text": "x = 10"},
        ],
        source_type="TEST",
    )
    db.add(problem)
    db.flush()
    return problem


def _problem(problem_id: str, curriculum_id) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        skill = db.get(Skill, problem.primary_skill_id)
        assert skill is not None
        assert skill.curriculum_id == curriculum_id
        db.expunge(problem)
        return problem


def _workspace(session_id: str) -> dict:
    response = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    assert response.status_code == 200
    return response.json()


def test_adaptive_tutor_remediates_prerequisite_and_resumes_target() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        target = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        distributive = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert target is not None
        assert distributive is not None

        student = Student(curriculum_id=curriculum.id, first_name="Adaptive Learner", grade_level="8", school_system="MCPS")
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)

        prerequisite_problems = db.scalars(select(Problem).where(Problem.primary_skill_id == distributive.id).order_by(Problem.id).limit(2)).all()
        assert len(prerequisite_problems) == 2
        evidence_session = TutorSession(student_id=student.id, primary_skill_id=distributive.id, active_skill_id=distributive.id, curriculum_id=curriculum.id)
        db.add(evidence_session)
        db.flush()
        for problem in prerequisite_problems:
            db.add(Attempt(session_id=evidence_session.id, student_id=student.id, problem_id=problem.id, student_answer="incorrect", normalized_answer="incorrect", is_correct=False, attempt_number=1, assistance_level=0))
        db.commit()
        db.refresh(student)
        student_id, curriculum_id, target_id, distributive_id = student.id, curriculum.id, target.id, distributive.id

    # Deterministic MC problems with a DIST_001 distractor — avoids relying
    # on which variants the bank happens to serve first.
    with SessionLocal() as db:
        distractor_problems = [
            _distractor_problem(db, target_id) for _ in range(3)
        ]
        db.commit()

    created = client.post("/api/v1/adaptive-tutor/sessions", json={"student_id": str(student_id), "skill_id": str(target_id)})
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]
    problem_id = payload["problem"]["id"]

    initial_workspace = _workspace(session_id)
    assert initial_workspace["curriculum"]["id"] == str(curriculum_id)
    assert initial_workspace["focus"]["active_skill_id"] == str(target_id)
    assert initial_workspace["focus"]["in_remediation"] is False
    assert initial_workspace["problem"]["id"] == problem_id
    assert initial_workspace["allowed_actions"] == ["SUBMIT_ANSWER"]

    for distractor_problem in distractor_problems:
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={"problem_id": str(distractor_problem.id), "answer": "a", "assistance_level": 0},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["evaluation"]["misconception_code"] == "DIST_001"

    problem_id = payload["next_problem"]["id"]
    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(distributive_id)
    assert payload["tutor"]["action"] == "REMEDIATE"
    remediation_workspace = _workspace(session_id)
    assert remediation_workspace["curriculum"]["id"] == str(curriculum_id)
    assert remediation_workspace["focus"]["primary_skill_id"] == str(target_id)
    assert remediation_workspace["focus"]["active_skill_id"] == str(distributive_id)
    assert remediation_workspace["focus"]["in_remediation"] is True
    assert remediation_workspace["problem"]["id"] == problem_id

    with SessionLocal() as db:
        intervention = db.scalar(select(InterventionRecord).where(InterventionRecord.student_id == student_id, InterventionRecord.target_skill_id == target_id, InterventionRecord.status == "STARTED"))
        assert intervention is not None
        assert intervention.prerequisite_skill_id == distributive_id
        assert intervention.policy_version == "pilot-v1"
        assert intervention.reason_code == "DECLARED_PREREQUISITE_GAP_CONFIRMED"

    remediation_problem = _problem(problem_id, curriculum_id)
    assisted = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": problem_id, "answer": remediation_problem.canonical_answer, "assistance_level": 3})
    assert assisted.status_code == 200
    payload = assisted.json()
    assert payload["focus"]["in_remediation"] is True
    problem_id = payload["next_problem"]["id"]

    for _ in range(5):
        remediation_problem = _problem(problem_id, curriculum_id)
        independent = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": problem_id, "answer": remediation_problem.canonical_answer, "assistance_level": 0})
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

    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        assert session.active_skill_id == target_id
        assert session.curriculum_id == curriculum_id
        assert session.remediation_reason is None
        intervention = db.scalar(select(InterventionRecord).where(InterventionRecord.student_id == student_id, InterventionRecord.target_skill_id == target_id, InterventionRecord.status == "COMPLETED"))
        assert intervention is not None
        assert intervention.outcome_code == "RETURN_CONDITION_MET"
        assert intervention.completed_at is not None
