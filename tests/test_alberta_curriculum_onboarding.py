from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_draft_ingestion import ingest_draft_pack
from app.curriculum_lifecycle import is_learner_selectable
from app.curriculum_models import CurriculumStandard, StandardSkillMapping
from app.models import StudentSkill
from scripts.alberta_ingestion_proof import (
    AB_SOURCE,
    alberta_grade9_pilot_pack,
    register_alberta_grade9_draft,
)
from scripts.map_canonical_curricula import map_existing_skills
from scripts.seed_mth1w import seed as seed_on


def test_alberta_pilot_uses_shared_pipeline_without_becoming_implemented():
    seed_on()
    db = SessionLocal()
    try:
        map_existing_skills(db)
        curriculum = register_alberta_grade9_draft(db)
        db.commit()

        assert not curriculum.active
        before_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
        pack = alberta_grade9_pilot_pack()
        version = ingest_draft_pack(db, pack)
        db.flush()

        same_version = ingest_draft_pack(db, pack)
        db.flush()
        assert same_version.id == version.id
        assert version.lifecycle_status == "PILOT"
        assert not version.active
        assert not is_learner_selectable(version)
        assert version.provenance_json["lifecycle_status"] == "PILOT"

        standards = list(
            db.scalars(
                select(CurriculumStandard).where(
                    CurriculumStandard.curriculum_version_id == version.id
                )
            )
        )
        assert [standard.code for standard in standards] == [
            "AB9.DRAFT.LINEAR_INEQUALITIES"
        ]
        mappings = list(
            db.scalars(
                select(StandardSkillMapping).where(
                    StandardSkillMapping.standard_id == standards[0].id
                )
            )
        )
        assert len(mappings) == 1
        assert mappings[0].mapping_type == "PARTIAL"
        assert mappings[0].coverage == "PARTIAL"
        assert mappings[0].review_status == "DRAFT"

        after_evidence = db.scalar(select(func.count()).select_from(StudentSkill))
        assert before_evidence == after_evidence
    finally:
        db.rollback()
        db.close()


def test_alberta_authoritative_source_and_pilot_status_are_explicit():
    pack = alberta_grade9_pilot_pack()
    assert pack.source_uri == AB_SOURCE
    assert pack.curriculum_version == "2026-draft"
    assert pack.lifecycle_status == "PILOT"
