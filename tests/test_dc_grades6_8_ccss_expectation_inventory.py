import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "dc_grades6_8_ccss.expectations.v1.json"
)


def _ids(grade: int, domains: dict) -> set:
    return {
        f"{grade}.{domain}.{cluster}.{number}"
        for domain, clusters in domains.items()
        for cluster, numbers in clusters.items()
        for number in numbers
    }


EXPECTED_IDS = {
    *_ids(6, {
        "RP": {"A": [1, 2, 3]},
        "NS": {"A": [1], "B": [2, 3, 4], "C": [5, 6, 7, 8]},
        "EE": {"A": [1, 2, 3, 4], "B": [5, 6, 7, 8], "C": [9]},
        "G": {"A": [1, 2, 3, 4]},
        "SP": {"A": [1, 2, 3], "B": [4, 5]},
    }),
    *_ids(7, {
        "RP": {"A": [1, 2, 3]},
        "NS": {"A": [1, 2, 3]},
        "EE": {"A": [1, 2], "B": [3, 4]},
        "G": {"A": [1, 2, 3], "B": [4, 5, 6]},
        "SP": {"A": [1, 2], "B": [3, 4], "C": [5, 6, 7, 8]},
    }),
    *_ids(8, {
        "NS": {"A": [1, 2]},
        "EE": {"A": [1, 2, 3, 4], "B": [5, 6], "C": [7, 8]},
        "F": {"A": [1, 2, 3], "B": [4, 5]},
        "G": {"A": [1, 2, 3, 4, 5], "B": [6, 7, 8], "C": [9]},
        "SP": {"A": [1, 2, 3, 4]},
    }),
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 81
    assert len(set(identifiers)) == 81
    assert set(identifiers) == EXPECTED_IDS


def test_every_expectation_uses_ccss_domain_and_matches_grade() -> None:
    rows = _manifest()["expectations"]
    domains = {"RP", "NS", "EE", "G", "SP", "F"}

    for row in rows:
        grade, domain, cluster, _ = row["expectation_id"].split(".")
        assert int(grade) == row["grade"]
        assert row["grade"] in (6, 7, 8)
        assert domain == row["domain"] in domains
        assert cluster == row["cluster"]


def test_repository_existing_rows_are_narrow_and_unverified() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert len(existing) == 30
    for row in rows:
        if row["expectation_id"] in {"8.NS.A.2", "8.SP.A.3"}:
            assert row["repository_existing_crosswalks"] == []
            expected_candidates = {
                "8.NS.A.2": ["M8.NS.RAD"],
                "8.SP.A.3": ["M8.SP.STAT", "MATH.DATA.LINEFIT.SLOPE"],
            }
            assert row["repository_candidate_crosswalks"] == expected_candidates[row["expectation_id"]]
            assert row["classification"]["standards_mapped"] == "NO"
            assert "no accepted crosswalk" in row[
                "repository_existing_crosswalks_semantics"
            ].lower()
        elif row["expectation_id"] in existing:
            assert row["repository_existing_crosswalks"]
            assert all(
                code.startswith(("DC6.", "DC7."))
                for code in row["repository_existing_crosswalks"]
            )
            assert row["classification"]["standards_mapped"] == (
                "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            )
        else:
            assert row["repository_existing_crosswalks"] == []
            assert row["classification"]["standards_mapped"] == "NO"
            assert row["proposed_mapping_status"] == (
                "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
            )


def test_grade8_repository_candidates_remain_unaccepted() -> None:
    rows = _manifest()["expectations"]
    grade8 = [row for row in rows if row["grade"] == 8]
    existing = [
        row
        for row in grade8
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    ]

    assert len(grade8) == 28
    assert [row["expectation_id"] for row in existing] == ["8.NS.A.2", "8.SP.A.3"]
    assert existing[0]["classification"]["standards_mapped"] == "NO"
    assert existing[0]["repository_existing_crosswalks"] == []
    assert all(
        row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        for row in grade8
        if row["expectation_id"] not in {"8.NS.A.2", "8.SP.A.3"}
    )
    # No geometry seed exists for DC at any grade.
    assert all(
        row["repository_existing_crosswalks"] == []
        for row in rows
        if row["domain"] == "G"
    )


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
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_DC_TARGET"
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

    assert reconciliation["official_expectation_count"] == len(rows) == 81
    assert reconciliation["repository_existing_expectation_rows"] == existing == 30
    assert reconciliation["unmapped_expectations"] == 81 - existing == 51
    assert reconciliation["existing_seed_rows_by_grade"] == {
        "6": 5,
        "7": 5,
        "8": 2,
    }


def test_dc_standards_provenance_is_reproducible_and_separate_from_inventory_date() -> None:
    manifest = _manifest()
    curriculum = manifest['curriculum']
    provenance = manifest['provenance']
    assert curriculum['course_code'] == 'DC_CCSS_MATH_GRADES_6_8'
    assert curriculum['standards_version'] == 'CCSS-2010 (current DC adoption)'
    assert curriculum['implementation_school_year'] == '2014-2015'
    assert curriculum['implementation_milestone'] == 'FULL_IMPLEMENTATION_OF_2010_CCSS'
    assert provenance['inventory_as_of'] == provenance['checked_date'] == '2026-10-12'
    assert provenance['adoption_history_authority_url'] == 'https://osse.dc.gov/page/common-core-state-standards-mathematics'
    assert all(row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED' for row in manifest['expectations'])


def test_dc_2023_review_preserves_grade8_geometry_volume_standard() -> None:
    manifest = _manifest()
    row = next(r for r in manifest['expectations'] if r['expectation_id'] == '8.G.C.9')
    assert row['source_locator'] == (
        'https://corestandards.org/wp-content/uploads/2023/09/'
        'ADA-Compliant-Math-Standards.pdf'
    )
    assert row['source_publication_version'] == '2010'
    assert row['source_printed_page'] == 56
    assert row['official_subpart_identifiers'] == []
    scope = row['scope_summary'].lower()
    assert 'know the formulas' in scope
    assert 'cones, cylinders, and spheres' in scope
    assert 'real-world and mathematical problems' in scope
    assert row['classification']['standards_mapped'] == 'NO'
    assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
    boundary = row['mapping_evidence_boundary']
    assert boundary['status'] == 'NO_COVERAGE_CLAIM'
    assert boundary['missing_mathematical_content_inferred'] is False
    assert boundary['coverage_credit'] is False
    assert boundary['mapping_activation'] is False
    assert boundary['canonical_correspondence'] == 'NOT_ESTABLISHED'
    assert len([r for r in manifest['expectations'] if r['grade'] == 8 and r['domain'] == 'G']) == 9


def test_dc_source_fidelity_ledger_is_total_and_fail_closed() -> None:
    evidence = json.loads((MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    manifest = _manifest()
    assert evidence['status'] == 'AUTHOR_SOURCE_LOCATORS_REVIEW_REQUIRED'
    assert len(evidence['records']) == len(manifest['expectations']) == 81
    for row, source in zip(manifest['expectations'], evidence['records'], strict=True):
        assert row['expectation_id'] == source['expectation_id']
        assert row['source_locator'] == source['source_text_url']
        assert row['official_subpart_identifiers'] == source['lettered_subpart_ids']
        assert row['source_domain_section_url'] == source['source_section_url']
        assert source['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
    assert next(x for x in evidence['records'] if x['expectation_id'] == '7.SP.C.8')['lettered_subpart_ids'] == ['7.SP.C.8.a','7.SP.C.8.b','7.SP.C.8.c']


def test_dc_grade8_unlettered_scope_conditions_are_preserved_fail_closed() -> None:
    manifest = _manifest()
    ledger = json.loads(
        (MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8')
    )
    assert ledger['scope_summary_policy'] == (
        'NON_EXHAUSTIVE_DISCOVERY_ONLY_NOT_FULL_MATHEMATICAL_SCOPE_EVIDENCE'
    )
    records = {row['expectation_id']: row for row in ledger['records']}
    expectations = {row['expectation_id']: row for row in manifest['expectations']}
    for expectation_id in ('8.EE.A.2', '8.SP.A.4'):
        row = expectations[expectation_id]
        record = records[expectation_id]
        scope = record['bounded_mathematical_scope_evidence']
        assert row['official_subpart_identifiers'] == []
        assert record['lettered_subpart_ids'] == []
        assert scope['unlettered_standard'] is True
        assert scope['source_text_url'] == row['source_locator']
        assert scope['short_summary_is_exhaustive'] is False
        assert scope['scope_verification'] == 'PENDING_INDEPENDENT_SOURCE_FIDELITY'
        assert scope['canonical_equivalence'] == 'NOT_ESTABLISHED'
        assert scope['downstream_full_coverage_allowed'] is False
        assert record['independent_acceptance'] == 'PENDING'
        assert row['classification']['standards_mapped'] == 'NO'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'

    roots = ' '.join(records['8.EE.A.2']['bounded_mathematical_scope_evidence']['required_conditions'])
    assert 'positive rational' in roots
    assert '√2' in roots and 'irrational' in roots

    tables = ' '.join(records['8.SP.A.4']['bounded_mathematical_scope_evidence']['required_conditions']).lower()
    assert all(term in tables for term in (
        'construct', 'interpret', 'same subjects', 'row-relative', 'column-relative', 'associations'
    ))


def test_additional_dc_geometric_and_scientific_scope_conditions() -> None:
    manifest = _manifest()
    ledger = json.loads(
        (MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8')
    )
    records = {row['expectation_id']: row for row in ledger['records']}
    rows = {row['expectation_id']: row for row in manifest['expectations']}
    expected_pages = {'7.G.A.2': 50, '8.G.A.2': 55, '8.G.A.4': 56, '8.EE.A.4': 54}
    for standard_id, page in expected_pages.items():
        row = rows[standard_id]
        record = records[standard_id]
        scope = record['bounded_mathematical_scope_evidence']
        assert scope['source_printed_page'] == page
        assert scope['source_text_url'] == row['source_locator']
        assert scope['unlettered_standard'] is True
        assert row['official_subpart_identifiers'] == []
        assert scope['short_summary_is_exhaustive'] is False
        assert scope['scope_verification'] == 'PENDING_INDEPENDENT_SOURCE_FIDELITY'
        assert scope['canonical_equivalence'] == 'NOT_ESTABLISHED'
        assert scope['downstream_full_coverage_allowed'] is False
        assert record['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'

    def evidence(standard_id: str) -> str:
        return ' '.join(records[standard_id]['bounded_mathematical_scope_evidence']['required_conditions']).lower()

    assert all(term in evidence('7.G.A.2') for term in (
        'freehand', 'ruler/protractor', 'technology', 'exactly one', 'multiple', 'no triangle'
    ))
    assert 'given congruent figures' in evidence('8.G.A.2')
    assert 'describe a sequence' in evidence('8.G.A.2')
    assert 'given similar figures' in evidence('8.G.A.4')
    assert 'describe a transformation sequence' in evidence('8.G.A.4')
    assert 'measurement units' in evidence('8.EE.A.4')
    assert 'technology' in evidence('8.EE.A.4')


def test_dc_three_new_grade7_8_unlettered_scope_findings_are_preserved() -> None:
    manifest = _manifest()
    ledger = json.loads(
        (MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8')
    )
    assert len(manifest['expectations']) == len(ledger['records']) == 81
    rows = {r['expectation_id']: r for r in manifest['expectations']}
    records = {r['expectation_id']: r for r in ledger['records']}
    for standard_id in ('7.SP.B.3', '7.EE.B.3', '8.NS.A.1'):
        row = rows[standard_id]
        record = records[standard_id]
        scope = record['bounded_mathematical_scope_evidence']
        assert row['official_subpart_identifiers'] == record['lettered_subpart_ids'] == []
        assert scope['source_text_url'] == row['source_locator']
        assert scope['unlettered_standard'] is True
        assert scope['required_conditions']
        assert scope['short_summary_is_exhaustive'] is False
        assert scope['scope_verification'] == 'PENDING_INDEPENDENT_SOURCE_FIDELITY'
        assert scope['canonical_equivalence'] == 'NOT_ESTABLISHED'
        assert scope['downstream_full_coverage_allowed'] is False
        assert record['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'

    def conditions(standard_id: str) -> str:
        return ' '.join(records[standard_id]['bounded_mathematical_scope_evidence']['required_conditions']).lower()

    assert all(word in conditions('7.SP.B.3') for word in (
        'separation', 'measures of center', 'multiple', 'variability', 'mean absolute deviation'
    ))
    assert all(word in conditions('7.EE.B.3') for word in (
        'properties of operations', 'convert', 'mental computation', 'estimation', 'reasonableness'
    ))
    assert all(word in conditions('8.NS.A.1') for word in (
        'eventually repeats', 'eventually repeating', 'rational-number fraction'
    ))


def test_dc_6_ns_b_4_relatively_prime_factorization_scope_is_preserved() -> None:
    manifest = _manifest()
    ledger = json.loads(
        (MANIFEST.parent / 'dc_grades6_8_ccss.source_fidelity_locators.v1.json').read_text(encoding='utf-8')
    )
    assert len(manifest['expectations']) == len(ledger['records']) == 81
    row = next(r for r in manifest['expectations'] if r['expectation_id'] == '6.NS.B.4')
    record = next(r for r in ledger['records'] if r['expectation_id'] == '6.NS.B.4')
    scope = record['bounded_mathematical_scope_evidence']
    assert row['official_subpart_identifiers'] == record['lettered_subpart_ids'] == []
    assert scope['source_text_url'] == row['source_locator']
    assert scope['unlettered_standard'] is True
    assert scope['short_summary_is_exhaustive'] is False
    assert scope['scope_verification'] == 'PENDING_INDEPENDENT_SOURCE_FIDELITY'
    assert scope['canonical_equivalence'] == 'NOT_ESTABLISHED'
    assert scope['downstream_full_coverage_allowed'] is False
    conditions = ' '.join(scope['required_conditions']).lower()
    assert all(term in conditions for term in (
        '100', '12', 'common factor', 'product', 'no common factor'
    ))
    assert record['independent_acceptance'] == 'PENDING'
    assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
