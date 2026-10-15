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


def test_grade2_page_splits_and_math_qualifiers():
    tx = json.loads((P / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    rows = {r["id"]: r for name in tx["regular_grade2_source_files"]
            for r in json.loads((P / name).read_text())["rows"]}
    for ident, row in rows.items():
        group = int(ident.split("(b)(")[1].split(")")[0])
        sub = ident.rsplit("(", 1)[1][0]
        page = 8 if group == 1 else 9 if group <= 6 else (
            10 if group <= 9 or (group == 10 and sub in "AB") else 11)
        assert row["source_pdf_printed_page"] == page, ident
    assert "40" in rows["111.4(b)(7)(A)"]["scope"]
    assert "12 sides" in rows["111.4(b)(8)(C)"]["scope"]
    assert "gaps or overlaps" in rows["111.4(b)(9)(F)"]["scope"]
    assert "intervals of one or more" in rows["111.4(b)(10)(B)"]["scope"]
    assert "intervals are one" in rows["111.4(b)(10)(C)"]["scope"]
