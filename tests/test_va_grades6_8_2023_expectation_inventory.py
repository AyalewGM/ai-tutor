import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "va_grades6_8_2023.expectations.v1.json"
)

EXPECTED_IDS = {
    *(f"6.NS.{number}" for number in range(1, 4)),
    *(f"6.CE.{number}" for number in range(1, 3)),
    *(f"6.MG.{number}" for number in range(1, 5)),
    *(f"6.PS.{number}" for number in range(1, 3)),
    *(f"6.PFA.{number}" for number in range(1, 5)),
    *(f"7.NS.{number}" for number in range(1, 4)),
    *(f"7.CE.{number}" for number in range(1, 3)),
    *(f"7.MG.{number}" for number in range(1, 5)),
    *(f"7.PS.{number}" for number in range(1, 3)),
    *(f"7.PFA.{number}" for number in range(1, 5)),
    *(f"8.NS.{number}" for number in range(1, 3)),
    "8.CE.1",
    *(f"8.MG.{number}" for number in range(1, 6)),
    *(f"8.PS.{number}" for number in range(1, 4)),
    *(f"8.PFA.{number}" for number in range(1, 6)),
}

REPOSITORY_EXISTING_IDS = {
    "6.NS.1",
    "6.CE.1",
    "6.PFA.1",
    "6.PFA.2",
    "6.PFA.3",
    "7.CE.1",
    "7.CE.2",
    "7.MG.1",
    "7.MG.2",
    "7.MG.3",
    "7.MG.4",
    "7.PS.1",
    "7.PFA.1",
    "7.PFA.3",
    "7.PFA.4",
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 46
    assert len(set(identifiers)) == 46
    assert set(identifiers) == EXPECTED_IDS


def test_every_expectation_carries_grade_and_valid_strand() -> None:
    rows = _manifest()["expectations"]
    strands = {"NS", "CE", "MG", "PS", "PFA"}

    for row in rows:
        grade, strand, _ = row["expectation_id"].split(".")
        assert int(grade) == row["grade"]
        assert row["grade"] in (6, 7, 8)
        assert strand == row["strand"] in strands


def test_repository_existing_rows_are_narrow_and_unverified() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert existing == REPOSITORY_EXISTING_IDS
    assert len(existing) == 16
    for row in rows:
        if row["expectation_id"] in existing:
            assert row["repository_existing_crosswalks"]
            assert all(
                code.startswith(("VA6.", "VA7."))
                for code in row["repository_existing_crosswalks"]
            )
            assert row["classification"]["standards_mapped"] == (
                "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            )
        else:
            assert row["repository_existing_crosswalks"] == []
            assert row["classification"]["standards_mapped"] == "NO"
            assert row["proposed_mapping_status"] == (
                "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
            )


def test_grade8_has_no_repository_rows_at_all() -> None:
    rows = _manifest()["expectations"]

    assert [row["expectation_id"] for row in rows if row["grade"] == 8] == [
        f"8.{prefix}"
        for prefix in (
            "NS.1", "NS.2", "CE.1", "MG.1", "MG.2", "MG.3", "MG.4", "MG.5",
            "PS.1", "PS.2", "PS.3", "PFA.1", "PFA.2", "PFA.3", "PFA.4", "PFA.5",
        )
    ]
    assert all(
        row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        for row in rows
        if row["grade"] == 8
    )


def test_all_readiness_and_mastery_claims_fail_closed() -> None:
    manifest = _manifest()

    assert manifest["safety"] == {
        "activation": "FORBIDDEN",
        "mapping_review_required": True,
        "new_canonical_ids_created": False,
        "learner_mastery_mutation": False,
        "verified_coverage_claim": False,
    }
    for row in manifest["expectations"]:
        classification = row["classification"]
        assert classification["mathematically_reviewed_skill"] == (
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_VA_TARGET"
        )
        assert classification["generator_available"] == (
            "NOT_AUDITED_FOR_EXACT_EXPECTATION_AND_TARGET"
        )
        assert classification["validated_practice"] == "NO_VERIFIED_EVIDENCE"
        assert classification["assessment_ready"] == "NO_VERIFIED_EVIDENCE"
        assert classification["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_reconciliation_counts_are_internally_consistent() -> None:
    manifest = _manifest()
    reconciliation = manifest["reconciliation"]
    rows = manifest["expectations"]
    existing = sum(
        1
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    )

    assert reconciliation["official_expectation_count"] == len(rows) == 46
    assert reconciliation["repository_existing_expectation_rows"] == existing == 15
    assert reconciliation["unmapped_expectations"] == 46 - existing == 31
    assert reconciliation["existing_seed_rows_by_grade"] == {
        "6": 5,
        "7": 5,
        "8": 0,
    }
    assert reconciliation["seed_rows_without_clear_expectation"] == [
        "VA6.PFA.EXPR"
    ]


def test_each_va_expectation_links_to_official_grade_sol_document() -> None:
    manifest = _manifest()
    sources = manifest['provenance']['grade_standards_documents']
    assert set(sources) == {'6', '7', '8'}
    assert manifest['provenance']['instructional_support_role'] == 'IMPLEMENTATION_GUIDANCE_ONLY_NOT_STANDARDS_AUTHORITY'
    for grade, source in sources.items():
        assert source['grade'] == int(grade)
        assert source['publication_or_revision'] == 'August 2023'
        assert source['authority'] == 'VDOE_2023_STANDARDS_DOCUMENT'
        assert source['source_url'].startswith('https://www.doe.virginia.gov/home/showpublisheddocument/')
        assert source['checked_date'] == '2026-10-12'
    for row in manifest['expectations']:
        source = sources[str(row['grade'])]
        assert row['source_locator'] == source['source_url']
        assert row['source_document_id'] == source['source_id']
        assert row['instructional_support_locator'] == manifest['provenance']['instructional_resources_url']
        assert row['source_locator'] != row['instructional_support_locator']
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'


def test_va7_histogram_data_cycle_is_not_inferred_from_probability_seed() -> None:
    manifest = _manifest()
    row = next(r for r in manifest['expectations'] if r['expectation_id'] == '7.PS.2')
    assert row['repository_existing_crosswalks'] == []
    assert row['classification']['standards_mapped'] == 'NO'
    assert row['proposed_mapping_status'] == 'NO_REPOSITORY_EXPECTATION_EQUIVALENCE_EVIDENCE'
    assert row['mapping_correction_evidence']['decision'] == 'REMOVE_UNSUPPORTED_PROVISIONAL_RELATION_NOT_A_MISSING_CORE_CLAIM'
    assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'


def test_repository_relation_presence_matches_standards_mapped_classification() -> None:
    manifest = _manifest()
    for row in manifest['expectations']:
        if row['repository_existing_crosswalks']:
            assert row['proposed_mapping_status'] == 'REPOSITORY_EXISTING_UNVERIFIED'
            assert row['classification']['standards_mapped'] == 'REPOSITORY_ROW_EXISTS_NOT_ACCEPTED'
        else:
            assert row['classification']['standards_mapped'] == 'NO'
            assert row['proposed_mapping_status'] != 'REPOSITORY_EXISTING_UNVERIFIED'
