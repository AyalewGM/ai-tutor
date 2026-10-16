"""Draft MSDE public item tags cannot confer mapping or mastery readiness."""

import json
from pathlib import Path

STANDARDS = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_algebra1_traditional_2026_27.expectations.v1.json"
)
EVIDENCE = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_algebra1_2024_public_assessment_evidence.v1.json"
)


def test_public_item_tags_refer_to_inventoried_parent_standards() -> None:
    standards = json.loads(STANDARDS.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    identifiers = {row["expectation_id"] for row in standards["expectations"]}
    items = evidence["items"]
    assert len(items) == 10
    assert len({row["item_number"] for row in items}) == len(items)
    for row in items:
        for standard in row["standards"]:
            # Released item labels can identify lettered subparts (e.g. .4.a).
            parent = standard.rsplit(".", 1)[0] if standard[-1].islower() else standard
            assert parent in identifiers
        assert row["calculator"] in {"CALCULATOR", "NO_CALCULATOR"}


def test_public_release_is_not_accepted_assessment_or_mastery() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == (
        "DRAFT_PUBLIC_ASSESSMENT_EVIDENCE_INDEX_NOT_MASTERY"
    )
    assert evidence["source"]["release_year"] == 2024
    assert evidence["readiness"] == {
        "accepted_standards_mapping": False,
        "mathematically_reviewed_skill": False,
        "generator_available": "NOT_AUDITED",
        "validated_practice": False,
        "assessment_ready": False,
        "verified_mastery_evidence": False,
    }
