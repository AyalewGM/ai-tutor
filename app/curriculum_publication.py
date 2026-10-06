"""Operator-facing review and publication workflow for curriculum mappings."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_mapping_validation import (
    CurriculumMappingValidationError,
    MappingReview,
    publish_standard_skill_mapping,
)
from app.curriculum_models import CurriculumStandard, CurriculumVersion, StandardSkillMapping


@dataclass(frozen=True)
class MappingPublicationRequest:
    mapping_id: object
    reviewer: str
    source_uri: str
    basis: str


def publish_mapping_request(
    session: Session, request: MappingPublicationRequest
) -> StandardSkillMapping:
    """Resolve a draft mapping and publish it only through the #216 review gate."""
    mapping = session.get(StandardSkillMapping, request.mapping_id)
    if mapping is None:
        raise CurriculumMappingValidationError("Standard skill mapping not found")
    if mapping.review_status != "DRAFT":
        raise CurriculumMappingValidationError("Only DRAFT mappings may be reviewed for publication")

    standard = session.get(CurriculumStandard, mapping.standard_id)
    if standard is None:
        raise CurriculumMappingValidationError("Curriculum standard not found")
    version = session.get(CurriculumVersion, standard.curriculum_version_id)
    if version is None:
        raise CurriculumMappingValidationError("Curriculum version not found")
    if version.review_status == "REJECTED":
        raise CurriculumMappingValidationError(
            "Mappings for a rejected curriculum version cannot be published"
        )

    return publish_standard_skill_mapping(
        session,
        curriculum_version=version,
        standard=standard,
        mapping=mapping,
        review=MappingReview(
            reviewer=request.reviewer,
            source_uri=request.source_uri,
            basis=request.basis,
        ),
    )


def publish_curriculum_version_if_ready(
    session: Session, *, curriculum_version_id: object, reviewer: str
) -> CurriculumVersion:
    """Publish a version only when every proposed mapping has passed human review."""
    version = session.get(CurriculumVersion, curriculum_version_id)
    if version is None:
        raise CurriculumMappingValidationError("Curriculum version not found")
    if version.review_status == "PUBLISHED":
        return version
    reviewer = reviewer.strip()
    if not reviewer:
        raise CurriculumMappingValidationError("Human reviewer is required")
    if not version.source_uri or not version.source_uri.strip():
        raise CurriculumMappingValidationError("Official curriculum source URI is required")

    standards = list(
        session.scalars(
            select(CurriculumStandard).where(
                CurriculumStandard.curriculum_version_id == version.id
            )
        )
    )
    if not standards:
        raise CurriculumMappingValidationError(
            "Curriculum version cannot be published without standards"
        )
    standard_ids = [standard.id for standard in standards]
    mappings = list(
        session.scalars(
            select(StandardSkillMapping).where(
                StandardSkillMapping.standard_id.in_(standard_ids)
            )
        )
    )
    if not mappings:
        raise CurriculumMappingValidationError(
            "Curriculum version cannot be published without reviewed mappings"
        )
    unreviewed = [mapping for mapping in mappings if mapping.review_status != "PUBLISHED"]
    if unreviewed:
        raise CurriculumMappingValidationError(
            "All proposed mappings must be human-reviewed before version publication"
        )

    provenance = dict(version.provenance_json or {})
    provenance["publication"] = "HUMAN_REVIEWED"
    provenance["published_by"] = reviewer
    version.provenance_json = provenance
    version.review_status = "PUBLISHED"
    session.flush()
    return version
