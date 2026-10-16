"""Texas Grade 1 partial author scopes, not publisher acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade1_process_number_operations_source_boundaries():
    d = json.loads((ROOT / "tx_regular_grade1_process_number_operations_author.v1.json").read_text())
    rows = {r["id"]: r for r in d["rows"]}
    ids = ([f"111.3(b)(1)({c})" for c in "ABCDEFG"] +
           [f"111.3(b)(2)({c})" for c in "ABCDEFG"] +
           [f"111.3(b)(3)({c})" for c in "ABCDEF"])
    assert list(rows) == ids
    assert len(rows) == 20
    assert "up to 120" in rows["111.3(b)(2)(B)"]["scope"]
    assert "up to 100" in rows["111.3(b)(2)(G)"]["scope"]
    assert "multiple of ten" in rows["111.3(b)(3)(A)"]["scope"]
    assert "up to 99" in rows["111.3(b)(3)(A)"]["scope"]
    assert "within 20" in rows["111.3(b)(3)(B)"]["scope"]
    assert all(r["source_pdf_page_index"] + 1 == r["source_printed_page"] for r in rows.values())
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert d["publisher_original_bytes_authenticated"] is False
    assert d["remaining_grade1_sections"].startswith("111.3(b)(4)-(9)")
