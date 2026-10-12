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
        "G": {"A": [1, 2, 3, 4, 5], "B": [6, 7, 8], "C": [9]},
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
    assert len(identifiers) == 81
    assert len(set(identifiers)) == 81
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

    assert len(grade8) == 28
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

    assert reconciliation["official_expectation_count"] == len(rows) == 81
    assert reconciliation["repository_existing_expectation_rows"] == existing == 28
    assert reconciliation["unmapped_expectations"] == 81 - existing == 52
    assert reconciliation["existing_seed_rows_by_grade"] == {
        "6": 5,
        "7": 5,
        "8": 0,
    }


def test_dc_standards_provenance_is_reproducible_and_separate_from_inventory_date() -> None:
    manifest = _manifest()
    curriculum = manifest['curriculum']
    provenance = manifest['provenance']
    assert curriculum['course_code'] == 'DC_CCSS_MATH_GRADES_6_8'
    assert curriculum['standards_version'] == 'CCSS-2010 (current DC adoption)'
    assert curriculum['implementation_school_year'] == '2014-2015'
    assert curriculum['implementation_milestone'] == 'FULL_IMPLEMENTATION_OF_2010_CCSS'
    assert provenance['inventory_as_of'] == provenance['checked_date'] == '2026-10-12'
    assert provenance['adoption_history_authority_url'] == 'https://osse.dc.gov/page/common-core-state-standards-mathematics'
    assert all(row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED' for row in manifest['expectations'])


def test_dc_2023_review_detects_missing_grade8_geometry_volume_standard() -> None:
    manifest = _manifest()
    row = next(r for r in manifest['expectations'] if r['expectation_id'] == '8.G.C.9')
    assert row['source_locator'] == 'https://www.thecorestandards.org/Math/Content/8/G/C/9/'
    assert row['scope_summary'].startswith('Use formulas for the volumes of cones')
    assert row['classification']['standards_mapped'] == 'NO'
    assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
    assert len([r for r in manifest['expectations'] if r['grade'] == 8 and r['domain'] == 'G']) == 9


def test_dc_source_fidelity_ledger_is_total_and_fail_closed() -> None:
    evidence = json.loads((MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    manifest = _manifest()
    assert evidence['status'] == 'AUTHOR_SOURCE_LOCATORS_REVIEW_REQUIRED'
    assert len(evidence['records']) == len(manifest['expectations']) == 81
    for row, source in zip(manifest['expectations'], evidence['records'], strict=True):
        assert row['expectation_id'] == source['expectation_id']
        assert row['source_locator'] == source['source_text_url']
        assert row['official_subpart_identifiers'] == source['lettered_subpart_ids']
        assert row['source_domain_section_url'] == source['source_section_url']
        assert source['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
    assert next(x for x in evidence['records'] if x['expectation_id'] == '7.SP.C.8')['lettered_subpart_ids'] == ['7.SP.C.8.a','7.SP.C.8.b','7.SP.C.8.c']
