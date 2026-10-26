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
OFFICIAL_PDF = (
    "https://corestandards.org/wp-content/uploads/2023/09/"
    "ADA-Compliant-Math-Standards.pdf"
)
ADOPTION_URL = (
    "https://osse.dc.gov/release/dc-state-board-education-holds-"
    "regularly-scheduled-public-meeting-10"
)
SOURCE_BLOB = "149b03e24695a4e32efb34e1cc673dfd38ce9d00"


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
