import uuid

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_draft_ingestion import CurriculumDraftIngestionError, ingest_draft_pack
from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    ProposedSkillMapping,
    StandardDraft,
)
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumStandard,
    CurriculumVersion,
    StandardSkillMapping,
)
from app.models import Curriculum
from scripts.seed_mth1w import seed as seed_mth1w


def _pack():
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code="MTH1W",
        curriculum_version="2021",
        authority_code="ON_MIN_ED",
        source_uri="https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w",
        standards=(
            StandardDraft(
                code="C1.5",
                title="Create and solve equations",
                source_uri="https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w",
            ),
        ),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="C1.5",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                rationale="Draft alignment for human review",
            ),
        ),
    )


def test_draft_ingestion_is_idempotent_and_unpublished():
    seed_mth1w()
    db = SessionLocal()
    try:
        canonical = db.scalar(
            select(CanonicalSkill).where(CanonicalSkill.code == "MATH.EE.EQUATION.MULTISTEP")
        )
        if canonical is None:
            canonical = CanonicalSkill(
                id=uuid.uuid4(),
                code="MATH.EE.EQUATION.MULTISTEP",
                name="Multi-step equations",
                subject="MATHEMATICS",
            )
            db.add(canonical)
            db.commit()

        first = ingest_draft_pack(db, _pack())
        db.commit()
        second = ingest_draft_pack(db, _pack())
        db.commit()

        versions = list(
            db.scalars(
                select(CurriculumVersion).where(
                    CurriculumVersion.curriculum_id == first.curriculum_id,
                    CurriculumVersion.version == "2021",
                )
            )
        )
        standards = list(
            db.scalars(
                select(CurriculumStandard).where(
                    CurriculumStandard.curriculum_version_id == first.id
                )
            )
        )
        mappings = list(
            db.scalars(
                select(StandardSkillMapping).where(
                    StandardSkillMapping.standard_id == standards[0].id
                )
            )
        )
        assert first.id == second.id
        assert len(versions) == 1
        assert len(standards) == 1
        assert len(mappings) == 1
        assert versions[0].review_status == "DRAFT"
        assert mappings[0].review_status == "DRAFT"
        assert mappings[0].reviewed_by is None
        assert mappings[0].reviewed_at is None
        assert mappings[0].provenance_json["source_type"] == "PROPOSED_MAPPING"
    finally:
        db.close()


def test_draft_ingestion_rejects_authority_mismatch():
    seed_mth1w()
    pack = _pack()
    bad = CurriculumIngestionPack(
        **{**pack.__dict__, "authority_code": "WRONG_AUTHORITY"}
    )
    db = SessionLocal()
    try:
        with pytest.raises(CurriculumDraftIngestionError):
            ingest_draft_pack(db, bad)
        db.rollback()
    finally:
        db.close()
