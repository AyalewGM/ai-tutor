"""Read-only contract checks for source-linked Grades 1–9 gap triage."""

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "grades1_9_gap_triage.wave1.v1.json"
)


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_grade9_inventory_has_no_false_coverage() -> None:
    data = _load()
    courses = data["courses"]
    assert len(courses) == 3
    assert {course["code"]: len(course["items"]) for course in courses} == {
        "ON_MTH1W_2021": 43,
        "MD_INTEGRATED_ALGEBRA_1_2027_28": 30,
        "MD_ALGEBRA_1_2026_27": 40,
    }
    assert data["inventory_summary"]["grade9_expectations_total"] == 113
    assert data["inventory_summary"]["accepted_coverage_claims"] == 0
    for course in courses:
        assert len({row["id"] for row in course["items"]}) == len(course["items"])
        for row in course["items"]:
            assert row["source"].startswith("https://")
            assert row["provisional_relation"] in {
                "NONE_IDENTIFIED",
                "EXISTING_REVIEW_REQUIRED",
                "CANDIDATE_PARTIAL_OR_RELATED",
            }


def test_grade1_aliases_are_explicitly_unapproved() -> None:
    data = _load()
    aliases = data["grade1_5_aliases"]
    assert len(aliases) == data["inventory_summary"]["grade1_5_pack_aliases"] == 42
    assert len({row["alias"] for row in aliases}) == len(aliases)
    assert sum(x["status"] == "UNMAPPED" for x in aliases) == 38
    assert sum(x["status"] == "PROPOSED" for x in aliases) == 4
    assert all(x["reviewed_by"] is None for x in aliases)
    assert data["inventory_summary"][
        "grades6_8_authoritative_expectation_inventory_in_this_register"
    ] is False


def test_priority_ids_are_source_grounded_and_draft_only() -> None:
    data = _load()
    ids = {row["id"] for course in data["courses"] for row in course["items"]}
    batches = data["priority_batches"]
    assert [batch["rank"] for batch in batches] == [1, 2, 3, 4]
    assert len({batch["id"] for batch in batches}) == 4
    for batch in batches:
        assert set(batch["exact_source_ids"]).issubset(ids)
        assert batch["production_gate"]
    assert data["safety"] == {
        "activation": "FORBIDDEN",
        "auto_accept_relations": False,
        "auto_promote_mastery": False,
        "change_canonical_registry": False,
        "mutate_student_records": False,
    }


def test_grade1_gate5_dispositions_remain_fail_closed() -> None:
    data = _load()
    gate = data["grade1_alias_gate"]
    aliases = gate["aliases"]

    assert data["inventory_summary"]["grade1_aliases_independently_accepted"] == 0
    assert data["inventory_summary"]["grade1_alias_gate"] == "GATE_5_OPEN"
    assert gate["status"] == "GATE_5_OPEN_ZERO_OF_SEVEN_ALIASES_ACCEPTED"
    assert gate["independent_review"]["result"] == "0_OF_7_ACCEPTED"
    assert gate["architecture"]["gate"] == "GATE_5_OPEN_NOT_PASSED"
    assert len(aliases) == 7
    assert len({row["alias"] for row in aliases}) == 7
    assert all(row["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED" for row in aliases)
    assert all(row["candidate_components"] for row in aliases)

    assert gate["evidence_dimensions"] == {
        "standards_mapped": "PROVISIONAL_NOT_ACCEPTED",
        "mathematically_reviewed_skill_exists": (
            "MIXED_EXISTING_DRAFT_AND_NEW_DRAFT_REQUIRED"
        ),
        "generator_available": "NOT_AUDITED_BY_THIS_DECISION",
        "validated_practice": "NOT_AUDITED",
        "assessment_ready": "NOT_AUDITED",
        "verified_mastery_evidence": "NOT_INFERRED",
    }
    assert gate["preservation"] == {
        "rewrite_historical_uuid": False,
        "rewrite_student_mastery": False,
        "copy_evidence_between_atoms": False,
        "reporting_profiles_create_credit": False,
        "activate_drafts": False,
    }
