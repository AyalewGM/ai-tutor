from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/curriculum/drafts/scientific-notation-learning-package-r1"
GENERATOR = ROOT / "docs/curriculum/drafts/ontario-algebra-family-generators-r1/seeded_family_extensions.py"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _flow():
    return _module(PACKAGE / "learning_flow.py", "scientific_notation_learning_flow")


def _generator():
    return _module(GENERATOR, "scientific_notation_source_generator")


def _exact(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _correct_response(flow, item) -> dict[str, object]:
    oracle = item.teacher_oracle
    operation = item.parameters["operation"]
    return {
        "normalized_coefficient": _exact(oracle["coefficient"]),
        "power_of_ten": oracle["exponent"],
        "exact_ordinary_value": _exact(oracle["ordinary_value"]),
        "normalization_explanation": flow.EXPLANATION_CODES[operation],
    }


def test_package_and_provenance_remain_fail_closed() -> None:
    package = json.loads((PACKAGE / "package.json").read_text())
    provenance = json.loads((PACKAGE / "provenance.json").read_text())

    assert package["status"] == provenance["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is provenance["runtime_activation"] is False
    assert package["canonical_family"] == provenance["canonical"]["family"]
    assert provenance["canonical"]["new_identity"] is False
    assert provenance["standards"]["mapping_status"] == "NONE_NOT_CLAIMED"
    assert provenance["learner_data_writes"] is False
    assert provenance["attempt_writes"] is False
    assert provenance["mastery_writes"] is False
    assert package["independent_assessment_contract"]["mastery_credit"] is False


def test_full_mihur_sequence_and_cvs_are_explicit() -> None:
    package = json.loads((PACKAGE / "package.json").read_text())
    phases = [step["phase"] for step in package["learning_sequence"]]
    representations = {
        representation
        for step in package["learning_sequence"]
        for representation in step["representations"]
    }

    assert phases == [
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    ]
    assert "CONCRETE_PLACE_VALUE" in representations
    assert "VISUAL_EXPONENT_SCALE" in representations
    assert "SYMBOLIC" in representations


def test_existing_generator_is_reused_with_mode_and_transfer_separation() -> None:
    flow = _flow()
    generators = _generator()

    for index in range(40):
        guided_seed = flow.scientific_seed(index)
        transfer_seed = flow.scientific_seed(index, transfer=True)
        assert guided_seed % 5 == transfer_seed % 5 == 4
        guided = generators.generate(guided_seed, "guided")
        independent = generators.generate(transfer_seed, "independent")
        assert guided.structure == independent.structure == "SCIENTIFIC_NOTATION"
        assert guided.variant_id != independent.variant_id
        assert guided.mode == "guided"
        assert independent.mode == "independent"


def test_independent_oracle_reconstruction_covers_all_operations_and_modes() -> None:
    flow = _flow()
    generators = _generator()
    operations = set()

    for mode in ("guided", "independent"):
        for index in range(200):
            item = generators.generate(flow.scientific_seed(index), mode)
            operations.add(item.parameters["operation"])
            assert flow.verify_teacher_oracle(item)

    assert operations == {"TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE"}


def test_guided_lesson_has_no_oracle_and_exact_only_boundary() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(3), "guided")

    lesson = flow.guided_lesson(item)
    assert "teacher_oracle" not in lesson
    assert lesson["exact_only"] is True
    assert lesson["rounded_response_policy"] == "PROVISIONAL_NOT_IMPLEMENTED"
    assert lesson["mastery_credit"] is False


def test_independent_payload_excludes_parameters_oracle_hints_and_worked_steps() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(9, transfer=True), "independent")

    public = flow.independent_public_task(item)
    assert "variant_id" not in public
    assert "parameters" not in public
    assert "teacher_oracle" not in public
    assert str(flow.scientific_seed(9, transfer=True)) not in public["task_id"]
    assert public["hints"] == []
    assert public["worked_steps"] == []
    assert public["guided_feedback_available"] is False
    assert public["mastery_credit"] is False


def test_guided_evaluator_accepts_all_exact_oracles() -> None:
    flow = _flow()
    generators = _generator()

    for index in range(80):
        item = generators.generate(flow.scientific_seed(index), "guided")
        result = flow.evaluate_guided_response(item, _correct_response(flow, item))
        assert result == {"correct": True, "misconception_id": None, "socratic_questions": []}


