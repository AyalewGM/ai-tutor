"""Author-side guard for California Grade 7 probability supplement source parity.

This tests authored evidence only; it does not approve publisher source fidelity.
"""

import json
from pathlib import Path


STANDARDS = (
    Path(__file__).resolve().parents[1] / "docs" / "curriculum" / "standards"
)
PARENT = STANDARDS / "ca_2013_grade7_24_source_author_slice.v1.json"
SUPPLEMENT = (
    STANDARDS / "ca_2013_grade7_probability_subparts_author_supplement.v1.json"
)


def test_grade7_probability_supplement_parent_identity_and_fail_closed():
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    parents = {row["expectation_id"]: row for row in parent["rows"]}

    assert len(parent["rows"]) == len(parents) == 24
    assert supplement["existing_grade7_parent_count"] == 24
    assert supplement["new_standard_count"] == 0
    assert supplement["publisher_original_bytes_authenticated"] is False
    assert supplement["reference_author_scope_file"] == PARENT.name
    assert supplement["source_url"] == parent["official_source"]
    assert {r["expectation_id"] for r in supplement["rows"]} == {
        "7.SP.6", "7.SP.7", "7.SP.8"
    }

    for row in supplement["rows"]:
        original = parents[row["expectation_id"]]
        assert row["subparts"] == original["required_lettered_subparts"]
        assert row["printed_page"] == original["source_printed_page"]
        assert row["pdf_zero_based_page"] == original["source_pdf_page_index"]
        assert original["source_review_status"].startswith("AUTHOR_")
        for key in ("canonical_equivalence", "assessment", "mastery"):
            assert original[key] == "UNVERIFIED"

    for document in (parent, supplement):
        assert document["independent_source_fidelity"] == "PENDING"
        assert document["activation"] == "FORBIDDEN"
        for key in ("canonical_equivalence", "assessment", "mastery"):
            assert document[key] == "UNVERIFIED"


def test_grade7_sp6_supplement_retains_bidirectional_probability():
    supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    row = next(
        row for row in supplement["rows"]
        if row["expectation_id"] == "7.SP.6"
    )
    conditions = " ".join(row["material_conditions"]).lower()

    assert "collecting data on the chance process" in conditions
    assert "long-run relative frequency" in conditions
    assert "given a probability" in conditions
    assert "approximate relative frequency" in conditions
    assert "need not equal exact expected counts" in conditions


def test_grade7_sp7_sp8_lettered_structure_retained():
    supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    rows = {row["expectation_id"]: row for row in supplement["rows"]}

    assert rows["7.SP.7"]["subparts"] == ["a", "b"]
    assert rows["7.SP.8"]["subparts"] == ["a", "b", "c"]
    sp7 = " ".join(rows["7.SP.7"]["material_conditions"]).lower()
    sp8 = " ".join(rows["7.SP.8"]["material_conditions"]).lower()
    for required in ("uniform", "observed frequencies", "discrepancies"):
        assert required in sp7
    for required in ("sample space", "tree diagrams", "simulation"):
        assert required in sp8
