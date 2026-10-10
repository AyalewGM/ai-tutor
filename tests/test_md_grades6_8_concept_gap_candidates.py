"""Validate concept-level gap triage without inventing repo-wide absence."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1] / "docs" / "curriculum" / "standards"


def test_concept_candidates_trace_to_reviewed_source_reconciliation() -> None:
    source = json.loads(
        (ROOT / "md_grades6_8_2025.seed_skill_reconciliation.v1.json").read_text()
    )
    data = json.loads(
        (ROOT / "md_grades6_8_concept_gap_candidates.wave1.v1.json").read_text()
    )
    rows = {row["local_seed_code"]: row for row in source["rows"]}
    candidates = data["candidates"]
    assert len(candidates) == 14
    assert len({c["id"] for c in candidates}) == 14
    for candidate in candidates:
        assert candidate["local_skill_code"] in rows
        target = candidate["official_expectation_id"]
        if target is not None:
            row = rows[candidate["local_skill_code"]]
            target_ids = set(row["official_targets"])
            for displaced in row["displaced_or_extra_scope"]:
                if displaced.get("current_md_target"):
                    target_ids.add(displaced["current_md_target"])
            assert target in target_ids
        assert candidate["repo_wide_absence_proven"] is False
        assert candidate["mathematical_review"] == "PENDING"
        assert candidate["content_production"] == "NOT_AUTHORIZED_AS_APPROVED"


def test_batches_partition_candidates_and_preserve_safety() -> None:
    data = json.loads(
        (ROOT / "md_grades6_8_concept_gap_candidates.wave1.v1.json").read_text()
    )
    ids = [c["id"] for c in data["candidates"]]
    grouped = [
        id_
        for batch in data["handoff_batches"]
        for id_ in batch["candidate_ids"]
    ]
    assert len(ids) == len(grouped)
    assert set(ids) == set(grouped)
    assert data["counts"]["confirmed_repo_wide_missing"] == 0
    assert data["counts"]["placement_conflicts"] == sum(
        c["gap_type"] == "PLACEMENT_CONFLICT" for c in data["candidates"]
    )
    assert data["safety"] == {
        "verified_coverage_claim": False,
        "student_data_changes": False,
        "canonical_identity_changes": False,
        "release_activation": False,
    }
