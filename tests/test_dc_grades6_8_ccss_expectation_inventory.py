import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "dc_grades6_8_ccss.expectations.v1.json"
)


def _ids(grade: int, domains: dict) -> set:
    return {
        f"{grade}.{domain}.{cluster}.{number}"
        for domain, clusters in domains.items()
        for cluster, numbers in clusters.items()
        for number in numbers
    }


EXPECTED_IDS = {
    *_ids(6, {
        "RP": {"A": [1, 2, 3]},
        "NS": {"A": [1], "B": [2, 3, 4], "C": [5, 6, 7, 8]},
        "EE": {"A": [1, 2, 3, 4], "B": [5, 6, 7, 8], "C": [9]},
        "G": {"A": [1, 2, 3, 4]},
        "SP": {"A": [1, 2, 3], "B": [4, 5]},
    }),
    *_ids(7, {
        "RP": {"A": [1, 2, 3]},
        "NS": {"A": [1, 2, 3]},
        "EE": {"A": [1, 2], "B": [3, 4]},
        "G": {"A": [1, 2, 3], "B": [4, 5, 6]},
        "SP": {"A": [1, 2], "B": [3, 4], "C": [5, 6, 7, 8]},
    }),
    *_ids(8, {
        "NS": {"A": [1, 2]},
        "EE": {"A": [1, 2, 3, 4], "B": [5, 6], "C": [7, 8]},
        "F": {"A": [1, 2, 3], "B": [4, 5]},
        "G": {"A": [1, 2, 3, 4, 5], "B": [6, 7, 8]},
        "SP": {"A": [1, 2, 3, 4]},
    }),
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 80
    assert len(set(identifiers)) == 80
    assert set(identifiers) == EXPECTED_IDS


def test_every_expectation_uses_ccss_domain_and_matches_grade() -> None:
    rows = _manifest()["expectations"]
    domains = {"RP", "NS", "EE", "G", "SP", "F"}

    for row in rows:
        grade, domain, cluster, _ = row["expectation_id"].split(".")
        assert int(grade) == row["grade"]
        assert row["grade"] in (6, 7, 8)
        assert domain == row["domain"] in domains
        assert cluster == row["cluster"]


def test_repository_existing_rows_are_narrow_and_unverified() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert len(existing) == 28
    for row in rows:
        if row["expectation_id"] in existing:
            assert row["repository_existing_crosswalks"]
            assert all(
                code.startswith(("DC6.", "DC7."))
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
    grade8 = [row for row in rows if row["grade"] == 8]

    assert len(grade8) == 27
    assert all(
        row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        for row in grade8
    )
    # No geometry seed exists for DC at any grade.
    assert all(
        row["repository_existing_crosswalks"] == []
        for row in rows
        if row["domain"] == "G"
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
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_DC_TARGET"
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

    assert reconciliation["official_expectation_count"] == len(rows) == 80
    assert reconciliation["repository_existing_expectation_rows"] == existing == 28
    assert reconciliation["unmapped_expectations"] == 80 - existing == 52
    assert reconciliation["existing_seed_rows_by_grade"] == {
        "6": 5,
        "7": 5,
        "8": 0,
    }
