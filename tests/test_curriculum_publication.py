import uuid

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_draft_ingestion import ingest_draft_pack
from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    ProposedSkillMapping,
    StandardDraft,
)
from app.curriculum_mapping_validation import CurriculumMappingValidationError
from app.curriculum_models import CanonicalSkill, StandardSkillMapping
from app.curriculum_publication import (
    MappingPublicationRequest,
    publish_curriculum_version_if_ready,
    publish_mapping_request,
)
from scripts.seed_mth1w import seed as seed_mth1w

SOURCE = "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w"


def _pack():
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code="MTH1W",
        curriculum_version="2021",
        authority_code="ON_MIN_ED",
        source_uri=SOURCE,
        standards=(StandardDraft(code="C1.5", title="Create and solve equations", source_uri=SOURCE),),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="C1.5",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                rationale="Proposed alignment",
            ),
        ),
    )


def _draft(db):
    seed_mth1w()
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
    version = ingest_draft_pack(db, _pack())
    db.commit()
    mapping = db.scalar(select(StandardSkillMapping))
    return version, mapping


def test_version_cannot_publish_while_mapping_is_draft():
    db = SessionLocal()
    try:
        version, _ = _draft(db)
        with pytest.raises(CurriculumMappingValidationError):
            publish_curriculum_version_if_ready(
                db, curriculum_version_id=version.id, reviewer="reviewer"
            )
    finally:
        db.rollback()
        db.close()


def test_human_review_then_version_publication():
    db = SessionLocal()
    try:
        version, mapping = _draft(db)
        published_mapping = publish_mapping_request(
            db,
            MappingPublicationRequest(
                mapping_id=mapping.id,
                reviewer="curriculum-reviewer",
                source_uri=SOURCE,
                basis="Compared with the official Ontario curriculum source",
            ),
        )
        assert published_mapping.review_status == "PUBLISHED"
        assert published_mapping.reviewed_by == "curriculum-reviewer"

        published_version = publish_curriculum_version_if_ready(
            db, curriculum_version_id=version.id, reviewer="curriculum-reviewer"
        )
        assert published_version.review_status == "PUBLISHED"
        assert published_version.provenance_json["publication"] == "HUMAN_REVIEWED"
        db.rollback()
    finally:
        db.close()


def test_mapping_cannot_be_self_republished():
    db = SessionLocal()
    try:
        _, mapping = _draft(db)
        request = MappingPublicationRequest(
            mapping_id=mapping.id,
            reviewer="curriculum-reviewer",
            source_uri=SOURCE,
            basis="Compared with official source",
        )
        publish_mapping_request(db, request)
        with pytest.raises(CurriculumMappingValidationError):
            publish_mapping_request(db, request)
    finally:
        db.rollback()
        db.close()
