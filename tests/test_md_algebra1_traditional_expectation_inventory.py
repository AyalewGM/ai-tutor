"""Fail-closed checks for the draft Maryland traditional Algebra I standards inventory."""

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_algebra1_traditional_2026_27.expectations.v1.json"
)

DOMAIN_COUNTS = {
    "Number and Quantity": 4,
    "Algebra": 17,
    "Functions": 15,
    "Statistics": 4,
}


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_traditional_course_identity_and_inventory() -> None:
    manifest = _load()
    ids = [row["expectation_id"] for row in manifest["expectations"]]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert manifest["course"]["course_code"] == "MD_ALGEBRA_1_2026_27"
    assert manifest["course"]["distinct_from_course_code"] == (
        "MD_INTEGRATED_ALGEBRA_1_2027_28"
    )
    assert len(ids) == len(set(ids)) == 40
    assert {row["domain"] for row in manifest["expectations"]} == set(DOMAIN_COUNTS)
    for domain, count in DOMAIN_COUNTS.items():
        assert sum(row["domain"] == domain for row in manifest["expectations"]) == count


def test_source_provenance_and_fail_closed_status() -> None:
    manifest = _load()
    assert manifest["provenance"]["standards_url"] == (
        "https://msde.maryland.gov/media/17798"
    )
    assert manifest["provenance"]["assessment_evidence_url"] == (
        "https://msde.maryland.gov/media/17801"
    )
    assert manifest["inventory"]["accepted_mappings"] == 0
    assert manifest["inventory"]["verified_coverage"] == 0
    assert manifest["safety"] == {
        "activation": "FORBIDDEN",
        "mapping_review_required": True,
        "new_canonical_ids_created": False,
        "learner_mastery_mutation": False,
        "verified_coverage_claim": False,
    }
    for row in manifest["expectations"]:
        assert row["source_page"] in range(1, 8)
        assert row["source_url"] == manifest["provenance"]["standards_url"]
        assert row["scope_summary_type"] == (
            "EDITORIAL_PARAPHRASE_REQUIRES_SOURCE_REVIEW"
        )
        assert row["proposed_mapping_status"] == "NOT_PROPOSED"
        assert row["proposed_canonical_skill_ids"] == []
        assert row["classification"]["standards_mapped"] == "NO_ACCEPTED_MAPPING"
        assert row["classification"]["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_traditional_algebra1_source_ledger_includes_all_parent_and_lettered_keys() -> None:
    data = _load()
    ledger = json.loads((MANIFEST.parent / 'md_algebra1_traditional_2026_27.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    subparts = json.loads((MANIFEST.parent / 'md_algebra1_2026_27.lettered_subparts.v1.json').read_text(encoding='utf-8'))
    assert ledger['status'] == 'AUTHOR_SOURCE_LOCATORS_REVIEW_REQUIRED'
    assert len(ledger['records']) == len(data['expectations']) == 40
    expected_subparts = {row['normalized_subpart_id'] for row in subparts['subparts']}
    actual_subparts = set()
    for row, source in zip(data['expectations'], ledger['records'], strict=True):
        assert row['expectation_id'] == source['expectation_id']
        assert row['source_page'] == source['printed_page']
        assert row['full_scope_source_locator'].endswith('#page=' + str(row['source_page']))
        assert row['official_subpart_identifiers'] == source['lettered_subpart_ids']
        assert row['parent_scope_independently_verified'] is False
        assert source['unlettered_parent_scope_review'] == 'REQUIRED_EVEN_IF_SUBPARTS_ARE_COMPLETE'
        assert source['independent_acceptance'] == 'PENDING'
        assert row['proposed_canonical_skill_ids'] == []
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
        actual_subparts.update(source['lettered_subpart_ids'])
    assert actual_subparts == expected_subparts
    assert len(actual_subparts) == 17
