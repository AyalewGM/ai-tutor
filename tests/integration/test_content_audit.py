import uuid

import pytest

from app.content_audit import audit_curriculum_skill_traceability
from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.content_validation import ContentValidationError
from app.core.database import SessionLocal
from app.models import Curriculum, Skill


def _isolated_curriculum(db) -> tuple[Curriculum, Skill]:
    suffix = uuid.uuid4().hex[:10]
    curriculum = Curriculum(
        code=f"F007_AUDIT_{suffix}",
        name="F-007 traceability audit fixture",
        jurisdiction="TEST",
        grade_level="TEST",
        version="2026-test",
        source_uri="https://example.edu/f007/audit",
        active=True,
    )
    db.add(curriculum)
    db.flush()
    skill = Skill(
        curriculum_id=curriculum.id,
        code="AUDIT.SKILL.1",
        name="Audit skill",
        difficulty_level=1,
    )
    db.add(skill)
    db.flush()
    return curriculum, skill


def test_traceability_audit_rejects_unmapped_skill() -> None:
    with SessionLocal() as db:
        curriculum, _ = _isolated_curriculum(db)

        with pytest.raises(ContentValidationError, match="must map to at least one"):
            audit_curriculum_skill_traceability(db, curriculum_id=curriculum.id)
        db.rollback()


def test_traceability_audit_accepts_explicit_curriculum_scoped_mapping() -> None:
    with SessionLocal() as db:
        curriculum, skill = _isolated_curriculum(db)
        pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            expectations=(
                ExpectationInput(
                    source_identifier="TEST.EXPECTATION.1",
                    title="Test expectation",
                    strand="Test",
                    source_uri="https://example.edu/f007/audit/expectation-1",
                ),
            ),
            mappings=(
                ExpectationSkillMappingInput(
                    source_identifier="TEST.EXPECTATION.1",
                    skill_code=skill.code,
                ),
            ),
        )
        persist_expectation_pack(db, pack)

        audit_curriculum_skill_traceability(db, curriculum_id=curriculum.id)
        db.rollback()
