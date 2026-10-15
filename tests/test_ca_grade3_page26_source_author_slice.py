import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_ca_grade3_p26_identifiers_and_safety():
    j = json.loads((ROOT / "ca_2013_grade3_page26_source_author_slice.v1.json").read_text())
    ids = [r["expectation_id"] for r in j["rows"]]
    assert ids == ["3.NBT.2", "3.NBT.3", "3.NF.1", "3.NF.2.a",
                   "3.NF.2.b", "3.NF.3.a", "3.NF.3.b", "3.NF.3.c",
                   "3.NF.3.d", "3.MD.1", "3.MD.2"]
    assert j["expectation_count"] == len(ids) == len(set(ids)) == 11
    assert (j["source_printed_page"], j["source_pdf_zero_based_page_index"]) == (26, 32)
    assert j["fraction_allowed_denominators"] == [2, 3, 4, 6, 8]
    assert j["independent_source_fidelity"] == "PENDING"
    assert j["activation"] == "FORBIDDEN"
    assert all(j[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    rows = {r["expectation_id"]: r for r in j["rows"]}
    assert "same whole" in rows["3.NF.3.d"]["author_mathematical_scope"]
    assert "for example" in rows["3.NF.3.d"]["author_mathematical_scope"]
    assert "multiplicative-comparison" in rows["3.MD.2"]["author_mathematical_scope"]
    assert all(r["source_review_status"].startswith("AUTHOR_EDITORIAL") for r in j["rows"])
    early = json.loads((ROOT / "ca_2013_grade3_page25_source_author_slice.v1.json").read_text())
    assert not set(ids).intersection(r["expectation_id"] for r in early["rows"])
