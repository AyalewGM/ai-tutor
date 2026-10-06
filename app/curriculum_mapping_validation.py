"""Validation and controlled publication for canonical curriculum mappings."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.curriculum_models import CurriculumStandard, CurriculumVersion, StandardSkillMapping


class CurriculumMappingValidationError(ValueError):
    pass


@dataclass(frozen=True)
class MappingReview:
    reviewer: str
    source_uri: str
    basis: str


def validate_standard_skill_mapping(
    *,
    curriculum_version: CurriculumVersion,
    standard: CurriculumStandard,
    mapping: StandardSkillMapping,
) -> None:
    """Fail closed when mapping identity/provenance crosses a version boundary."""
    if standard.curriculum_version_id != curriculum_version.id:
        raise CurriculumMappingValidationError(
            "Standard does not belong to the supplied curriculum version"
        )
    if mapping.standard_id != standard.id:
        raise CurriculumMappingValidationError("Mapping references a different standard")
    if not curriculum_version.version.strip():
        raise CurriculumMappingValidationError("Curriculum version is required")
    if not curriculum_version.source_uri or not curriculum_version.source_uri.strip():
        raise CurriculumMappingValidationError("Official curriculum source URI is required")
    if not standard.code.strip():
        raise CurriculumMappingValidationError("Standard code is required")
    if standard.source_uri and standard.source_uri.strip() != curriculum_version.source_uri.strip():
        raise CurriculumMappingValidationError(
            "Standard source must match the authoritative curriculum-version source"
        )


def publish_standard_skill_mapping(
    session: Session,
    *,
    curriculum_version: CurriculumVersion,
    standard: CurriculumStandard,
    mapping: StandardSkillMapping,
    review: MappingReview,
) -> StandardSkillMapping:
    """Publish only after an explicit human review with source provenance."""
    validate_standard_skill_mapping(
        curriculum_version=curriculum_version, standard=standard, mapping=mapping
    )
    reviewer = review.reviewer.strip()
    source_uri = review.source_uri.strip()
    basis = review.basis.strip()
    if not reviewer:
        raise CurriculumMappingValidationError("Human reviewer is required")
    if not source_uri or source_uri != curriculum_version.source_uri.strip():
        raise CurriculumMappingValidationError(
            "Review must cite the authoritative curriculum-version source"
        )
    if not basis:
        raise CurriculumMappingValidationError("Review basis is required")

    provenance = dict(mapping.provenance_json or {})
    provenance.update(
        {
            "source_type": "OFFICIAL_CURRICULUM",
            "source_uri": source_uri,
            "review_basis": basis,
            "publication": "HUMAN_REVIEWED",
        }
    )
    mapping.provenance_json = provenance
    mapping.review_status = "PUBLISHED"
    mapping.reviewed_by = reviewer
    mapping.reviewed_at = datetime.now(UTC)
    session.flush()
    return mapping
