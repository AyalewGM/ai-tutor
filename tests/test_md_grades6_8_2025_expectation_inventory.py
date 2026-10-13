import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_grades6_8_2025.expectations.v1.json"
)

def _ids(grade: int, clusters: dict) -> set:
    return {
        f"{grade}.{domain}.{cluster}.{number}"
        for domain, parts in clusters.items()
        for cluster, numbers in parts.items()
        for number in numbers
    }


EXPECTED_IDS = {
    *_ids(6, {
        "NOS": {"A": [1], "B": [2, 3, 4], "C": [5, 6, 7, 8, 9]},
        "AT": {"A": [1, 2, 3, 4], "B": [5, 6, 7], "C": [8, 9, 10], "D": [11]},
        "GR": {"A": [1, 2, 3, 4]},
        "DS": {"A": [1, 2, 3, 4], "B": [5, 6]},
    }),
    *_ids(7, {
        "NOS": {"A": [1, 2, 3]},
        "AT": {"A": [1, 2, 3, 4], "B": [5, 6], "C": [7, 8, 9]},
        "GR": {"A": [1, 2], "B": [3, 4]},
        "DS": {"A": [1, 2], "B": [3], "C": [4, 5, 6]},
    }),
    *_ids(8, {
        "NOS": {"A": [1, 2], "B": [3, 4, 5]},
        "AT": {"A": [1, 2], "B": [3, 4, 5], "C": [6, 7, 8], "D": [9, 10, 11]},
        "GR": {"A": [1, 2, 3], "B": [4, 5]},
        "DS": {"A": [1], "B": [2, 3, 4], "C": [5, 6]},
    }),
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 79
    assert len(set(identifiers)) == 79
    assert set(identifiers) == EXPECTED_IDS


def test_every_expectation_uses_2025_domain_and_matches_grade() -> None:
    rows = _manifest()["expectations"]
    domains = {"NOS", "AT", "GR", "DS"}

    for row in rows:
        grade, domain, cluster, _ = row["expectation_id"].split(".")
        assert int(grade) == row["grade"]
        assert row["grade"] in (6, 7, 8)
        assert domain == row["domain"] in domains
        assert cluster.isalpha() and len(cluster) == 1
        # Legacy 2010-column identifiers must never appear as new IDs.
        assert domain != "NS"


def test_repository_links_match_merged_seed_reconciliation() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert len(existing) == 46
    for row in rows:
        if row["expectation_id"] in existing:
            assert row["repository_existing_crosswalks"]
            assert all(
                code.startswith(("M6.", "M7.", "M8."))
                for code in row["repository_existing_crosswalks"]
            )
            assert set(row["repository_existing_crosswalks"]) == set(
                row["provisional_relations"]
            )
            assert all(
                relation
                in {
                    "COMPOSITE_SCOPE",
                    "PARTIAL_SCOPE",
                    "NARROW_SUBSCOPE",
                    "CLOSE_SCOPE_REVIEW_REQUIRED",
                    "PARTIAL_OR_EXTRA_SCOPE",
                    "CROSS_GRADE_COMPOSITE",
                }
                for relation in row["provisional_relations"].values()
            )
            assert row["classification"]["standards_mapped"] == (
                "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            )
        else:
            assert row["repository_existing_crosswalks"] == []
            assert row["provisional_relations"] == {}
            assert row["classification"]["standards_mapped"] == "NO"


def test_all_readiness_and_mastery_claims_fail_closed() -> None:
    manifest = _manifest()

    assert manifest["safety"] == {
        "activation": "FORBIDDEN",
        "mapping_review_required": True,
        "new_canonical_ids_created": False,
        "learner_mastery_mutation": False,
        "verified_coverage_claim": False,
    }
    for row in manifest["expectations"]:
        classification = row["classification"]
        assert classification["mathematically_reviewed_skill"] == (
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_MD_TARGET"
        )
        assert classification["generator_available"] == (
            "NOT_AUDITED_FOR_EXACT_EXPECTATION_AND_TARGET"
        )
        assert classification["validated_practice"] == "NO_VERIFIED_EVIDENCE"
        assert classification["assessment_ready"] == "NO_VERIFIED_EVIDENCE"
        assert classification["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_reconciliation_counts_are_internally_consistent() -> None:
    manifest = _manifest()
    reconciliation = manifest["reconciliation"]
    rows = manifest["expectations"]
    existing = sum(
        1
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    )

    assert reconciliation["official_expectation_count"] == len(rows) == 79
    assert reconciliation["repository_existing_expectation_rows"] == existing == 46
    assert reconciliation["unmapped_expectations"] == 79 - existing == 33
    assert reconciliation["seed_rows_reconciled"] == 28
    assert {r["grade"] for r in rows} == {6, 7, 8}


def test_grade_specific_official_document_versions_and_adoption_sources() -> None:
    manifest = _manifest()
    curriculum = manifest['curriculum']
    assert curriculum['adopted_date'] == '2025-07'
    assert curriculum['board_adoption_date'] == '2025-07-29'
    assert curriculum['board_adoption_source_url'] == manifest['provenance']['authoritative_landing_page']
    sources = manifest['provenance']['grade_source_documents']
    assert {grade: source['revision'] for grade, source in sources.items()} == {
        '6': 'February 2026', '7': 'July 2025', '8': 'July 2025',
    }
    assert sources['6']['companion']['revision'] == 'Version 2, June 2026'
    assert sources['7']['companion']['revision'] == 'Version 2, June 2026'
    assert sources['8']['companion']['revision'] == 'Version 1, February 2026'
    assert sources['8']['companion']['version_verification'] == 'DIRECT_MSDE_COMPANION_GUIDE_COVER_PAGE'
    for row in manifest['expectations']:
        source = sources[str(row['grade'])]
        assert row['source_locator'] == source['url']
        assert row['source_document_id'] == source['source_id']
        assert row['source_document_revision'] == source['revision']
        assert source['role'] == 'AUTHORITATIVE_STANDARD_ID_AND_SCOPE'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'


def test_source_fidelity_ledger_covers_all_2025_parent_and_lettered_rows() -> None:
    path = MANIFEST.parent / 'md_grades6_8_2025.source_fidelity_locators.v1.json'
    evidence = json.loads(path.read_text(encoding='utf-8'))
    manifest = _manifest()
    records = evidence['records']
    assert evidence['status'] == 'AUTHOR_SOURCE_LOCATORS_REVIEW_REQUIRED'
    assert evidence['completeness_status'].endswith('PENDING_INDEPENDENT_ACCEPTANCE')
    assert len(records) == len(manifest['expectations']) == 79
    assert {r['expectation_id'] for r in records} == {r['expectation_id'] for r in manifest['expectations']}
    for row, record in zip(manifest['expectations'], records, strict=True):
        assert row['expectation_id'] == record['expectation_id']
        assert row['source_page'] == record['printed_page_start']
        assert row['source_page_end'] == record['printed_page_end']
        assert row['official_subpart_identifiers'] == record['official_subpart_ids']
        assert row['source_locator'] == record['source_url']
        assert row['source_fidelity_status'] == 'AUTHOR_LOCATED_PENDING_INDEPENDENT_REVIEW'
        assert record['independent_acceptance'] == 'PENDING'
        assert record['column'] == '2025 MD Index / 2025 Standards Statement'
        assert record['printed_page_start'] >= 1
        assert record['printed_page_end'] >= record['printed_page_start']
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'


def test_official_pdf_printed_page_and_zero_based_index_are_not_conflated() -> None:
    manifest = _manifest()
    evidence = json.loads((MANIFEST.parent / 'md_grades6_8_2025.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    rows = {r['expectation_id']: r for r in manifest['expectations']}
    locators = {r['expectation_id']: r for r in evidence['records']}
    for expectation_id, pdf_index, printed in [
        ('7.NOS.A.1', 1, 1), ('7.AT.A.2', 4, 4), ('8.NOS.A.1', 1, 1),
    ]:
        assert rows[expectation_id]['pdf_page_index_zero_based'] == pdf_index
        assert rows[expectation_id]['source_page'] == printed
        assert locators[expectation_id]['pdf_page_index_zero_based'] == pdf_index
        assert locators[expectation_id]['printed_page_start'] == printed
        assert locators[expectation_id]['page_locator_evidence'] == 'OFFICIAL_MSDE_PDF_2025_STANDARDS_COLUMN_PAGE_AND_FOOTER'


def test_all_grade7_8_printed_pages_match_official_crosswalk_page_locations() -> None:
    manifest = _manifest()
    ledger = json.loads((MANIFEST.parent / 'md_grades6_8_2025.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    records = {r['expectation_id']: r for r in ledger['records']}
    pages = {
        7: {'NOS': [(1,1),(2,2),(3,3)], 'AT': [(4,4),(4,4),(5,5),(5,5),(5,5),(6,6),(6,6),(6,6),(7,7)], 'GR': [(8,8),(8,8),(9,9),(9,9)], 'DS': [(10,10),(10,10),(11,11),(11,12),(12,12),(12,12)]},
        8: {'NOS': [(1,1),(1,1),(1,1),(2,2),(2,2)], 'AT': [(3,3),(3,3),(4,4),(4,4),(4,5),(5,5),(5,6),(6,6),(6,6),(6,7),(7,7)], 'GR': [(8,8),(8,8),(8,8),(9,10),(10,10)], 'DS': [(11,11),(11,11),(11,11),(12,12),(12,12),(12,13)]},
    }
    for grade, groups in pages.items():
        for domain, expected_pages in groups.items():
            rows = [r for r in manifest['expectations'] if r['grade'] == grade and r['domain'] == domain]
            assert len(rows) == len(expected_pages)
            for row, (first, last) in zip(rows, expected_pages, strict=True):
                record = records[row['expectation_id']]
                assert (row['source_page'], row['source_page_end']) == (first, last)
                assert (record['printed_page_start'], record['printed_page_end']) == (first, last)
                assert (row['pdf_page_index_zero_based'], row['pdf_page_end_index_zero_based']) == (first, last)
                assert record['page_locator_evidence'] == 'OFFICIAL_MSDE_PDF_2025_STANDARDS_COLUMN_PAGE_AND_FOOTER'
                assert record['independent_acceptance'] == 'PENDING'


def test_bounded_mathematical_scope_evidence_preserves_reviewed_conditions() -> None:
    """A short editorial summary or subpart ID is never full coverage evidence."""
    manifest = _manifest()
    ledger = json.loads(
        (MANIFEST.parent / 'md_grades6_8_2025.source_fidelity_locators.v1.json').read_text(encoding='utf-8')
    )
    assert ledger['scope_summary_policy'] == (
        'NON_EXHAUSTIVE_DISCOVERY_ONLY_NOT_FULL_PARENT_OR_SUBPART_COVERAGE_EVIDENCE'
    )
    rows = {r['expectation_id']: r for r in manifest['expectations']}
    records = {r['expectation_id']: r for r in ledger['records']}
    required_parts = {
        '7.GR.A.2': set(),
        '8.GR.B.4': {'8.GR.B.4.a', '8.GR.B.4.b'},
        '8.NOS.B.4': {'8.NOS.B.4.a', '8.NOS.B.4.b'},
        '8.AT.B.5': {'8.AT.B.5.a', '8.AT.B.5.b', '8.AT.B.5.c', '8.AT.B.5.d'},
    }
    for expectation_id, parts in required_parts.items():
        row = rows[expectation_id]
        record = records[expectation_id]
        scope = record['bounded_mathematical_scope_evidence']
        assert set(row['official_subpart_identifiers']) == parts
        assert set(scope['subpart_requirements']) == parts
        assert scope['parent_requirements']
        assert scope['short_summary_is_exhaustive'] is False
        assert scope['scope_verification'] == 'PENDING_INDEPENDENT_SOURCE_FIDELITY'
        assert scope['canonical_equivalence'] == 'NOT_ESTABLISHED'
        assert scope['downstream_full_coverage_allowed'] is False
        assert scope['printed_page_start'] == record['printed_page_start']
        assert scope['printed_page_end'] == record['printed_page_end']
        assert record['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'

    cross_sections = ' '.join(records['7.GR.A.2']['bounded_mathematical_scope_evidence']['parent_requirements']).lower()
    assert 'volume' in cross_sections and 'surface-area' in cross_sections
    inequalities = ' '.join(records['8.GR.B.4']['bounded_mathematical_scope_evidence']['subpart_requirements']['8.GR.B.4.b']).lower()
    assert all(word in inequalities for word in ('inequalities', 'acute', 'obtuse'))
    powers = ' '.join(records['8.NOS.B.4']['bounded_mathematical_scope_evidence']['subpart_requirements']['8.NOS.B.4.b']).lower()
    assert '1 through 100' in powers and '1 through 125' in powers
    system = records['8.AT.B.5']['bounded_mathematical_scope_evidence']['subpart_requirements']
    assert 'graph' in ' '.join(system['8.AT.B.5.b']).lower()
    assert 'substitution' in ' '.join(system['8.AT.B.5.b']).lower()
    assert all(s in ' '.join(system['8.AT.B.5.c']).lower() for s in ('no solution', 'exactly one', 'infinitely many'))
    assert 'contextual' in ' '.join(system['8.AT.B.5.d']).lower()
