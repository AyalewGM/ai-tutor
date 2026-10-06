import uuid

import pytest

from app.curriculum_mapping_validation import (
    CurriculumMappingValidationError,
    MappingReview,
    publish_standard_skill_mapping,
    validate_standard_skill_mapping,
)
from app.curriculum_models import CurriculumStandard, CurriculumVersion, StandardSkillMapping


def _records():
    version = CurriculumVersion(
        id=uuid.uuid4(),
        curriculum_id=uuid.uuid4(),
        version="2021",
        source_uri="https://official.example/curriculum",
        review_status="DRAFT",
    )
    standard = CurriculumStandard(
        id=uuid.uuid4(),
        curriculum_version_id=version.id,
        code="C1.5",
        title="Solve equations",
        source_uri=version.source_uri,
    )
    mapping = StandardSkillMapping(
        standard_id=standard.id,
        canonical_skill_id=uuid.uuid4(),
        review_status="DRAFT",
    )
    return version, standard, mapping


def test_mapping_validation_rejects_cross_version_standard():
    version, standard, mapping = _records()
    standard.curriculum_version_id = uuid.uuid4()
    with pytest.raises(CurriculumMappingValidationError):
        validate_standard_skill_mapping(
            curriculum_version=version, standard=standard, mapping=mapping
        )


def test_mapping_validation_requires_authoritative_source():
    version, standard, mapping = _records()
    version.source_uri = None
    with pytest.raises(CurriculumMappingValidationError):
        validate_standard_skill_mapping(
            curriculum_version=version, standard=standard, mapping=mapping
        )


def test_publish_requires_human_reviewer():
    version, standard, mapping = _records()

    class SessionStub:
        def flush(self):
            raise AssertionError("invalid mapping must not be persisted")

    with pytest.raises(CurriculumMappingValidationError):
        publish_standard_skill_mapping(
            SessionStub(),
            curriculum_version=version,
            standard=standard,
            mapping=mapping,
            review=MappingReview(
                reviewer="",
                source_uri=version.source_uri,
                basis="Reviewed against official standard",
            ),
        )


def test_publish_marks_mapping_human_reviewed():
    version, standard, mapping = _records()

    class SessionStub:
        flushed = False
        def flush(self):
            self.flushed = True

    session = SessionStub()
    published = publish_standard_skill_mapping(
        session,
        curriculum_version=version,
        standard=standard,
        mapping=mapping,
        review=MappingReview(
            reviewer="curriculum-reviewer",
            source_uri=version.source_uri,
            basis="Reviewed against official standard",
        ),
    )
    assert session.flushed
    assert published.review_status == "PUBLISHED"
    assert published.reviewed_by == "curriculum-reviewer"
    assert published.reviewed_at is not None
    assert published.provenance_json["publication"] == "HUMAN_REVIEWED"
