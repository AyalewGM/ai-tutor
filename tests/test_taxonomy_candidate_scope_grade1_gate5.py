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
    "MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES_2D",
    "MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES_3D",
    "MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES_2D",
    "MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES_3D",
    "MATH.GEOMETRY.SHAPE.COMPOSE_2D",
    "MATH.GEOMETRY.SHAPE.COMPOSE_3D",
    "MATH.MEASUREMENT.TIME.READ_HOUR_HALF_HOUR",
    "MATH.MEASUREMENT.TIME.REPRESENT_HOUR_HALF_HOUR",
}


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_grade1_gate5_cards_are_draft_and_complete() -> None:
    data = _load()
    assert data["review_status"] == "DRAFT_PENDING_INDEPENDENT_MATHEMATICAL_REVIEW"
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    assert data["revision"] == "2026-10-11-grade1-gate5-r2"

    cards = data["skills"]
    assert len(cards) == 13
    assert {card["code"] for card in cards} == EXPECTED_CODES
    assert len({card["code"] for card in cards}) == len(cards)

    for card in cards:
        assert card["identity_decision"] in {
            "ARCHITECTURE_BOUNDARY_DECIDED_SCOPE_PENDING_REVIEW",
            "ARCHITECTURE_SPLIT_AUTHORIZED_SCOPE_PENDING_INDEPENDENT_REVIEW",
        }
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
    shape_profile = next(
        profile for profile in profiles if profile["label"] == "identify_compose_shapes"
    )
    assert len(shape_profile["members"]) == 6
    assert shape_profile["evaluation"] == "FAIL_CLOSED_ALL_OF"
    assert shape_profile["one_primary_atom_per_attempt"] is True
    assert shape_profile["creates_additional_credit"] is False
    assert shape_profile["back_credits_missing_members"] is False
    assert shape_profile["direct_alias_target"] is False
    assert data["profile_prohibitions"] == [
        "No canonical row or UUID",
        "No mastery event, attempt, diagnostic attempt or variant namespace",
        "One primary atom per attempt",
        "No inferred member mastery or cross-dimension credit",
        "No duplicate, seventh or back-credit",
        "No direct alias target or runtime alias activation",
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

    defining_2d = cards["MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES_2D"]
    conventions = defining_2d["shape_universe"]["classification_conventions"]
    assert conventions["rectangle"] == "quadrilateral with four right angles"
    assert conventions["square"] == "rectangle with four equal sides"
    assert conventions["trapezoid"] == (
        "quadrilateral with at least one pair of parallel sides"
    )
    assert any(
        row.get("must_accept_all_valid_labels")
        for row in defining_2d["assessment_evidence_matrix"]["required"]
    )

    defining_3d = cards["MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES_3D"]
    vocabulary = defining_3d["shape_universe"]["vocabulary"]
    assert vocabulary["face"] == "flat 2-D boundary of a solid"
    assert vocabulary["curved_surface"] == "non-flat boundary of a solid"

    construct_3d = cards["MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES_3D"]
    modes = construct_3d["assessment_evidence_matrix"]["required"][0][
        "accepted_modes"
    ]
    assert set(modes) == {
        "physical_model",
        "virtual_model",
        "valid_drawn_representation",
    }
    assert any(
        example.get("valid_as_construction_evidence") is False
        for example in construct_3d["examples"]
    )

    compose_2d = cards["MATH.GEOMETRY.SHAPE.COMPOSE_2D"]
    triangle_example = next(
        example
        for example in compose_2d["examples"]
        if example["dimension"] == "diagonal_halves_rectangle"
    )
    assert "half-turn" in triangle_example["input"]
    assert "hypotenuses" in triangle_example["input"]
    assert "disjoint" in compose_2d["shape_universe"]["composition_contract"]

    compose_3d = cards["MATH.GEOMETRY.SHAPE.COMPOSE_3D"]
    assert "disjoint" in compose_3d["shape_universe"]["composition_contract"]

    history = _load()["revision_history"]
    assert history[0]["superseded_draft_codes"] == [
        "MATH.GEOMETRY.SHAPE.DEFINING_ATTRIBUTES",
        "MATH.GEOMETRY.SHAPE.CONSTRUCT_FROM_ATTRIBUTES",
        "MATH.GEOMETRY.SHAPE.COMPOSE",
    ]

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
