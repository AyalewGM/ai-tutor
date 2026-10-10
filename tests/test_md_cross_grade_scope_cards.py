"""Fail-closed checks for Maryland cross-grade draft scope cards."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "docs"
    / "curriculum"
    / "taxonomy_candidate_scope.md_cross_grade.v1.json"
)


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_scope_bundle_is_draft_and_non_authoritative() -> None:
    data = _load()
    assert data["revision"] == "2026-10-10-r3"
    assert data["review_state"] == (
        "DRAFT_CORRECTIONS_PENDING_LIMITED_INDEPENDENT_MATHEMATICAL_REVIEW"
    )
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    assert data["standards_context"]["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert data["architecture_basis"]["issue"] == 282
    assert data["architecture_basis"]["comment_id"] == 6094147290


def test_eleven_bounded_candidates_are_complete_and_unique() -> None:
    cards = _load()["cards"]
    expected = {
        "MATH.GEO.CIRCLE.CIRCUMFERENCE",
        "MATH.GEO.CIRCLE.AREA",
        "MATH.GEO.ANGLE.COMPLEMENT",
        "MATH.GEO.ANGLE.SUPPLEMENT",
        "MATH.GEO.ANGLE.VERTICAL_EQUALITY",
        "MATH.GEO.ANGLE.ADJACENT_ADDITION",
        "MATH.GEO.TRIANGLE.ANGLE_RELATIONSHIPS",
        "MATH.PROB.EVENT.LIKELIHOOD_0_TO_1",
        "MATH.PROB.EXPERIMENTAL.FREQUENCY",
        "MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT",
        "MATH.PROB.COMPOUND.SAMPLE_SPACE",
    }
    assert {card["code"] for card in cards} == expected
    assert len(cards) == len(expected)

    required = {
        "scope",
        "inclusions",
        "exclusions",
        "prerequisites",
        "examples",
        "misconceptions",
        "assessment_criteria",
        "possible_overlaps",
    }
    for card in cards:
        assert card["review_state"] == "DRAFT"
        assert card["identity_status"] == (
            "PROPOSED_BOUNDED_ATOM_PENDING_ARCHITECTURE_AND_MATH_REVIEW"
        )
        assert required <= card.keys()
        assert all(card[field] for field in required)
        assert any(example.get("valid") is False for example in card["examples"])


def test_decomposition_keeps_distinct_evidence_distinct() -> None:
    data = _load()
    by_code = {card["code"]: card for card in data["cards"]}

    circumference = by_code["MATH.GEO.CIRCLE.CIRCUMFERENCE"]
    area = by_code["MATH.GEO.CIRCLE.AREA"]
    assert "Circle area evidence" in circumference["exclusions"]
    assert "Circumference evidence" in area["exclusions"]

    assert "MATH.GEO.ANGLE.RELATIONSHIPS" not in by_code
    angle_members = {
        "MATH.GEO.ANGLE.COMPLEMENT",
        "MATH.GEO.ANGLE.SUPPLEMENT",
        "MATH.GEO.ANGLE.VERTICAL_EQUALITY",
        "MATH.GEO.ANGLE.ADJACENT_ADDITION",
    }
    assert angle_members < set(by_code)
    profile = data["noncanonical_profiles"][0]
    assert profile["role"] == "REPORTING_ONLY_FAIL_CLOSED_ALL_OF"
    assert set(profile["members"]) == angle_members
    assert "No evidence propagation or duplicate credit" in profile["prohibitions"]

    triangle = by_code["MATH.GEO.TRIANGLE.ANGLE_RELATIONSHIPS"]
    assert "supplementary linear pairs" in triangle["prerequisites"]

    simple_probability = {
        "MATH.PROB.EVENT.LIKELIHOOD_0_TO_1",
        "MATH.PROB.EXPERIMENTAL.FREQUENCY",
        "MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT",
    }
    assert simple_probability < set(by_code)
    assert "Compound-event sample-space construction" in by_code[
        "MATH.PROB.MODEL.COMPARE_THEORY_EXPERIMENT"
    ]["exclusions"]


def test_r3_closes_reviewed_scope_boundaries() -> None:
    by_code = {card["code"]: card for card in _load()["cards"]}

    likelihood = by_code["MATH.PROB.EVENT.LIKELIHOOD_0_TO_1"]
    inclusions = " ".join(likelihood["inclusions"])
    assert "[0,1]" in inclusions
    assert "0% to 100%" in inclusions
    assert any(
        example.get("evidence") == "cross-representation equivalence"
        for example in likelihood["examples"]
    )

    experimental = by_code["MATH.PROB.EXPERIMENTAL.FREQUENCY"]
    assert "Expected-count prediction using n×p as mastery evidence" in experimental[
        "exclusions"
    ]
    assert "do not award or infer expected-count mastery" in experimental[
        "assessment_criteria"
    ]
    assert "multiplication for expected counts" not in experimental["prerequisites"]
    assert "independent repeated trials" in experimental["scope"]
    assert "unchanged conditions" in experimental["scope"]
    assert "constant event probability" in experimental["scope"]
    assert any(
        example.get("evidence") == "changed-condition boundary"
        for example in experimental["examples"]
    )

    adjacent = by_code["MATH.GEO.ANGLE.ADJACENT_ADDITION"]
    assert "whole is supplied and a part is missing" in adjacent["scope"]
    assert "every constituent part is supplied and the whole is missing" in adjacent[
        "scope"
    ]
    assert any(
        example.get("evidence") == "missing whole from supplied parts"
        for example in adjacent["examples"]
    )
    assert (
        "independent missing-whole evidence with all nonoverlapping constituent parts "
        "supplied"
        in adjacent["assessment_criteria"]
    )

    assert "finite discrete probability model" in likelihood["scope"]
    assert "every elementary outcome has positive probability" in likelihood["scope"]
    endpoint_evidence = {
        example.get("evidence")
        for example in likelihood["examples"]
    }
    assert "finite-discrete probability-zero event" in endpoint_evidence
    assert "finite-discrete probability-one event" in endpoint_evidence
    assert any(
        "continuous probability model" in misconception
        for misconception in likelihood["misconceptions"]
    )


def test_bundle_does_not_claim_runtime_mapping_or_mastery() -> None:
    data = _load()
    serialized = json.dumps(data).lower()
    assert "canonical_uuid" not in serialized
    assert "reviewed" not in {
        card["review_state"].lower() for card in data["cards"]
    }
    assert "student_id" not in serialized
    assert "verified_mastery" not in serialized
    assert "accepted_mapping" not in serialized
