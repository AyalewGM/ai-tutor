import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_grades6_8_2025.expectations.v1.json"
)

def _ids(grade: int, clusters: dict) -> set:
    return {
        f"{grade}.{domain}.{cluster}.{number}"
        for domain, parts in clusters.items()
        for cluster, numbers in parts.items()
        for number in numbers
    }


EXPECTED_IDS = {
    *_ids(6, {
        "NOS": {"A": [1], "B": [2, 3, 4], "C": [5, 6, 7, 8, 9]},
        "AT": {"A": [1, 2, 3, 4], "B": [5, 6, 7], "C": [8, 9, 10], "D": [11]},
        "GR": {"A": [1, 2, 3, 4]},
        "DS": {"A": [1, 2, 3, 4], "B": [5, 6]},
    }),
    *_ids(7, {
        "NOS": {"A": [1, 2, 3]},
        "AT": {"A": [1, 2, 3, 4], "B": [5, 6], "C": [7, 8, 9]},
        "GR": {"A": [1, 2], "B": [3, 4]},
        "DS": {"A": [1, 2], "B": [3], "C": [4, 5, 6]},
    }),
    *_ids(8, {
        "NOS": {"A": [1, 2], "B": [3, 4, 5]},
        "AT": {"A": [1, 2], "B": [3, 4, 5], "C": [6, 7, 8], "D": [9, 10, 11]},
        "GR": {"A": [1, 2, 3], "B": [4, 5]},
        "DS": {"A": [1], "B": [2, 3, 4], "C": [5, 6]},
    }),
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 79
    assert len(set(identifiers)) == 79
    assert set(identifiers) == EXPECTED_IDS


def test_every_expectation_uses_2025_domain_and_matches_grade() -> None:
    rows = _manifest()["expectations"]
    domains = {"NOS", "AT", "GR", "DS"}

    for row in rows:
        grade, domain, cluster, _ = row["expectation_id"].split(".")
        assert int(grade) == row["grade"]
        assert row["grade"] in (6, 7, 8)
        assert domain == row["domain"] in domains
        assert cluster.isalpha() and len(cluster) == 1
        # Legacy 2010-column identifiers must never appear as new IDs.
        assert domain != "NS"


def test_repository_links_match_merged_seed_reconciliation() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert len(existing) == 46
    for row in rows:
        if row["expectation_id"] in existing:
            assert row["repository_existing_crosswalks"]
            assert all(
                code.startswith(("M6.", "M7.", "M8."))
                for code in row["repository_existing_crosswalks"]
            )
            assert set(row["repository_existing_crosswalks"]) == set(
                row["provisional_relations"]
            )
            assert all(
                relation
                in {
                    "COMPOSITE_SCOPE",
                    "PARTIAL_SCOPE",
                    "NARROW_SUBSCOPE",
                    "CLOSE_SCOPE_REVIEW_REQUIRED",
                    "PARTIAL_OR_EXTRA_SCOPE",
                    "CROSS_GRADE_COMPOSITE",
                }
                for relation in row["provisional_relations"].values()
            )
            assert row["classification"]["standards_mapped"] == (
                "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            )
        else:
            assert row["repository_existing_crosswalks"] == []
            assert row["provisional_relations"] == {}
            assert row["classification"]["standards_mapped"] == "NO"


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
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_MD_TARGET"
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

    assert reconciliation["official_expectation_count"] == len(rows) == 79
    assert reconciliation["repository_existing_expectation_rows"] == existing == 46
    assert reconciliation["unmapped_expectations"] == 79 - existing == 33
    assert reconciliation["seed_rows_reconciled"] == 28
    assert {r["grade"] for r in rows} == {6, 7, 8}


def test_grade_specific_official_document_versions_and_adoption_sources() -> None:
    manifest = _manifest()
    curriculum = manifest['curriculum']
    assert curriculum['adopted_date'] == '2025-07'
    assert curriculum['board_adoption_date'] == '2025-07-29'
    assert curriculum['board_adoption_source_url'] == manifest['provenance']['authoritative_landing_page']
    sources = manifest['provenance']['grade_source_documents']
    assert {grade: source['revision'] for grade, source in sources.items()} == {
        '6': 'February 2026', '7': 'July 2025', '8': 'July 2025',
    }
    assert sources['6']['companion']['revision'] == 'Version 2, June 2026'
    assert sources['7']['companion']['revision'] == 'Version 2, June 2026'
    assert sources['8']['companion']['revision'] == 'Version 1, February 2026'
    assert sources['8']['companion']['version_verification'] == 'DIRECT_MSDE_COMPANION_GUIDE_COVER_PAGE'
    for row in manifest['expectations']:
        source = sources[str(row['grade'])]
        assert row['source_locator'] == source['url']
        assert row['source_document_id'] == source['source_id']
        assert row['source_document_revision'] == source['revision']
        assert source['role'] == 'AUTHORITATIVE_STANDARD_ID_AND_SCOPE'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
