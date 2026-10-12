"""Opt-in rollback-only persistence proof for a generatorless canonical skill."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.canonical_skill_taxonomy import (
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
)
from app.curriculum_models import CanonicalSkill
from app.models import MasteryEvent, StudentSkill


def test_generatorless_canonical_skill_additive_persistence():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires isolated migrated TEST_DATABASE_URL")
    engine = create_engine(url)
    try:
        with Session(engine) as session:
            original = dict(session.execute(select(CanonicalSkill.code, CanonicalSkill.id)).all())
            mastery = set(session.execute(select(StudentSkill.student_id, StudentSkill.skill_id)).all())
            events = dict(session.execute(select(MasteryEvent.id, MasteryEvent.skill_id)).all())
            code = f"MATH.TEST.GENERATORLESS.{uuid4().hex.upper()}"
            definition = CanonicalSkillDefinition(
                code=code,
                name="Synthetic generatorless skill",
                description="Test-only definition; no generator",
                review_state=SkillReviewState.REVIEWED,
                reviewed_by="test-reviewer",
            )
            taxonomy = CanonicalTaxonomy("test-only", {code: definition})
            assert taxonomy.capability(code, set()) == (True, False)
            try:
                session.add(CanonicalSkill(
                    id=uuid4(),
                    code=code,
                    name=definition.name,
                    description=definition.description,
                ))
                session.flush()
                assert session.scalar(
                    select(CanonicalSkill.id).where(CanonicalSkill.code == code)
                ) is not None
                assert dict(
                    session.execute(select(CanonicalSkill.code, CanonicalSkill.id)).all()
                ).items() >= original.items()
                assert set(
                    session.execute(select(StudentSkill.student_id, StudentSkill.skill_id)).all()
                ) == mastery
                assert dict(
                    session.execute(select(MasteryEvent.id, MasteryEvent.skill_id)).all()
                ) == events
            finally:
                session.rollback()
            assert session.scalar(
                select(CanonicalSkill.id).where(CanonicalSkill.code == code)
            ) is None
    finally:
        engine.dispose()
