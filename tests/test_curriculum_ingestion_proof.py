from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_draft_ingestion import ingest_draft_pack
from app.curriculum_models import (
    CurriculumStandard,
    StandardSkillMapping,
)
from app.curriculum_publication import (
    MappingPublicationRequest,
    publish_curriculum_version_if_ready,
    publish_mapping_request,
)
from app.models import StudentSkill
from scripts.curriculum_ingestion_proof import (
    MD_SOURCE,
    ON_SOURCE,
    maryland_proof_pack,
    ontario_proof_pack,
)
from scripts.map_canonical_curricula import map_existing_skills
from scripts.seed_md_algebra1 import seed as seed_md
from scripts.seed_mth1w import seed as seed_on


def _publish_pack(db, pack, source):
    before_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
    version = ingest_draft_pack(db, pack)
    db.flush()
    standards = list(
        db.scalars(
            select(CurriculumStandard).where(
                CurriculumStandard.curriculum_version_id == version.id
            )
        )
    )
    mappings = list(
        db.scalars(
            select(StandardSkillMapping).where(
                StandardSkillMapping.standard_id.in_([s.id for s in standards])
            )
        )
    )
    assert mappings
    for mapping in mappings:
        publish_mapping_request(
            db,
            MappingPublicationRequest(
                mapping_id=mapping.id,
                reviewer="curriculum-proof-reviewer",
                source_uri=source,
                basis="End-to-end proof against existing reviewed curriculum mapping",
            ),
        )
    publish_curriculum_version_if_ready(
        db,
        curriculum_version_id=version.id,
        reviewer="curriculum-proof-reviewer",
    )
    db.flush()
    after_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
    assert before_evidence == after_evidence
    return version, tuple(mapping.id for mapping in mappings)


def test_maryland_and_ontario_publish_without_learner_evidence_transfer():
    seed_md()
    seed_on()
    db = SessionLocal()
    try:
        map_existing_skills(db)
        db.commit()

        md_version, md_mapping_ids = _publish_pack(db, maryland_proof_pack(), MD_SOURCE)
        on_version, on_mapping_ids = _publish_pack(db, ontario_proof_pack(), ON_SOURCE)

        assert md_version.review_status == "PUBLISHED"
        assert on_version.review_status == "PUBLISHED"
        assert md_version.curriculum_id != on_version.curriculum_id
        assert set(md_mapping_ids).isdisjoint(on_mapping_ids)

        # Re-running a published pack fails closed rather than silently
        # downgrading human-reviewed publication back to DRAFT.
        from app.curriculum_draft_ingestion import CurriculumDraftIngestionError

        try:
            ingest_draft_pack(db, ontario_proof_pack())
        except CurriculumDraftIngestionError:
            pass
        else:
            raise AssertionError("Published curriculum must not be overwritten by draft ingestion")
    finally:
        db.rollback()
        db.close()
