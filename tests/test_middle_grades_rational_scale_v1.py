import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "middle-grades-rational-scale-v1"
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


def load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text())


def load_variants_module():
    path = DRAFT / "seeded_variants.py"
    spec = importlib.util.spec_from_file_location("middle_grades_rational_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_and_fail_closed() -> None:
    provenance = load("provenance.v1.json")

    assert provenance["package_id"] == "MG-G7-RATIONAL-SCALE-INVERSE"
    assert provenance["revision"] == "middle-grades-rational-scale-v1-r4"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["standards"]["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["canonical"]["canonical_identity_change"] is False
    assert provenance["source_heads"] == {
        "main": "13f1cf7bfcdbaa73bb248319b1ece1be649e59df",
        "standards_pr_325": "c1fa26a560ebea022202bace38d51e91ca5d08fa",
        "learning_packages_pr_327": "5d4e613b4aa241384809e048c60ee082e6f14fe4",
        "learning_packages_pr_328": "2445f197259ff27b5c99dd2b45c4bcbc2e5292f8",
    }
    assert provenance["approvals"] == {
        "standards": "PENDING",
        "mathematics": "PENDING",
        "pedagogy": "R3_CHANGES_REQUIRED_R4_REVIEW_DEFERRED",
        "muse_accessibility_and_assessment": "PENDING",
        "engineering_integration": "NOT_REQUESTED",
        "release": "NOT_APPROVED",
    }


def test_package_has_full_phase_and_representation_progression() -> None:
    package = load("package.v1.json")
    sequence = package["learning_sequence"]

    assert [stage["phase"] for stage in sequence] == PHASES
    representations = {
        representation for stage in sequence for representation in stage["representations"]
    }
    assert representations == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["mastery_writes"] is False


def test_scope_does_not_claim_signed_integer_addition_or_other_owned_packages() -> None:
    provenance = load("provenance.v1.json")
    boundary = provenance["coverage"]["scope_boundary"]

    assert boundary["included"] == [
        "signed rational multiplication as direction and scale",
        "signed rational division as a missing scale factor",
        "inverse verification",
    ]
    assert "signed-integer addition or subtraction" in boundary["excluded"]
    assert "ratio or double-number-line instruction" in boundary["excluded"]
    assert provenance["canonical"]["reused_generators"] == ["MATH.RAT.MUL", "MATH.RAT.DIV"]


def test_misconception_paths_are_reasoning_specific() -> None:
    package = load("package.v1.json")
    pathways = package["misconception_pathways"]
    diagnostic = package["entry_diagnostic"]

    assert len(pathways) == 4
    assert len({path["id"] for path in pathways}) == 4
    assert len({path["diagnostic_probe"] for path in pathways}) == 4
    assert all(len(path["socratic_prompts"]) == 3 for path in pathways)
    assert all(path["observed_reasoning"] != path["repair"] for path in pathways)
    assert all(path["repair_task_id"] for path in pathways)
    assert all(path["follow_up_check"] for path in pathways)
    assert all(path["scaffold_fade_condition"] for path in pathways)
    assert set(diagnostic["routing_precedence"]) == {path["id"] for path in pathways}
    assert {route["misconception_id"] for route in diagnostic["routes"]} == {
        path["id"] for path in pathways
    }
    assert all(route["observable_response_pattern"] for route in diagnostic["routes"])
    assert all(route["selected_repair"] for route in diagnostic["routes"])
    assert all(route["follow_up_check"] for route in diagnostic["routes"])
    assert all(route["scaffold_fade_condition"] for route in diagnostic["routes"])


def test_authored_oracles_are_exact() -> None:
    package = load("package.v1.json")
    examples = {item["id"]: item["answer_teacher_only"] for item in package["guided_examples"]}

    assert Fraction(examples["guided-positive-shrink"]) == Fraction(-4, 3) * Fraction(1, 2)
    assert Fraction(examples["guided-double-negative"]) == Fraction(-3, 4) * Fraction(-2, 3)
    assert Fraction(examples["guided-missing-scale"]) * Fraction(3, 4) == Fraction(-3, 2)
    transfer = package["transfer_oracle_teacher_only"]
    direct = transfer["direct_record"]
    missing = transfer["missing_scale_record"]
    assert Fraction(direct["answer"]) == Fraction(-3, 2) * Fraction(-4, 5)
    assert Fraction(missing["answer"]) * Fraction(3, 4) == Fraction(-3, 2)
    assert direct["operation"] == "MULTIPLY"
    assert missing["operation"] == "DIVIDE_AS_MISSING_SCALE"


def test_seeded_variants_are_deterministic_and_use_exact_oracles() -> None:
    variants = load_variants_module()
    observed_structures = set()

    for mode in ("guided", "independent"):
        for seed in range(40):
            first = variants.generate(seed, mode)
            second = variants.generate(seed, mode)
            assert first == second
            observed_structures.add(first.structure)
            if first.hidden_quantity == "output":
                assert first.answer == first.input_value * first.given_value
                output = first.answer
            else:
                assert first.answer * first.input_value == first.given_value
                output = first.given_value
            assert first.direction == ("POSITIVE" if output > 0 else "NEGATIVE")
            expected_relation = (
                "GROWS"
                if abs(output) > abs(first.input_value)
                else "SHRINKS"
                if abs(output) < abs(first.input_value)
                else "SAME"
            )
            assert first.magnitude_relation == expected_relation
            assert set(first.teacher_oracle()) == set(variants.RESPONSE_FIELDS)

    assert observed_structures == {
        "DIRECT_NEGATIVE_GROW",
        "DIRECT_DOUBLE_NEGATIVE_SHRINK",
        "MISSING_SCALE_INVERT_DIVISOR",
        "MISSING_SCALE_POSITIVE_SHRINK",
    }


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "7", None])
def test_seeded_variants_reject_invalid_seed_values(seed: object) -> None:
    variants = load_variants_module()

    with pytest.raises((TypeError, ValueError)):
        variants.generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_seeded_variants_reject_invalid_modes(mode: object) -> None:
    variants = load_variants_module()

    with pytest.raises(ValueError, match="Unsupported mode"):
        variants.generate(7, mode)


