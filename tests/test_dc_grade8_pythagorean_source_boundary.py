"""Focused fail-closed regression for the DC Grade 8 Pythagorean slice.

This test locks source identity and qualifier-safe reuse boundaries only. It does
not establish canonical equivalence, mathematical depth, or runtime coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARDS = (
    ROOT
    / "docs"
    / "curriculum"
    / "standards"
    / "dc_grades6_8_ccss.expectations.v1.json"
)
LOCATORS = STANDARDS.with_name(
    "dc_grades6_8_ccss.source_fidelity_locators.v1.json"
)
TRIAGE = (
    ROOT
    / "docs"
    / "curriculum"
    / "coverage"
    / "dmv_grades7_8_expectation_depth_triage.v1.json"
)

IDS = ("8.G.B.6", "8.G.B.7", "8.G.B.8")
VOLUME_ID = "8.G.C.9"
GEOMETRY_CLUSTER_IDS = (
    "8.G.A.1",
    "8.G.A.2",
    "8.G.A.3",
    "8.G.A.4",
    "8.G.A.5",
)
GEOMETRY_CLUSTER_PAGES = {
    "8.G.A.1": 55,
    "8.G.A.2": 55,
    "8.G.A.3": 56,
    "8.G.A.4": 56,
    "8.G.A.5": 56,
}
OFFICIAL_PDF = (
    "https://corestandards.org/wp-content/uploads/2023/09/"
    "ADA-Compliant-Math-Standards.pdf"
)
ADOPTION_URL = (
    "https://osse.dc.gov/release/dc-state-board-education-holds-"
    "regularly-scheduled-public-meeting-10"
)
SOURCE_BLOB = "4e2a95c37bace6b1efcb0ff733eade42c44888c9"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dc_pythagorean_rows_use_official_versioned_source() -> None:
    manifest = _read(STANDARDS)
    rows = {row["expectation_id"]: row for row in manifest["expectations"]}
    correction = manifest["provenance"]["pythagorean_slice_correction"]

    assert correction["expectation_ids"] == list(IDS)
    assert correction["source_url"] == OFFICIAL_PDF
    assert correction["source_printed_page"] == 56
    assert correction["version_date"] == "2010"
    assert correction["adoption_url"] == ADOPTION_URL
    assert correction["adoption_date"] == "2010-07-21"
    assert correction["access_date"] == "2026-10-26"
    assert "JULY_29_RELEASE_DISCREPANCY_RETAINED" in (
        correction["adoption_date_status"]
    )
    assert "2010-07-28" in correction["adoption_date_conflict_note"]

    for expectation_id in IDS:
        row = rows[expectation_id]
        assert row["source_locator"] == OFFICIAL_PDF
        assert row["source_domain_section_url"] == OFFICIAL_PDF
        assert row["source_publication_version"] == "2010"
        assert row["source_printed_page"] == 56
        assert row["adoption_url"] == ADOPTION_URL
        assert row["adoption_date"] == "2010-07-21"
        assert row["access_date"] == "2026-10-26"
        assert "2010-07-28" in row["adoption_date_conflict_note"]
        assert row["source_fidelity_status"] == (
            "AUTHOR_CORRECTED_OFFICIAL_PUBLICATION_PENDING_INDEPENDENT_ACCEPTANCE"
        )
        assert row["classification"]["standards_mapped"] == "NO"
        assert row["classification"]["verified_mastery_evidence"] == (
            "NO_AND_MUST_NOT_BE_INFERRED"
        )

    assert manifest["safety"]["activation"] == "FORBIDDEN"
    assert manifest["safety"]["verified_coverage_claim"] is False


def test_dc_pythagorean_locator_scope_and_reuse_stay_fail_closed() -> None:
    ledger = _read(LOCATORS)
    rows = {row["expectation_id"]: row for row in ledger["records"]}
    expected_status = {
        "8.G.B.6": "NO_COVERAGE_CLAIM",
        "8.G.B.7": "PARTIAL_NON_EXHAUSTIVE",
        "8.G.B.8": "PROVISIONAL_NOT_ACCEPTED",
    }

    for expectation_id, status in expected_status.items():
        row = rows[expectation_id]
        scope = row["bounded_mathematical_scope_evidence"]
        relation = row["provisional_reuse_boundary"]

        assert row["source_text_url"] == OFFICIAL_PDF
        assert row["source_section_url"] == OFFICIAL_PDF
        assert row["source_printed_page"] == 56
        assert row["adoption_date"] == "2010-07-21"
        assert row["independent_acceptance"] == "PENDING"
        assert scope["source_printed_page"] == 56
        assert scope["required_conditions"]
        assert scope["short_summary_is_exhaustive"] is False
        assert scope["canonical_equivalence"] == "NOT_ESTABLISHED"
        assert scope["downstream_full_coverage_allowed"] is False
        assert relation["candidate"] == "M8.G.PYTH"
        assert relation["status"] == status
        assert relation["coverage_credit"] is False
        assert relation["mapping_activation"] is False
        assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
        assert relation["union_inheritance_forbidden"] is True

    proof_exclusions = " ".join(
        rows["8.G.B.6"]["provisional_reuse_boundary"]["excluded_required_scope"]
    ).lower()
    assert "proof of the pythagorean theorem" in proof_exclusions
    assert "proof of its converse" in proof_exclusions

    side_exclusions = " ".join(
        rows["8.G.B.7"]["provisional_reuse_boundary"]["excluded_required_scope"]
    ).lower()
    assert "three-dimensional" in side_exclusions
    assert "real-world" in side_exclusions


def test_dmv_triage_records_three_separate_inactive_relations() -> None:
    report = _read(TRIAGE)
    dc_source = next(
        source
        for source in report["source_manifests"]
        if source["jurisdiction"] == "DC"
    )
    assert dc_source["blob_sha"] == SOURCE_BLOB

    rows = {
        row["expectation_id"]: row
        for row in report["rows"]
        if row["jurisdiction"] == "DC"
    }
    expected_status = {
        "8.G.B.6": "NO_COVERAGE_CLAIM",
        "8.G.B.7": "PARTIAL_NON_EXHAUSTIVE",
        "8.G.B.8": "PROVISIONAL_NOT_ACCEPTED",
    }

    for expectation_id, status in expected_status.items():
        row = rows[expectation_id]
        relation = row["reuse_relation"]
        assert row["source_blob_sha"] == SOURCE_BLOB
        assert row["source_url"] == OFFICIAL_PDF
        assert row["coverage_classification"] == "NEEDS_IDENTITY_DECISION"
        assert row["shared_core_reuse_candidates"] == "M8.G.PYTH"
        assert row["verified_depth"] is False
        assert row["missing_core_verified"] is False
        assert row["provisional"] is True
        assert relation["status"] == status
        assert relation["coverage_credit"] is False
        assert relation["mapping_activation"] is False
        assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
        assert relation["union_inheritance_forbidden"] is True


def test_dc_geometry_cluster_uses_official_pages_and_no_coverage_claim() -> None:
    manifest = _read(STANDARDS)
    rows = {row["expectation_id"]: row for row in manifest["expectations"]}
    correction = manifest["provenance"][
        "geometry_congruence_similarity_slice_correction"
    ]

    assert correction["expectation_ids"] == list(GEOMETRY_CLUSTER_IDS)
    assert correction["source_url"] == OFFICIAL_PDF
    assert correction["source_printed_pages"] == [55, 56]
    assert correction["version_date"] == "2010"
    assert correction["adoption_date"] == "2010-07-21"
    assert correction["access_date"] == "2026-10-26"
    assert correction["mapping_evidence_status"] == (
        "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND; "
        "EXPLICIT_BOUNDARY_NOT_PROOF_OF_MISSING_MATHEMATICS"
    )

    for expectation_id in GEOMETRY_CLUSTER_IDS:
        row = rows[expectation_id]
        boundary = row["mapping_evidence_boundary"]
        assert row["source_locator"] == OFFICIAL_PDF
        assert row["source_domain_section_url"] == OFFICIAL_PDF
        assert row["source_printed_page"] == GEOMETRY_CLUSTER_PAGES[expectation_id]
        assert row["adoption_date"] == "2010-07-21"
        assert row["source_fidelity_status"] == (
            "AUTHOR_CORRECTED_OFFICIAL_PUBLICATION_PENDING_INDEPENDENT_ACCEPTANCE"
        )
        assert boundary["status"] == "NO_COVERAGE_CLAIM"
        assert boundary["repository_specific_mapping_located"] is False
        assert boundary["missing_mathematical_content_inferred"] is False
        assert boundary["coverage_credit"] is False
        assert boundary["mapping_activation"] is False
        assert boundary["canonical_correspondence"] == "NOT_ESTABLISHED"

    assert rows["8.G.A.1"]["official_subpart_identifiers"] == [
        "8.G.A.1.a",
        "8.G.A.1.b",
        "8.G.A.1.c",
    ]


def test_dc_geometry_cluster_locator_and_triage_stay_fail_closed() -> None:
    ledger = _read(LOCATORS)
    locator_rows = {
        row["expectation_id"]: row
        for row in ledger["records"]
        if row["expectation_id"] in GEOMETRY_CLUSTER_IDS
    }
    report = _read(TRIAGE)
    triage_rows = {
        row["expectation_id"]: row
        for row in report["rows"]
        if row["jurisdiction"] == "DC"
        and row["expectation_id"] in GEOMETRY_CLUSTER_IDS
    }
    dc_source = next(
        source
        for source in report["source_manifests"]
        if source["jurisdiction"] == "DC"
    )
    assert dc_source["blob_sha"] == SOURCE_BLOB

    for expectation_id in GEOMETRY_CLUSTER_IDS:
        locator = locator_rows[expectation_id]
        scope = locator["bounded_mathematical_scope_evidence"]
        boundary = locator["no_coverage_boundary"]
        triage = triage_rows[expectation_id]
        relation = triage["reuse_relation"]

        assert locator["source_text_url"] == OFFICIAL_PDF
        assert locator["source_section_url"] == OFFICIAL_PDF
        assert locator["source_printed_page"] == (
            GEOMETRY_CLUSTER_PAGES[expectation_id]
        )
        assert locator["independent_acceptance"] == "PENDING"
        assert scope["required_conditions"]
        assert scope["canonical_equivalence"] == "NOT_ESTABLISHED"
        assert scope["downstream_full_coverage_allowed"] is False
        assert boundary["status"] == "NO_COVERAGE_CLAIM"
        assert boundary["candidate"] is None
        assert boundary["missing_mathematical_content_inferred"] is False
        assert boundary["coverage_credit"] is False
        assert boundary["mapping_activation"] is False

        assert triage["source_blob_sha"] == SOURCE_BLOB
        assert triage["source_url"] == OFFICIAL_PDF
        assert triage["coverage_classification"] == "UNKNOWN"
        assert triage["reuse_relation"]["status"] == "NO_COVERAGE_CLAIM"
        assert triage["missing_core_verified"] is False
        assert triage["verified_depth"] is False
        assert relation["candidate"] is None
        assert relation["missing_mathematical_content_inferred"] is False
        assert relation["coverage_credit"] is False
        assert relation["mapping_activation"] is False
        assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
        assert relation["union_inheritance_forbidden"] is True


def test_dc_volume_row_uses_official_page_and_complete_know_use_scope() -> None:
    manifest = _read(STANDARDS)
    rows = {row["expectation_id"]: row for row in manifest["expectations"]}
    correction = manifest["provenance"]["volume_slice_correction"]
    row = rows[VOLUME_ID]
    boundary = row["mapping_evidence_boundary"]

    assert correction["expectation_ids"] == [VOLUME_ID]
    assert correction["source_url"] == OFFICIAL_PDF
    assert correction["source_printed_page"] == 56
    assert correction["version_date"] == "2010"
    assert correction["adoption_date"] == "2010-07-21"
    assert correction["access_date"] == "2026-10-26"

    assert row["source_locator"] == OFFICIAL_PDF
    assert row["source_domain_section_url"] == OFFICIAL_PDF
    assert row["source_printed_page"] == 56
    assert row["official_subpart_identifiers"] == []
    scope = row["scope_summary"].lower()
    assert "know the formulas" in scope
    assert "cones, cylinders, and spheres" in scope
    assert "real-world and mathematical problems" in scope
    assert boundary["status"] == "NO_COVERAGE_CLAIM"
    assert boundary["repository_specific_mapping_located"] is False
    assert boundary["missing_mathematical_content_inferred"] is False
    assert boundary["coverage_credit"] is False
    assert boundary["mapping_activation"] is False
    assert boundary["canonical_correspondence"] == "NOT_ESTABLISHED"


def test_dc_volume_locator_and_triage_stay_unknown_and_inactive() -> None:
    ledger = _read(LOCATORS)
    locator = next(
        row for row in ledger["records"] if row["expectation_id"] == VOLUME_ID
    )
    scope = locator["bounded_mathematical_scope_evidence"]
    boundary = locator["no_coverage_boundary"]

    assert locator["source_text_url"] == OFFICIAL_PDF
    assert locator["source_section_url"] == OFFICIAL_PDF
    assert locator["source_printed_page"] == 56
    assert locator["lettered_subpart_ids"] == []
    assert locator["independent_acceptance"] == "PENDING"
    required = " ".join(scope["required_conditions"]).lower()
    assert "know the formulas" in required
    assert "real-world problems" in required
    assert "mathematical problems" in required
    assert scope["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert scope["downstream_full_coverage_allowed"] is False
    assert boundary["candidate"] is None
    assert boundary["missing_mathematical_content_inferred"] is False
    assert boundary["coverage_credit"] is False
    assert boundary["mapping_activation"] is False

    report = _read(TRIAGE)
    dc_source = next(
        source
        for source in report["source_manifests"]
        if source["jurisdiction"] == "DC"
    )
    triage = next(
        row
        for row in report["rows"]
        if row["jurisdiction"] == "DC" and row["expectation_id"] == VOLUME_ID
    )
    relation = triage["reuse_relation"]

    assert dc_source["blob_sha"] == SOURCE_BLOB
    assert triage["source_blob_sha"] == SOURCE_BLOB
    assert triage["source_url"] == OFFICIAL_PDF
    assert triage["coverage_classification"] == "UNKNOWN"
    assert triage["shared_core_reuse_candidates"] is None
    assert triage["missing_core_verified"] is False
    assert triage["verified_depth"] is False
    assert relation["candidate"] is None
    assert relation["status"] == "NO_COVERAGE_CLAIM"
    assert relation["missing_mathematical_content_inferred"] is False
    assert relation["coverage_credit"] is False
    assert relation["mapping_activation"] is False
    assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
    assert relation["union_inheritance_forbidden"] is True
