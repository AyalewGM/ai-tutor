"""California Grade 2 CDE printed pages 21-22: author scope and fail-closed checks.

A passing test establishes structural accounting only, never source-fidelity acceptance.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
NEW = BASE / "ca_2013_grade2_pages21_22_source_author_slice.v1.json"
PAGE20 = BASE / "ca_2013_grade2_page20_source_author_slice.v1.json"
CA_ADDITIONS = BASE / "ca_2013_grade2_ca_additions_author_slice.v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_pages_and_exact_14_new_ids():
    d = _load(NEW)
    expected = ["2.NBT.8", "2.NBT.9"]
    expected += [f"2.MD.{i}" for i in (1, 2, 3, 4, 5, 6, 8, 9, 10)]
    expected += [f"2.G.{i}" for i in (1, 2, 3)]
    rows = d["rows"]
    assert [r["expectation_id"] for r in rows] == expected
    assert len(set(expected)) == len(rows) == d["expectation_count"] == 14
    assert d["source_printed_pages"] == [21, 22]
    assert d["source_pdf_zero_based_page_indices"] == [27, 28]
    for r in rows:
        assert r["source_printed_page"] == (22 if r["expectation_id"].startswith("2.G.") else 21)
        assert r["source_pdf_zero_based_page_index"] == r["source_printed_page"] + 6
        assert r["author_mathematical_scope"].strip()
        assert r["required_material_conditions"]
        assert r["source_review_status"] == "AUTHOR_EDITORIAL_PENDING_INDEPENDENT_PUBLISHER_FIDELITY"


def test_grade2_27_author_ids_across_three_nonoverlapping_files():
    p, ca, later = (_load(f) for f in (PAGE20, CA_ADDITIONS, NEW))
    ids = [r["expectation_id"] for d in (p, ca, later) for r in d["rows"]]
    expected = {f"2.OA.{i}" for i in range(1, 5)}
    expected |= {f"2.NBT.{i}" for i in range(1, 10)}
    expected |= {"2.NBT.7.1"}
    expected |= {f"2.MD.{i}" for i in range(1, 11)}
    expected |= {f"2.G.{i}" for i in range(1, 4)}
    assert len(ids) == len(set(ids)) == len(expected) == 27
    assert set(ids) == expected
    assert {r["expectation_id"] for r in ca["rows"]} == {"2.NBT.7", "2.NBT.7.1", "2.MD.7"}
    assert all(r["printed_page"] == (20 if r["expectation_id"] == "2.NBT.7" else 21) for r in ca["rows"])


def test_grade2_mathematical_qualifiers_and_independence_boundaries():
    d = _load(NEW)
    rows = {r["expectation_id"]: r for r in d["rows"]}
    required = {
        "2.NBT.8": ("10 or 100", "100–900"),
        "2.NBT.9": ("explain why", "place value", "operation properties"),
        "2.MD.2": ("twice", "two length-unit sizes"),
        "2.MD.5": ("within 100", "same units", "unknown"),
        "2.MD.6": ("from zero", "within 100"),
        "2.MD.9": ("line plot", "nearest whole unit", "whole-number horizontal scale"),
        "2.MD.10": ("single-unit scale", "at most four categories", "compare"),
        "2.G.1": ("directly or visually", "not by measurement"),
        "2.G.3": ("2, 3 or 4", "halves, thirds, fourths", "may differ in shape"),
    }
    for code, terms in required.items():
        normalized = " ".join(rows[code]["required_material_conditions"]).casefold()
        for term in terms:
            assert term.casefold() in normalized, (code, term)
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    for r in d["rows"]:
        assert all(r[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
