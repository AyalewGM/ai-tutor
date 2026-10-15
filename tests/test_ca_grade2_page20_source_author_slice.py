"""Fail-closed CDE Grade 2 page-20 author scope evidence checks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade2_page20_source_ids_and_material_bounds():
    d = json.loads((ROOT / "ca_2013_grade2_page20_source_author_slice.v1.json").read_text())
    rows = {r["expectation_id"]: r for r in d["rows"]}
    expected = [f"2.OA.{i}" for i in range(1, 5)]
    expected += [f"2.NBT.{i}" for i in range(1, 7)]
    assert list(rows) == expected
    assert len(rows) == d["expectation_count"] == 10
    assert all(r["source_printed_page"] == 20 and
               r["source_pdf_zero_based_page_index"] == 26 for r in rows.values())
    for code, conditions in {
        "2.OA.1": ["within 100", "one- and two-step", "unknowns in all positions"],
        "2.OA.2": ["within 20", "mental strategies", "memory"],
        "2.OA.3": ["up to 20", "odd or even", "equal addends"],
        "2.OA.4": ["five rows", "five columns", "equal addends"],
        "2.NBT.1": ["three-digit", "ten tens", "100–900"],
        "2.NBT.2": ["within 1,000", "2s, 5s, 10s and 100s", "California"],
        "2.NBT.3": ["1,000", "number names", "expanded form"],
        "2.NBT.4": ["three-digit", "hundreds/tens/ones", "symbols"],
        "2.NBT.5": ["within 100", "place-value", "inverse"],
        "2.NBT.6": ["four two-digit", "place-value", "properties"],
    }.items():
        assert rows[code]["required_material_conditions"] == conditions
        assert rows[code]["author_mathematical_scope"]
        assert rows[code]["canonical_equivalence"] == "UNVERIFIED"
        assert rows[code]["assessment"] == "UNVERIFIED"
        assert rows[code]["mastery"] == "UNVERIFIED"
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"


def test_grade2_separate_california_additions_stay_separate():
    page20 = json.loads((ROOT / "ca_2013_grade2_page20_source_author_slice.v1.json").read_text())
    additions = json.loads((ROOT / "ca_2013_grade2_ca_additions_author_slice.v1.json").read_text())
    ids = {r["expectation_id"] for r in page20["rows"]}
    addition_ids = {r["expectation_id"] for r in additions["rows"]}
    assert not ids.intersection(addition_ids)
    assert "2.NBT.7.1" in addition_ids
