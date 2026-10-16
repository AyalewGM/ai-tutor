"""Structural guards for TEA regular Grade 6 provisional source notes."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = (
    "tx_regular_grade6_proportionality_4a_4d_author.v1.json",
    "tx_regular_grade6_proportionality_4e_5c_author.v1.json",
)


def test_regular_grade6_proportionality_ids_and_fail_closed_status():
    docs = [json.loads((BASE / name).read_text()) for name in FILES]
    ids = [row["id"] for doc in docs for row in doc["rows"]]
    expected = [f"111.26(b)(4)({x})" for x in "ABCDEFGH"]
    expected += [f"111.26(b)(5)({x})" for x in "ABC"]
    assert ids == expected
    assert len(ids) == len(set(ids)) == 11
    for doc in docs:
        assert doc["track"] == "REGULAR_GRADE_6"
        assert doc["source_pdf_page_index"] == 2
        assert doc["source_pdf_printed_page"] == 3
        assert doc["publisher_original_bytes_authenticated"] is False
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        assert all(doc[k] == "UNVERIFIED" for k in
                   ("canonical_mapping", "assessment", "mastery"))
