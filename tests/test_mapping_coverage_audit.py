"""Structural tests for scripts/audit_curriculum_mapping_coverage.py.

The audit is a read-only, fail-closed coverage report. These tests pin the
invariants that keep it honest — they must not assert specific counts (those
change as inventories land) but must guarantee the audit can never fabricate
coverage.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "audit_curriculum_mapping_coverage",
    ROOT / "scripts" / "audit_curriculum_mapping_coverage.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

VALID_STATUSES = {
    "NOT_INVENTORIED",
    "PACK_ONLY_NOT_INVENTORIED",
    "INVENTORIED_NO_CANDIDATES",
    "PROVISIONAL_ONLY",
    "ACCEPTED_PARTIAL",
    "ACCEPTED_FULL",
}


def test_audit_runs_and_has_required_shape():
    a = mod.audit()
    for key in ("schema_version", "status", "cells", "totals", "manifests", "safety"):
        assert key in a, f"missing top-level key: {key}"
    for key in (
        "inventoried_expectations", "with_provisional_candidate", "no_candidate",
        "accepted_mappings", "catalog_canonical_codes", "alias_statuses",
    ):
        assert key in a["totals"], f"missing totals key: {key}"


def test_cell_totals_reconcile_with_manifest_rows():
    a = mod.audit()
    assert sum(c["inventoried_expectations"] for c in a["cells"]) == a["totals"]["inventoried_expectations"]
    for c in a["cells"]:
        assert c["status"] in VALID_STATUSES
        assert c["with_provisional_candidate"] <= c["inventoried_expectations"]
        assert len(c["no_candidate_ids"]) == c["inventoried_expectations"] - c["with_provisional_candidate"]


def test_fail_closed_no_coverage_without_accepted_evidence():
    a = mod.audit()
    for c in a["cells"]:
        # A cell with no inventory can never claim accepted coverage.
        if c["inventoried_expectations"] == 0:
            assert c["accepted_mappings"] == 0
            assert c["status"] in {"NOT_INVENTORIED", "PACK_ONLY_NOT_INVENTORIED"}
        # Provisional links never promote a cell to ACCEPTED_*.
        if c["accepted_mappings"] == 0:
            assert not c["status"].startswith("ACCEPTED")


def test_markdown_renders_and_discloses_safety():
    a = mod.audit()
    md = mod.to_markdown(a)
    assert "READ_ONLY" in a["status"]
    assert "provisional" in md.lower()
    assert "| Juris | Grade |" in md


def test_every_manifest_is_counted():
    a = mod.audit()
    assert len(a["manifests"]) >= 1
    assert all(m["count"] > 0 for m in a["manifests"])
