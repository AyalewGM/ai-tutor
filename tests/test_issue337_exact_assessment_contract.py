"""Backend contract evidence for the draft Issue #337 algebra milestone.

The contract stays unrouted and performs no persistence.  These regressions
prove exact hidden-oracle scoring and response validation while the content,
mathematics, API and QA gates remain independent.
"""

from __future__ import annotations

import inspect
from fractions import Fraction

import pytest

from app.services import draft_exact_algebra_assessment as contract


def _wire_fraction(value: Fraction | int) -> str:
    value = Fraction(value)
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _correct_wire_response(variant: contract.HiddenExactVariant) -> dict[str, object]:
    oracle = variant.oracle
    if variant.kind in {
        contract.ExactAlgebraKind.LINEAR_EQUATION,
        contract.ExactAlgebraKind.ROOT_EQUATION,
    }:
        return {
            "classification": oracle["classification"],
            "solutions": [_wire_fraction(value) for value in oracle["solutions"]],
            "substitution_check": oracle["substitution_check"],
        }
    if variant.kind == contract.ExactAlgebraKind.MONOMIAL_QUOTIENT:
        return {
            "coefficient": _wire_fraction(oracle["coefficient"]),
            "x_exponent": oracle["x_exponent"],
            "y_exponent": oracle["y_exponent"],
            "domain_restrictions": list(oracle["domain_restrictions"]),
        }
    if variant.kind == contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT:
        return {
            "terms": [
                {
                    "coefficient": _wire_fraction(coefficient),
                    "x_exponent": x_exponent,
                    "y_exponent": y_exponent,
                }
                for coefficient, x_exponent, y_exponent in oracle["terms"]
            ],
            "domain_restrictions": list(oracle["domain_restrictions"]),
        }
    if variant.kind == contract.ExactAlgebraKind.EXPONENT_LAWS:
        return {
            "result_exponent": oracle["result_exponent"],
            "exact_value": _wire_fraction(oracle["exact_value"]),
        }
    if variant.kind == contract.ExactAlgebraKind.SCIENTIFIC_NOTATION:
        return {
            "normalized_coefficient": _wire_fraction(oracle["normalized_coefficient"]),
            "power_of_ten": oracle["power_of_ten"],
            "ordinary_value": _wire_fraction(oracle["ordinary_value"]),
        }
    return {
        "result_coefficient": oracle["result_coefficient"],
        "result_exponent": oracle["result_exponent"],
        "exact_value": oracle["exact_value"],
        "units": oracle["units"],
    }


def test_contract_is_explicitly_unrouted_and_has_no_persistence_dependency() -> None:
    assert contract.DRAFT_RUNTIME_ACTIVATION is False
    source = inspect.getsource(contract)
    assert "APIRouter" not in source
    assert "Session" not in source
    assert "Attempt" not in source
    assert "DiagnosticAttempt" not in source
    assert "MasteryEvent" not in source


@pytest.mark.parametrize("kind", list(contract.ExactAlgebraKind))
def test_seeded_variants_replay_and_public_payload_never_discloses_oracle(
    kind: contract.ExactAlgebraKind,
) -> None:
    first = contract.generate_hidden_variant(kind, 17)
    replay = contract.generate_hidden_variant(kind, 17)
    distinct = contract.generate_hidden_variant(kind, 18)

    assert first == replay
    assert first.variant_id != distinct.variant_id
    payload = first.public_payload()
    assert set(payload) == {
        "contract_version",
        "variant_id",
        "kind",
        "prompt",
        "response_fields",
        "assessment_mode",
    }
    assert payload["assessment_mode"] == "INDEPENDENT"
    assert "oracle" not in payload
    assert "parameters" not in payload
    assert "seed" not in payload
    assert "hints" not in payload


@pytest.mark.parametrize("kind", list(contract.ExactAlgebraKind))
def test_every_kind_accepts_exact_oracle_response_as_unassisted(
    kind: contract.ExactAlgebraKind,
) -> None:
    for seed in range(12):
        variant = contract.generate_hidden_variant(kind, seed)
        score = contract.score_exact_response(variant, _correct_wire_response(variant))
        assert score == contract.ExactScore(
            is_correct=True,
            misconception_code=None,
            assistance_level=0,
        )


