"""Isolated PostgreSQL concurrency proof for inactive rational attempt recording.

No content activation or mastery credit. The trusted scorer is replaced with a
fixed, accepted decision in this test: only database locking/replay is tested.
"""
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

import app.services.atomic_rational_attempt as recorder
from app.core.database import Base
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
from app.services.family_activation_adapter import DENIED, RegistrationDecision
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.persisted_rational_resolution import TrustedAssessmentContext


@pytest.mark.skipif(
    os.getenv("MIHUR_GATE4_ISOLATED_DB") != "1" or not os.getenv("TEST_DATABASE_URL"),
    reason="requires isolated PostgreSQL CI database with explicit opt-in",
)
def test_two_connections_one_student_problem_commit_then_replay_denied(monkeypatch):
    url = os.environ["TEST_DATABASE_URL"]
    schema = "atomic_rational_" + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"}, pool_size=4)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db, db.begin():
            curriculum = Curriculum(code="SYNTHETIC_ATOMIC", name="Isolated atomic test", version="1")
            db.add(curriculum)
            db.flush()
            skill = Skill(curriculum_id=curriculum.id, code="SYNTHETIC.ATOMIC", name="Atomic test")
            db.add(skill)
            db.flush()
            student = Student(curriculum_id=curriculum.id, first_name="Synthetic", grade_level="9")
            db.add(student)
            db.flush()
            problem = Problem(
                primary_skill_id=skill.id, problem_type="SYNTHETIC",
                difficulty=1, prompt="Synthetic test only", canonical_answer="x=1/2",
            )
            db.add(problem)
            db.flush()
            sessions = []
            for _ in range(2):
                session = TutorSession(
                    student_id=student.id, curriculum_id=curriculum.id,
                    primary_skill_id=skill.id, current_state=TutorState.INDEPENDENT_PRACTICE,
                    status="ACTIVE",
                )
                db.add(session)
                db.flush()
                sessions.append(session.id)
            student_id, problem_id = student.id, problem.id

        # Reject an unsupported real PostgreSQL transaction before any scorer or
        # recorder writes. Read back both tables after commit to prove no effect.
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            with Session(bind=connection) as db, db.begin():
                assert db.connection().get_isolation_level() == "REPEATABLE READ"
                scorer_calls = []
                monkeypatch.setattr(
                    recorder, "score_persisted_rational",
                    lambda *_args, **_kwargs: scorer_calls.append(True),
                )
                rejected = recorder.record_rational_attempt(
                    db,
                    context=TrustedAssessmentContext(
                        student_id, sessions[0], problem_id, AssessmentMode.INDEPENDENT,
                    ),
                    submission="x=2/4", approval_source=object(),
                    service_principal="synthetic",
                )
                assert rejected.decision == DENIED and rejected.attempt_id is None
                assert not scorer_calls
        # SQLAlchemy still reports READ COMMITTED under driver AUTOCOMMIT,
        # despite db.begin() creating a logical Session transaction.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            with Session(bind=connection) as db, db.begin():
                assert db.in_transaction()
                actual = db.connection()
                assert actual.get_isolation_level() == "READ COMMITTED"
                assert actual.connection.driver_connection.autocommit is True
                monkeypatch.setattr(
                    db, "scalar",
                    lambda *_args, **_kwargs: pytest.fail("recorder queried before autocommit denial"),
                )
                scorer_calls = []
                monkeypatch.setattr(
                    recorder, "score_persisted_rational",
                    lambda *_args, **_kwargs: scorer_calls.append(True),
                )
                rejected = recorder.record_rational_attempt(
                    db,
                    context=TrustedAssessmentContext(
                        student_id, sessions[0], problem_id, AssessmentMode.INDEPENDENT,
                    ),
                    submission="x=2/4", approval_source=object(),
                    service_principal="synthetic",
                )
                assert rejected.decision == DENIED and rejected.attempt_id is None
                assert not scorer_calls
        with Session(engine) as db:
            assert db.connection().get_isolation_level() == "READ COMMITTED"
            assert db.connection().connection.driver_connection.autocommit is False
            assert db.scalar(select(func.count()).select_from(Attempt)) == 0
            assert db.scalar(select(func.count()).select_from(MasteryEvent)) == 0

        # Only the attempt-store serialization contract is tested here; the
        # real trusted registration and issuance checks have separate tests.
        monkeypatch.setattr(
            recorder, "score_persisted_rational",
            lambda *_args, **_kwargs: RegistrationDecision(True, True, False),
        )
        written = threading.Event()
        allow_commit = threading.Event()
        second_started = threading.Event()
        second_done = threading.Event()

        def submit(session_id, hold=False):
            with Session(engine) as db, db.begin():
                context = TrustedAssessmentContext(
                    student_id, session_id, problem_id, AssessmentMode.INDEPENDENT,
                )
                if not hold:
                    second_started.set()
                decision = recorder.record_rational_attempt(
                    db, context=context, submission="x=2/4",
                    approval_source=object(), service_principal="synthetic",
                )
                if hold:
                    written.set()
                    assert allow_commit.wait(20), "first transaction was not released"
                else:
                    second_done.set()
                return decision

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(submit, sessions[0], True)
            try:
                assert written.wait(20), "first attempt was not written"
                second = pool.submit(submit, sessions[1], False)
                assert second_started.wait(20), "second transaction did not start"
                assert not second_done.wait(0.3), "concurrent submission bypassed row lock"
            finally:
                allow_commit.set()
            first_result = first.result(timeout=30)
            second_result = second.result(timeout=30)

        assert first_result.decision.eligible and first_result.attempt_id is not None
        assert second_result.decision == DENIED and second_result.attempt_id is None
        with Session(engine) as db:
            attempts = db.scalars(select(Attempt)).all()
            assert len(attempts) == 1
            assert attempts[0].session_id == sessions[0]
            assert attempts[0].student_id == student_id
            assert db.scalar(select(func.count()).select_from(MasteryEvent)) == 0
        with Session(engine) as db, db.begin():
                replay = recorder.record_rational_attempt(
                    db,
                    context=TrustedAssessmentContext(
                        student_id, sessions[1], problem_id, AssessmentMode.INDEPENDENT,
                    ),
                    submission="x=2/4", approval_source=object(),
                    service_principal="synthetic",
                )
                assert replay.decision == DENIED and replay.attempt_id is None
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()
