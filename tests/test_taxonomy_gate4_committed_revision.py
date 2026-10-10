"""Gate-4 committed-revision regression against an isolated, seeded PostgreSQL DB.

Requires TEST_DATABASE_URL and MIHUR_GATE4_ISOLATED_DB=1. Seed at least one
Attempt, DiagnosticAttempt and MasteryEvent before running. No production use.
"""
import os
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
    try:
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
            assert all(before.values()), "Seed one or more records in each evidence table"

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
        engine.dispose()
