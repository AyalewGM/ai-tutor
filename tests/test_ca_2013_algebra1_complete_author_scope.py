"""Traditional California Algebra I 62-identifier author-source inventory checks.

Passing checks do not constitute independent official-source authentication.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
EARLY = BASE / "ca_2013_algebra1_pages64_65_source_author_slice.v1.json"
LATER = BASE / "ca_2013_algebra1_pages66_68_source_author_slice.v1.json"
HISTORIC = BASE / "national_ca_grades7_9.author_intake.v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_combined_62_id_author_scope_parity_not_independent_acceptance():
    e, l, h = (_load(p) for p in (EARLY, LATER, HISTORIC))
    rows = e["rows"] + l["rows"]
    ids = [r["expectation_id"] for r in rows]
    original_ids = [r["expectation_id"] for r in h["expectations"] if r["track"] == "ALGEBRA_I"]
    assert ids == original_ids
    assert len(ids) == len(set(ids)) == 62
    assert e["author_scoped_identifier_rows"] == 22
    assert l["author_scoped_identifier_rows"] == 40
    assert l["combined_algebra_i_authored_identifier_rows"] == 62
    assert l["remaining_algebra_i_historical_ids_unscoped"] == 0
    assert all(r["track"] == "ALGEBRA_I" for r in rows)
    assert e["course_not_grade9_automatic_equivalence"] is True
    assert l["course_not_grade9_automatic_equivalence"] is True


def test_exact_traditional_algebra1_printed_page_boundaries():
    e, l = (_load(p) for p in (EARLY, LATER))
    assert l["source_printed_pages"] == [66, 67, 68]
    assert l["source_pdf_zero_based_indices"] == [72, 73, 74]
    ids = [r["expectation_id"] for r in l["rows"]]
    pages = [r["source_printed_page"] for r in l["rows"]]
    assert (pages.count(66), pages.count(67), pages.count(68)) == (12, 11, 17)
    assert ids[:12] == [
        "A-REI.5", "A-REI.6", "A-REI.7", "A-REI.10", "A-REI.11", "A-REI.12",
        "F-IF.1", "F-IF.2", "F-IF.3", "F-IF.4", "F-IF.5", "F-IF.6",
    ]
    assert ids[12:23] == [
        "F-IF.7.a", "F-IF.7.b", "F-IF.7.e", "F-IF.8.a", "F-IF.8.b", "F-IF.9",
        "F-BF.1.a", "F-BF.1.b", "F-BF.2", "F-BF.3", "F-BF.4.a",
    ]
    assert ids[23:] == [
        "F-LE.1.a", "F-LE.1.b", "F-LE.1.c", "F-LE.2", "F-LE.3", "F-LE.5", "F-LE.6",
        "S-ID.1", "S-ID.2", "S-ID.3", "S-ID.5",
        "S-ID.6.a", "S-ID.6.b", "S-ID.6.c", "S-ID.7", "S-ID.8", "S-ID.9",
    ]
    assert all(r["source_pdf_page_index"] == r["source_printed_page"] + 6 for r in e["rows"] + l["rows"])


def test_material_scope_restrictions_remain_visible():
    d = _load(LATER)
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert "COURSE_BOUNDARY_CONFLICT_PENDING_INDEPENDENT_INTERPRETATION" in rows["F-IF.7.e"]["test_material_conditions"]
    f_if_7e = rows["F-IF.7.e"]
    assert f_if_7e["source_standard_full_scope_components"] == [
        "exponential graphs: intercepts and end behavior",
        "logarithmic graphs: intercepts and end behavior",
        "trigonometric graphs: period, midline and amplitude",
    ]
    assert set(f_if_7e["deferred_by_explicit_course_introduction"]) == {
        "logarithmic functions", "trigonometric functions",
    }
    assert f_if_7e["course_introduction_source_printed_page"] == 60
    assert f_if_7e["course_introduction_source_pdf_zero_based_index"] == 66
    assert "PENDING_INDEPENDENT_VERIFICATION" in f_if_7e["course_scope_disposition"]
    assert "exponential" in f_if_7e["algebra1_course_instructional_scope"][0]
    assert "square root and cube root" in rows["F-IF.7.b"]["test_material_conditions"]
    fbf3 = rows["F-BF.3"]
    assert "find the value of k given the graphs" in fbf3["author_mathematical_scope_summary"]
    assert "find k from given graphs" in fbf3["test_material_conditions"]
    assert fbf3["source_printed_page"] == 67
    assert fbf3["source_pdf_page_index"] == 73
    assert "F-BF.4a linear-only course note" in rows["F-BF.4.a"]["test_material_conditions"]
    assert "California addition" in rows["F-LE.6"]["test_material_conditions"]
    assert "IQR and standard deviation" in rows["S-ID.2"]["test_material_conditions"]
    assert "joint marginal conditional relative frequencies" in rows["S-ID.5"]["test_material_conditions"]
    assert "residual plot" in rows["S-ID.6.b"]["test_material_conditions"]
    assert "correlation" in rows["S-ID.9"]["test_material_conditions"]
    assert all(r["author_mathematical_scope_summary"].strip() for r in rows.values())


def test_all_algebra1_author_records_remain_review_only():
    for d in (_load(EARLY), _load(LATER)):
        assert d["independent_source_fidelity"] == "PENDING"
        assert d["activation"] == "FORBIDDEN"
        assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
        for r in d["rows"]:
            assert r["source_review_status"] == "AUTHOR_DIRECT_CDE_PDF_PAGE_CHECK_PENDING_INDEPENDENT_FIDELITY"
            assert all(r[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