def test_linear_equation_oracle_is_independently_verified_by_substitution() -> None:
    for seed in range(100):
        variant = contract.generate_hidden_variant(
            contract.ExactAlgebraKind.LINEAR_EQUATION,
            seed,
        )
        parameters = variant.parameters
        solution = variant.oracle["solutions"][0]
        left = parameters["left_coefficient"] * solution + parameters["left_constant"]
        right = parameters["right_coefficient"] * solution + parameters["right_constant"]
        assert left == right
        assert parameters["left_coefficient"] != parameters["right_coefficient"]


def test_root_oracle_is_complete_or_correctly_reports_no_real_solutions() -> None:
    observed: set[str] = set()
    for seed in range(100):
        variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.ROOT_EQUATION, seed)
        parameters = variant.parameters
        classification = variant.oracle["classification"]
        observed.add(classification)
        solutions = variant.oracle["solutions"]
        if parameters["radicand"] < 0:
            assert classification == "NO_REAL_SOLUTIONS"
            assert solutions == ()
        else:
            assert classification == "TWO_REAL_SOLUTIONS"
            assert len(solutions) == 2
            assert all(
                (parameters["coefficient"] * value + parameters["shift"]) ** 2
                == parameters["radicand"]
                for value in solutions
            )
    assert observed == {"NO_REAL_SOLUTIONS", "TWO_REAL_SOLUTIONS"}


@pytest.mark.parametrize(
    ("kind", "term_count"),
    [
        (contract.ExactAlgebraKind.MONOMIAL_QUOTIENT, 1),
        (contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT, 2),
    ],
)
def test_quotient_oracle_round_trips_every_term_and_retains_domain(
    kind: contract.ExactAlgebraKind,
    term_count: int,
) -> None:
    for seed in range(100):
        variant = contract.generate_hidden_variant(kind, seed)
        divisor_coefficient, divisor_x, divisor_y = variant.parameters["divisor"]
        if term_count == 1:
            quotient_terms = (
                (
                    variant.oracle["coefficient"],
                    variant.oracle["x_exponent"],
                    variant.oracle["y_exponent"],
                ),
            )
        else:
            quotient_terms = variant.oracle["terms"]
        assert len(quotient_terms) == term_count
        for dividend, quotient in zip(
            variant.parameters["dividend_terms"],
            quotient_terms,
            strict=True,
        ):
            assert quotient[0] * divisor_coefficient == dividend[0]
            assert quotient[1] + divisor_x == dividend[1]
            assert quotient[2] + divisor_y == dividend[2]
        assert variant.oracle["domain_restrictions"] == ("x", "y")


def test_exponent_oracle_covers_negative_results_with_exact_reciprocals() -> None:
    negative_count = 0
    for seed in range(300):
        variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.EXPONENT_LAWS, seed)
        parameters = variant.parameters
        exponent = parameters["m"] + parameters["n"] - parameters["p"] * parameters["q"]
        expected = (
            Fraction(parameters["base"] ** exponent)
            if exponent >= 0
            else Fraction(1, parameters["base"] ** (-exponent))
        )
        assert variant.oracle["result_exponent"] == exponent
        assert variant.oracle["exact_value"] == expected
        negative_count += exponent < 0
    assert negative_count > 25


def test_scientific_oracle_is_normalized_and_value_preserving() -> None:
    operations: set[str] = set()
    for seed in range(200):
        variant = contract.generate_hidden_variant(
            contract.ExactAlgebraKind.SCIENTIFIC_NOTATION,
            seed,
        )
        coefficient = variant.oracle["normalized_coefficient"]
        exponent = variant.oracle["power_of_ten"]
        ordinary = variant.oracle["ordinary_value"]
        operations.add(variant.parameters["operation"])
        assert Fraction(1) <= abs(coefficient) < 10
        power = Fraction(10**exponent) if exponent >= 0 else Fraction(1, 10 ** (-exponent))
        assert coefficient * power == ordinary
    assert operations == {"TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE"}


