"""Texas regular Grade 6 complete author inventory is not independent acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade6_59_distinct_author_scopes_and_publisher_pages():
    matrix = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())
    tx = matrix["states"]["TX"]
    rows = []
    for name in tx["regular_grade6_source_files"]:
        d = json.loads((ROOT / name).read_text())
        assert d["independent_source_fidelity"] == "PENDING"
        assert d["activation"] == "FORBIDDEN"
        rows.extend(d["rows"])
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 59
    assert tx["regular_grade6_111_26_author_scope_rows"] == 59
    assert tx["regular_grade6_111_26_independently_accepted_source_rows"] == 0
    by_id = {r["id"]: r for r in rows}
    assert "greater or less than one" in by_id["111.26(b)(3)(B)"]["scope"]
    assert "IQR" in by_id["111.26(b)(12)(C)"]["scope"]
    assert "deposits, withdrawals and transfers" in by_id["111.26(b)(14)(C)"]["scope"]
    for r in rows:
        if "source_pdf_page_index" in r:
            assert r["source_pdf_page_index"] + 1 == r["source_pdf_printed_page"]
