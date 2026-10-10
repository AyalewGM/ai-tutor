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
    allowed_review_states = {
        "PENDING",
        "REQUEST_CHANGES_DECOMPOSITION_REQUIRED",
        "DRAFT_SCOPE_APPROVED_NOT_MAPPING_ACCEPTED",
    }
    for candidate in candidates:
        assert candidate["local_skill_code"] in rows
        row = rows[candidate["local_skill_code"]]
        target = candidate["official_expectation_id"]
        basis = candidate["traceability_basis"]
        mapped_or_displaced = set(row["official_targets"])
        for displaced in row["displaced_or_extra_scope"]:
            if displaced.get("current_md_target"):
                mapped_or_displaced.add(displaced["current_md_target"])

        if basis == "LOCAL_RECONCILIATION_TARGET":
            assert target is not None
            assert target in mapped_or_displaced
        elif basis == "OFFICIAL_SOURCE_EXPECTATION_GAP":
            assert target is not None
            trace = candidate["source_traceability"]
            source_gaps = {
                item["expectation_id"]: item
                for item in row["source_grounded_unmapped_expectations"]
            }
            assert target not in mapped_or_displaced
            assert trace["expectation_id"] == target
            assert trace["source_url"] in data["source_urls"]
            assert trace["local_row_relation"].startswith("NOT_ESTABLISHED")
            assert source_gaps[target]["status"] == (
                "OFFICIAL_SOURCE_EXPECTATION_NOT_ESTABLISHED_BY_LOCAL_ROW"
            )
            assert source_gaps[target]["source_url"] == trace["source_url"]
        else:
            assert basis == "PLACEMENT_WITHOUT_CURRENT_GRADE_TARGET"
            assert target is None
            assert candidate["gap_type"] == "PLACEMENT_CONFLICT"

        assert candidate["repo_wide_absence_proven"] is False
        assert candidate["mathematical_review"] in allowed_review_states
        assert candidate["content_production"] == "NOT_AUTHORIZED_AS_APPROVED"


def test_review_evidence_does_not_promote_mapping_or_activation() -> None:
    data = json.loads(
        (ROOT / "md_grades6_8_concept_gap_candidates.wave1.v1.json").read_text()
    )
    candidates = {candidate["id"]: candidate for candidate in data["candidates"]}

    angles = candidates["MD7_CROSS_GRADE_ANGLES"]["canonical_candidate_evidence"]
    assert angles["architecture_disposition"] == "REPORTING_ONLY_ALL_OF_NOT_CANONICAL"
    assert angles["verdict"] == "APPROVE_MATHEMATICAL_SCOPE_ONLY"
    assert angles["identity_state"] == "DRAFT_NOT_ACTIVATED"
    assert angles["pinned_head"] == "6e30bd5522ba299a73b39c1e8d493577a033a5b6"
    assert angles["artifact_blob"] == "9f4773c7e5964d8336b59d9ee2f76950bac7d280"
    assert angles["review_comment"] == 6095975833
    assert set(angles["reviewed_codes"]) == {
        "MATH.GEO.ANGLE.COMPLEMENT",
        "MATH.GEO.ANGLE.SUPPLEMENT",
        "MATH.GEO.ANGLE.VERTICAL_EQUALITY",
        "MATH.GEO.ANGLE.ADJACENT_ADDITION",
    }
    assert angles["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"

    for id_ in ("MD7_CROSS_GRADE_PROBABILITY", "MD8_COMPOUND_PROBABILITY"):
        evidence = candidates[id_]["canonical_candidate_evidence"]
        assert evidence["verdict"] == "APPROVE_MATHEMATICAL_SCOPE_ONLY"
        assert evidence["identity_state"] == "DRAFT_NOT_ACTIVATED"
        assert evidence["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"


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
