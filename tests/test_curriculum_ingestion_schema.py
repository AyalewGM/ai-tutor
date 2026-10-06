from datetime import UTC, datetime

import pytest

from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    CurriculumPackValidationError,
    ProposedSkillMapping,
    StandardDraft,
    stable_pack_keys,
    validate_ingestion_pack,
)


def _pack(**changes):
    values = {
        "schema_version": SCHEMA_VERSION,
        "curriculum_code": "MTH1W",
        "curriculum_version": "2021",
        "authority_code": "ON_MIN_ED",
        "source_uri": "https://official.example/math",
        "standards": (
            StandardDraft(
                code="C1.5",
                title="Solve equations",
                source_uri="https://official.example/math",
            ),
        ),
        "proposed_mappings": (
            ProposedSkillMapping(
                standard_code="C1.5",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                rationale="Proposed alignment for review",
            ),
        ),
    }
    values.update(changes)
    return CurriculumIngestionPack(**values)


def test_pack_has_stable_versioned_identity():
    pack = _pack()
    validate_ingestion_pack(pack)
    assert stable_pack_keys(pack) == (("MTH1W", "2021", "C1.5"),)


def test_unknown_schema_version_fails_closed():
    with pytest.raises(CurriculumPackValidationError):
        validate_ingestion_pack(_pack(schema_version="2.0"))


def test_standard_must_cite_authoritative_source():
    standard = StandardDraft(
        code="C1.5",
        title="Solve equations",
        source_uri="https://unreviewed.example/summary",
    )
    with pytest.raises(CurriculumPackValidationError):
        validate_ingestion_pack(_pack(standards=(standard,)))


def test_mapping_cannot_reference_unknown_standard():
    mapping = ProposedSkillMapping(
        standard_code="UNKNOWN",
        canonical_skill_code="MATH.EE.EXPR",
    )
    with pytest.raises(CurriculumPackValidationError):
        validate_ingestion_pack(_pack(proposed_mappings=(mapping,)))


def test_duplicate_mapping_fails_closed():
    mapping = ProposedSkillMapping(
        standard_code="C1.5",
        canonical_skill_code="MATH.EE.EXPR",
    )
    with pytest.raises(CurriculumPackValidationError):
        validate_ingestion_pack(_pack(proposed_mappings=(mapping, mapping)))


def test_invalid_effective_window_fails_closed():
    when = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(CurriculumPackValidationError):
        validate_ingestion_pack(_pack(effective_from=when, effective_to=when))
