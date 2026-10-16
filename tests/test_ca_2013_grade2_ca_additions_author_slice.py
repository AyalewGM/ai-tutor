import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade2_ca_additions_author_slice.v1.json"


def test_california_grade2_additions_distinct_and_source_scoped():
    d = json.loads(P.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert len(rows) == len(d["rows"]) == 3
    assert set(rows) == {"2.NBT.7", "2.NBT.7.1", "2.MD.7"}
    assert [(r["printed_page"], r["pdf_page_index"]) for r in d["rows"]] == [
        (20, 26), (21, 27), (21, 27)
    ]
    assert rows["2.NBT.7.1"]["ca_addition_kind"] == "SEPARATE_CA_REQUIREMENT"
    assert rows["2.MD.7"]["ca_addition_kind"] == "CA_CLAUSE_WITHIN_PARENT"
    assert "2.MD.7.CA" not in rows
    assert "reasonable estimates" in rows["2.NBT.7.1"]["author_scope"]
    assert all(x in rows["2.MD.7"]["author_scope"] for x in ("five minutes", "a.m.", "p.m.", "weeks per year"))
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[x] == "UNVERIFIED" for x in ("canonical_mapping", "assessment", "mastery"))
    assert all(r["source_fidelity"] == "PENDING" for r in d["rows"])
