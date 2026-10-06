"""Versioned, deterministic input contract for scalable curriculum ingestion."""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0"
_ALLOWED_MAPPING_TYPES = frozenset({"ALIGNS_TO", "EQUIVALENT", "PARTIAL"})


class CurriculumPackValidationError(ValueError):
    pass


@dataclass(frozen=True)
class StandardDraft:
    code: str
    title: str
    source_uri: str
    description: str | None = None
    strand: str | None = None
    sequence: int | None = None


@dataclass(frozen=True)
class ProposedSkillMapping:
    standard_code: str
    canonical_skill_code: str
    mapping_type: str = "ALIGNS_TO"
    coverage: str | None = None
    rationale: str | None = None


@dataclass(frozen=True)
class CurriculumIngestionPack:
    schema_version: str
    curriculum_code: str
    curriculum_version: str
    authority_code: str
    source_uri: str
    standards: tuple[StandardDraft, ...]
    proposed_mappings: tuple[ProposedSkillMapping, ...] = ()
    effective_from: datetime | None = None
    effective_to: datetime | None = None


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise CurriculumPackValidationError(f"{field} is required")
    return normalized


def _absolute_http_uri(value: str, field: str) -> str:
    uri = _required(value, field)
    parsed = urlparse(uri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CurriculumPackValidationError(f"{field} must be an absolute HTTP(S) URI")
    return uri


def validate_ingestion_pack(pack: CurriculumIngestionPack) -> None:
    """Validate the portable pack before any database write occurs."""
    if pack.schema_version != SCHEMA_VERSION:
        raise CurriculumPackValidationError(
            f"Unsupported curriculum pack schema version: {pack.schema_version}"
        )
    _required(pack.curriculum_code, "Curriculum code")
    _required(pack.curriculum_version, "Curriculum version")
    _required(pack.authority_code, "Authority code")
    authoritative_source = _absolute_http_uri(pack.source_uri, "Official source URI")
    if pack.effective_from and pack.effective_to and pack.effective_from >= pack.effective_to:
        raise CurriculumPackValidationError("effective_from must precede effective_to")
    if not pack.standards:
        raise CurriculumPackValidationError("At least one standard is required")

    standard_codes: set[str] = set()
    for standard in pack.standards:
        code = _required(standard.code, "Standard code")
        _required(standard.title, f"Standard {code} title")
        source = _absolute_http_uri(standard.source_uri, f"Standard {code} source URI")
        if source != authoritative_source:
            raise CurriculumPackValidationError(
                f"Standard {code} must cite the authoritative curriculum source"
            )
        if code in standard_codes:
            raise CurriculumPackValidationError(f"Duplicate standard code: {code}")
        standard_codes.add(code)

    mapping_keys: set[tuple[str, str]] = set()
    for mapping in pack.proposed_mappings:
        standard_code = _required(mapping.standard_code, "Mapping standard code")
        canonical_code = _required(mapping.canonical_skill_code, "Canonical skill code")
        mapping_type = _required(mapping.mapping_type, "Mapping type")
        if standard_code not in standard_codes:
            raise CurriculumPackValidationError(
                f"Mapping references unknown standard: {standard_code}"
            )
        if mapping_type not in _ALLOWED_MAPPING_TYPES:
            raise CurriculumPackValidationError(f"Unsupported mapping type: {mapping_type}")
        key = (standard_code, canonical_code)
        if key in mapping_keys:
            raise CurriculumPackValidationError(
                f"Duplicate proposed mapping: {standard_code} -> {canonical_code}"
            )
        mapping_keys.add(key)


def stable_pack_keys(
    pack: CurriculumIngestionPack,
) -> tuple[tuple[str, str, str], ...]:
    """Return deterministic standard identity keys for idempotent persistence."""
    validate_ingestion_pack(pack)
    prefix = (pack.curriculum_code.strip(), pack.curriculum_version.strip())
    return tuple(prefix + (standard.code.strip(),) for standard in pack.standards)
