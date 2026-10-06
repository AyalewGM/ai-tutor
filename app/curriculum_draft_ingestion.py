"""Idempotent persistence of validated curriculum ingestion packs as DRAFT data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_ingestion_schema import CurriculumIngestionPack, validate_ingestion_pack
from app.curriculum_lifecycle import set_curriculum_lifecycle
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumStandard,
    CurriculumVersion,
    EducationAuthority,
    StandardSkillMapping,
)
from app.models import Curriculum


class CurriculumDraftIngestionError(ValueError):
    pass


def ingest_draft_pack(session: Session, pack: CurriculumIngestionPack) -> CurriculumVersion:
    """Persist a validated pack without publishing anything or touching learner evidence."""
    validate_ingestion_pack(pack)

    curriculum = session.scalar(
        select(Curriculum).where(Curriculum.code == pack.curriculum_code.strip())
    )
    if curriculum is None:
        raise CurriculumDraftIngestionError("Curriculum registry entry not found")

    authority = session.scalar(
        select(EducationAuthority).where(
            EducationAuthority.id == curriculum.authority_id,
            EducationAuthority.code == pack.authority_code.strip(),
        )
    )
    if authority is None:
        raise CurriculumDraftIngestionError(
            "Pack authority does not match the curriculum registry authority"
        )

    version = session.scalar(
        select(CurriculumVersion).where(
            CurriculumVersion.curriculum_id == curriculum.id,
            CurriculumVersion.version == pack.curriculum_version.strip(),
        )
    )
    version_provenance = {
        "source_type": "OFFICIAL_CURRICULUM",
        "ingestion_schema_version": pack.schema_version,
        "authority_code": pack.authority_code.strip(),
        "lifecycle_status": pack.lifecycle_status.strip().upper(),
    }
    if version is None:
        version = CurriculumVersion(
            curriculum_id=curriculum.id,
            version=pack.curriculum_version.strip(),
            effective_from=pack.effective_from,
            effective_to=pack.effective_to,
            source_uri=pack.source_uri.strip(),
            provenance_json=version_provenance,
            review_status="DRAFT",
        )
        set_curriculum_lifecycle(version, pack.lifecycle_status)
        session.add(version)
        session.flush()
    else:
        if version.review_status == "PUBLISHED":
            raise CurriculumDraftIngestionError(
                "Published curriculum versions cannot be overwritten by draft ingestion"
            )
        version.effective_from = pack.effective_from
        version.effective_to = pack.effective_to
        version.source_uri = pack.source_uri.strip()
        version.provenance_json = version_provenance
        version.review_status = "DRAFT"
        set_curriculum_lifecycle(version, pack.lifecycle_status)

    standards: dict[str, CurriculumStandard] = {}
    for draft in pack.standards:
        code = draft.code.strip()
        standard = session.scalar(
            select(CurriculumStandard).where(
                CurriculumStandard.curriculum_version_id == version.id,
                CurriculumStandard.code == code,
            )
        )
        provenance = {
            "source_type": "OFFICIAL_CURRICULUM",
            "ingestion_schema_version": pack.schema_version,
        }
        if standard is None:
            standard = CurriculumStandard(
                curriculum_version_id=version.id,
                code=code,
                title=draft.title.strip(),
                description=draft.description.strip() if draft.description else None,
                strand=draft.strand.strip() if draft.strand else None,
                sequence=draft.sequence,
                source_uri=draft.source_uri.strip(),
                provenance_json=provenance,
            )
            session.add(standard)
            session.flush()
        else:
            standard.title = draft.title.strip()
            standard.description = draft.description.strip() if draft.description else None
            standard.strand = draft.strand.strip() if draft.strand else None
            standard.sequence = draft.sequence
            standard.source_uri = draft.source_uri.strip()
            standard.provenance_json = provenance
        standards[code] = standard

    for proposal in pack.proposed_mappings:
        canonical = session.scalar(
            select(CanonicalSkill).where(
                CanonicalSkill.code == proposal.canonical_skill_code.strip()
            )
        )
        if canonical is None:
            raise CurriculumDraftIngestionError(
                f"Canonical skill not found: {proposal.canonical_skill_code.strip()}"
            )
        standard = standards[proposal.standard_code.strip()]
        mapping = session.scalar(
            select(StandardSkillMapping).where(
                StandardSkillMapping.standard_id == standard.id,
                StandardSkillMapping.canonical_skill_id == canonical.id,
            )
        )
        provenance = {
            "source_type": "PROPOSED_MAPPING",
            "official_source_uri": pack.source_uri.strip(),
            "ingestion_schema_version": pack.schema_version,
        }
        if proposal.rationale:
            provenance["rationale"] = proposal.rationale.strip()
        if mapping is None:
            mapping = StandardSkillMapping(
                standard_id=standard.id,
                canonical_skill_id=canonical.id,
                mapping_type=proposal.mapping_type.strip(),
                coverage=proposal.coverage.strip() if proposal.coverage else None,
                review_status="DRAFT",
                provenance_json=provenance,
            )
            session.add(mapping)
        else:
            if mapping.review_status == "PUBLISHED":
                raise CurriculumDraftIngestionError(
                    "Published mappings cannot be overwritten by draft ingestion"
                )
            mapping.mapping_type = proposal.mapping_type.strip()
            mapping.coverage = proposal.coverage.strip() if proposal.coverage else None
            mapping.review_status = "DRAFT"
            mapping.provenance_json = provenance
            mapping.reviewed_by = None
            mapping.reviewed_at = None

    session.flush()
    return version
