"""Opt-in database regression for existing canonical and learner UUID references.

Requires TEST_DATABASE_URL pointing to an isolated, fully migrated test DB.
This check reads existing records and never mutates learner evidence.
"""
import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.canonical_skill_taxonomy import CanonicalTaxonomy
from app.canonical_taxonomy_reconciliation import (
    PersistedSkillIdentity,
    validate_identity_revision,
)
from app.curriculum_models import CanonicalSkill
from app.models import Attempt, Problem, Skill, StudentSkill


def test_database_identity_and_evidence_references():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for isolated migrated database regression")
    engine = create_engine(url)
    try:
        with Session(engine) as session:
            catalog = session.execute(select(CanonicalSkill)).scalars().all()
            snapshot = {
                row.code: PersistedSkillIdentity(row.code, row.id) for row in catalog
            }
            assert len(snapshot) == len(catalog)
            validate_identity_revision(snapshot, dict(snapshot), CanonicalTaxonomy("db-check", {}))
            local_ids = set(session.execute(select(Skill.id)).scalars())
            assert set(session.execute(select(StudentSkill.skill_id)).scalars()) <= local_ids
            problem_skills = dict(session.execute(select(Problem.id, Problem.primary_skill_id)))
            assert set(problem_skills.values()) <= local_ids
            for attempt in session.execute(select(Attempt)).scalars():
                assert attempt.problem_id in problem_skills
                assert problem_skills[attempt.problem_id] in local_ids
            assert {
                row.code: row.id
                for row in session.execute(select(CanonicalSkill)).scalars()
            } == {code: row.skill_id for code, row in snapshot.items()}
    finally:
        engine.dispose()
