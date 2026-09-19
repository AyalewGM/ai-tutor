"""Synthetic F-007A learner-flow evidence for the Maryland Algebra I pilot."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession
from app.services.intervention_evidence import evaluate_persisted_intervention
from app.services.intervention_policy import InterventionState
from scripts.seed_algebra1 import seed
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _problem(problem_id: str, curriculum_id) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        skill = db.get(Skill, problem.primary_skill_id)
        assert skill is not None and skill.curriculum_id == curriculum_id
        db.expunge(problem)
        return problem


def test_algebra1_pilot_remediation_requires_fresh_independent_evidence() -> None:
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_ALGEBRA_1_2026_27"))
        target = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == "A1.LINEAR.EQ"))
        prerequisite = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == "A1.EXPR"))
        assert curriculum is not None and target is not None and prerequisite is not None
        misconception_problem = db.scalar(select(Problem).where(Problem.primary_skill_id == target.id, Problem.prompt == "Solve 2(x + 4) = 18."))
        assert misconception_problem is not None
        student = Student(curriculum_id=curriculum.id, first_name="Synthetic Algebra Learner", grade_level="Algebra 1", school_system="MCPS")
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        prerequisite_problems = db.scalars(select(Problem).where(Problem.primary_skill_id == prerequisite.id).order_by(Problem.id)).all()
        target_problems = db.scalars(select(Problem).where(Problem.primary_skill_id == target.id).order_by(Problem.id)).all()
        assert len(prerequisite_problems) >= 2 and len(target_problems) >= 2
        evidence_session = TutorSession(student_id=student.id, primary_skill_id=target.id, active_skill_id=target.id, curriculum_id=curriculum.id)
        db.add(evidence_session)
        db.flush()
        for problem in [*prerequisite_problems[:2], *target_problems[:2]]:
            db.add(Attempt(session_id=evidence_session.id, student_id=student.id, problem_id=problem.id, student_answer="synthetic-incorrect", normalized_answer="synthetic-incorrect", is_correct=False, attempt_number=1, assistance_level=0))
        db.commit()
        decision = evaluate_persisted_intervention(db, student_id=student.id, curriculum_id=curriculum.id, target_skill_id=target.id, evidence_window_start=datetime.now(UTC) - timedelta(days=30))
        assert decision.state == InterventionState.PREREQUISITE_GAP_CONFIRMED
        assert decision.selected_prerequisite_skill_id == prerequisite.id
        assert decision.reason_code == "DECLARED_PREREQUISITE_GAP_CONFIRMED"
        assert len(decision.evidence_ids) >= 4
        student_id, curriculum_id, target_id, prerequisite_id = student.id, curriculum.id, target.id, prerequisite.id
        prerequisite_problem_ids = [problem.id for problem in prerequisite_problems[:2]]
        misconception_problem_id = misconception_problem.id
        misconception_problem_answer = misconception_problem.canonical_answer

    created = client.post("/api/v1/adaptive-tutor/sessions", json={"student_id": str(student_id), "skill_id": str(target_id)})
    assert created.status_code == 200
    payload = created.json(); session_id = payload["session_id"]
    diagnostic = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": str(misconception_problem_id), "answer": misconception_problem_answer, "assistance_level": 0})
    assert diagnostic.status_code == 200
    payload = diagnostic.json(); assert payload["state"] == "GUIDED_PRACTICE"; assert payload["focus"]["in_remediation"] is False
    for _ in range(2):
        response = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": str(misconception_problem_id), "answer": "2x+4=18", "assistance_level": 0})
        assert response.status_code == 200
        payload = response.json(); assert payload["evaluation"]["misconception_code"] == "DIST_001"; assert payload["next_problem"] is not None
    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(prerequisite_id)
    assisted_problem = _problem(str(prerequisite_problem_ids[0]), curriculum_id)
    assisted = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": str(assisted_problem.id), "answer": assisted_problem.canonical_answer, "assistance_level": 3})
    assert assisted.status_code == 200 and assisted.json()["focus"]["in_remediation"] is True
    for index, prerequisite_problem_id in enumerate(prerequisite_problem_ids):
        problem = _problem(str(prerequisite_problem_id), curriculum_id)
        independent = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={"problem_id": str(problem.id), "answer": problem.canonical_answer, "assistance_level": 0})
        assert independent.status_code == 200
        payload = independent.json()
        if index == 0: assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["in_remediation"] is False
    assert payload["focus"]["active_skill_id"] == str(target_id)
    assert payload["tutor"]["action"] == "RESUME_TARGET"
    assert payload["next_problem"] is not None
