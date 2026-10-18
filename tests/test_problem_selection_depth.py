import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.core.database import Base
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    TutorSession,
    TutorState,
)
from app.services.evaluation import evaluate_problem
from app.services.problem_selection import select_next_problem


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@compiles(UUID, "sqlite")
def _compile_uuid_for_sqlite(_type, _compiler, **_kwargs):
    return "CHAR(36)"


@contextmanager
def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [
        Curriculum.__table__,
        Student.__table__,
        Skill.__table__,
        Problem.__table__,
        TutorSession.__table__,
        Attempt.__table__,
        ProblemContentMetadata.__table__,
        MasteryEvent.__table__,
        DiagnosticSession.__table__,
        DiagnosticAttempt.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    with Session(engine) as db:
        yield db


def _curriculum(db):
    curriculum = Curriculum(
        code=f"SELECTION-QA-{uuid.uuid4().hex[:10]}",
        name="Synthetic selection curriculum",
        version="1",
    )
    db.add(curriculum)
    db.flush()
    return curriculum


def _skill(db, curriculum, *, problem_type: str = "UNSUPPORTED_TYPE"):
    skill = Skill(
        curriculum_id=curriculum.id,
        code=f"SELECTION.QA.{uuid.uuid4().hex[:12]}",
        name="Synthetic selection isolation",
        description="Synthetic fixture for server-side selection tests.",
        difficulty_level=1,
    )
    db.add(skill)
    db.flush()
    seed = Problem(
        primary_skill_id=skill.id,
        problem_type=problem_type,
        difficulty=1,
        prompt=f"Synthetic seed {uuid.uuid4()}",
        canonical_answer="1",
    )
    db.add(seed)
    db.flush()
    return skill, seed


def _student_and_session(db, curriculum, skill):
    student = Student(
        curriculum_id=curriculum.id,
        first_name="Selection QA",
        grade_level="8",
        school_system="SYNTHETIC",
    )
    db.add(student)
    db.flush()
    session = TutorSession(student_id=student.id, primary_skill_id=skill.id)
    db.add(session)
    db.flush()
    return student, session


def _authorized_problem(db, curriculum, skill, *, mode: str, label: str):
    problem = Problem(
        primary_skill_id=skill.id,
        problem_type="UNSUPPORTED_TYPE",
        difficulty=1,
        prompt=f"{label} {uuid.uuid4()}",
        canonical_answer="1",
    )
    db.add(problem)
    db.flush()
    flags = {
        "diagnostic_eligible": False,
        "guided_eligible": False,
        "independent_eligible": False,
        "mastery_eligible": False,
    }
    flags[mode] = True
    db.add(
        ProblemContentMetadata(
            problem_id=problem.id,
            curriculum_id=curriculum.id,
            objective=f"Synthetic {label} candidate.",
            evaluation_type="EXACT",
            **flags,
        )
    )
    db.flush()
    return problem


@pytest.mark.parametrize(
    ("state", "mode"),
    [
        (TutorState.DIAGNOSE, "diagnostic_eligible"),
        (TutorState.INTRODUCE, "guided_eligible"),
        (TutorState.MODEL, "guided_eligible"),
        (TutorState.GUIDED_PRACTICE, "guided_eligible"),
        (TutorState.REMEDIATION, "guided_eligible"),
        (TutorState.INDEPENDENT_PRACTICE, "independent_eligible"),
        (TutorState.REVIEW, "independent_eligible"),
        (TutorState.MASTERY_CHECK, "mastery_eligible"),
    ],
)
def test_selection_uses_only_explicit_mode_metadata(state, mode) -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, metadata_free = _skill(db, curriculum)
        expected = _authorized_problem(db, curriculum, skill, mode=mode, label=mode)
        for other_mode in {
            "diagnostic_eligible",
            "guided_eligible",
            "independent_eligible",
            "mastery_eligible",
        } - {mode}:
            _authorized_problem(db, curriculum, skill, mode=other_mode, label=other_mode)
        student, session = _student_and_session(db, curriculum, skill)

        selected = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=state,
            student_id=student.id,
            session_id=session.id,
        )

        assert selected is not None
        assert selected.id == expected.id
        assert selected.id != metadata_free.id
        db.rollback()


