"""Texas Grade 2 page-9 author evidence; no independent source approval."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade2_18_publisher_page9_rows_remain_provisional():
    tx = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    names = tx["regular_grade2_source_files"][:2]
    assert names == ["tx_regular_grade2_number_fraction_author.v1.json",
                     "tx_regular_grade2_operations_4_6_author.v1.json"]
    docs = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in names]
    ids = [row["id"] for doc in docs for row in doc["rows"]]
    expected = (
        [f"111.4(b)(2)({x})" for x in "ABCDEF"]
        + [f"111.4(b)(3)({x})" for x in "ABCD"]
        + [f"111.4(b)(4)({x})" for x in "ABCD"]
        + [f"111.4(b)(5)({x})" for x in "AB"]
        + [f"111.4(b)(6)({x})" for x in "AB"]
    )
    assert ids == expected
    assert len(ids) == len(set(ids)) == 18
    assert tx["regular_grade2_111_4_author_scope_rows"] >= 18
    assert tx["regular_grade2_111_4_independently_accepted_source_rows"] == 0
    assert "REGULAR_GRADE_2" not in tx["unextracted_tracks"]
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["publisher_original_bytes_authenticated"] is False
        assert doc["activation"] == "FORBIDDEN"
        assert all(doc[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
        for row in doc["rows"]:
            assert row["source_pdf_printed_page"] == 9
            assert row["source_pdf_page_index"] == 8
            assert row["independent_source_fidelity"] == "PENDING"
    scopes = {r["id"]: r["scope"].lower() for doc in docs for r in doc["rows"]}
    assert "four two-digit" in scopes["111.4(b)(4)(B)"]
    assert "multi-step" in scopes["111.4(b)(4)(C)"]
    assert "within 1,000" in scopes["111.4(b)(4)(D)"]
    assert "one dollar" in scopes["111.4(b)(5)(A)"]
    assert "decimal point" in scopes["111.4(b)(5)(B)"]
    assert "multiplication" in scopes["111.4(b)(6)(A)"]
    assert "division" in scopes["111.4(b)(6)(B)"]
