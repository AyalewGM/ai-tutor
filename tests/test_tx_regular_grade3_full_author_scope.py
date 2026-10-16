"""Texas regular Grade 3 source author inventory, not independent acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = ("tx_regular_grade3_process_place_value_fractions_author.v1.json",
         "tx_regular_grade3_operations_geometry_data_finance_author.v1.json")


def test_grade3_exact_53_identifiers_and_source_page_parity():
    docs = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES]
    rows = [r for doc in docs for r in doc["rows"]]
    expected = [f"111.5(b)({g})({letter})" for g, letters in
                ((1, "ABCDEFG"), (2, "ABCD"), (3, "ABCDEFGH"),
                 (4, "ABCDEFGHIJK"), (5, "ABCDE"), (6, "ABCDE"),
                 (7, "ABCDE"), (8, "AB"), (9, "ABCDEF"))
                for letter in letters]
    assert [r["id"] for r in rows] == expected
    assert len(rows) == len(set(expected)) == 53
    assert all(r["source_pdf_page_index"] + 1 == r["source_printed_page"] for r in rows)
    by_id = {r["id"]: r["scope"] for r in rows}
    assert "10 by 10" in by_id["111.5(b)(4)(D)"]
    assert "standard algorithm" in by_id["111.5(b)(4)(G)"]
    assert "within 100" in by_id["111.5(b)(4)(K)"]
    assert "multiplicative comparison" in by_id["111.5(b)(5)(C)"]
    assert "non-overlapping rectangles" in by_id["111.5(b)(6)(D)"]
    assert "equal shares may differ in shape" in by_id["111.5(b)(6)(E)"]
    assert "scaled intervals" in by_id["111.5(b)(8)(A)"]
    assert "usually with interest" in by_id["111.5(b)(9)(D)"]
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["publisher_original_bytes_authenticated"] is False
        assert doc["activation"] == "FORBIDDEN"
        assert all(doc[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))


def test_grade3_matrix_counts_unaccepted():
    tx = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade3_author_scope_rows"] == 53
    assert tx["regular_grade3_independently_accepted_source_rows"] == 0
    assert tx["regular_grade3_source_files"] == list(FILES)
    assert "REGULAR_GRADE_3" not in tx["unextracted_tracks"]
