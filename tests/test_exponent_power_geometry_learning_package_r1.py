from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    ROOT
    / "docs"
    / "curriculum"
    / "drafts"
    / "exponent-power-geometry-learning-package-r1"
)
GENERATOR = (
    ROOT
    / "docs"
    / "curriculum"
    / "drafts"
    / "ontario-algebra-family-generators-r1"
    / "seeded_family_extensions.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _flow():
    return _load_module("exponent_power_geometry_learning_flow", PACKAGE / "learning_flow.py")


def _generators():
    return _load_module("exponent_power_geometry_source_generators", GENERATOR)


def _json(name: str) -> dict:
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def test_package_and_provenance_remain_complete_and_fail_closed() -> None:
    package = _json("package.json")
    provenance = _json("provenance.json")

    assert package["status"] == provenance["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is provenance["runtime_activation"] is False
    assert package["canonical_family"] == provenance["canonical"]["family"]
    assert provenance["canonical"]["new_identity"] is False
    assert provenance["canonical"]["build_once_map_many"] is True
    assert provenance["canonical"]["jurisdiction_specific_identity"] is False
    assert provenance["standards"]["official_source_url"].startswith("UNKNOWN")
    assert provenance["standards"]["exact_expectation_ids"] == []
    assert provenance["standards"]["coverage_credit"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["attempt_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["delivery_status"]["wired"] is False
    assert provenance["delivery_status"]["independently_accepted"] is False
    assert provenance["delivery_status"]["deployed"] is False


def test_full_mihur_and_concrete_visual_symbolic_progression_is_authored() -> None:
    package = _json("package.json")
    flow = _flow()
    sequence = package["learning_sequence"]

    assert tuple(stage["phase"] for stage in sequence) == flow.PHASES
    representations = {
        representation
        for stage in sequence
        for representation in stage["representations"]
    }
    assert any("CONCRETE" in value for value in representations)
    assert any("VISUAL" in value for value in representations)
    assert "SYMBOLIC" in representations
    assert package["independent_assessment_contract"]["mastery_credit"] is False
    assert package["independent_assessment_contract"]["guided_mve_visible"] is False
    assert package["accessible_mve_requirements"]["independent_mode_scaffolds"] is False


def test_package_variants_are_deterministic_exact_diverse_and_mode_separated() -> None:
    flow = _flow()
    seen = set()

    for mode in ("guided", "independent"):
        for index in range(700):
            item = flow.generate_package_variant(index, mode)
            assert item == flow.generate_package_variant(index, mode)
            assert flow.verify_oracle(item) is True
            seen.add(item.kind)
            public = item.public_payload()
            assert "teacher_oracle" not in public
            assert "parameters" not in public
            assert "variant_id" not in public
            assert "seed" not in public
            assert public["mastery_credit"] is False
            assert public["guided_feedback_available"] is (mode == "guided")

    assert seen == set(flow.KINDS)
    for index in range(100):
        guided = flow.generate_package_variant(index, "guided")
        independent = flow.generate_package_variant(index, "independent")
        assert guided.variant_id != independent.variant_id
        assert guided.prompt != independent.prompt
        assert guided.teacher_oracle != {} and independent.teacher_oracle != {}


def test_exact_power_product_quotient_and_requested_base_oracles() -> None:
    flow = _flow()

    for index in range(0, 350, 7):
        item = flow.generate_package_variant(index, "independent")
        p, o = item.parameters, item.teacher_oracle
        assert item.kind == "POWER_OF_PRODUCT"
        assert o["coefficient"] == p["coefficient"] ** p["outer_power"]
        assert o["x_exponent"] == p["base_exponent"] * p["outer_power"]

    for index in range(1, 351, 7):
        item = flow.generate_package_variant(index, "independent")
        p, o = item.parameters, item.teacher_oracle
        assert item.kind == "POWER_OF_QUOTIENT"
        assert o["coefficient"] == Fraction(
            p["numerator"] ** p["outer_power"],
            p["denominator"] ** p["outer_power"],
        )
        assert o["domain_restrictions"] == ("y != 0",)

    for index in range(2, 352, 7):
        item = flow.generate_package_variant(index, "independent")
        p, o = item.parameters, item.teacher_oracle
        assert item.kind == "REWRITE_TO_REQUESTED_BASE"
        assert p["displayed_base"] == p["requested_base"] ** p["base_power"]
        assert o["result_exponent"] == p["base_power"] * p["displayed_exponent"]


def test_comparison_covers_equal_and_both_inequality_directions_without_large_values() -> None:
    flow = _flow()
    observed = set()

    for index in range(3, 1403, 7):
        item = flow.generate_package_variant(index, "independent")
        observed.add(item.teacher_oracle["relation"])
        assert "without evaluating" in item.prompt
        assert flow.verify_oracle(item)

    assert observed == {"EQUAL", "LEFT_GREATER", "RIGHT_GREATER"}


def test_geometry_transfer_preserves_dimensional_powers_units_and_area_identity() -> None:
    flow = _flow()

    for index in range(4, 704, 7):
        item = flow.generate_package_variant(index, "independent")
        p, o = item.parameters, item.teacher_oracle
        assert o["surface_coefficient"] == 6 * p["coefficient"] ** 2
        assert o["surface_exponent"] == 2 * p["exponent"]
        assert o["surface_units"] == "square units"
        assert o["volume_coefficient"] == p["coefficient"] ** 3
        assert o["volume_exponent"] == 3 * p["exponent"]
        assert o["volume_units"] == "cubic units"

    for index in range(5, 705, 7):
        item = flow.generate_package_variant(index, "independent")
        o = item.teacher_oracle
        assert o["leg_a_area_coefficient"] + o["leg_b_area_coefficient"] == o[
            "hypotenuse_area_coefficient"
        ]
        assert o["area_identity_verified"] is True
        assert o["units"] == "square units"


def test_simplify_then_substitute_covers_positive_zero_and_negative_exact_values() -> None:
    flow = _flow()
    observed = set()

    for index in range(6, 1406, 7):
        item = flow.generate_package_variant(index, "independent")
        exponent = item.teacher_oracle["result_exponent"]
        observed.add("negative" if exponent < 0 else "zero" if exponent == 0 else "positive")
        assert item.teacher_oracle["exact_value"] == flow._pow_fraction(
            item.parameters["substitution"], exponent
        )
        assert item.teacher_oracle["base_nonzero_required"] is True

    assert observed == {"positive", "zero", "negative"}


def test_accepted_combined_and_geometry_generators_are_reused_without_math_changes() -> None:
    flow = _flow()
    generators = _generators()

    for seed in range(2, 1002, 5):
        item = generators.generate(seed, "independent")
        adapted = flow.adapt_accepted_combined(item)
        assert adapted["prompt"] == item.prompt
        assert adapted["response_fields"] == list(item.response_schema)
        assert adapted["teacher_oracle_hidden"] is True
        assert adapted["mastery_credit"] is False

    for seed in range(200):
        item = generators.generate_geometry_transfer(seed, "independent")
        adapted = flow.adapt_accepted_geometry(item)
        assert adapted["prompt"] == item.prompt
        assert adapted["response_fields"] == list(item.response_schema)
        assert adapted["teacher_oracle_hidden"] is True


def test_every_diagnosis_has_a_unique_socratic_path_and_targeted_fresh_exit() -> None:
    package = _json("package.json")
    flow = _flow()
    authored = {row["misconception_id"] for row in package["diagnostic_router"]}

    assert authored == set(flow.SOCRATIC_PATHS)
    assert set(flow.EVIDENCE_TO_MISCONCEPTION.values()) == authored
    assert len({tuple(value) for value in flow.SOCRATIC_PATHS.values()}) == len(authored)

    for misconception in authored:
        for index in range(20):
            public = flow.fresh_exit(misconception, index)
            assert public["kind"] == flow._REPAIR_KINDS[misconception]
            assert "teacher_oracle" not in public
            assert "parameters" not in public
            assert public["mastery_credit"] is False
            if misconception == "EXP.ZERO_WRITTEN_AS_ZERO":
                candidate_index = next(
                    candidate
                    for candidate in range(5000)
                    if flow.generate_package_variant(candidate, "guided").public_payload()[
                        "task_id"
                    ]
                    == public["task_id"]
                )
                assert flow.generate_package_variant(
                    candidate_index, "guided"
                ).teacher_oracle["result_exponent"] == 0
            if misconception == "EXP.NEGATIVE_IS_NEGATIVE_VALUE":
                candidate_index = next(
                    candidate
                    for candidate in range(5000)
                    if flow.generate_package_variant(candidate, "guided").public_payload()[
                        "task_id"
                    ]
                    == public["task_id"]
                )
                assert flow.generate_package_variant(
                    candidate_index, "guided"
                ).teacher_oracle["result_exponent"] < 0


def test_guided_diagnosis_is_specific_and_independent_feedback_fails_closed() -> None:
    flow = _flow()
    guided = flow.generate_package_variant(0, "guided")
    independent = flow.generate_package_variant(0, "independent")

    correct = flow.evaluate_guided_evidence(guided, {"response_correct": True})
    assert correct == {
        "correct": True,
        "misconception_id": None,
        "socratic_questions": [],
    }
    for field, misconception in flow.EVIDENCE_TO_MISCONCEPTION.items():
        result = flow.evaluate_guided_evidence(guided, {field: True})
        assert result["misconception_id"] == misconception
        assert result["socratic_questions"] == list(flow.SOCRATIC_PATHS[misconception])
        assert result["mastery_credit"] is False

    with pytest.raises(PermissionError, match="independent"):
        flow.evaluate_guided_evidence(independent, {"response_correct": False})
    with pytest.raises(ValueError, match="exactly one"):
        flow.evaluate_guided_evidence(guided, {"response_correct": False})
    with pytest.raises(ValueError, match="Unsupported evidence"):
        flow.evaluate_guided_evidence(guided, {"generic_wrong": True})
    with pytest.raises(TypeError, match="booleans"):
        flow.evaluate_guided_evidence(guided, {"response_correct": 1})


@pytest.mark.parametrize("index", [-1, True, False, 1.5, "2", None])
def test_invalid_indices_fail_closed(index: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _flow().generate_package_variant(index, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _flow().generate_package_variant(1, mode)


def test_package_is_not_registered_as_a_runtime_family() -> None:
    from app.canonical_problem_families import FAMILIES

    assert "EXPONENT-POWER-GEOMETRY-LEARNING-PACKAGE-R1" not in FAMILIES
    assert "exponent-power-geometry-learning-package-r1" not in str(FAMILIES)
