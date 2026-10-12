import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_ia1_2025.expectations.v1.json"
)

EXPECTED_IDS = {
    "IA1.AT.A.1",
    *(f"IA1.AT.B.{number}" for number in range(2, 10)),
    *(f"IA1.AT.C.{number}" for number in range(10, 13)),
    *(f"IA1.AT.D.{number}" for number in range(13, 18)),
    "IA1.GR.A.1",
    "IA1.GR.A.2",
    *(f"IA1.GR.B.{number}" for number in range(3, 6)),
    *(f"IA1.DS.A.{number}" for number in range(1, 5)),
    *(f"IA1.DS.B.{number}" for number in range(5, 9)),
}

REPOSITORY_EXISTING_IDS = {
    "IA1.AT.A.1",
    "IA1.AT.B.8",
    "IA1.AT.C.10",
    "IA1.AT.C.11",
    "IA1.AT.C.12",
    "IA1.AT.D.13",
    "IA1.AT.D.14",
    "IA1.AT.D.15",
    "IA1.AT.D.16",
    "IA1.AT.D.17",
    "IA1.GR.A.1",
    "IA1.DS.A.1",
    "IA1.DS.B.6",
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_pins_official_top_level_identifier_set() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    identifiers = [row["expectation_id"] for row in rows]

    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(identifiers) == 30
    assert len(set(identifiers)) == 30
    assert set(identifiers) == EXPECTED_IDS


def test_repository_existing_rows_are_narrow_and_unverified() -> None:
    rows = _manifest()["expectations"]
    existing = {
        row["expectation_id"]
        for row in rows
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }

    assert existing == REPOSITORY_EXISTING_IDS
    assert len(existing) == 13
    for row in rows:
        if row["expectation_id"] in existing:
            assert len(row["repository_existing_crosswalks"]) == 1
            assert row["classification"]["standards_mapped"] == (
                "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            )
        else:
            assert row["repository_existing_crosswalks"] == []
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
            "NO_CURRENT_INDEPENDENT_ACCEPTANCE_FOR_EXACT_IA1_TARGET"
        )
        assert classification["generator_available"] == (
            "NOT_AUDITED_FOR_EXACT_EXPECTATION_AND_TARGET"
        )
        assert classification["validated_practice"] == "NO_VERIFIED_EVIDENCE"
        assert classification["assessment_ready"] == "NO_VERIFIED_EVIDENCE"
        assert classification["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )


def test_traditional_and_integrated_course_identities_remain_separate() -> None:
    reconciliation = _manifest()["reconciliation"]

    assert reconciliation["official_expectation_count"] == 30
    assert reconciliation["repository_existing_expectation_rows"] == 13
    assert reconciliation["unmapped_expectations"] == 17
    assert reconciliation["traditional_algebra_course_code"] == (
        "MD_ALGEBRA_1_2026_27"
    )
    assert reconciliation["traditional_pack_status"] == (
        "SEPARATE_COURSE_IDENTITY_NOT_CROSSWALKED_BY_THIS_MANIFEST"
    )


def test_integrated_algebra_i_2025_source_ledger_has_printed_pages_and_subparts() -> None:
    data = _manifest()
    ledger = json.loads((MANIFEST.parent / 'md_ia1_2025.source_fidelity_locators.v1.json').read_text(encoding='utf-8'))
    assert ledger['status'] == 'AUTHOR_SOURCE_LOCATORS_REVIEW_REQUIRED'
    assert len(ledger['records']) == len(data['expectations']) == 30
    for row, source in zip(data['expectations'], ledger['records'], strict=True):
        assert row['expectation_id'] == source['expectation_id']
        assert row['source_page'] == source['pdf_page_index']
        assert row['source_printed_page'] == row['source_page'] + 1 == source['printed_page']
        assert row['official_subpart_identifiers'] == source['lettered_subpart_ids']
        assert source['document_url'] == data['provenance']['authoritative_crosswalk_url']
        assert source['independent_acceptance'] == 'PENDING'
        assert row['classification']['verified_mastery_evidence'] == 'NO_AND_MUST_NOT_BE_INFERRED'
    assert next(r for r in ledger['records'] if r['expectation_id']=='IA1.AT.B.2')['lettered_subpart_ids'] == ['IA1.AT.B.2.a','IA1.AT.B.2.b','IA1.AT.B.2.c','IA1.AT.B.2.d']
