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
