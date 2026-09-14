from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.content_models import CurriculumExpectation, ExpectationSkillMapping
from app.content_validation import ContentValidationError
from app.core.database import SessionLocal
from app.models import Curriculum


def _active_curriculum(db, code: str) -> Curriculum:
    curriculum = db.scalar(
        select(Curriculum).where(
            Curriculum.code == code,
            Curriculum.active.is_(True),
        )
    )
    assert curriculum is not None
    return curriculum


def _pack(
    curriculum: Curriculum,
    *,
    title: str = "Test expectation",
    skill_code: str | None = None,
) -> ContentPackInput:
    mappings = ()
    if skill_code is not None:
        mappings = (
            ExpectationSkillMappingInput(
                source_identifier="F007.TEST.EXPECTATION",
                skill_code=skill_code,
            ),
        )
    return ContentPackInput(
        curriculum_code=curriculum.code,
        curriculum_version=curriculum.version,
        expectations=(
            ExpectationInput(
                source_identifier="F007.TEST.EXPECTATION",
                title=title,
                strand="F-007 integration",
                source_uri="https://example.edu/f007/test-expectation",
            ),
        ),
        mappings=mappings,
    )


def test_persist_expectation_pack_is_idempotent_and_updates_in_place() -> None:
    with SessionLocal() as db:
        curriculum = _active_curriculum(db, "MTH1W")

        first = persist_expectation_pack(db, _pack(curriculum, title="First title"))
        first_id = first[0].id
        second = persist_expectation_pack(db, _pack(curriculum, title="Updated title"))

        assert second[0].id == first_id
        assert second[0].title == "Updated title"
        assert second[0].provenance_json == {"source_type": "OFFICIAL_CURRICULUM"}

        count = db.scalar(
            select(func.count())
            .select_from(CurriculumExpectation)
            .where(
                CurriculumExpectation.curriculum_id == curriculum.id,
                CurriculumExpectation.curriculum_version == curriculum.version,
                CurriculumExpectation.source_identifier == "F007.TEST.EXPECTATION",
            )
        )
        assert count == 1
        db.rollback()


def test_persist_expectation_pack_preserves_source_metadata() -> None:
    with SessionLocal() as db:
        curriculum = _active_curriculum(db, "MTH1W")
        effective_from = datetime(2021, 9, 1, tzinfo=UTC)
        pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            expectations=(
                ExpectationInput(
                    source_identifier="F007.TEST.METADATA",
                    title="Metadata expectation",
                    description="Official expectation description",
                    strand="C. Algebra",
                    parent_source_identifier="C2",
                    source_uri="https://example.edu/f007/metadata-expectation",
                    provenance_metadata={
                        "authority": "Ontario Ministry of Education",
                        "document_version": "2021",
                        "source_type": "UNTRUSTED_OVERRIDE",
                    },
                    effective_from=effective_from,
                ),
            ),
        )

        expectation = persist_expectation_pack(db, pack)[0]

        assert expectation.description == "Official expectation description"
        assert expectation.parent_source_identifier == "C2"
        assert expectation.effective_from == effective_from
        assert expectation.provenance_json == {
            "authority": "Ontario Ministry of Education",
            "document_version": "2021",
            "source_type": "OFFICIAL_CURRICULUM",
        }
        db.rollback()


def test_persist_expectation_pack_requires_exact_active_registry_version() -> None:
    with SessionLocal() as db:
        curriculum = _active_curriculum(db, "MTH1W")
        wrong_version_pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=f"{curriculum.version}-wrong",
            expectations=_pack(curriculum).expectations,
        )

        with pytest.raises(
            ContentValidationError,
            match="Active curriculum registry entry not found",
        ):
            persist_expectation_pack(db, wrong_version_pack)
        db.rollback()


def test_same_source_identifier_persists_separately_across_curricula() -> None:
    with SessionLocal() as db:
        mcps = _active_curriculum(db, "MCPS_MATH_8")
        ontario = _active_curriculum(db, "MTH1W")

        mcps_rows = persist_expectation_pack(db, _pack(mcps, title="MCPS test"))
        ontario_rows = persist_expectation_pack(db, _pack(ontario, title="Ontario test"))

        assert mcps_rows[0].id != ontario_rows[0].id
        assert mcps_rows[0].curriculum_id == mcps.id
        assert ontario_rows[0].curriculum_id == ontario.id
        assert mcps_rows[0].source_identifier == ontario_rows[0].source_identifier
        db.rollback()


def test_expectation_skill_mapping_is_idempotent_and_curriculum_scoped() -> None:
    with SessionLocal() as db:
        curriculum = _active_curriculum(db, "MCPS_MATH_8")
        pack = _pack(curriculum, skill_code="M8.ALG.DIST")

        expectations = persist_expectation_pack(db, pack)
        persist_expectation_pack(db, pack)

        mappings = db.scalars(
            select(ExpectationSkillMapping).where(
                ExpectationSkillMapping.expectation_id == expectations[0].id,
            )
        ).all()
        assert len(mappings) == 1
        assert mappings[0].curriculum_id == curriculum.id
        assert mappings[0].provenance_json == {
            "source_type": "AI_TUTOR_CURATED_MAPPING"
        }
        db.rollback()


def test_mapping_cannot_resolve_skill_from_another_curriculum() -> None:
    with SessionLocal() as db:
        ontario = _active_curriculum(db, "MTH1W")
        pack = _pack(ontario, skill_code="M8.ALG.DIST")

        with pytest.raises(
            ContentValidationError,
            match="skill not found in content-pack curriculum",
        ):
            persist_expectation_pack(db, pack)
        db.rollback()
