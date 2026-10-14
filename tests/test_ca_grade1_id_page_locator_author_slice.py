"""California Grade 1 author identifier/page slice must not imply accepted scope."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_ca_grade1_identifier_page_slice_is_fail_closed():
    source = json.loads((ROOT / "ca_2013_grade1_id_page_locator_author_slice.v1.json").read_text())
    rows = source["expectations"]
    assert len(rows) == len({r["expectation_id"] for r in rows}) == 21
    assert {r["source_printed_page"] for r in rows} == {16, 17}
    assert source["full_author_scope_audit_imported"] is False
    assert source["independent_source_fidelity"] == "PENDING"
    assert source["official_page_byte_authentication"] == "PENDING"
    assert all(source[field] == "UNVERIFIED" for field in
               ("canonical_equivalence", "assessment", "mastery"))
