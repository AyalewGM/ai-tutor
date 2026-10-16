"""California traditional Algebra I (not integrated Math I) source audit guardrails.

These tests validate author evidence consistency, NOT CDE source acceptance.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
AUTHOR = BASE / "ca_2013_algebra1_pages64_65_source_author_slice.v1.json"
HISTORIC = BASE / "national_ca_grades7_9.author_intake.v1.json"

EXPECTED_IDS = (
    "N-RN.1", "N-RN.2", "N-RN.3",
    "N-Q.1", "N-Q.2", "N-Q.3",
    "A-SSE.1.a", "A-SSE.1.b", "A-SSE.2",
    "A-SSE.3.a", "A-SSE.3.b", "A-SSE.3.c",
    "A-APR.1", "A-CED.1", "A-CED.2", "A-CED.3", "A-CED.4",
    "A-REI.1", "A-REI.3", "A-REI.3.1", "A-REI.4.a", "A-REI.4.b",
)


def _load():
    return json.loads(AUTHOR.read_text(encoding="utf-8"))


def test_traditional_algebra1_identifier_and_historic_order_parity():
    d = _load()
    historic = json.loads(HISTORIC.read_text(encoding="utf-8"))
    historic_ids = [
        r["expectation_id"] for r in historic["expectations"]
        if r["track"] == "ALGEBRA_I"
    ]
    ids = [r["expectation_id"] for r in d["rows"]]
    assert tuple(ids) == EXPECTED_IDS
    assert ids == historic_ids[:22]
    assert len(ids) == len(set(ids)) == d["author_scoped_identifier_rows"] == 22
    assert len(historic_ids) == d["expected_total_historical_algebra_i_rows"] == 62
    assert d["remaining_algebra_i_historical_ids_unscoped"] == 40
    assert all(r["track"] == "ALGEBRA_I" for r in d["rows"])
    assert d["course_not_grade9_automatic_equivalence"] is True


def test_author_page_locators_and_course_boundaries():
    d = _load()
    pages = {r["expectation_id"]: r["source_printed_page"] for r in d["rows"]}
    assert set(pages.values()) == {64, 65}
    assert all(pages[id_] == 64 for id_ in EXPECTED_IDS[:11])
    assert all(pages[id_] == 65 for id_ in EXPECTED_IDS[11:])
    assert d["source_pdf_zero_based_indices"] == [70, 71]
    assert d["course_intro_pdf_index"] == 66
    assert all(r["source_pdf_page_index"] == r["source_printed_page"] + 6 for r in d["rows"])
    assert all(r["source_printed_page_span"] == [r["source_printed_page"]] for r in d["rows"])


def test_california_additions_and_mathematically_material_clauses():
    d = _load()
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert "nonzero rational multiplier" in rows["N-RN.3"]["test_material_conditions"]
    assert "annual-to-monthly rate" in rows["A-SSE.3.c"]["test_material_conditions"]
    assert "linear and quadratic" in rows["A-APR.1"]["test_material_conditions"]
    assert "California-added rational and exponential clauses" in rows["A-CED.1"]["test_material_conditions"]
    assert "linear-only course limitation" in rows["A-CED.3"]["test_material_conditions"]
    assert "California-added standard" in rows["A-REI.3.1"]["test_material_conditions"]
    assert "derive quadratic formula" in rows["A-REI.4.a"]["test_material_conditions"]
    assert "complex roots a ± bi" in rows["A-REI.4.b"]["test_material_conditions"]
    assert all(r["author_mathematical_scope_summary"].strip() for r in rows.values())
    assert all(r["test_material_conditions"] for r in rows.values())
    assert not any(id_ in rows for id_ in ("A-SSE.1", "A-SSE.3", "A-REI.4"))


def test_acceptance_is_blocked_in_every_author_row():
    d = _load()
    assert d["status"] == "AUTHOR_ALGEBRA_I_PAGES64_65_DRAFT_NOT_ACCEPTED"
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    for r in d["rows"]:
        assert r["source_review_status"] == "AUTHOR_DIRECT_CDE_PDF_PAGE_CHECK_PENDING_INDEPENDENT_FIDELITY"
        assert all(r[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