def test_independent_namespace_and_payload_do_not_leak_answers_or_hints() -> None:
    variants = load_variants_module()
    package = load("package.v1.json")
    contract = package["independent_assessment_contract"]

    assert contract["hints_allowed"] is False
    assert contract["answer_in_client_payload"] is False
    assert contract["guided_practice_credit"] is False
    assert contract["historical_mastery_mutation"] is False
    for seed in contract["reserved_seeds"]:
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert (guided.input_value, guided.given_value) != (
            independent.input_value,
            independent.given_value,
        )
        payload = independent.public_payload()
        serialized = json.dumps(payload).lower()
        assert "answer" not in serialized
        assert "teacher_oracle" not in serialized
        assert "hint" not in serialized
        assert payload["response_fields"] == list(variants.RESPONSE_FIELDS)


def test_entry_diagnostic_routes_all_four_observed_error_patterns() -> None:
    variants = load_variants_module()
    double_negative = variants.generate(1, "guided")
    negative_grow = variants.generate(0, "guided")
    missing_scale = variants.generate(2, "guided")

    assert variants.diagnose_response(
        double_negative,
        {
            "output_direction_prediction": "NEGATIVE",
            "exact_result": str(-double_negative.answer),
        },
    ) == "ONE_NEGATIVE_MEANS_ALWAYS_NEGATIVE"
    assert variants.diagnose_response(
        negative_grow,
        {
            "output_direction_prediction": negative_grow.direction,
            "magnitude_relation": "SHRINKS",
            "exact_result": str(negative_grow.answer),
        },
    ) == "NEGATIVE_MEANS_SMALLER_MAGNITUDE"
    assert variants.diagnose_response(
        missing_scale,
        {
            "operation_choice": missing_scale.operation,
            "inverse_strategy": "DIVIDE_COMPONENTS_INDEPENDENTLY",
            "exact_result": str(missing_scale.answer + 1),
            "recomposition_check": "invalid",
        },
    ) == "DIVIDE_STRAIGHT_ACROSS"
    assert variants.diagnose_response(
        missing_scale,
        {
            "operation_choice": missing_scale.operation,
            "inverse_strategy": "MULTIPLY_INPUT_BY_RECIPROCAL_OF_OUTPUT",
            "exact_result": str(missing_scale.input_value / missing_scale.given_value),
            "recomposition_check": "invalid",
        },
    ) == "RECIPROCAL_WRONG_OPERAND"


