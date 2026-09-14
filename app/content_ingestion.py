"""Deterministic content-pack ingestion primitives for F-007.

This module deliberately contains no LLM calls. Curriculum identity, source
expectations, mappings, prerequisites, and problem metadata are application-
owned data and must be validated before persistence.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_models import CurriculumExpectation, ExpectationSkillMapping
from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_expectation_skill_mapping,
    validate_source_identity,
)
from app.models import Curriculum, Skill


@dataclass(frozen=True)
class ExpectationInput:
    source_identifier: str
    title: str
    source_uri: str
    strand: str | None = None
    description: str | None = None
    parent_source_identifier: str | None = None
    provenance_metadata: dict[str, object] | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


@dataclass(frozen=True)
class ExpectationSkillMappingInput:
    source_identifier: str
    skill_code: str
    mapping_type: str = "ALIGNS_TO"


@dataclass(frozen=True)
class ContentPackInput:
    curriculum_code: str
    curriculum_version: str
    expectations: tuple[ExpectationInput, ...]
    mappings: tuple[ExpectationSkillMappingInput, ...] = ()


@dataclass(frozen=True)
class ExpectationUpsert:
    """Stable upsert command keyed by curriculum/version/source identifier."""

    key: tuple[str, str, str]
    value: ExpectationInput


def build_expectation_upserts(pack: ContentPackInput) -> tuple[ExpectationUpsert, ...]:
    """Validate and normalize a pack into deterministic idempotent upserts."""
    curriculum_code = pack.curriculum_code.strip()
    curriculum_version = pack.curriculum_version.strip()
    if not curriculum_code:
        raise ContentValidationError("Curriculum code is required")
    if not curriculum_version:
        raise ContentValidationError("Curriculum version is required")

    seen: set[str] = set()
    commands: list[ExpectationUpsert] = []
    for expectation in pack.expectations:
        source_identifier = expectation.source_identifier.strip()
        validate_source_identity(
            curriculum_version=curriculum_version,
            source_identifier=source_identifier,
            source_uri=expectation.source_uri,
        )
        if source_identifier in seen:
            raise ContentValidationError(
                "Duplicate source identifier in curriculum/version: "
                f"{source_identifier}"
            )
        seen.add(source_identifier)
        commands.append(
            ExpectationUpsert(
                key=(curriculum_code, curriculum_version, source_identifier),
                value=expectation,
            )
        )

    return tuple(commands)


def expectation_keys(
    commands: Iterable[ExpectationUpsert],
) -> tuple[tuple[str, str, str], ...]:
    """Expose stable keys for persistence/integration tests without DB coupling."""
    return tuple(command.key for command in commands)


def _official_provenance(value: ExpectationInput) -> dict[str, object]:
    """Preserve source metadata while keeping official-source identity authoritative."""
    metadata = dict(value.provenance_metadata or {})
    metadata["source_type"] = "OFFICIAL_CURRICULUM"
    return metadata


def _persist_mappings(
    session: Session,
    *,
    curriculum: Curriculum,
    expectations_by_source: dict[str, CurriculumExpectation],
    mappings: tuple[ExpectationSkillMappingInput, ...],
) -> tuple[ExpectationSkillMapping, ...]:
    persisted: list[ExpectationSkillMapping] = []
    seen: set[tuple[str, str]] = set()

    for mapping_input in mappings:
        source_identifier = mapping_input.source_identifier.strip()
        skill_code = mapping_input.skill_code.strip()
        key = (source_identifier, skill_code)
        if key in seen:
            raise ContentValidationError(
                "Duplicate expectation-to-skill mapping in content pack: "
                f"{source_identifier} -> {skill_code}"
            )
        seen.add(key)

        expectation = expectations_by_source.get(source_identifier)
        if expectation is None:
            raise ContentValidationError(
                f"Mapping references expectation not present in content pack: {source_identifier}"
            )
        skill = session.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == skill_code,
            )
        )
        if skill is None:
            raise ContentValidationError(
                f"Mapping references skill not found in content-pack curriculum: {skill_code}"
            )

        validate_expectation_skill_mapping(
            mapping_curriculum_id=curriculum.id,
            expectation=CurriculumScopedRef(
                id=expectation.id,
                curriculum_id=expectation.curriculum_id,
            ),
            skill=CurriculumScopedRef(id=skill.id, curriculum_id=skill.curriculum_id),
        )

        mapping = session.scalar(
            select(ExpectationSkillMapping).where(
                ExpectationSkillMapping.expectation_id == expectation.id,
                ExpectationSkillMapping.skill_id == skill.id,
            )
        )
        if mapping is None:
            mapping = ExpectationSkillMapping(
                curriculum_id=curriculum.id,
                expectation_id=expectation.id,
                skill_id=skill.id,
                mapping_type=mapping_input.mapping_type.strip() or "ALIGNS_TO",
                provenance_json={"source_type": "AI_TUTOR_CURATED_MAPPING"},
            )
            session.add(mapping)
        else:
            mapping.curriculum_id = curriculum.id
            mapping.mapping_type = mapping_input.mapping_type.strip() or "ALIGNS_TO"
            mapping.provenance_json = {"source_type": "AI_TUTOR_CURATED_MAPPING"}
        persisted.append(mapping)

    session.flush()
    return tuple(persisted)


def persist_expectation_pack(
    session: Session,
    pack: ContentPackInput,
) -> tuple[CurriculumExpectation, ...]:
    """Persist expectation metadata and explicit skill mappings idempotently.

    The curriculum registry remains the authority for curriculum identity. A
    pack must match both registry code and version; ingestion never creates a
    curriculum implicitly. Existing expectations and mappings are updated in
    place using curriculum-scoped identity keys.
    """
    commands = build_expectation_upserts(pack)
    curriculum = session.scalar(
        select(Curriculum).where(
            Curriculum.code == pack.curriculum_code.strip(),
            Curriculum.version == pack.curriculum_version.strip(),
            Curriculum.active.is_(True),
        )
    )
    if curriculum is None:
        raise ContentValidationError(
            "Active curriculum registry entry not found for content pack"
        )

    persisted: list[CurriculumExpectation] = []
    expectations_by_source: dict[str, CurriculumExpectation] = {}
    for command in commands:
        value = command.value
        expectation = session.scalar(
            select(CurriculumExpectation).where(
                CurriculumExpectation.curriculum_id == curriculum.id,
                CurriculumExpectation.curriculum_version == command.key[1],
                CurriculumExpectation.source_identifier == command.key[2],
            )
        )
        if expectation is None:
            expectation = CurriculumExpectation(
                curriculum_id=curriculum.id,
                curriculum_version=command.key[1],
                source_identifier=command.key[2],
                title=value.title.strip(),
                description=value.description.strip() if value.description else None,
                strand=value.strand.strip() if value.strand else None,
                parent_source_identifier=(
                    value.parent_source_identifier.strip()
                    if value.parent_source_identifier
                    else None
                ),
                source_uri=value.source_uri.strip(),
                provenance_json=_official_provenance(value),
                effective_from=value.effective_from,
                effective_to=value.effective_to,
            )
            session.add(expectation)
        else:
            expectation.title = value.title.strip()
            expectation.description = value.description.strip() if value.description else None
            expectation.strand = value.strand.strip() if value.strand else None
            expectation.parent_source_identifier = (
                value.parent_source_identifier.strip()
                if value.parent_source_identifier
                else None
            )
            expectation.source_uri = value.source_uri.strip()
            expectation.provenance_json = _official_provenance(value)
            expectation.effective_from = value.effective_from
            expectation.effective_to = value.effective_to
            expectation.active = True
        session.flush()
        persisted.append(expectation)
        expectations_by_source[command.key[2]] = expectation

    _persist_mappings(
        session,
        curriculum=curriculum,
        expectations_by_source=expectations_by_source,
        mappings=pack.mappings,
    )
    return tuple(persisted)
