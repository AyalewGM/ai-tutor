"""Author-only California Grade 2 inventory parity across three source slices."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = (
    "ca_2013_grade2_page20_source_author_slice.v1.json",
    "ca_2013_grade2_ca_additions_author_slice.v1.json",
    "ca_2013_grade2_pages21_22_source_author_slice.v1.json",
)


def test_grade2_27_distinct_parent_ids_and_publisher_locators():
    docs = [json.loads((ROOT / name).read_text()) for name in FILES]
    assert [len(doc["rows"]) for doc in docs] == [10, 3, 14]
    seen = set()
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        for row in doc["rows"]:
            identifier = row["expectation_id"]
            assert identifier.startswith("2.")
            assert identifier not in seen
            seen.add(identifier)
            printed = row.get("source_printed_page", row.get("printed_page"))
            index = row.get("source_pdf_zero_based_page_index", row.get("pdf_page_index"))
            assert printed in (20, 21, 22)
            assert index == printed + 6
            assert row["canonical_equivalence"] == "UNVERIFIED"
    assert len(seen) == 27
    nbt1 = next(r for r in docs[0]["rows"] if r["expectation_id"] == "2.NBT.1")
    assert nbt1["required_lettered_subparts"] == ["a", "b"]
