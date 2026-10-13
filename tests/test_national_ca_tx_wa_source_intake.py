"""Fail-closed source-intake checks; not independent standards verification."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = {
    "CA": "national_ca_grades7_9.author_intake.v1.json",
    "TX": "national_tx_grades7_9.author_intake.v1.json",
    "WA": "national_wa_2026_grades7_9.source_blocker.v1.json",
}


def _data(key):
    return json.loads((ROOT / FILES[key]).read_text(encoding="utf-8"))


def test_historical_ca_tx_rows_are_source_pending_and_not_mastery_evidence():
    for key, count in (("CA", 173), ("TX", 88)):
        data = _data(key)
        assert data["status"] == "DRAFT_INCOMPLETE_SOURCE_FIDELITY"
        assert len(data["expectations"]) == count
        assert len({(r["track"], r["expectation_id"]) for r in data["expectations"]}) == count
        for row in data["expectations"]:
            assert row["source_fidelity"].startswith("AUTHOR_REUSE_FROM_HISTORIC_AUDIT_PENDING")
            assert row["exact_mathematical_scope"] is None
            assert row["canonical_equivalence"] == "UNVERIFIED"
            assert row["assessment"] == "UNVERIFIED"
            assert row["mastery"] == "UNVERIFIED"


def test_california_grade8_irrational_candidates_do_not_imply_coverage():
    data = _data("CA")
    rows = {r["expectation_id"]: r for r in data["expectations"] if r["track"] == "GRADE_8"}
    for code in ("8.NS.1", "8.NS.2"):
        assert rows[code]["candidate_canonical"] == "M8.NS.RAD"
        assert rows[code]["canonical_equivalence"] == "UNVERIFIED"


def test_texas_regular_and_advanced_are_not_conflated():
    data = _data("TX")
    assert {r["track"] for r in data["expectations"]} == {"REGULAR_GRADE_7", "REGULAR_GRADE_8"}
    assert {p["section"] for p in data["separate_courses"]} == {"111.39", "111.29", "111.30", "111.31"}
    for row in data["expectations"]:
        assert row["exact_mathematical_scope"] is None


def test_wa_2026_missing_originals_fail_closed():
    data = _data("WA")
    assert data["status"] == "BLOCKED_AUTHORITATIVE_2026_DOCUMENT_BYTES_NOT_RETRIEVED"
    assert data["expectations"] == []
    assert data["required"] == "2027-2028"
    assert "2011" in data["crosswalk"]


def test_wa_high_school_tracks_are_separate_from_legacy_2011_crosswalk():
    data = _data("WA")
    tracks = data["high_school_arrangements"]
    assert tracks["not_grade9_equivalences"] is True
    assert set(tracks["tracks"]) == {
        "Integrated 1", "Integrated 2", "Integrated 3", "Geometry",
        "Algebra 1", "Algebra 2", "Credit 3",
    }
    acquisition = data["source_acquisition"]
    assert acquisition["initial_adoption_2025_role"].startswith("HISTORICAL_TRANSITION_RESEARCH_ONLY")
    assert acquisition["official_2026_spreadsheet"] == "UNRESOLVED_DIRECT_URL"
    assert acquisition["no_2011_2026_crosswalk_rows_invented"] is True


def test_texas_instructional_research_cannot_promote_irrational_gap_to_coverage():
    data = _data("TX")
    research = data["legacy_gap_reuse_research"]
    assert research["role"] == "TEA_INSTRUCTIONAL_MATERIALS_REVIEW_CONTEXT_NOT_AUTHORITATIVE_TEK_STANDARD_TEXT"
    rows = {r["expectation_id"]: r for r in data["expectations"] if r["track"] == "REGULAR_GRADE_8"}
    for code in ("8.2A", "8.2B", "8.2D"):
        assert rows[code]["candidate_canonical"] == "M8.NS.RAD"
        assert rows[code]["canonical_equivalence"] == "UNVERIFIED"
        assert rows[code]["mastery"] == "UNVERIFIED"
    assert data["authority_section_audit"]["status"].endswith("NOT_EXPECTATION_TEXT_ACCEPTED")


def test_texas_algebra1_official_lettered_identifier_intake_remains_unaccepted():
    data = _data("TX")
    a1 = data["algebra1_official_identifier_inventory"]
    assert a1["section"] == "111.39"
    assert a1["parent_groups"] == 12
    assert a1["lettered_expectations"] == 56
    rows = a1["expectations"]
    assert len(rows) == len({r["expectation_id"] for r in rows}) == 56
    assert {r["source_parent_group"] for r in rows} == {str(n) for n in range(1, 13)}
    for row in rows:
        assert row["official_reference"].startswith("19 TAC §111.39(c)")
        assert row["source_fidelity"].endswith("SCOPE_PENDING_EXACT_LETTERED_REVIEW")
        assert row["official_scope_editorial"]
        assert row["scope_author_status"] == "EDITORIAL_PARAPHRASE_OF_TEA_2015_PDF_PENDING_INDEPENDENT_SCOPE_AND_NOTATION_CHECK"
        assert row["scope_requires_parent_context"] is True
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["assessment"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"


def test_california_irrational_source_scope_does_not_imply_reuse_acceptance():
    data = _data("CA")
    evidence = data["official_pdf_source_evidence"]
    assert evidence["grade8_source_pdf_indices"] == [60, 62]
    rows = {r["expectation_id"]: r for r in data["expectations"] if r["track"] == "GRADE_8"}
    for code in ("8.NS.1", "8.NS.2"):
        row = rows[code]
        assert row["source_pdf_page_index"] == 60
        assert row["scope_audit_status"].endswith("PENDING_INDEPENDENT_ACCEPTANCE")
        assert row["candidate_canonical"] == "M8.NS.RAD"
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"


def test_texas_algebra1_critical_source_scope_distinctions():
    data = _data("TX")
    rows = {r["expectation_id"]: r for r in data["algebra1_official_identifier_inventory"]["expectations"]}
    assert len(rows) == 56
    assert "continuous/discrete" in rows["A1.2A"]["official_scope_editorial"]
    assert "zero versus undefined slope" in rows["A1.2G"]["official_scope_editorial"]
    assert "causation" in rows["A1.4B"]["official_scope_editorial"]
    assert "completing square" in rows["A1.8A"]["official_scope_editorial"]
    assert "rational exponent" in rows["A1.11B"]["official_scope_editorial"]
    assert "literal equations" in rows["A1.12E"]["official_scope_editorial"]
    for row in rows.values():
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"


def test_texas_algebra1_per_letter_pages_are_not_parent_stem_pages():
    data = _data("TX")
    inventory = data["algebra1_official_identifier_inventory"]
    rows = inventory["expectations"]
    assert len(rows) == 56
    parent_spans = {int(k): v for k, v in inventory["source_locator_audit"]["parent_stem_pages"].items()}
    assert parent_spans[2] == [2, 3]
    assert parent_spans[6] == [3, 4]
    assert parent_spans[10] == [4, 5]
    expected = {}
    for row in rows:
        parent = int(row["source_parent_group"])
        letter = row["expectation_id"][-1]
        span = list(parent_spans[parent])
        if parent == 2:
            span = [2, 2] if letter <= "G" else [3, 3]
        elif parent == 6:
            span = [4, 4]
        elif parent == 10:
            span = [4, 4] if letter == "A" else [4, 5] if letter == "B" else [5, 5]
        assert row["printed_page_span"] == span
        assert row["parent_stem_printed_page_span"] == parent_spans[parent]
        assert row["source_pdf_zero_based_index_span"] == [p - 1 for p in span]
        assert row["canonical_equivalence"] == "UNVERIFIED"
        expected[row["expectation_id"]] = span
    assert expected["A1.2H"] == [3, 3]
    assert expected["A1.6B"] == [4, 4]
    assert expected["A1.10B"] == [4, 5]


def test_texas_2025_advanced_final_rule_is_not_proposal_or_regular_algebra1():
    data = _data("TX")
    final = data["advanced_2025_final_adoption_evidence"]
    assert final["publication_date"] == "2025-06-27"
    assert set(final["sections"]) == {"111.29", "111.30", "111.31"}
    changes = {x["section"]: x for x in final["adoption_differences"]}
    assert changes["111.29"]["final_adoption"].startswith("ADOPTED_WITHOUT_CHANGE")
    assert changes["111.30"]["expectation"] == "111.30(c)(8)(C)"
    assert changes["111.31"]["graduation_credit"].startswith("One credit")
    assert changes["111.31"]["prerequisite"] == (
        "Middle School Advanced Mathematics, Grade 7 or Mathematics, Grade 8"
    )
    assert all(x["expectations_extracted"] is False for x in changes.values())
    assert final["relationship_to_regular_algebra1"].startswith("NOT_ASSUMED_IDENTICAL")
    assert final["review_status"].endswith("NOT_FULL_STUDENT_EXPECTATION_SOURCE_FIDELITY")
