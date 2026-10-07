import pytest

from app.california_curriculum import CA_CURRICULUM_VERSION, CA_SOURCE_URI
from app.california_standard_mappings import (
    california_grade9_pathway_pack,
    california_grade_1_8_mapping_pack,
    proposed_standard_count_by_grade,
)
from app.canonical_problem_families import FAMILIES
from app.curriculum_ingestion_schema import stable_pack_keys, validate_ingestion_pack


def _canonical_skill_codes() -> set[str]:
    return {spec.canonical_skill_code for spec in FAMILIES.values()}


def test_california_grade_1_8_pack_is_valid_and_idempotent() -> None:
    pack = california_grade_1_8_mapping_pack()
    validate_ingestion_pack(pack)
    assert pack.curriculum_version == CA_CURRICULUM_VERSION
    assert pack.source_uri == CA_SOURCE_URI
    assert pack.lifecycle_status == "IMPLEMENTED"
    assert len(pack.standards) == 59
    assert len(pack.proposed_mappings) == 59
    assert len(stable_pack_keys(pack)) == len(set(stable_pack_keys(pack)))


def test_every_grade_1_8_mapping_targets_existing_canonical_math() -> None:
    canonical = _canonical_skill_codes()
    pack = california_grade_1_8_mapping_pack()
    missing = {
        mapping.canonical_skill_code
        for mapping in pack.proposed_mappings
        if mapping.canonical_skill_code not in canonical
    }
    assert missing == set()


def test_grade_1_8_preserves_official_identifier_shapes() -> None:
    pack = california_grade_1_8_mapping_pack()
    codes = {standard.code for standard in pack.standards}
    assert {"1.OA.1", "3.MD.8", "5.NF.7", "6.RP.1", "7.SP.8", "8.SP.4"} <= codes
    assert all(not code.startswith("MIHUR.") for code in codes)


@pytest.mark.parametrize(
    ("pathway", "expected_code", "discipline"),
    [
        ("ALGEBRA_I", "CA_CCSSM_ALGEBRA_I", "Algebra I"),
        ("MATHEMATICS_I", "CA_CCSSM_MATHEMATICS_I", "Mathematics I"),
    ],
)
def test_grade9_pathways_are_explicit_not_fabricated_grade_bucket(
    pathway: str, expected_code: str, discipline: str
) -> None:
    pack = california_grade9_pathway_pack(pathway)
    validate_ingestion_pack(pack)
    assert pack.curriculum_code == expected_code
    assert len(pack.standards) == 7
    assert all(discipline in standard.title for standard in pack.standards)
    assert {standard.code for standard in pack.standards} >= {
        "A-SSE.1.a",
        "A-CED.1",
        "A-REI.3",
        "F-IF.2",
        "S-ID.1",
    }
    assert not any(standard.code.startswith("9.") for standard in pack.standards)


@pytest.mark.parametrize("pathway", ["ALGEBRA_I", "MATHEMATICS_I"])
def test_grade9_mapping_targets_existing_canonical_math(pathway: str) -> None:
    canonical = _canonical_skill_codes()
    pack = california_grade9_pathway_pack(pathway)
    assert {
        mapping.canonical_skill_code for mapping in pack.proposed_mappings
    } <= canonical


def test_mapping_types_fail_closed_where_canonical_skill_is_narrower() -> None:
    pack = california_grade_1_8_mapping_pack()
    mappings = {m.standard_code: m for m in pack.proposed_mappings}
    assert mappings["8.SP.4"].mapping_type == "EQUIVALENT"
    assert mappings["8.F.1"].mapping_type == "PARTIAL"
    assert mappings["6.NS.6"].mapping_type == "PARTIAL"
    assert mappings["5.NBT.7"].mapping_type == "PARTIAL"


def test_mapping_slice_does_not_claim_california_complete() -> None:
    counts = proposed_standard_count_by_grade()
    assert set(counts) == set(range(1, 10))
    assert all(count > 0 for count in counts.values())
    # These are mapping proposals only. Completion remains owned by the
    # national coverage gates: full ingestion, review, and publication.
    pack = california_grade_1_8_mapping_pack()
    assert all(
        "human review/publication remains required" in (mapping.rationale or "")
        for mapping in pack.proposed_mappings
    )


def test_invalid_grade9_pathway_fails_closed() -> None:
    with pytest.raises(ValueError, match="ALGEBRA_I or MATHEMATICS_I"):
        california_grade9_pathway_pack("grade_9")
