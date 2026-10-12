"""Fail-closed, source-pinned assertions for Issue #377 and PR #381.

These tests validate documentation provenance, not mathematical coverage or
independent source-fidelity acceptance.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

MATRIX = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"
)
VA_CORRECTED_MANIFEST_BLOB = "155d1953fec9be996954ea6be755c8fe7a47a716"
EXPECTED_COUNTS = {
    ("MD", 7): (22, 18, 4),
    ("MD", 8): (27, 20, 7),
    ("VA", 7): (15, 11, 4),
    ("VA", 8): (16, 10, 6),
    ("DC", 7): (24, 18, 6),
    ("DC", 8): (28, 22, 6),
}
ALLOWED = {"CORE_EXISTS_NOT_MAPPED", "PARTIAL_DEPTH", "MISSING_CORE", "NEEDS_IDENTITY_DECISION", "UNKNOWN"}


def _matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_complete_unique_parent_expectations_and_summary() -> None:
    report = _matrix()
    rows = report["rows"]
    assert report["count"] == len(rows) == 132
    assert len({(r["jurisdiction"], r["grade"], r["expectation_id"]) for r in rows}) == 132

    for (jurisdiction, grade), (total, identity, unknown) in EXPECTED_COUNTS.items():
        group = [r for r in rows if r["jurisdiction"] == jurisdiction and r["grade"] == grade]
        assert len(group) == total
        observed = Counter(r["coverage_classification"] for r in group)
        assert observed["NEEDS_IDENTITY_DECISION"] == identity
        assert observed["UNKNOWN"] == unknown
        assert report["summary"][f"{jurisdiction} G{grade}"] == {
            "total": total, "identity": identity, "unknown": unknown,
        }


def test_every_row_matches_its_manifest_provenance_and_stays_fail_closed() -> None:
    report = _matrix()
    manifests = {m["jurisdiction"]: m for m in report["source_manifests"]}
    assert set(manifests) == {"MD", "VA", "DC"}
    for row in report["rows"]:
        assert row["source_blob_sha"] == manifests[row["jurisdiction"]]["blob_sha"]
        assert row["source_pr"] == f'#{manifests[row["jurisdiction"]]["pr"]}'
        assert row["coverage_classification"] in ALLOWED
        assert row["coverage_classification"] in {"NEEDS_IDENTITY_DECISION", "UNKNOWN"}
        assert row["verified_depth"] is False
        assert row["missing_core_verified"] is False
        assert row["provisional"] is True
        assert row["review_gates"]


def test_corrected_virginia_source_reconciled_in_all_31_rows() -> None:
    report = _matrix()
    va_rows = [r for r in report["rows"] if r["jurisdiction"] == "VA"]
    assert len(va_rows) == 31
    assert report["source_manifests"][1]["jurisdiction"] == "VA"
    assert report["source_manifests"][1]["blob_sha"] == VA_CORRECTED_MANIFEST_BLOB
    assert all(row["source_blob_sha"] == VA_CORRECTED_MANIFEST_BLOB for row in va_rows)
    rejected = next(r for r in va_rows if r["expectation_id"] == "7.PS.2")
    assert rejected["local_seed_candidates"] == []
    assert rejected["coverage_classification"] == "UNKNOWN"
    assert rejected["rejected_local_seed_relation"]["seed"] == "VA7.PS.PROBABILITY"
    assert rejected["rejected_local_seed_relation"]["correction_pr"] == 380
    assert rejected["rejected_local_seed_relation"]["correction_source_blob_sha"] == VA_CORRECTED_MANIFEST_BLOB
