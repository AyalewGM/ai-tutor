"""Synthetic F-007A learner-flow evidence for the Maryland Algebra I pilot.

The test deliberately keeps pedagogy application-owned: deterministic evaluation,
remediation selection, and mastery evidence remain in the tutor service. No real
learner data or external LLM call is used.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession
from app.services.intervention_evidence import evaluate_persisted_intervention
from app.services.intervention_policy import InterventionState
from scripts.seed_algebra1 import seed

client = TestClient(app)


def _problem(problem_id: str, curriculum_id) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        skill = db.get(Skill, problem.primary_skill_id)
        assert skill is not None
        assert skill.curriculum_id == curriculum_id
        db.expunge(problem)
        return problem


def test_algebra1_pilot_remediation_requires_fresh_independent_evidence() -> None:
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_ALGEBRA_1_2026_27")
        )
        target = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "A1.LINEAR.EQ",
            )
        )
        prerequisite = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "A1.EXPR",
            )
        )
        assert curriculum is not None and target is not None and prerequisite is not None

        misconception_problem = db.scalar(
            select(Problem).where(
                Problem.primary_skill_id == target.id,
                Problem.prompt == "Solve 2(x + 4) = 18.",
            )
        )
        assert misconception_problem is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Synthetic Algebra Learner",
            grade_level="Algebra 1",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()

        prerequisite_problems = db.scalars(
            select(Problem)
            .where(Problem.primary_skill_id == prerequisite.id)
            .order_by(Problem.id)
        ).all()
        target_problems = db.scalars(
            select(Problem)
            .where(Problem.primary_skill_id == target.id)
            .order_by(Problem.id)
        ).all()
        assert len(prerequisite_problems) >= 2
        assert len(target_problems) >= 2

        evidence_session = TutorSession(
            student_id=student.id,
            primary_skill_id=target.id,
            active_skill_id=target.id,
            curriculum_id=curriculum.id,
        )
        db.add(evidence_session)
        db.flush()
        for problem in [*prerequisite_problems[:2], *target_problems[:2]]:
            db.add(
                Attempt(
                    session_id=evidence_session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="synthetic-incorrect",
                    normalized_answer="synthetic-incorrect",
                    is_correct=False,
                    attempt_number=1,
                    assistance_level=0,
                )
            )
        db.commit()

        # Make the release-gate precondition explicit: the persisted, curriculum-local
        # evidence itself must satisfy the deterministic intervention policy before
        # the tutor state machine is asked to route the learner into remediation.
        decision = evaluate_persisted_intervention(
            db,
            student_id=student.id,
            curriculum_id=curriculum.id,
            target_skill_id=target.id,
            evidence_window_start=datetime.now(UTC) - timedelta(days=30),
        )
        assert decision.state == InterventionState.PREREQUISITE_GAP_CONFIRMED
        assert decision.selected_prerequisite_skill_id == prerequisite.id
        assert decision.reason_code == "DECLARED_PREREQUISITE_GAP_CONFIRMED"
        assert len(decision.evidence_ids) >= 4

        student_id = student.id
        curriculum_id = curriculum.id
        target_id = target.id
        prerequisite_id = prerequisite.id
        misconception_problem_id = misconception_problem.id

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(target_id)},
    )
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]

    # Repeated evidence of the same deterministic misconception activates the
    # state-machine remediation transition; the persisted intervention gate then
    # consumes the independently asserted prerequisite-gap evidence above.
    for _ in range(3):
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": str(misconception_problem_id),
                "answer": "2x+4=18",
                "assistance_level": 0,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["evaluation"]["misconception_code"] == "DIST_001"
        assert payload["next_problem"] is not None

    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(prerequisite_id)
    problem_id = payload["next_problem"]["id"]
    _problem(problem_id, curriculum_id)

    problem = _problem(problem_id, curriculum_id)
    assisted = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": problem_id,
            "answer": problem.canonical_answer,
            "assistance_level": 3,
        },
    )
    assert assisted.status_code == 200
    payload = assisted.json()
    assert payload["focus"]["in_remediation"] is True
    problem_id = payload["next_problem"]["id"]

    for _ in range(6):
        problem = _problem(problem_id, curriculum_id)
        independent = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": problem_id,
                "answer": problem.canonical_answer,
                "assistance_level": 0,
            },
        )
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
