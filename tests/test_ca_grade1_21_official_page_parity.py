"""California Grade 1 author-source inventory parity; no independent acceptance."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = (
    "ca_2013_grade1_bounded_scope_author_slice.v1.json",
    "ca_2013_grade1_remaining16_scope_author_slice.v1.json",
)


def test_grade1_all_21_unique_parent_standards_and_locators():
    documents = [json.loads((ROOT / filename).read_text()) for filename in FILES]
    rows = [r for d in documents for r in d["rows"]]
    ids = [r["expectation_id"] for r in rows]
    expected = (
        [f"1.OA.{i}" for i in range(1, 9)]
        + [f"1.NBT.{i}" for i in range(1, 7)]
        + [f"1.MD.{i}" for i in range(1, 5)]
        + [f"1.G.{i}" for i in range(1, 4)]
    )
    assert len(ids) == len(set(ids)) == 21
    assert set(ids) == set(expected)
    for d in documents:
        assert d["independent_source_fidelity"] == "PENDING"
        assert d["activation"] == "FORBIDDEN"
    for row in rows:
        assert row["pdf_page_index"] == row["printed_page"] + 6
        assert row["printed_page"] in (16, 17)
    nbt2 = next(row for row in rows if row["expectation_id"] == "1.NBT.2")
    assert nbt2["required_subparts"] == ["a", "b", "c"]
