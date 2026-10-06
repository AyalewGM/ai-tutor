from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_draft_ingestion import ingest_draft_pack
from app.curriculum_models import CurriculumStandard, StandardSkillMapping
from app.curriculum_publication import (
    MappingPublicationRequest,
    publish_curriculum_version_if_ready,
    publish_mapping_request,
)
from app.models import StudentSkill
from scripts.map_canonical_curricula import map_existing_skills
from scripts.seed_mth1w import seed as seed_on
from scripts.virginia_ingestion_proof import (
    VA_SOURCE,
    register_virginia_algebra1,
    virginia_algebra1_proof_pack,
)


def test_virginia_onboards_through_shared_pipeline_without_evidence_mutation():
    seed_on()
    db = SessionLocal()
    try:
        map_existing_skills(db)
        register_virginia_algebra1(db)
        db.commit()

        before_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
        pack = virginia_algebra1_proof_pack()
        version = ingest_draft_pack(db, pack)
        db.flush()

        # DRAFT ingestion is idempotent and reuses the same version/standard/mapping.
        same_version = ingest_draft_pack(db, pack)
        db.flush()
        assert same_version.id == version.id

        standards = list(
            db.scalars(
                select(CurriculumStandard).where(
                    CurriculumStandard.curriculum_version_id == version.id
                )
            )
        )
        assert [standard.code for standard in standards] == ["A.EI.1"]

        mappings = list(
            db.scalars(
                select(StandardSkillMapping).where(
                    StandardSkillMapping.standard_id == standards[0].id
                )
            )
        )
        assert len(mappings) == 1
        assert mappings[0].mapping_type == "ALIGNS_TO"
        assert mappings[0].coverage == "PARTIAL"

        publish_mapping_request(
            db,
            MappingPublicationRequest(
                mapping_id=mappings[0].id,
                reviewer="curriculum-proof-reviewer",
                source_uri=VA_SOURCE,
                basis="Verified VDOE 2023 Algebra 1 A.EI.1 source alignment",
            ),
        )
        publish_curriculum_version_if_ready(
            db,
            curriculum_version_id=version.id,
            reviewer="curriculum-proof-reviewer",
        )
        db.flush()

        assert version.review_status == "PUBLISHED"
        after_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
        assert before_evidence == after_evidence
    finally:
        db.rollback()
        db.close()
