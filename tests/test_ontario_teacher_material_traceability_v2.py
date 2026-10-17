"""Fail-closed checks for Ontario Grade 9 teacher-material traceability v2."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/curriculum/drafts/ontario-seven-unit-algebra-r1/teacher_material_traceability.v2.json"


def _load() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_traceability_is_evidence_only_and_runtime_off() -> None:
    data = _load()
    assert data["schema_version"] == "2.0.0"
    assert data["revision"] == "teacher-material-traceability-v2.1"
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert data["source_policy"]["role"] == "OWNER_SUPPLIED_CLASSROOM_EVIDENCE_ONLY"
    assert data["source_policy"]["standards_authority"] is False
    assert data["source_policy"]["learner_data"] is False
    assert "Do not reproduce worksheet wording" in data["source_policy"]["copyright_boundary"]


def test_every_row_has_bounded_evidence_and_allowed_status() -> None:
    data = _load()
    rows = data["rows"]
    assert len(rows) == data["summary"]["total_rows"]
    assert len({row["id"] for row in rows}) == len(rows)
    allowed = {"VERIFIED", "PARTIAL", "ABSENT", "BLOCKED"}
    source_ids = {doc["id"] for doc in data["source_policy"]["source_documents"]}
    for row in rows:
        assert row["status"] in allowed
        assert row["structure"]
        assert row["gap"]
        assert row["next_action"]
        assert row["source"]
        assert all(item["document"] in source_ids for item in row["source"])
        assert all(item["pages"] for item in row["source"])
        assert row["existing_evidence"] or row["status"] == "ABSENT"


def test_summary_counts_are_exact_and_conservative() -> None:
    data = _load()
    rows = data["rows"]
    counts = {status: sum(row["status"] == status for row in rows) for status in ("VERIFIED", "PARTIAL", "ABSENT", "BLOCKED")}
    assert counts == {
        "VERIFIED": data["summary"]["verified"],
        "PARTIAL": data["summary"]["partial"],
        "ABSENT": data["summary"]["absent"],
        "BLOCKED": data["summary"]["blocked"],
    }
    assert data["summary"]["verified"] == 0
    assert data["summary"]["partial"] == 21
    assert data["summary"]["absent"] == 0
    assert data["summary"]["policy"].startswith("Do not create a new broad Ontario Grade 9 package")


def test_merged_depth_extensions_are_partial_not_verified() -> None:
    data = _load()
    by_id = {row["id"]: row for row in data["rows"]}
    for row_id in (
        "G9T-EXPONENT-FIRST-ERROR",
        "G9T-ALGEBRAIC-MEASUREMENT-INVERSION",
    ):
        assert by_id[row_id]["status"] == "PARTIAL"
        assert by_id[row_id]["existing_evidence"]

    assert "independent mathematical and pedagogical re-review" in by_id[
        "G9T-EXPONENT-FIRST-ERROR"
    ]["gap"]
    assert "create no jurisdiction-specific identity" in by_id[
        "G9T-ALGEBRAIC-MEASUREMENT-INVERSION"
    ]["next_action"]
    assert data["summary"]["key_absent"] == []


def test_strong_reuse_rows_do_not_request_duplicate_packages() -> None:
    data = _load()
    by_id = {row["id"]: row for row in data["rows"]}
    for row_id in (
        "G9T-EQUATION-TWO-STEP-EXACT",
        "G9T-EQUATION-MULTISTEP-BOTH-SIDES",
        "G9T-MONOMIAL-QUOTIENT",
        "G9T-POLYNOMIAL-BY-MONOMIAL",
        "G9T-EXPONENT-POWER-OF-POWER",
        "G9T-SCI-CONVERT",
        "G9T-SCI-NORMALIZE",
        "G9T-SCI-MULT-DIV",
    ):
        action = by_id[row_id]["next_action"].lower()
        assert "new package" not in action
        assert "reuse" in action or "close existing" in action or "delivery" in action
