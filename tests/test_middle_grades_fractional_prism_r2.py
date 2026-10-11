from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "middle-grades-fractional-prism-r2"
PHASES = [
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
]


def _load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _variants():
    path = DRAFT / "seeded_variants.py"
    spec = importlib.util.spec_from_file_location("middle_grades_fractional_prism_r2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_and_fail_closed() -> None:
    provenance = _load("provenance.json")

    assert provenance["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert provenance["package_id"] == "W1-G6-FRACTIONAL-PRISM-VOLUME"
    assert provenance["revision"] == "middle-grades-fractional-prism-r4"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["official_standards"]["official_crosswalk_url"].startswith(
        "https://msde.maryland.gov/"
    )
    assert provenance["official_standards"]["exact_expectation_ids"] == ["6.GR.A.2"]
    assert provenance["official_standards"]["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert provenance["official_standards"]["coverage_credit"] == "NONE"
    assert provenance["canonical"]["new_canonical_identity"] is False
    assert provenance["independent_verdicts"]["mathematics"].startswith("R3_APPROVED_AT_0A24EEA")
    assert provenance["independent_verdicts"]["muse_accessibility_and_assessment"] == "PENDING"
    assert provenance["independent_verdicts"]["deployment"] == "NOT_DEPLOYED"


def test_reuse_audit_and_non_overlap_are_machine_readable() -> None:
    provenance = _load("provenance.json")
    reuse = provenance["reuse_audit"]

    assert reuse["source_package"]["pull_request"] == 327
    assert reuse["source_package"]["pinned_head_sha"] == (
        "5d4e613b4aa241384809e048c60ee082e6f14fe4"
    )
    assert reuse["generator"]["family"] == "MATH.GEO.VOLUME.PRISM"
    assert reuse["visualization"]["fractional_interaction_status"] == "NOT_IMPLEMENTED_OR_WIRED"
    assert "Signed integers remain in PR #328" in reuse["non_overlap"]
    matrix = provenance["existing_work_gap_improvement_verification"]
    assert set(matrix) == {"existing_work", "actual_gap", "improvement", "verification"}
    assert all(matrix.values())


def test_package_has_full_mihur_sequence_and_cvs_progression() -> None:
    package = _load("package.json")

    assert [stage["phase"] for stage in package["learning_sequence"]] == PHASES
    representations = {
        representation
        for stage in package["learning_sequence"]
        for representation in stage["representations"]
    }
    assert representations == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["implementation"] == "DRAFT_EXECUTABLE_CONTENT_NOT_WIRED"


def test_assessment_and_accessibility_contracts_are_isolated() -> None:
    package = _load("package.json")
    assessment = package["independent_assessment_contract"]
    accessibility = package["accessibility_and_mve"]

    assert assessment["fresh_seed_required"] is True
    assert len(assessment["required_evidence"]) == 7
    assert assessment["hints_allowed"] is False
    assert assessment["guided_mve_visible"] is False
    assert assessment["partition_cell_counts_visible"] is False
    assert assessment["worked_steps_visible"] is False
    assert assessment["answer_in_public_payload"] is False
    assert assessment["guided_practice_credit"] is False
    assert assessment["historical_mastery_mutation"] is False
    assert assessment["backend_status"] == "NOT_IMPLEMENTED"
    assert accessibility["interactive_fractional_prism_status"] == "REQUIREMENT_ONLY_NOT_IMPLEMENTED_OR_WIRED"
    assert accessibility["keyboard_requirements"]
    assert accessibility["screen_reader_equivalence"]
    assert accessibility["reduced_motion"]
    assert accessibility["no_visual_answer_leakage"] is True


def test_seeded_replay_mode_separation_and_all_structures() -> None:
    variants = _variants()
    guided_structures = set()
    independent_structures = set()

    for seed in range(250):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided == variants.generate(seed, "guided")
        assert independent == variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert (guided.structure, guided.prompt) != (independent.structure, independent.prompt)
        guided_structures.add(guided.structure)
        independent_structures.add(independent.structure)

    assert guided_structures == set(variants.STRUCTURES)
    assert independent_structures == set(variants.STRUCTURES)


def test_public_payload_never_discloses_answer_or_guidance() -> None:
    variants = _variants()

    for seed in range(250):
        payload = variants.generate(seed, "independent").public_payload()
        assert set(payload) == {
            "variant_id",
            "mode",
            "structure",
            "context",
            "prompt",
            "response_fields",
        }
        keys = " ".join(payload).lower()
        assert "answer" not in keys
        assert "hint" not in keys
        assert "worked" not in keys
        assert len(payload["response_fields"]) == 7


def test_volume_and_inverse_oracles_are_independently_exact() -> None:
    variants = _variants()

    for seed in range(500):
        item = variants.generate(seed, "independent")
        expected_base = item.length * item.width
        expected_volume = item.length * item.width * item.height
        assert item.base_area == expected_base
        assert item.volume == expected_volume
        if item.target == "volume":
            assert item.exact_answer == expected_volume
            assert item.expected_operation == "MULTIPLY_THREE_EDGES"
            assert item.expected_unit_power == 3
        else:
            assert expected_base != 0
            assert item.exact_answer == expected_volume / expected_base == item.height
            assert item.expected_operation == "DIVIDE_VOLUME_BY_BASE_AREA"
            assert item.expected_unit_power == 1
        assert item.expected_unit_family in {"unit", "cm", "m", "dm"}


def test_mixed_edge_prediction_compares_like_volumes_at_fixed_reference_height() -> None:
    variants = _variants()

    for seed in range(250):
        item = variants.generate(seed, "independent")
        if item.structure != "MIXED_EDGE_VOLUME":
            continue
        reference_volume = item.base_area * 1
        assert item.height > 1
        assert item.volume > reference_volume
        assert "reference prism" in item.prompt
        assert "height 1 cm" in item.prompt
        assert "greater or less than the base area" not in item.prompt


def test_fractional_cell_model_repeats_partitions_across_whole_unit_cubes() -> None:
    variants = _variants()

    for seed in range(250):
        item = variants.generate(seed, "guided")
        if item.structure != "PACK_FRACTIONAL_CELLS":
            continue
        assert item.width.denominator == 1 and item.width >= 2
        assert f"Arrange {item.width.numerator} unit cubes in a row" in item.prompt
        assert "In every cube" in item.prompt
        assert "full row and layers" in item.prompt


def test_decomposition_matches_direct_product() -> None:
    variants = _variants()
    observed = 0

    for seed in range(500):
        item = variants.generate(seed, "independent")
        if item.structure != "DECOMPOSE_MIXED_EDGE":
            continue
        assert item.decomposition is not None
        whole, fractional = item.decomposition
        assert whole + fractional == item.length
        partial_sum = whole * item.width * item.height + fractional * item.width * item.height
        assert partial_sum == item.volume
        observed += 1

    assert observed == 100


def test_unseen_transfer_alternates_direct_and_inverse_operation_selection() -> None:
    variants = _variants()
    targets = set()

    for seed in range(500):
        item = variants.generate(seed, "independent")
        if item.structure != "TRANSFER_MOLD_PLAN":
            continue
        targets.add(item.target)
        assert "Decide what operation" in item.prompt
        assert item.context == "unfamiliar mold planning"

    assert targets == {"volume", "height"}


def test_all_seven_misconception_routes_are_response_specific() -> None:
    variants = _variants()
    package = _load("package.json")
    codes = {path["code"] for path in package["misconception_pathways"]}
    assert codes == {
        "AREA_AS_VOLUME",
        "ADDED_EDGE_LENGTHS",
        "IGNORED_FRACTIONAL_EDGE",
        "UNIT_DIMENSION_ERROR",
        "OPERATION_SELECTION_ERROR",
        "MULTIPLIED_INSTEAD_OF_DIVIDED",
        "SUBTRACTED_BASE_FROM_VOLUME",
    }
    assert len({path["observed_signature"] for path in package["misconception_pathways"]}) == 7
    assert all(path["socratic_probe"] for path in package["misconception_pathways"])
    assert all(path["repair"] for path in package["misconception_pathways"])
    assert all(path["exit_check"] for path in package["misconception_pathways"])
    assert all(path["fade_when"] for path in package["misconception_pathways"])

    volume = next(
        item
        for seed in range(30)
        if (item := variants.generate(seed, "guided")).target == "volume"
        and item.base_area != item.length + item.width + item.height
    )
    inverse = next(
        item
        for seed in range(30)
        if (item := variants.generate(seed, "guided")).target == "height"
    )
    assert variants.diagnose_response(volume, "DIVIDE_VOLUME_BY_BASE_AREA", volume.volume, volume.expected_unit_family, 3) == (
        "OPERATION_SELECTION_ERROR"
    )
    assert variants.diagnose_response(volume, volume.expected_operation, volume.volume, volume.expected_unit_family, 2) == (
        "UNIT_DIMENSION_ERROR"
    )
    assert variants.diagnose_response(volume, volume.expected_operation, volume.volume, "wrong-unit", 3) == (
        "UNIT_DIMENSION_ERROR"
    )
    assert variants.diagnose_response(volume, volume.expected_operation, volume.base_area, volume.expected_unit_family, 3) == "AREA_AS_VOLUME"
    assert variants.diagnose_response(
        volume,
        volume.expected_operation,
        volume.length + volume.width + volume.height,
        volume.expected_unit_family,
        3,
    ) == "ADDED_EDGE_LENGTHS"
    truncated = Fraction(int(volume.length) * int(volume.width) * int(volume.height))
    if truncated != volume.volume:
        assert variants.diagnose_response(volume, volume.expected_operation, truncated, volume.expected_unit_family, 3) == (
            "IGNORED_FRACTIONAL_EDGE"
        )
    assert variants.diagnose_response(
        inverse,
        inverse.expected_operation,
        inverse.volume * inverse.base_area,
        inverse.expected_unit_family,
        1,
    ) == "MULTIPLIED_INSTEAD_OF_DIVIDED"
    assert variants.diagnose_response(
        inverse,
        inverse.expected_operation,
        inverse.volume - inverse.base_area,
        inverse.expected_unit_family,
        1,
    ) == "SUBTRACTED_BASE_FROM_VOLUME"
    assert variants.diagnose_response(
        inverse,
        inverse.expected_operation,
        inverse.exact_answer,
        inverse.expected_unit_family,
        inverse.expected_unit_power,
    ) == "CORRECT_PRACTICE_ONLY"


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _variants().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "INDEPENDENT", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _variants().generate(4, mode)


def test_invalid_diagnostic_values_fail_closed() -> None:
    variants = _variants()
    item = variants.generate(4, "guided")

    with pytest.raises(TypeError, match="PrismVariant"):
        variants.diagnose_response({}, item.expected_operation, item.exact_answer, "unit", 3)
    with pytest.raises(TypeError, match="operation"):
        variants.diagnose_response(item, None, item.exact_answer, "unit", 3)
    with pytest.raises(TypeError, match="exact_answer"):
        variants.diagnose_response(item, item.expected_operation, True, "unit", 3)
    with pytest.raises(TypeError, match="unit_family"):
        variants.diagnose_response(item, item.expected_operation, item.exact_answer, None, 3)
    with pytest.raises(TypeError, match="unit_power"):
        variants.diagnose_response(item, item.expected_operation, item.exact_answer, "unit", False)
    with pytest.raises(ValueError, match="1, 2, or 3"):
        variants.diagnose_response(item, item.expected_operation, item.exact_answer, "unit", 0)


def test_complete_seven_field_guided_evidence_is_practice_only() -> None:
    variants = _variants()

    for seed in range(250):
        guided = variants.generate(seed, "guided")
        evidence = guided.teacher_evidence()
        assert set(evidence) == set(guided.public_payload()["response_fields"])
        assert variants.diagnose_reasoning_evidence(guided, evidence) == (
            "CORRECT_STRUCTURED_PRACTICE_ONLY_MODEL_EVIDENCE_CAPTURED"
        )
        independent = variants.generate(seed, "independent")
        assert variants.diagnose_reasoning_evidence(
            independent, independent.teacher_evidence()
        ) == "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"


def test_correct_answer_cannot_hide_wrong_model_reasoning_or_reconstruction() -> None:
    variants = _variants()
    by_structure = {
        item.structure: item
        for seed in range(50)
        if (item := variants.generate(seed, "guided"))
    }

    for item in by_structure.values():
        evidence = item.teacher_evidence()

        wrong_base = dict(evidence)
        wrong_base["base_area_or_layer_size"] = item.base_area + 1
        assert variants.diagnose_reasoning_evidence(item, wrong_base) == (
            "BASE_LAYER_MODEL_ERROR"
        )

        wrong_equation = dict(evidence)
        wrong_equation["equation"] = {"relation": "L+W+H=V"}
        assert variants.diagnose_reasoning_evidence(item, wrong_equation) == (
            "EQUATION_RECONSTRUCTION_ERROR"
        )

        wrong_check = dict(evidence)
        wrong_check["check_or_explanation"] = {"relation": "UNVERIFIED"}
        assert variants.diagnose_reasoning_evidence(item, wrong_check) == (
            "CHECK_OR_EXPLANATION_NOT_ESTABLISHED"
        )

    expected_reasoning_errors = {
        "PACK_FRACTIONAL_CELLS": "FRACTIONAL_CELL_REPETITION_NOT_ESTABLISHED",
        "MIXED_EDGE_VOLUME": "REFERENCE_VOLUME_COMPARISON_NOT_ESTABLISHED",
        "MISSING_HEIGHT": "LAYER_RELATION_NOT_ESTABLISHED",
        "DECOMPOSE_MIXED_EDGE": "DECOMPOSITION_MODEL_NOT_ESTABLISHED",
        "TRANSFER_MOLD_PLAN": "LAYER_RELATION_NOT_ESTABLISHED",
    }
    for structure, item in by_structure.items():
        wrong_reasoning = dict(item.teacher_evidence())
        wrong_reasoning["layer_reasoning"] = "GENERIC_VOLUME_RULE"
        assert variants.diagnose_reasoning_evidence(item, wrong_reasoning) == (
            expected_reasoning_errors[structure]
        )


def test_teacher_model_evidence_is_not_in_public_payload() -> None:
    variants = _variants()

    for seed in range(100):
        item = variants.generate(seed, "independent")
        public = item.public_payload()
        assert "teacher_evidence" not in public
        assert "base_area" not in public
        assert "volume" not in public
        assert "expected_operation" not in public
        assert "exact_answer" not in public


def test_invalid_structured_reasoning_evidence_fails_closed() -> None:
    variants = _variants()
    item = variants.generate(5, "guided")

    assert variants.diagnose_reasoning_evidence(item, {}) == (
        "INCOMPLETE_REASONING_EVIDENCE"
    )
    invalid = dict(item.teacher_evidence())
    invalid["unit_and_power"] = {"family": item.expected_unit_family}
    assert variants.diagnose_reasoning_evidence(item, invalid) == (
        "UNIT_DIMENSION_ERROR"
    )
    invalid = dict(item.teacher_evidence())
    invalid["base_area_or_layer_size"] = True
    assert variants.diagnose_reasoning_evidence(item, invalid) == (
        "BASE_LAYER_MODEL_ERROR"
    )


def test_draft_module_is_not_in_runtime_family_registry() -> None:
    from app.canonical_problem_families import FAMILIES

    assert "W1-G6-FRACTIONAL-PRISM-VOLUME" not in FAMILIES
    assert "middle-grades-fractional-prism-r2" not in str(FAMILIES)
