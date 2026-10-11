from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "foundations-reuse-v1"


def _module():
    path = DRAFT / "place_value_seeded.py"
    spec = importlib.util.spec_from_file_location("foundations_place_value", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _item_for(structure: str):
    variants = _module()
    return next(
        variants.generate(seed, "guided")
        for seed in range(20)
        if variants.generate(seed, "guided").structure == structure
    )


def test_package_is_fail_closed_and_covers_mihur_flow() -> None:
    package = json.loads((DRAFT / "place_value.depth.v1.json").read_text())

    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["mastery_writes"] is False
    assert package["implementation"] == "DRAFT_EXECUTABLE_CONTENT_NOT_WIRED"
    assert [stage["phase"] for stage in package["stages"]] == [
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    ]
    assert [level["level"] for level in package["representational_progression"]] == [
        "CONCRETE",
        "VISUAL",
        "SYMBOLIC",
    ]
    assert package["assessment_contract"]["guided_practice_credit"] is False
    assert package["assessment_contract"]["hints_allowed"] is False
    assert package["assessment_contract"]["backend_status"] == "NOT_IMPLEMENTED"
    assert package["accessibility"]["mve_requirement_status"].startswith("REQUIREMENT_ONLY")


def test_provenance_is_current_specific_and_fail_closed() -> None:
    provenance = json.loads((DRAFT / "provenance.v1.json").read_text())
    packages = {package["package_id"]: package for package in provenance["packages"]}
    place_value = packages["W1-G2-PLACE-VALUE-REGROUP"]

    assert provenance["runtime_activation"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["reconciled_repository_state"]["main_head_sha"] == (
        "313c13c9df4d530777cf89fb34f21dcedd91f454"
    )
    assert provenance["reconciled_repository_state"]["package_pr_328_head_sha"] == (
        "0036253470c3f47ce0b35b0bba8264cd2cc4817f"
    )
    assert provenance["inspected_issues"] == [278, 293]
    assert place_value["proposed_revision"] == "foundations-reuse-r2"
    assert place_value["upstream_draft"]["pinned_head_sha"] == (
        "5d4e613b4aa241384809e048c60ee082e6f14fe4"
    )
    assert place_value["standards"]["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert place_value["existing_work"]["canonical_approval"] == "UNKNOWN"
    assert place_value["approvals"]["release"] == "NOT_APPROVED"
    assert "CURRENT_R2_REVIEW_PENDING" in place_value["pedagogy"]["source_design_review"]


def test_seeded_replay_mode_separation_and_public_non_disclosure() -> None:
    variants = _module()

    for seed in range(100):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided == variants.generate(seed, "guided")
        assert independent == variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert guided.structure != independent.structure
        payload = independent.public_payload()
        assert "answer" not in payload
        assert "total" not in payload
        assert "canonical_inventory" not in payload
        assert "verification" not in payload
        assert "hint" not in payload


def test_all_structures_include_distinct_bundle_transfer() -> None:
    variants = _module()
    guided = {variants.generate(seed, "guided").structure for seed in range(20)}
    independent = {variants.generate(seed, "independent").structure for seed in range(20)}

    assert guided == set(variants.STRUCTURES)
    assert independent == set(variants.STRUCTURES)
    assert "TRANSFER_BUNDLES" in independent


def test_independent_coefficient_oracle_and_canonical_inventory() -> None:
    variants = _module()

    for seed in range(250):
        item = variants.generate(seed, "independent")
        if item.structure == "COMPARE_FIRST_DIFFERENCE":
            assert item.comparison_values is not None
            left, right = item.comparison_values
            oracle = "<" if left < right else ">" if left > right else "="
            assert item.answer == oracle
            assert item.first_differing_place == "tens"
            continue

        independently_reconstructed = 100 * item.hundreds + 10 * item.tens + item.ones
        assert item.total == independently_reconstructed
        canonical = (item.total // 100, (item.total // 10) % 10, item.total % 10)
        if item.structure == "EXCHANGE_INVARIANT":
            after_hundreds, after_tens, after_ones = item.canonical_inventory
            assert 100 * after_hundreds + 10 * after_tens + after_ones == item.total
            assert after_hundreds == item.hundreds - 1
            assert after_tens == item.tens + 10
        else:
            assert item.canonical_inventory == canonical


def test_numeric_diagnosis_uses_observed_response_evidence() -> None:
    variants = _module()
    compose = _item_for("COMPOSE_NONSTANDARD")
    exchange = _item_for("EXCHANGE_INVARIANT")
    zero = _item_for("ZERO_PLACEHOLDER")

    assert variants.diagnose_numeric_response(compose, compose.total) == "CORRECT_PRACTICE_ONLY"
    assert (
        variants.diagnose_numeric_response(compose, compose.hundreds + compose.tens + compose.ones)
        == "DIGIT_VS_VALUE"
    )
    lost_hundred = 100 * compose.hundreds + 10 * (compose.tens % 10) + compose.ones
    assert (
        variants.diagnose_numeric_response(compose, lost_hundred)
        == "NONSTANDARD_COUNT_AS_DIGIT"
    )
    assert (
        variants.diagnose_numeric_response(exchange, exchange.total + 100)
        == "EXCHANGE_CREATES_VALUE"
    )
    omitted_zero = 10 * zero.hundreds + zero.ones
    assert (
        variants.diagnose_numeric_response(zero, omitted_zero)
        == "ZERO_PLACEHOLDER_OMITTED"
    )


def test_comparison_diagnosis_uses_symbol_and_reasoning_place() -> None:
    variants = _module()
    item = _item_for("COMPARE_FIRST_DIFFERENCE")
    assert item.answer == "<"

    assert (
        variants.diagnose_comparison_response(item, "<", "tens")
        == "CORRECT_PRACTICE_ONLY"
    )
    assert variants.diagnose_comparison_response(item, ">", "ones") == "COMPARED_ONES_FIRST"
    assert (
        variants.diagnose_comparison_response(item, ">", "tens")
        == "INEQUALITY_SYMBOL_REVERSED"
    )
    assert (
        variants.diagnose_comparison_response(item, "<", "ones")
        == "PLACE_SEQUENCE_CONFUSION"
    )


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _module().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _module().generate(4, mode)