def test_geometry_transfer_oracle_applies_dimensional_power_and_units() -> None:
    observed: set[str] = set()
    for seed in range(100):
        variant = contract.generate_hidden_variant(
            contract.ExactAlgebraKind.GEOMETRY_TRANSFER, seed
        )
        parameters = variant.parameters
        oracle = variant.oracle
        observed.add(parameters["shape"])
        assert oracle["result_coefficient"] == (
            parameters["coefficient"] ** parameters["dimensional_power"]
        )
        assert oracle["result_exponent"] == (
            parameters["exponent"] * parameters["dimensional_power"]
        )
        assert oracle["exact_value"] == (
            oracle["result_coefficient"] * parameters["base"] ** oracle["result_exponent"]
        )
        expected_units = "square units" if parameters["shape"] == "SQUARE" else "cubic units"
        assert oracle["units"] == expected_units
    assert observed == {"SQUARE", "CUBE"}


def test_duplicate_scoring_fails_closed_without_mutating_the_hidden_variant() -> None:
    variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.LINEAR_EQUATION, 9)
    snapshot = variant
    with pytest.raises(ValueError, match="already answered"):
        contract.score_exact_response(
            variant,
            _correct_wire_response(variant),
            already_answered=True,
        )
    assert variant == snapshot


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "3", None])
def test_invalid_seeds_are_rejected(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        contract.generate_hidden_variant(contract.ExactAlgebraKind.EXPONENT_LAWS, seed)


def test_invalid_values_and_unexpected_fields_are_rejected() -> None:
    scientific = contract.generate_hidden_variant(
        contract.ExactAlgebraKind.SCIENTIFIC_NOTATION,
        4,
    )
    bad = _correct_wire_response(scientific)
    bad["normalized_coefficient"] = "10"
    with pytest.raises(ValueError, match="normalized"):
        contract.score_exact_response(scientific, bad)

    exponent = contract.generate_hidden_variant(contract.ExactAlgebraKind.EXPONENT_LAWS, 2)
    unexpected = _correct_wire_response(exponent)
    unexpected["hint_used"] = False
    with pytest.raises(ValueError, match="fields"):
        contract.score_exact_response(exponent, unexpected)

    monomial = contract.generate_hidden_variant(contract.ExactAlgebraKind.MONOMIAL_QUOTIENT, 7)
    invalid_denominator = _correct_wire_response(monomial)
    invalid_denominator["coefficient"] = "3/0"
    with pytest.raises(ValueError, match="exact number"):
        contract.score_exact_response(monomial, invalid_denominator)


def test_known_misconceptions_are_classified_without_returning_hints() -> None:
    found = set()
    for kind in (
        contract.ExactAlgebraKind.LINEAR_EQUATION,
        contract.ExactAlgebraKind.ROOT_EQUATION,
        contract.ExactAlgebraKind.EXPONENT_LAWS,
        contract.ExactAlgebraKind.GEOMETRY_TRANSFER,
    ):
        for seed in range(50):
            variant = contract.generate_hidden_variant(kind, seed)
            for code, response in variant.misconception_responses.items():
                wire = _correct_wire_response(variant)
                if kind in {
                    contract.ExactAlgebraKind.LINEAR_EQUATION,
                    contract.ExactAlgebraKind.ROOT_EQUATION,
                }:
                    wire = {
                        "classification": response["classification"],
                        "solutions": [_wire_fraction(value) for value in response["solutions"]],
                        "substitution_check": response["substitution_check"],
                    }
                elif kind == contract.ExactAlgebraKind.EXPONENT_LAWS:
                    wire = {
                        "result_exponent": response["result_exponent"],
                        "exact_value": _wire_fraction(response["exact_value"]),
                    }
                elif kind == contract.ExactAlgebraKind.GEOMETRY_TRANSFER:
                    wire = dict(response)
                score = contract.score_exact_response(variant, wire)
                assert score.is_correct is False
                assert score.misconception_code == code
                assert set(vars(score)) == {
                    "is_correct",
                    "misconception_code",
                    "assistance_level",
                }
                found.add(code)
    assert found == {
        "EQ.SIGN.MOVE_WITHOUT_BALANCE",
        "ROOT.PRINCIPAL_ONLY",
        "EXP.NEGATIVE_IS_NEGATIVE_VALUE",
        "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED",
    }
