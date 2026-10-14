"""Fail-closed tests for 28 provisional California Grade 8 source-scope records."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
AUTHOR = BASE / "ca_2013_grade8_28_source_author_slice.v1.json"
HISTORIC = BASE / "national_ca_grades7_9.author_intake.v1.json"


def test_grade8_author_inventory_parity_with_historic_intake():
    author = json.loads(AUTHOR.read_text(encoding="utf-8"))
    historic = json.loads(HISTORIC.read_text(encoding="utf-8"))
    rows = author["rows"]
    ids = [r["expectation_id"] for r in rows]
    historic_ids = [r["expectation_id"] for r in historic["expectations"] if r["track"] == "GRADE_8"]
    assert len(ids) == len(set(ids)) == 28
    assert ids == historic_ids
    assert author["author_scoped_parent_expectation_count"] == 28
    assert author["source_printed_page_span"] == [54, 56]
    assert author["source_pdf_page_index_span"] == [60, 62]
    assert all(r["source_pdf_page_index"] == r["source_printed_page"] + 6 for r in rows)
    expected_pages = {
        **{code: 54 for code in ("8.NS.1", "8.NS.2", *(f"8.EE.{i}" for i in range(1, 8)))},
        **{code: 55 for code in ("8.EE.8", *(f"8.F.{i}" for i in range(1, 6)), "8.G.1")},
        **{code: 56 for code in (*(f"8.G.{i}" for i in range(2, 10)), *(f"8.SP.{i}" for i in range(1, 5)))},
    }
    assert {r["expectation_id"]: r["source_printed_page"] for r in rows} == expected_pages
    assert all(r["source_printed_page_span"] == [r["source_printed_page"]] for r in rows)


def test_grade8_material_qualifiers_and_lettered_subparts():
    author = json.loads(AUTHOR.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in author["rows"]}
    expected = {"8.EE.7": ["a", "b"], "8.EE.8": ["a", "b", "c"], "8.G.1": ["a", "b", "c"]}
    actual = {code: r["required_lettered_subparts"] for code, r in rows.items() if r["required_lettered_subparts"]}
    assert actual == expected
    assert "eventual repetition" in rows["8.NS.1"]["test_material_conditions"]
    assert "positive rational p" in rows["8.EE.2"]["test_material_conditions"]
    assert "function notation not required" in rows["8.F.1"]["test_material_conditions"]
    assert "converse" in rows["8.G.6"]["test_material_conditions"]
    assert "row or column relative frequency" in rows["8.SP.4"]["test_material_conditions"]


def test_grade8_source_acceptance_remains_fail_closed():
    author = json.loads(AUTHOR.read_text(encoding="utf-8"))
    assert author["status"] == "AUTHOR_GRADE8_SOURCE_SCOPE_DRAFT_NOT_ACCEPTED"
    assert author["independent_source_fidelity"] == "PENDING"
    assert author["activation"] == "FORBIDDEN"
    assert all(author[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    assert all(r["source_review_status"] == "AUTHOR_DIRECT_CDE_PDF_PAGE_CHECK_PENDING_INDEPENDENT_FIDELITY" for r in author["rows"])
    assert all(r["author_mathematical_scope_summary"].strip() for r in author["rows"])
    assert all(r["test_material_conditions"] for r in author["rows"])
    assert all(all(r[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery")) for r in author["rows"])