def test_correct_diagnostic_response_has_explicit_success_without_mastery() -> None:
    variants = load_variants_module()
    variant = variants.generate(2, "guided")

    assert variants.diagnose_response(
        variant,
        variant.teacher_oracle(),
    ) == "CORRECT_NO_REMEDIATION"


def test_independent_contract_requires_reasoning_and_contrast_evidence() -> None:
    package = load("package.v1.json")
    contract = package["independent_assessment_contract"]

    assert contract["required_response_fields"] == package["entry_diagnostic"][
        "response_fields"
    ]
    assert contract["contrast_cases"] == [
        "MISSING_SCALE_INVERT_DIVISOR_NOT_COMPONENTWISE",
        "NEGATIVE_DIRECTION_WITH_GROWING_MAGNITUDE",
    ]
    assert contract["hints_allowed"] is False
    assert contract["guided_practice_credit"] is False


def test_accessibility_contract_has_nonvisual_state_and_recovery() -> None:
    accessibility = load("package.v1.json")["accessibility_contract"]

    assert accessibility["keyboard_only"]
    assert accessibility["screen_reader_state"]
    assert accessibility["nonvisual_equivalent"]
    assert accessibility["focus_recovery"]
    assert accessibility["reduced_motion"]
    assert accessibility["color_independence"] is True
    assert accessibility["independent_scaffolds"] is False


def test_incomplete_or_inconsistent_guided_evidence_never_passes() -> None:
    variants = load_variants_module()
    variant = variants.generate(2, "guided")
    oracle = variant.teacher_oracle()
    for field in variants.RESPONSE_FIELDS:
        incomplete = dict(oracle)
        del incomplete[field]
        assert variants.diagnose_response(variant, incomplete) != "CORRECT_NO_REMEDIATION"
    incorrect = dict(oracle)
    incorrect["recomposition_check"] = "incorrect recomposition"
    assert variants.diagnose_response(variant, incorrect) != "CORRECT_NO_REMEDIATION"
    incorrect = dict(oracle)
    incorrect["output_direction_prediction"] = "POSITIVE"
    assert variants.diagnose_response(variant, incorrect) != "CORRECT_NO_REMEDIATION"
    incorrect = dict(oracle)
    incorrect["exact_result"] = True
    assert variants.diagnose_response(variant, incorrect) != "CORRECT_NO_REMEDIATION"


@pytest.mark.parametrize("seed", [2, 3, 6, 7])
def test_missing_scale_prompts_mean_output_direction_not_scale_sign(seed: int) -> None:
    variants = load_variants_module()
    variant = variants.generate(seed, "guided")
    assert variant.hidden_quantity == "scale"
    assert "output's direction" in variant.prompt
    assert "hidden scale's sign" in variant.prompt
    assert "output_direction_prediction" in variant.teacher_oracle()
    output = variant.given_value
    assert variant.teacher_oracle()["output_direction_prediction"] == (
        "POSITIVE" if output > 0 else "NEGATIVE"
    )
    if variant.structure == "MISSING_SCALE_POSITIVE_SHRINK":
        assert variant.answer > 0 and output < 0
        assert variant.teacher_oracle()["output_direction_prediction"] == "NEGATIVE"


def test_full_guided_correct_response_requires_all_fields() -> None:
    variants = load_variants_module()
    for seed in range(24):
        item = variants.generate(seed, "guided")
        assert variants.diagnose_response(item, item.teacher_oracle()) == "CORRECT_NO_REMEDIATION"