def test_guided_evaluator_routes_non_normalized_equivalent_form() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(0), "guided")
    oracle = item.teacher_oracle
    coefficient = oracle["coefficient"] * 10
    exponent = oracle["exponent"] - 1
    response = _correct_response(flow, item)
    response["normalized_coefficient"] = _exact(coefficient)
    response["power_of_ten"] = exponent

    result = flow.evaluate_guided_response(item, response)
    assert result["misconception_id"] == "SCI.NOT_NORMALIZED"
    assert len(result["socratic_questions"]) == 3


def test_guided_evaluator_routes_operation_specific_exponent_errors() -> None:
    flow = _flow()
    generators = _generator()
    observed = set()

    for index in range(200):
        item = generators.generate(flow.scientific_seed(index), "guided")
        operation = item.parameters["operation"]
        response = _correct_response(flow, item)
        if operation == "MULTIPLY":
            wrong_exponent = item.parameters["e1"] * item.parameters["e2"]
            if wrong_exponent == item.teacher_oracle["exponent"]:
                continue
            response["power_of_ten"] = wrong_exponent
            expected = "SCI.PRODUCT.EXPONENTS_MULTIPLIED"
        elif operation == "DIVIDE":
            wrong_exponent = item.parameters["e1"] + item.parameters["e2"]
            if wrong_exponent == item.teacher_oracle["exponent"]:
                continue
            response["power_of_ten"] = wrong_exponent
            expected = "SCI.QUOTIENT.EXPONENTS_ADDED"
        else:
            continue

        result = flow.evaluate_guided_response(item, response)
        assert result["misconception_id"] == expected
        assert len(result["socratic_questions"]) == 3
        observed.add(expected)
        if len(observed) == 2:
            break

    assert observed == {
        "SCI.PRODUCT.EXPONENTS_MULTIPLIED",
        "SCI.QUOTIENT.EXPONENTS_ADDED",
    }


def test_seed_9_wrong_exponent_with_internally_consistent_ordinary_value() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(9, "guided")
    oracle = item.teacher_oracle

    assert item.parameters["operation"] == "TO_ORDINARY"
    assert oracle == {
        "coefficient": Fraction(47, 5),
        "exponent": 6,
        "ordinary_value": Fraction(9_400_000),
    }

    wrong_exponent = 5
    response = _correct_response(flow, item)
    response["power_of_ten"] = wrong_exponent
    response["exact_ordinary_value"] = _exact(
        oracle["coefficient"] * flow._power_of_ten(wrong_exponent)
    )

    result = flow.evaluate_guided_response(item, response)
    assert result["misconception_id"] == "SCI.EXPONENT.DIRECTION"


def test_correct_coefficient_wrong_power_routes_to_exponent_for_every_operation() -> None:
    flow = _flow()
    generators = _generator()
    observed = set()

    for index in range(200):
        item = generators.generate(flow.scientific_seed(index), "guided")
        operation = item.parameters["operation"]
        if operation in observed:
            continue

        oracle = item.teacher_oracle
        wrong_exponent = oracle["exponent"] + 1
        operation_specific_errors = {
            "MULTIPLY": item.parameters["e1"] * item.parameters["e2"],
            "DIVIDE": item.parameters["e1"] + item.parameters["e2"],
        }
        if wrong_exponent == operation_specific_errors.get(operation):
            wrong_exponent += 1

        response = _correct_response(flow, item)
        response["power_of_ten"] = wrong_exponent
        response["exact_ordinary_value"] = _exact(
            oracle["coefficient"] * flow._power_of_ten(wrong_exponent)
        )

        result = flow.evaluate_guided_response(item, response)
        assert result["misconception_id"] == "SCI.EXPONENT.DIRECTION"
        observed.add(operation)
        if len(observed) == 4:
            break

    assert observed == {"TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE"}


