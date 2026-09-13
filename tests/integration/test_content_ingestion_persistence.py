from sqlalchemy import func, select

from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    persist_expectation_pack,
)
from app.content_models import CurriculumExpectation
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


def _pack(curriculum: Curriculum, *, title: str = "Test expectation") -> ContentPackInput:
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


def test_persist_expectation_pack_requires_exact_active_registry_version() -> None:
    with SessionLocal() as db:
        curriculum = _active_curriculum(db, "MTH1W")
        wrong_version_pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=f"{curriculum.version}-wrong",
            expectations=_pack(curriculum).expectations,
        )

        try:
            persist_expectation_pack(db, wrong_version_pack)
        except ContentValidationError as exc:
            assert "Active curriculum registry entry not found" in str(exc)
        else:
            raise AssertionError("Version mismatch must be rejected")
        finally:
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
