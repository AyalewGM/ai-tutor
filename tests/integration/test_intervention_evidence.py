import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import (
    Attempt,
    Curriculum,
    InterventionRecord,
    Problem,
    Skill,
    SkillPrerequisite,
    Student,
    TutorSession,
)
from app.services.intervention_evidence import (
    evaluate_persisted_intervention,
    record_intervention_decision,
)
from app.services.intervention_policy import InterventionState
from tests.fixtures import TEST_PROVENANCE


def _problem(skill_id: uuid.UUID, suffix: str) -> Problem:
    return Problem(
        primary_skill_id=skill_id,
        problem_type="F010_TEST",
        difficulty=2,
        prompt=f"F-010 deterministic evidence {suffix}",
        canonical_answer="0",
        solution={"source": "integration-test", "provenance": TEST_PROVENANCE},
        source_type="CURATED",
    )


def test_persisted_evidence_projects_and_records_auditable_gap() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        assert curriculum is not None
        # Dedicated F010 skills keep fixture problems off real seeded skills so
        # they can never be served to other tests via problem selection.
        target = Skill(
            curriculum_id=curriculum.id,
            code=f"F010.TARGET.{uuid.uuid4().hex[:8]}",
            name="F010 evidence target",
            difficulty_level=99,
        )
        prerequisite = Skill(
            curriculum_id=curriculum.id,
            code=f"F010.PREREQ.{uuid.uuid4().hex[:8]}",
            name="F010 evidence prerequisite",
            difficulty_level=99,
        )
        db.add_all([target, prerequisite])
        db.flush()
        db.add(
            SkillPrerequisite(
                skill_id=target.id,
                prerequisite_skill_id=prerequisite.id,
            )
        )
        db.flush()

        student = Student(
            curriculum_id=curriculum.id,
            first_name="F010 Evidence Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()

        target_session = TutorSession(
            student_id=student.id,
            primary_skill_id=target.id,
            active_skill_id=target.id,
            curriculum_id=curriculum.id,
        )
        prerequisite_session = TutorSession(
            student_id=student.id,
            primary_skill_id=prerequisite.id,
            active_skill_id=prerequisite.id,
            curriculum_id=curriculum.id,
        )
        target_problems = [_problem(target.id, f"target-{index}") for index in range(2)]
        prerequisite_problems = [
            _problem(prerequisite.id, f"prerequisite-{index}") for index in range(2)
        ]
        db.add_all(
            [
                target_session,
                prerequisite_session,
                *target_problems,
                *prerequisite_problems,
            ]
        )
        db.flush()

        attempts = []
        for index, problem in enumerate(target_problems):
            attempts.append(
                Attempt(
                    session_id=target_session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="wrong",
                    is_correct=False,
                    attempt_number=1,
                    assistance_level=0,
                    created_at=now - timedelta(minutes=10 - index),
                )
            )
        for index, problem in enumerate(prerequisite_problems):
            attempts.append(
                Attempt(
                    session_id=prerequisite_session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="wrong",
                    is_correct=False,
                    attempt_number=1,
                    assistance_level=0,
                    created_at=now - timedelta(minutes=5 - index),
                )
            )
        db.add_all(attempts)
        db.flush()

        decision = evaluate_persisted_intervention(
            db,
            student_id=student.id,
            curriculum_id=curriculum.id,
            target_skill_id=target.id,
            evidence_window_start=now - timedelta(days=7),
        )

        assert decision.state == InterventionState.PREREQUISITE_GAP_CONFIRMED
        assert decision.selected_prerequisite_skill_id == prerequisite.id
        assert decision.policy_version == "pilot-v1"
        assert len(decision.evidence_ids) == 4

        record = record_intervention_decision(
            db,
            student_id=student.id,
            curriculum_id=curriculum.id,
            target_skill_id=target.id,
            decision=decision,
        )
        db.commit()
        record_id = record.id

    with SessionLocal() as db:
        persisted = db.get(InterventionRecord, record_id)
        assert persisted is not None
        assert persisted.state == InterventionState.PREREQUISITE_GAP_CONFIRMED.value
        assert persisted.status == "RECOMMENDED"
        assert persisted.policy_version == "pilot-v1"
        assert len(persisted.evidence_ids_json) == 4
