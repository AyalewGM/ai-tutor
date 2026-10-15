"""Texas Grade 5 source draft: exact 46 identifiers, no downstream authorization."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = ("tx_regular_grade5_process_decimal_operations_author.v1.json",
         "tx_regular_grade5_algebra_geometry_finance_author.v1.json")


def test_grade5_all_46_source_identifiers_and_material_bounds():
    docs = [json.loads((ROOT / f).read_text(encoding="utf-8")) for f in FILES]
    rows = [r for d in docs for r in d["rows"]]
    expected = ([f"111.7(b)({g})({x})" for g, letters in
                 ((1, "ABCDEFG"), (2, "ABC"), (3, "ABCDEFGHIJKL"),
                  (4, "ABCDEFGH"))
                 for x in letters]
                + ["111.7(b)(5)"]
                + [f"111.7(b)(6)({x})" for x in "AB"]
                + ["111.7(b)(7)"]
                + [f"111.7(b)(8)({x})" for x in "ABC"]
                + [f"111.7(b)(9)({x})" for x in "ABC"]
                + [f"111.7(b)(10)({x})" for x in "ABCDEF"])
    assert [r["id"] for r in rows] == expected
    assert len(rows) == len(set(expected)) == 46
    assert all(r["source_pdf_page_index"] == r["source_printed_page"] - 1 for r in rows)
    by_id = {r["id"]: r["scope"] for r in rows}
    assert "thousandths" in by_id["111.7(b)(2)(A)"]
    assert "three-digit by two-digit" in by_id["111.7(b)(3)(B)"]
    assert "unequal denominators" in by_id["111.7(b)(3)(H)"]
    assert "unit fraction divided by whole number" in by_id["111.7(b)(3)(J)"]
    assert "V=Bh" in by_id["111.7(b)(4)(G)"]
    assert "first quadrant" in by_id["111.7(b)(8)(B)"]
    assert "scatterplots" in by_id["111.7(b)(9)(B)"]
    assert "gross versus net" in by_id["111.7(b)(10)(B)"]
    for d in docs:
        assert d["independent_source_fidelity"] == "PENDING"
        assert d["publisher_original_bytes_authenticated"] is False
        assert d["activation"] == "FORBIDDEN"
        assert all(d[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))


def test_grade5_author_matrix_unaccepted():
    tx = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade5_author_scope_rows"] == 46
    assert tx["regular_grade5_source_files"] == list(FILES)
    assert tx["regular_grade5_independently_accepted_source_rows"] == 0
    assert "REGULAR_GRADE_5" not in tx["unextracted_tracks"]