@pytest.mark.parametrize(
    ("operation", "parameters", "oracle", "wrong_ordinary"),
    [
        (
            "DIVIDE",
            {"operation": "DIVIDE", "c1": Fraction(3), "e1": 2, "c2": Fraction(2), "e2": 0},
            {"coefficient": Fraction(3, 2), "exponent": 2, "ordinary_value": Fraction(150)},
            Fraction(100),
        ),
        (
            "MULTIPLY",
            {"operation": "MULTIPLY", "c1": Fraction(2), "e1": 2, "c2": Fraction(2), "e2": 2},
            {"coefficient": Fraction(4), "exponent": 4, "ordinary_value": Fraction(40000)},
            Fraction(4000),
        ),
    ],
)
def test_correct_exponent_with_wrong_value_does_not_invent_operation_error(
    operation, parameters, oracle, wrong_ordinary
) -> None:
    flow = _flow()
    generators = _generator()
    item = generators.DraftVariant(
        variant_id=f"review-collision:{operation.lower()}",
        mode="guided",
        structure="SCIENTIFIC_NOTATION",
        canonical_family="MATH.NS.SCIENTIFIC_NOTATION",
        prompt="Independent mathematical review collision regression.",
        response_schema=(
            "normalized_coefficient",
            "power_of_ten",
            "exact_ordinary_value",
            "normalization_explanation",
        ),
        parameters=parameters,
        teacher_oracle=oracle,
    )
    response = _correct_response(flow, item)
    response["exact_ordinary_value"] = _exact(wrong_ordinary)

    result = flow.evaluate_guided_response(item, response)
    assert result["misconception_id"] == "SCI.INEXACT.WHEN_EXACT_REQUIRED"


@pytest.mark.parametrize(("index", "operation"), [(35, "DIVIDE"), (58, "MULTIPLY")])
def test_generated_collision_boundaries_require_an_actually_wrong_exponent(index, operation) -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(index), "guided")
    oracle = item.teacher_oracle
    parameters = item.parameters

    assert parameters["operation"] == operation
    if operation == "DIVIDE":
        coincident_exponent = parameters["e1"] + parameters["e2"]
    else:
        coincident_exponent = parameters["e1"] * parameters["e2"]
    assert coincident_exponent == oracle["exponent"]

    response = _correct_response(flow, item)
    response["exact_ordinary_value"] = _exact(oracle["ordinary_value"] + 1)
    result = flow.evaluate_guided_response(item, response)
    assert result["misconception_id"] == "SCI.INEXACT.WHEN_EXACT_REQUIRED"


def test_coefficient_arithmetic_requires_an_actual_coefficient_error() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(4), "guided")
    oracle = item.teacher_oracle
    wrong_coefficient = oracle["coefficient"] + 1
    response = _correct_response(flow, item)
    response["normalized_coefficient"] = _exact(wrong_coefficient)
    response["exact_ordinary_value"] = _exact(
        wrong_coefficient * flow._power_of_ten(oracle["exponent"])
    )

    result = flow.evaluate_guided_response(item, response)
    assert result["misconception_id"] == "SCI.COEFFICIENT.ARITHMETIC"


def test_guided_feedback_is_unavailable_for_independent_variants() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(2, transfer=True), "independent")

    with pytest.raises(PermissionError, match="unavailable"):
        flow.evaluate_guided_response(item, _correct_response(flow, item))
    with pytest.raises(ValueError, match="guided variant"):
        flow.guided_lesson(item)


def test_exact_response_schema_rejects_float_and_zero_denominator() -> None:
    flow = _flow()
    generators = _generator()
    item = generators.generate(flow.scientific_seed(6), "guided")
    response = _correct_response(flow, item)
    response["normalized_coefficient"] = {"numerator": 1.2, "denominator": 1}
    with pytest.raises(TypeError, match="numerator"):
        flow.evaluate_guided_response(item, response)

    response = _correct_response(flow, item)
    response["exact_ordinary_value"] = {"numerator": 1, "denominator": 0}
    with pytest.raises(ValueError, match="nonzero"):
        flow.evaluate_guided_response(item, response)


def test_every_package_diagnostic_is_specific_and_has_fresh_exit() -> None:
    package = json.loads((PACKAGE / "package.json").read_text())
    paths = package["diagnostic_router"]

    assert {path["misconception_id"] for path in paths} == {
        "SCI.EXPONENT.DIRECTION",
        "SCI.NOT_NORMALIZED",
        "SCI.PRODUCT.EXPONENTS_MULTIPLIED",
        "SCI.QUOTIENT.EXPONENTS_ADDED",
        "SCI.COEFFICIENT.ARITHMETIC",
        "SCI.INEXACT.WHEN_EXACT_REQUIRED",
    }
    assert all(len(path["socratic_questions"]) == 3 for path in paths)
    assert len({tuple(path["socratic_questions"]) for path in paths}) == len(paths)
    assert all(path["fresh_exit"] for path in paths)


def test_invalid_seed_indices_fail_closed() -> None:
    flow = _flow()
    for invalid in (-1, True, 1.5, "2"):
        with pytest.raises(ValueError, match="non-negative integer"):
            flow.scientific_seed(invalid)
