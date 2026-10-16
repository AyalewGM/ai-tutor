"""Texas regular Grade 3 bounded TEA source intake, independent review pending."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade3_process_place_value_fractions_source_bounds():
    data = json.loads((ROOT / "tx_regular_grade3_process_place_value_fractions_author.v1.json").read_text())
    rows = data["rows"]
    expected = ([f"111.5(b)(1)({x})" for x in "ABCDEFG"]
                + [f"111.5(b)(2)({x})" for x in "ABCD"]
                + [f"111.5(b)(3)({x})" for x in "ABCDEFGH"])
    assert [r["id"] for r in rows] == expected
    assert len(rows) == len(set(expected)) == data["author_scope_rows"] == 19
    assert all(r["source_pdf_page_index"] + 1 == r["source_printed_page"] for r in rows)
    by_id = {r["id"]: r["scope"] for r in rows}
    assert "100,000" in by_id["111.5(b)(2)(A)"]
    assert "hundred-thousands" in by_id["111.5(b)(2)(B)"]
    assert "10, 100, 1,000 or 10,000" in by_id["111.5(b)(2)(C)"]
    assert "2, 3, 4, 6 or 8" in by_id["111.5(b)(3)(A)"]
    assert "nonzero whole number" in by_id["111.5(b)(3)(C)"]
    assert "no greater than b" in by_id["111.5(b)(3)(D)"]
    assert "equally sized whole" in by_id["111.5(b)(3)(G)"]
    assert "same numerator or same denominator" in by_id["111.5(b)(3)(H)"]
    assert data["not_yet_scoped_sections"] == "111.5(b)(4)-(9)"
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["publisher_original_bytes_authenticated"] is False
    assert data["activation"] == "FORBIDDEN"
    for r in rows:
        assert all(r[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
