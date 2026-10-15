"""Texas Grade 4 §111.6(b)(1)-(3): bounded author evidence only."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade4_22_source_ids_and_math_boundaries():
    data = json.loads((BASE / "tx_regular_grade4_process_place_value_fractions_author.v1.json").read_text())
    rows = data["rows"]
    expected = [f"111.6(b)({g})({letter})"
                for g, letters in ((1, "ABCDEFG"), (2, "ABCDEFGH"), (3, "ABCDEFG"))
                for letter in letters]
    assert [r["id"] for r in rows] == expected
    assert len(rows) == len(set(expected)) == data["author_scope_rows"] == 22
    assert all(r["source_pdf_page_index"] == r["source_printed_page"] - 1 for r in rows)
    by_id = {r["id"]: r for r in rows}
    assert "one-tenth" in by_id["111.6(b)(2)(A)"]["scope"]
    assert "1,000,000,000" in by_id["111.6(b)(2)(B)"]["scope"]
    assert "hundred-thousands" in by_id["111.6(b)(2)(D)"]["scope"]
    assert "a>b" in by_id["111.6(b)(3)(A)"]["scope"]
    assert "same denominator" in by_id["111.6(b)(3)(B)"]["scope"]
    assert "equal denominators" in by_id["111.6(b)(3)(E)"]["scope"]
    assert "same whole" in by_id["111.6(b)(3)(F)"]["scope"]
    assert by_id["111.6(b)(3)(A)"]["source_printed_page"] == 16
    assert by_id["111.6(b)(3)(C)"]["source_printed_page"] == 17
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["publisher_original_bytes_authenticated"] is False
    assert data["activation"] == "FORBIDDEN"
    assert all(data[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
    assert data["remaining_grade4_sections"].startswith("111.6(b)(4)")