def test_complete_state_and_missing_metadata_fail_closed() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, _ = _skill(db, curriculum)
        student, session = _student_and_session(db, curriculum, skill)

        selected = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=TutorState.COMPLETE,
            student_id=student.id,
            session_id=session.id,
        )

        assert selected is None
        db.rollback()


def test_cross_session_history_prefers_unseen_then_fails_closed() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, _ = _skill(db, curriculum)
        first = _authorized_problem(
            db, curriculum, skill, mode="independent_eligible", label="first"
        )
        second = _authorized_problem(
            db, curriculum, skill, mode="independent_eligible", label="second"
        )
        student, prior_session = _student_and_session(db, curriculum, skill)
        current_session = TutorSession(student_id=student.id, primary_skill_id=skill.id)
        db.add(current_session)
        db.flush()
        old = datetime.now(UTC) - timedelta(days=2)
        db.add(
            Attempt(
                session_id=prior_session.id,
                student_id=student.id,
                problem_id=first.id,
                student_answer="1",
                is_correct=True,
                created_at=old,
            )
        )
        db.flush()

        unseen = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=TutorState.INDEPENDENT_PRACTICE,
            session_id=current_session.id,
        )
        assert unseen is not None and unseen.id == second.id

        db.add(
            Attempt(
                session_id=current_session.id,
                student_id=student.id,
                problem_id=second.id,
                student_answer="1",
                is_correct=True,
                created_at=datetime.now(UTC),
            )
        )
        db.flush()
        exhausted = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=TutorState.INDEPENDENT_PRACTICE,
            session_id=current_session.id,
        )
        assert exhausted is None
        db.rollback()


def test_diagnostic_history_is_excluded_across_diagnostic_sessions() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, _ = _skill(db, curriculum)
        first = _authorized_problem(
            db, curriculum, skill, mode="diagnostic_eligible", label="first diagnostic"
        )
        second = _authorized_problem(
            db, curriculum, skill, mode="diagnostic_eligible", label="second diagnostic"
        )
        student, _ = _student_and_session(db, curriculum, skill)
        diagnostic_session = DiagnosticSession(
            student_id=student.id,
            target_skill_id=skill.id,
            current_skill_id=skill.id,
        )
        db.add(diagnostic_session)
        db.flush()
        db.add(
            DiagnosticAttempt(
                diagnostic_session_id=diagnostic_session.id,
                skill_id=skill.id,
                problem_id=first.id,
                student_answer="1",
                normalized_answer="1",
                is_correct=True,
                sequence_number=1,
            )
        )
        db.flush()

        selected = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=TutorState.DIAGNOSE,
            student_id=student.id,
        )

        assert selected is not None and selected.id == second.id
        db.rollback()


