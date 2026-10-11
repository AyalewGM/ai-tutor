"""Fail-closed contracts for the Grade 1 Gate 5 DRAFT scope-card batch."""

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "taxonomy_candidate_scope.grade1_gate5.v1.json"
)

EXPECTED_CODES = {
    "MATH.NUMBER_SENSE.REPRESENT_NUMERALS_TO_120",
    "MATH.NUMBER_SENSE.ORDER_WHOLE_NUMBERS_TO_120",
    "MATH.EARLY_ALGEBRA.EQUALITY_RELATION",
    "MATH.EARLY_ALGEBRA.ADDITION_EQUATION_UNKNOWN_WITHIN_20",
    "MATH.EARLY_ALGEBRA.SUBTRACTION_EQUATION_UNKNOWN_WITHIN_20",
    "MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES",
    "MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES",
    "MATH.GEOMETRY.SHAPE.COMPOSE",
    "MATH.MEASUREMENT.TIME.READ_HOUR_HALF_HOUR",
    "MATH.MEASUREMENT.TIME.REPRESENT_HOUR_HALF_HOUR",
}


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_grade1_gate5_cards_are_draft_and_complete() -> None:
    data = _load()
    assert data["review_status"] == "DRAFT_PENDING_INDEPENDENT_MATHEMATICAL_REVIEW"
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    assert data["revision"] == "2026-10-10-grade1-gate5-r1"

    cards = data["skills"]
    assert len(cards) == 10
    assert {card["code"] for card in cards} == EXPECTED_CODES
    assert len({card["code"] for card in cards}) == len(cards)

    for card in cards:
        assert card["identity_decision"] == (
            "ARCHITECTURE_BOUNDARY_DECIDED_SCOPE_PENDING_REVIEW"
        )
        assert card["components"]
        assert card["inclusions"]
        assert card["exclusions"]
        assert card["prerequisite_concepts"]
        assert card["examples"]
        assert card["misconception_probes"]
        assert card["assessment_evidence_matrix"]
        audit = card["collision_audit"]
        assert audit["exact_code_on_main"] == (
            "NOT_FOUND_IN_PERSISTED_SCOPE_CARDS_OR_GENERATOR_DERIVED_REGISTRY"
        )
        assert audit["possible_overlaps"]
        assert "PENDING_INDEPENDENT" in audit["disposition"]


def test_reporting_profiles_are_noncanonical_and_fail_closed() -> None:
    data = _load()
    profiles = data["noncanonical_profiles"]
    assert {profile["label"] for profile in profiles} == {
        "count_compare_to_120",
        "equation_balance",
        "identify_compose_shapes",
        "tell_time_hour_half_hour",
    }
    all_members = {member for profile in profiles for member in profile["members"]}
    assert all_members.issubset(
        EXPECTED_CODES
        | {
            "MATH.NUMBER_SENSE.COUNT_FORWARD_BY_ONE_TO_120",
            "MATH.NUMBER_SENSE.COMPARE_WHOLE_NUMBERS_TO_120",
        }
    )
    assert all(profile["role"] == "REPORTING_ONLY_ALL_OF" for profile in profiles)
    assert data["profile_prohibitions"] == [
        "No canonical row or UUID",
        "No mastery event, attempt or variant namespace",
        "No inferred member mastery",
        "No duplicate credit",
        "No runtime alias activation",
    ]


def test_grade1_boundaries_and_separate_evidence_dimensions_are_explicit() -> None:
    cards = {card["code"]: card for card in _load()["skills"]}

    representation = cards["MATH.NUMBER_SENSE.REPRESENT_NUMERALS_TO_120"]
    assert any("0..120" in item for item in representation["inclusions"])
    representation_directions = {
        row["direction"]
        for row in representation["assessment_evidence_matrix"]["required"]
    }
    assert representation_directions == {
        "to_written_numeral",
        "from_written_numeral",
    }

    ordering = cards["MATH.NUMBER_SENSE.ORDER_WHOLE_NUMBERS_TO_120"]
    ordering_directions = {
        row.get("direction")
        for row in ordering["assessment_evidence_matrix"]["required"]
    }
    assert ordering_directions >= {"ascending", "descending"}

    addition = cards[
        "MATH.EARLY_ALGEBRA.ADDITION_EQUATION_UNKNOWN_WITHIN_20"
    ]
    assert {
        row["unknown_position"]
        for row in addition["assessment_evidence_matrix"]["required"]
    } == {"first_addend", "second_addend", "sum"}

    subtraction = cards[
        "MATH.EARLY_ALGEBRA.SUBTRACTION_EQUATION_UNKNOWN_WITHIN_20"
    ]
    assert {
        row["unknown_position"]
        for row in subtraction["assessment_evidence_matrix"]["required"]
    } == {"minuend", "subtrahend", "difference"}

    for code in {
        "MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES",
        "MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES",
        "MATH.GEOMETRY.SHAPE.COMPOSE",
    }:
        assert "review_question" in cards[code]["assessment_evidence_matrix"]

    read_time = cards["MATH.MEASUREMENT.TIME.READ_HOUR_HALF_HOUR"]
    represent_time = cards["MATH.MEASUREMENT.TIME.REPRESENT_HOUR_HALF_HOUR"]
    assert read_time["components"] != represent_time["components"]
    assert any(
        "No production mastery inference" in item
        for item in read_time["assessment_evidence_matrix"]["prohibitions"]
    )
    assert any(
        "No reading mastery inference" in item
        for item in represent_time["assessment_evidence_matrix"]["prohibitions"]
    )
