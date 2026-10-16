"""Texas Grade 4 53 source clauses remain draft until independent fidelity review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = ("tx_regular_grade4_process_place_value_fractions_author.v1.json",
         "tx_regular_grade4_operations_geometry_finance_author.v1.json")


def test_grade4_all_53_author_ids_and_source_bounds():
    docs = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES]
    rows = [r for doc in docs for r in doc["rows"]]
    expected = [f"111.6(b)({g})({letter})"
                for g, letters in ((1, "ABCDEFG"), (2, "ABCDEFGH"),
                                   (3, "ABCDEFG"), (4, "ABCDEFGH"),
                                   (5, "ABCD"), (6, "ABCD"), (7, "ABCDE"),
                                   (8, "ABC"), (9, "AB"), (10, "ABCDE"))
                for letter in letters]
    assert [r["id"] for r in rows] == expected
    assert len(rows) == len(set(expected)) == 53
    assert all(r["source_pdf_page_index"] + 1 == r["source_printed_page"] for r in rows)
    by_id = {r["id"]: r["scope"] for r in rows}
    assert "a>b" in by_id["111.6(b)(3)(A)"]
    assert "same whole" in by_id["111.6(b)(3)(F)"]
    assert "15 by 15" in by_id["111.6(b)(4)(C)"]
    assert "remainders" in by_id["111.6(b)(4)(H)"]
    assert "4s" in by_id["111.6(b)(5)(C)"]
    assert "at most 180" in by_id["111.6(b)(7)(A)"]
    assert "1/360" in by_id["111.6(b)(7)(B)"]
    assert "safeguarding money" in by_id["111.6(b)(10)(E)"]
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["publisher_original_bytes_authenticated"] is False
        assert doc["activation"] == "FORBIDDEN"
        assert all(doc[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))


def test_grade4_matrix_is_author_only():
    tx = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade4_author_scope_rows"] == 53
    assert tx["regular_grade4_source_files"] == list(FILES)
    assert tx["regular_grade4_independently_accepted_source_rows"] == 0
    assert "REGULAR_GRADE_4" not in tx["unextracted_tracks"]
    assert "REGULAR_GRADE_4" not in tx["partially_author_scoped_tracks"]
