"""All Texas Grade 2 rows are author provisional, not activated."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade2_50_distinct_ids_stay_provisional():
    tx = json.loads((P / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade2_111_4_author_scope_rows"] == 50
    assert tx["regular_grade2_111_4_independently_accepted_source_rows"] == 0
    assert len(tx["regular_grade2_source_files"]) == 11
    ids = []
    for filename in tx["regular_grade2_source_files"]:
        doc = json.loads((P / filename).read_text())
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        ids.extend(row["id"] for row in doc["rows"])
    assert len(ids) == len(set(ids)) == 50


def test_grade2_exact_ids_and_page_locators():
    tx = json.loads((P / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    rows = [r for name in tx["regular_grade2_source_files"]
            for r in json.loads((P / name).read_text())["rows"]]
    expected = {f"111.4(b)({n})({s})" for n, letters in
                [(1, "ABCDEFG"), (2, "ABCDEF"), (3, "ABCD"), (4, "ABCD"),
                 (5, "AB"), (6, "AB"), (7, "ABC"), (8, "ABCDE"),
                 (9, "ABCDEFG"), (10, "ABCD"), (11, "ABCDEF")]
                for s in letters}
    assert {r["id"] for r in rows} == expected
    for row in rows:
        assert row["source_pdf_page_index"] + 1 == row["source_pdf_printed_page"]
        assert row["independent_source_fidelity"] == "PENDING"
