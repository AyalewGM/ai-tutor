"""Gate-4 committed-revision regression against an isolated, seeded PostgreSQL DB.

Requires TEST_DATABASE_URL and MIHUR_GATE4_ISOLATED_DB=1. Seed at least one
Attempt, DiagnosticAttempt and MasteryEvent before running. No production use.
"""
import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, Table, create_engine, delete, inspect, select
from sqlalchemy.orm import Session

from app.canonical_skill_taxonomy import (
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
)
from app.canonical_taxonomy_reconciliation import (
    PersistedSkillIdentity,
    validate_identity_revision,
)
from app.curriculum_models import CanonicalSkill
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.models import Attempt, MasteryEvent, Problem, Skill, Student, TutorSession


def test_committed_taxonomy_revision_preserves_all_three_evidence_models():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires TEST_DATABASE_URL for a seeded isolated PostgreSQL DB")
    if os.getenv("MIHUR_GATE4_ISOLATED_DB") != "1":
        pytest.skip("Requires explicit MIHUR_GATE4_ISOLATED_DB=1 safety opt-in")
    assert url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://"))
    engine = create_engine(url)
    code = f"MATH.TEST.GATE4.{uuid4().hex.upper()}"
    new_id = uuid4()
    committed = False
    fixture_ready = False
    fixture_ids = {}
    try:

        # Create representative persisted evidence in the isolated migrated DB.
        with Session(engine) as session:
            skill = session.scalar(select(Skill).limit(1))
            assert skill is not None, "CI must seed at least one local skill"
            student = Student(first_name="Gate4 synthetic", grade_level="1")
            session.add(student)
            session.flush()
            problem = Problem(
                primary_skill_id=skill.id, problem_type="GATE4_TEST",
                difficulty=1, prompt="1+1?", canonical_answer="2",
            )
            session.add(problem)
            session.flush()
            tutor = TutorSession(student_id=student.id, primary_skill_id=skill.id)
            diagnostic = DiagnosticSession(
                student_id=student.id, target_skill_id=skill.id,
                current_skill_id=skill.id,
            )
            session.add_all([tutor, diagnostic])
            session.flush()
            attempt = Attempt(
                session_id=tutor.id, student_id=student.id,
                problem_id=problem.id, student_answer="2", is_correct=True,
            )
            diagnostic_attempt = DiagnosticAttempt(
                diagnostic_session_id=diagnostic.id, skill_id=skill.id,
                problem_id=problem.id, student_answer="2",
                is_correct=True, sequence_number=1,
            )
            session.add_all([attempt, diagnostic_attempt])
            session.flush()
            mastery = MasteryEvent(
                student_id=student.id, skill_id=skill.id, attempt_id=attempt.id,
                previous_score=Decimal("0.100"), new_score=Decimal("0.200"),
                previous_confidence=Decimal("0.100"),
                new_confidence=Decimal("0.200"), reason="gate4-synthetic",
            )
            session.add(mastery)
            session.flush()
            fixture_ids = {
                MasteryEvent: mastery.id,
                DiagnosticAttempt: diagnostic_attempt.id,
                Attempt: attempt.id,
                DiagnosticSession: diagnostic.id,
                TutorSession: tutor.id,
                Problem: problem.id,
                Student: student.id,
            }
            session.commit()
            fixture_ready = True

        with engine.connect() as connection:
            inspector = inspect(connection)
            names = set(inspector.get_table_names())
            evidence_names = ("attempts", "diagnostic_attempts", "mastery_events")
            assert set(evidence_names) <= names, "All three evidence tables are required"
            metadata = MetaData()
            evidence_tables = {
                name: Table(name, metadata, autoload_with=connection)
                for name in evidence_names
            }
            # Capture every persisted column, not only skill references.
            before = {
                name: [dict(row) for row in connection.execute(select(table)).mappings()]
                for name, table in evidence_tables.items()
            }
            assert all(before.values()), "All three evidence tables must be populated"
            variant_tables = {
                name: Table(name, metadata, autoload_with=connection)
                for name in names if "variant" in name.lower()
            }
            variants_before = {
                name: [dict(row) for row in connection.execute(select(table)).mappings()]
                for name, table in variant_tables.items()
            }

        with Session(engine) as session:
            original = {
                row.code: PersistedSkillIdentity(row.code, row.id)
                for row in session.scalars(select(CanonicalSkill))
            }
            definition = CanonicalSkillDefinition(
                code=code,
                name="Gate-4 synthetic identity",
                description="Synthetic, isolated database test only",
                review_state=SkillReviewState.REVIEWED,
                reviewed_by="gate4-test-fixture",
            )
            taxonomy = CanonicalTaxonomy("gate4-test-only", {code: definition})
            proposed = {
                **original,
                code: PersistedSkillIdentity(code, new_id),
            }
            validate_identity_revision(original, proposed, taxonomy)
            session.add(CanonicalSkill(
                id=new_id, code=code, name=definition.name,
                description=definition.description,
            ))
            session.commit()  # Must be a real committed revision, not flush/rollback.
            committed = True

        with engine.connect() as connection:
            assert connection.scalar(
                select(CanonicalSkill.id).where(CanonicalSkill.code == code)
            ) == new_id
            after = {
                name: [dict(row) for row in connection.execute(select(table)).mappings()]
                for name, table in evidence_tables.items()
            }
            assert after == before, "Committed taxonomy revision mutated learner evidence"
            assert {
                name: [dict(row) for row in connection.execute(select(table)).mappings()]
                for name, table in variant_tables.items()
            } == variants_before, "Historical variant references changed"
            assert len(after["mastery_events"]) == len(before["mastery_events"])
        with Session(engine) as session:
            current = {
                row.code: PersistedSkillIdentity(row.code, row.id)
                for row in session.scalars(select(CanonicalSkill))
            }
            assert all(current[k] == v for k, v in original.items())
    finally:
        if committed:
            # Only remove our own synthetic row in the explicitly isolated DB.
            with engine.begin() as connection:
                connection.execute(
                    delete(CanonicalSkill).where(
                        CanonicalSkill.id == new_id,
                        CanonicalSkill.code == code,
                    )
                )
        if fixture_ready:
            with engine.begin() as connection:
                for model, row_id in fixture_ids.items():
                    connection.execute(delete(model).where(model.id == row_id))
        engine.dispose()
