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
    assert data["status"] == "AUTHOR_WORKBOOK_EXTRACTION_STAGED_PUBLISHER_AUTHENTICATION_AND_INDEPENDENT_REVIEW_PENDING"
    assert data["expectations"] == []  # source extraction is staged separately, not accepted coverage
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
    assert acquisition["official_2026_spreadsheet"] == "UPLOADED_FILE_HASH_RECORDED_PUBLISHER_URL_NOT_VERIFIED"
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


def test_texas_advanced_2025_final_adoption_slice_is_bounded_and_distinct():
    data = _data("TX")
    adopted = data["advanced_2025_final_adoption_evidence"]
    slice_ = adopted["verified_final_rule_scope_slice"]
    assert slice_["effective_date"] == "2025-07-06"
    assert slice_["school_year_implementation"] == "2025-2026"
    assert slice_["completeness"] == "BOUNDED_14_OF_130_ENUMERATED_STUDENT_EXPECTATIONS_NOT_A_COMPLETE_SCOPE_INVENTORY"
    rows = slice_["rows"]
    assert len(rows) == len({r["expectation_id"] for r in rows}) == 14
    assert sum(r["track"] == "ADVANCED_GRADE_7" for r in rows) == 8
    assert sum(r["track"] == "ADVANCED_GRADE_8_ALGEBRA_I" for r in rows) == 6
    ids = {r["expectation_id"] for r in rows}
    assert "111.30(c)(8)(C)" in ids
    assert "111.30(c)(13)(D)" in ids
    assert "111.31(d)(12)(F)" in ids
    assert adopted["critical_distinction_vs_regular_algebra1"]["status"].startswith("AUTHOR_SOURCE_STRUCTURE_DIFFERENCE")
    for row in rows:
        assert row["source_fidelity"].endswith("PENDING_INDEPENDENT_PUBLISHER_CHECK")
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["assessment"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"


def test_texas_advanced_2025_complete_author_identifier_enumeration_is_fail_closed():
    data = _data("TX")
    inventory = data["advanced_2025_final_adoption_evidence"]["advanced_course_expectation_identifier_inventory"]
    rows = inventory["expectations"]
    assert len(rows) == 130
    assert len({r["expectation_id"] for r in rows}) == 130
    assert inventory["count_grade7"] == 67
    assert inventory["count_grade8_advanced_algebra1"] == 63
    assert inventory["complete_scope_rows_independently_accepted"] == 0
    assert sum(r["editorial_mathematical_scope"] is not None for r in rows) == 130
    assert sum(r["editorial_mathematical_scope"] is None for r in rows) == 0
    grade7 = [r for r in rows if r["track"] == "ADVANCED_GRADE_7"]
    grade8 = [r for r in rows if r["track"] == "ADVANCED_GRADE_8_ALGEBRA_I"]
    assert len(grade7) == 67
    assert len(grade8) == 63
    assert [r["expectation_id"] for r in grade7 if r["lettered_subpart"] is None] == ["111.30(c)(9)"]
    assert all(r["lettered_subpart"] is not None for r in grade8)
    assert "111.30(c)(8)(C)" in {r["expectation_id"] for r in grade7}
    assert "111.31(d)(12)(F)" in {r["expectation_id"] for r in grade8}
    for r in rows:
        assert r["source_fidelity"].endswith("PENDING_INDEPENDENT_PUBLISHER_TEXT_AND_SUBPART_REVIEW")
        assert r["canonical_equivalence"] == "UNVERIFIED"
        assert r["generator"] == "UNVERIFIED"
        assert r["assessment"] == "UNVERIFIED"
        assert r["mastery"] == "UNVERIFIED"


def test_texas_advanced_parent_stems_and_scope_gap_accounting():
    data = _data("TX")
    inv = data["advanced_2025_final_adoption_evidence"]["advanced_course_expectation_identifier_inventory"]
    ledger = inv["parent_stem_review_ledger"]
    assert len(ledger) == 26
    assert len({r["source_id"] for r in ledger}) == 26
    assert sum(r["subpart_count"] for r in ledger) == 130
    assert inv["scope_gap_accounting"]["total_expectations"] == 130
    assert inv["scope_gap_accounting"]["with_editorial_scope"] == 130
    assert inv["scope_gap_accounting"]["without_editorial_scope"] == 0
    assert inv["scope_gap_accounting"]["independently_accepted_source_scopes"] == 0
    assert inv["scope_gap_accounting"]["canonical_equivalences_accepted"] == 0
    for r in ledger:
        assert r["scope_status"].startswith("EDITORIAL_PARENT_TOPIC_PENDING_INDEPENDENT")


def test_three_state_completion_matrix_stays_fail_closed():
    matrix = json.loads((ROOT / 'national_ca_tx_wa_completion_matrix.v1.json').read_text())
    assert matrix['status'] == 'INCOMPLETE_FAIL_CLOSED'
    assert matrix['acceptance_contract']['all_three_complete'] is False
    assert matrix['acceptance_contract']['runtime_activation'] == 'FORBIDDEN'
    assert set(matrix['states']) == {'CA', 'TX', 'WA'}
    ca, tx, wa = (_data(k) for k in ('CA', 'TX', 'WA'))
    assert sum(matrix['states']['CA']['historic_rows_by_track'].values()) == len(ca['expectations']) == 173
    assert sum(matrix['states']['TX']['historic_regular_rows_by_track'].values()) == len(tx['expectations']) == 88
    advanced = tx['advanced_2025_final_adoption_evidence']['advanced_course_expectation_identifier_inventory']
    assert matrix['states']['TX']['advanced_111_30_111_31_author_identifier_rows'] == len(advanced['expectations']) == 130
    assert matrix['states']['TX']['advanced_remaining_unscoped_rows'] == sum(
        r['editorial_mathematical_scope'] is None for r in advanced['expectations']
    ) == 0
    assert matrix['states']['WA']['verified_2026_expectation_rows'] == len(wa['expectations']) == 0
    assert matrix['states']['WA']['official_final_workbook_bytes_obtained'] is False
    assert matrix['states']['WA']['uploaded_workbook_source_extraction']['repository_expectation_import'] == (
        'AUTHOR_EXTRACTION_STAGED_IN_REPOSITORY_NOT_INDEPENDENTLY_VERIFIED'
    )
    for state in matrix['states'].values():
        assert state['grade9_course_equivalence'] == 'NOT_ASSUMED'


def test_wa_uploaded_2026_v3_1_source_provenance_is_not_accepted_coverage():
    data = _data("WA")
    uploaded = data["uploaded_final_adoption_workbook"]
    assert uploaded["workbook_label"] == "August 2026 | v3.1"
    assert len(uploaded["sha256"]) == 64
    assert uploaded["k8_rows"] == 264
    assert uploaded["high_school_course_rows"] == 464
    assert uploaded["crosswalk_rows"] == 425
    assert uploaded["publisher_hash_independently_verified"] is False
    assert uploaded["course_rows_not_unique_skills"] is True
    assert uploaded["scope_acceptance"] == "PENDING_INDEPENDENT_SOURCE_REVIEW"
    assert data["expectations"] == []


def test_wa_2026_null_priority_and_course_scope_cells_remain_distinct():
    ledger = json.loads(
        (ROOT / 'wa_2026_v3_1_course_scope_cell_audit.v1.json').read_text(encoding='utf-8')
    )
    extraction = json.loads(
        (ROOT / 'wa_2026_v3_1_source_extraction.json').read_text(encoding='utf-8')
    )
    assert ledger['priority_exception']['code'] == 'M.1.SR.G.2'
    assert ledger['priority_exception']['cell'] == 'F53'
    assert ledger['priority_exception']['source_value'] is None
    assert next(x for x in extraction['k8'] if x['code'] == 'M.1.SR.G.2')['priority'] is None
    variants = ledger['course_scope_variants']
    assert len(variants) == ledger['summary']['variant_codes'] == 22
    assert sum(len(v['scope_cells']) for v in variants) == ledger['summary']['course_placements'] == 116
    assert len({v['code'] for v in variants}) == 22
    grouped = {}
    for row in extraction['high_school_course_rows']:
        grouped.setdefault(row['code'], []).append(row)
    for variant in variants:
        rows = grouped[variant['code']]
        assert len(rows) == len(variant['scope_cells'])
        assert len({r['scope'] for r in rows}) == variant['distinct_source_scope_texts']
        assert variant['extraction_matches_original_cells'] is True
        assert variant['independent_source_acceptance'] == 'PENDING'
    assert ledger['publisher_byte_match'] == 'NOT_INDEPENDENTLY_VERIFIED'
    assert ledger['activation'] == 'FORBIDDEN'


def test_controlling_ca_tx_sources_preserve_version_and_course_boundaries():
    source = json.loads(
        (ROOT / "ca_tx_controlling_source_versions.v1.json").read_text(encoding="utf-8")
    )
    assert source["status"].endswith("NOT_FULL_SCOPE_ACCEPTANCE")
    assert "April 2014" in source["california"]["controlling_standard"]
    assert source["california"]["historical_intake_tracks"] == [
        "GRADE_7", "GRADE_8", "ALGEBRA_I", "MATHEMATICS_I"
    ]
    texas = source["texas"]
    assert texas["effective_date"] == "2025-07-06"
    assert texas["advanced_grade6"]["status"].startswith("ADOPTED_UNCHANGED")
    assert texas["advanced_grade7"]["critical_requirement"] == "111.30(c)(8)(C)"
    assert texas["advanced_grade8_algebra1"]["course_distinct_from"].startswith("111.39")
    assert texas["acceptance"].startswith("ALL_130_ADVANCED_SCOPE_ROWS_PENDING")
    assert source["acceptance"]["activation"] == "FORBIDDEN"
