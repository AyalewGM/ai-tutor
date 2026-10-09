"""Database-backed, non-destructive canonical identity regression for #282.

Runs inside a transaction that is always rolled back. No production data or
runtime taxonomy publication is modified.
"""
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.canonical_taxonomy_reconciliation import (
    PersistedSkillIdentity,
    validate_identity_revision,
)
from app.canonical_skill_taxonomy import CanonicalTaxonomy
from app.curriculum_models import CanonicalSkill
from app.models import Attempt, Problem, Skill, StudentSkill


@pytest.mark.asyncio
async def test_canonical_revision_preserves_existing_database_references(db_session):
    """Read actual rows; reject any proposed rekey before writing changes."""
    existing = (await db_session.execute(select(CanonicalSkill))).scalars().all()
    snapshot = {
        row.code: PersistedSkillIdentity(code=row.code, skill_id=row.id)
        for row in existing
    }
    # Empty or unchanged production catalog is a safe no-op, not an approval.
    validate_identity_revision(snapshot, dict(snapshot), CanonicalTaxonomy("db-check", {}))
    assert {
        row.code: row.id
        for row in (await db_session.execute(select(CanonicalSkill))).scalars()
    } == {code: row.skill_id for code, row in snapshot.items()}

    # All historical learner evidence must still resolve to local Skill UUIDs.
    local_ids = set((await db_session.execute(select(Skill.id))).scalars())
    mastery_ids = set((await db_session.execute(select(StudentSkill.skill_id))).scalars())
    problem_ids = set((await db_session.execute(select(Problem.primary_skill_id))).scalars())
    assert mastery_ids <= local_ids
    assert problem_ids <= local_ids

    problem_by_id = dict((await db_session.execute(select(Problem.id, Problem.primary_skill_id))).all())
    for attempt in (await db_session.execute(select(Attempt))).scalars():
        assert attempt.problem_id in problem_by_id
        assert problem_by_id[attempt.problem_id] in local_ids
