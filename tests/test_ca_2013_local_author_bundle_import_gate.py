"""Fail-closed status for independently unaccepted local California author bundle."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_california_author_bundle_is_not_integrated_or_accepted():
    data = json.loads((ROOT / "ca_2013_local_author_bundle_import_gate.v1.json").read_text())
    assert data["status"] == "LOCAL_AUTHOR_BUNDLE_VERIFIED_NOT_IMPORTED"
    assert data["manifest_entries"] == data["manifest_sha256_matches"] == 19
    assert sum(data["author_row_counts"].values()) == data["author_total_not_imported"] == 271
    assert data["mathematics_i_already_committed_author_rows"] == 59
    assert data["grade1_identifier_page_slice_staged"] == 21
    assert data["grade1_full_scope_rows_imported"] == 0
    assert data["author_full_scope_rows_not_imported"] == 271
    assert len(data["archive_sha256"]) == 64
    assert data["independent_source_acceptance"] == "PENDING"
    assert data["publisher_pdf_byte_authentication"] == "PENDING"
    for field in ("canonical_equivalence", "assessment", "mastery"):
        assert data[field] == "UNVERIFIED"
    assert data["runtime_activation"] == "FORBIDDEN"
