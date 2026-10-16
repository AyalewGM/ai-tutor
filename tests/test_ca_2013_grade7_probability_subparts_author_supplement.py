"""California Grade 7 author-side probability-subpart evidence, not acceptance."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
SUPPLEMENT = BASE / "ca_2013_grade7_probability_subparts_author_supplement.v1.json"
AUTHOR = BASE / "ca_2013_grade7_24_source_author_slice.v1.json"


def test_ca_grade7_probability_supplement_identity_and_page_parity():
    notes = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    author = json.loads(AUTHOR.read_text(encoding="utf-8"))
    rows = notes["rows"]
    ids = [r["expectation_id"] for r in rows]
    existing = {r["expectation_id"]: r for r in author["rows"]}
    assert ids == ["7.SP.6", "7.SP.7", "7.SP.8"]
    assert len(ids) == len(set(ids))
    assert notes["new_standard_count"] == 0
    assert notes["existing_grade7_parent_count"] == author["all_grade7_parent_identifiers_scoped_in_this_author_slice"] == 24
    assert notes["reference_author_scope_file"] == AUTHOR.name
    for row in rows:
        old = existing[row["expectation_id"]]
        assert row["printed_page"] == old["source_printed_page"]
        assert row["pdf_zero_based_page"] == old["source_pdf_page_index"]
        assert row["subparts"] == old["required_lettered_subparts"]


def test_ca_grade7_probability_material_subparts_preserved():
    notes = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in notes["rows"]}
    assert rows["7.SP.6"]["printed_page"] == 50
    assert any("approximate relative frequency" in v for v in rows["7.SP.6"]["material_conditions"])
    assert rows["7.SP.7"]["subparts"] == ["a", "b"]
    assert any("nonuniform" in v for v in rows["7.SP.7"]["material_conditions"])
    assert any("all outcomes" in v for v in rows["7.SP.7"]["material_conditions"])
    assert rows["7.SP.8"]["subparts"] == ["a", "b", "c"]
    assert any("everyday-language" in v for v in rows["7.SP.8"]["material_conditions"])
    assert any("generate event frequencies" in v for v in rows["7.SP.8"]["material_conditions"])


def test_ca_grade7_probability_remains_unapproved_and_inactive():
    notes = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    assert notes["status"] == "AUTHOR_SUPPLEMENT_PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert notes["publisher_original_bytes_authenticated"] is False
    assert notes["independent_source_fidelity"] == "PENDING"
    assert notes["activation"] == "FORBIDDEN"
    assert all(notes[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
