"""Fail-closed linkage checks for lettered MSDE Algebra I requirements."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1] / "docs" / "curriculum" / "standards"
PARENTS = ROOT / "md_algebra1_traditional_2026_27.expectations.v1.json"
SUBPARTS = ROOT / "md_algebra1_2026_27.lettered_subparts.v1.json"

EXPECTED = {
    "A.SSE.A.1": "ab",
    "A.SSE.B.3": "abc",
    "A.REI.B.4": "ab",
    "F.IF.C.7": "ab",
    "F.IF.C.8": "a",
    "F.BF.A.1": "a",
    "F.LE.A.1": "abc",
    "S.ID.B.6": "abc",
}


def test_lettered_requirements_are_linked_without_inventing_skill_ids() -> None:
    parents = json.loads(PARENTS.read_text(encoding="utf-8"))
    subparts = json.loads(SUBPARTS.read_text(encoding="utf-8"))
    parent_by_id = {
        row["expectation_id"]: row for row in parents["expectations"]
    }
    rows = subparts["subparts"]
    assert len(rows) == subparts["counts"]["lettered_subparts"] == 17
    assert len({row["normalized_subpart_id"] for row in rows}) == 17
    assert len(EXPECTED) == subparts["counts"]["parent_standards_with_lettered_subparts"]
    for parent, letters in EXPECTED.items():
        actual = "".join(
            row["subpart_letter"]
            for row in rows
            if row["parent_standard_id"] == parent
        )
        assert actual == letters
    for row in rows:
        parent = parent_by_id[row["parent_standard_id"]]
        assert row["source_page"] == parent["source_page"]
        assert row["normalized_subpart_id"] == (
            row["parent_standard_id"] + "." + row["subpart_letter"]
        )
        assert row["proposed_canonical_skill_ids"] == []
        assert row["readiness"]["accepted_mapping"] is False
        assert row["readiness"]["verified_mastery_evidence"] is False


def test_subpart_inventory_does_not_authorize_parent_coverage() -> None:
    data = json.loads(SUBPARTS.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_PROVISIONAL_SUBPART_EXTRACTION"
    assert data["safety"] == {
        "activation": "FORBIDDEN",
        "automatic_parent_coverage_from_one_subpart": False,
        "automatic_mastery_from_public_item": False,
        "create_canonical_ids": False,
        "change_historical_mastery": False,
    }
