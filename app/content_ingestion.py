"""Deterministic content-pack ingestion primitives for F-007.

This module deliberately contains no LLM calls. Curriculum identity, source
expectations, mappings, prerequisites, and problem metadata are application-
owned data and must be validated before persistence.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_models import CurriculumExpectation
from app.content_validation import ContentValidationError, validate_source_identity
from app.models import Curriculum


@dataclass(frozen=True)
class ExpectationInput:
    source_identifier: str
    title: str
    source_uri: str
    strand: str | None = None


@dataclass(frozen=True)
class ContentPackInput:
    curriculum_code: str
    curriculum_version: str
    expectations: tuple[ExpectationInput, ...]


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


def expectation_keys(commands: Iterable[ExpectationUpsert]) -> tuple[tuple[str, str, str], ...]:
    """Expose stable keys for persistence/integration tests without DB coupling."""
    return tuple(command.key for command in commands)


def persist_expectation_pack(session: Session, pack: ContentPackInput) -> tuple[CurriculumExpectation, ...]:
    """Persist expectation metadata idempotently for exactly one curriculum.

    The curriculum registry remains the authority for curriculum identity. A
    pack must match both registry code and version; ingestion never creates a
    curriculum implicitly. Existing expectations are updated in place using
    the repository's curriculum/version/source-identifier identity key.
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
                strand=value.strand.strip() if value.strand else None,
                source_uri=value.source_uri.strip(),
                provenance_json={"source_type": "OFFICIAL_CURRICULUM"},
            )
            session.add(expectation)
        else:
            expectation.title = value.title.strip()
            expectation.strand = value.strand.strip() if value.strand else None
            expectation.source_uri = value.source_uri.strip()
            expectation.provenance_json = {"source_type": "OFFICIAL_CURRICULUM"}
            expectation.active = True
        persisted.append(expectation)

    session.flush()
    return tuple(persisted)
