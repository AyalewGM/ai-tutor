"""Deterministic content-pack ingestion primitives for F-007.

This module deliberately contains no LLM calls. Curriculum identity, source
expectations, mappings, prerequisites, and problem metadata are application-
owned data and must be validated before persistence.
"""

from dataclasses import dataclass
from typing import Iterable

from app.content_validation import ContentValidationError, validate_source_identity


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
    """Validate and normalize a pack into deterministic idempotent upserts.

    Duplicate expectation identifiers inside one pack are rejected rather than
    silently choosing a winner. The returned commands have stable keys so the
    persistence adapter can use ON CONFLICT/update semantics safely.
    """
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
