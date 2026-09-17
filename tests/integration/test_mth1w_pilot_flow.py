"""Synthetic F-007A/F-016 learner-to-parent evidence for the Ontario MTH1W pilot.

Pedagogy remains application-owned: deterministic evaluation, remediation selection,
and mastery evidence stay in the tutor service. No real learner data or external LLM
call is used.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.identity import current_user
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession, User
from app.parent_models import ChildLinkClaim
from app.services.intervention_evidence import evaluate_persisted_intervention
from app.services.intervention_policy import InterventionState
from app.services.parent_dashboard import hash_claim_token
from scripts.seed_mth1w import seed

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


def _override_user(user: User) -> None:
    app.dependency_overrides[current_user] = lambda: user


def _clear_override() -> None:
    app.dependency_overrides.pop(current_user, None)


def test_mth1w_pilot_remediation_requires_fresh_independent_evidence() -> None:
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "ON_MTH1W_2021"))
        target = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.C.ALG",
            )
        )
        prerequisite = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM",
            )
        )
        assert curriculum is not None and target is not None and prerequisite is not None

        misconception_problem = db.scalar(
            select(Problem).where(
                Problem.primary_skill_id == target.id,
                Problem.prompt == "Simplify 4(x + 3).",
            )
        )
        assert misconception_problem is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Synthetic Ontario Learner",
            grade_level="9",
            school_system="Ontario",
        )
        db.add(student)
        db.flush()

        prerequisite_problems = db.scalars(
            select(Problem)
            .where(Problem.primary_skill_id == prerequisite.id)
            .order_by(Problem.id)
        ).all()
        target_problems = db.scalars(
            select(Problem).where(Problem.primary_skill_id == target.id).order_by(Problem.id)
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
        prerequisite_problem_ids = [problem.id for problem in prerequisite_problems[:2]]
        misconception_problem_id = misconception_problem.id
        misconception_problem_answer = misconception_problem.canonical_answer

    created = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(target_id)},
    )
    assert created.status_code == 200
    payload = created.json()
    session_id = payload["session_id"]

    diagnostic = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": str(misconception_problem_id),
            "answer": misconception_problem_answer,
            "assistance_level": 0,
        },
    )
    assert diagnostic.status_code == 200
    payload = diagnostic.json()
    assert payload["state"] == "GUIDED_PRACTICE"
    assert payload["focus"]["in_remediation"] is False

    for _ in range(2):
        response = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": str(misconception_problem_id),
                "answer": "4x+3",
                "assistance_level": 0,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["evaluation"]["misconception_code"] == "DIST_001"
        assert payload["next_problem"] is not None

    assert payload["focus"]["in_remediation"] is True
    assert payload["focus"]["active_skill_id"] == str(prerequisite_id)

    assisted_problem = _problem(str(prerequisite_problem_ids[0]), curriculum_id)
    assisted = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={
            "problem_id": str(assisted_problem.id),
            "answer": assisted_problem.canonical_answer,
            "assistance_level": 3,
        },
    )
    assert assisted.status_code == 200
    payload = assisted.json()
    assert payload["focus"]["in_remediation"] is True

    for index, prerequisite_problem_id in enumerate(prerequisite_problem_ids):
        problem = _problem(str(prerequisite_problem_id), curriculum_id)
        independent = client.post(
            f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
            json={
                "problem_id": str(problem.id),
                "answer": problem.canonical_answer,
                "assistance_level": 0,
            },
        )
        assert independent.status_code == 200
        payload = independent.json()
        if index == 0:
            assert payload["focus"]["in_remediation"] is True

    assert payload["focus"]["in_remediation"] is False
    assert payload["focus"]["active_skill_id"] == str(target_id)
    assert payload["tutor"]["action"] == "RESUME_TARGET"
    assert payload["next_problem"] is not None
    _problem(payload["next_problem"]["id"], curriculum_id)

    # F-016 release evidence: the same synthetic learner journey must project its
    # fresh independent evidence to an authorized parent, while unrelated families
    # remain fail-closed. Linking does not copy or broaden learner data.
    claim_token = "synthetic-f016-parent-claim-token"
    with SessionLocal() as db:
        parent = User(email="f016-parent@example.test", display_name="F016 Parent", role="PARENT")
        unrelated = User(
            email="f016-unrelated@example.test",
            display_name="F016 Unrelated Parent",
            role="PARENT",
        )
        db.add_all([parent, unrelated])
        db.flush()
        db.add(
            ChildLinkClaim(
                student_id=student_id,
                token_hash=hash_claim_token(claim_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        db.commit()
        parent_id = parent.id
        unrelated_id = unrelated.id

    try:
        with SessionLocal() as db:
            parent = db.get(User, parent_id)
            assert parent is not None
            _override_user(parent)
            assert client.post("/api/v1/parents/profile").status_code == 200
            linked = client.post(
                "/api/v1/parents/children/link",
                json={"claim_token": claim_token},
            )
            assert linked.status_code == 200
            assert linked.json()["child"]["curriculum_code"] == "ON_MTH1W_2021"

            dashboard = client.get(f"/api/v1/parents/children/{student_id}/dashboard")
            assert dashboard.status_code == 200
            dashboard_payload = dashboard.json()
            assert dashboard_payload["child"]["curriculum_code"] == "ON_MTH1W_2021"
            prerequisite_progress = next(
                row
                for row in dashboard_payload["skills"]
                if row["skill_code"] == "MTH1W.B.NUM"
            )
            assert prerequisite_progress["independent_correct_count"] >= 2
            assert prerequisite_progress["learning_state"] == "INDEPENDENT_PROGRESS"
            assert prerequisite_progress["assistance_signal"] == "MIXED_INDEPENDENT_AND_ASSISTED"

        with SessionLocal() as db:
            unrelated = db.get(User, unrelated_id)
            assert unrelated is not None
            _override_user(unrelated)
            assert client.post("/api/v1/parents/profile").status_code == 200
            denied = client.get(f"/api/v1/parents/children/{student_id}/dashboard")
            assert denied.status_code == 403
    finally:
        _clear_override()