def test_generated_retry_is_idempotent_and_mode_bound_without_history_writes() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, seed = _skill(db, curriculum, problem_type="SOLVE_EQUATION")
        db.add(
            ProblemContentMetadata(
                problem_id=seed.id,
                curriculum_id=curriculum.id,
                objective="Synthetic authorized generator source.",
                evaluation_type="EXACT",
                mastery_eligible=True,
            )
        )
        db.flush()
        student, session = _student_and_session(db, curriculum, skill)
        attempt = Attempt(
            session_id=session.id,
            student_id=student.id,
            problem_id=seed.id,
            student_answer="x=1",
            normalized_answer="x=1",
            is_correct=False,
            state_at_attempt=TutorState.MASTERY_CHECK,
        )
        db.add(attempt)
        db.flush()
        mastery_event = MasteryEvent(
            student_id=student.id,
            skill_id=skill.id,
            attempt_id=attempt.id,
            previous_score=Decimal("0.400"),
            new_score=Decimal("0.400"),
            previous_confidence=Decimal("0.500"),
            new_confidence=Decimal("0.500"),
            reason="SYNTHETIC_PRESERVATION_SENTINEL",
            metadata_json={"sentinel": True},
        )
        db.add(mastery_event)
        diagnostic_session = DiagnosticSession(
            student_id=student.id,
            target_skill_id=skill.id,
            current_skill_id=skill.id,
            status="COMPLETED",
        )
        db.add(diagnostic_session)
        db.flush()
        diagnostic_attempt = DiagnosticAttempt(
            diagnostic_session_id=diagnostic_session.id,
            skill_id=skill.id,
            problem_id=seed.id,
            student_answer="x=1",
            normalized_answer="x=1",
            is_correct=False,
            sequence_number=1,
        )
        db.add(diagnostic_attempt)
        db.flush()
        before = {
            "attempt": (
                attempt.id,
                attempt.student_answer,
                attempt.normalized_answer,
                attempt.is_correct,
                attempt.state_at_attempt,
            ),
            "diagnostic_attempts": tuple(
                db.execute(
                    select(
                        DiagnosticAttempt.id,
                        DiagnosticAttempt.student_answer,
                        DiagnosticAttempt.is_correct,
                    ).order_by(DiagnosticAttempt.id)
                ).all()
            ),
            "mastery_event": (
                mastery_event.id,
                mastery_event.previous_score,
                mastery_event.new_score,
                mastery_event.reason,
                mastery_event.metadata_json,
            ),
        }

        first = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=2,
            state=TutorState.MASTERY_CHECK,
            session_id=session.id,
        )
        second = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=2,
            state=TutorState.MASTERY_CHECK,
            session_id=session.id,
        )

        assert first is not None and second is not None
        assert first.id == second.id
        assert first.source_type == "GENERATED"
        assert evaluate_problem(
            first.prompt, first.canonical_answer, first.canonical_answer
        ).correct
        assert not evaluate_problem(first.prompt, first.canonical_answer, "x=999999").correct
        metadata = db.scalar(
            select(ProblemContentMetadata).where(
                ProblemContentMetadata.problem_id == first.id
            )
        )
        assert metadata is not None
        assert metadata.mastery_eligible is True
        assert metadata.diagnostic_eligible is False
        assert metadata.guided_eligible is False
        assert metadata.independent_eligible is False
        assert metadata.extension_eligible is False
        assert db.scalar(
            select(func.count())
            .select_from(Problem)
            .where(
                Problem.primary_skill_id == skill.id,
                Problem.source_type == "GENERATED",
            )
        ) == 1
        after = {
            "attempt": (
                attempt.id,
                attempt.student_answer,
                attempt.normalized_answer,
                attempt.is_correct,
                attempt.state_at_attempt,
            ),
            "diagnostic_attempts": tuple(
                db.execute(
                    select(
                        DiagnosticAttempt.id,
                        DiagnosticAttempt.student_answer,
                        DiagnosticAttempt.is_correct,
                    ).order_by(DiagnosticAttempt.id)
                ).all()
            ),
            "mastery_event": (
                mastery_event.id,
                mastery_event.previous_score,
                mastery_event.new_score,
                mastery_event.reason,
                mastery_event.metadata_json,
            ),
        }
        assert after == before
        db.rollback()


def test_metadata_free_generator_type_is_not_promoted_into_assessment() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, _ = _skill(db, curriculum, problem_type="SOLVE_EQUATION")
        _student, session = _student_and_session(db, curriculum, skill)

        selected = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=2,
            state=TutorState.MASTERY_CHECK,
            session_id=session.id,
        )

        assert selected is None
        assert db.scalar(
            select(func.count())
            .select_from(Problem)
            .where(Problem.source_type == "GENERATED")
        ) == 0
        db.rollback()


def test_session_student_mismatch_is_rejected() -> None:
    with _session() as db:
        curriculum = _curriculum(db)
        skill, _ = _skill(db, curriculum)
        student, session = _student_and_session(db, curriculum, skill)

        with pytest.raises(ValueError, match="does not match"):
            select_next_problem(
                db,
                skill_id=skill.id,
                current_problem_id=None,
                current_difficulty=1,
                state=TutorState.DIAGNOSE,
                student_id=uuid.uuid4(),
                session_id=session.id,
            )
        assert student.id != uuid.UUID(int=0)
        db.rollback()
