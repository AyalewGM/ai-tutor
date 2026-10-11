"""Backend contract evidence for the draft Issue #337 algebra milestone.

The contract stays unrouted and performs no persistence.  These regressions
prove exact hidden-oracle scoring and response validation while the content,
mathematics, API and QA gates remain independent.
"""

from __future__ import annotations

import inspect
import math
from fractions import Fraction

import pytest

from app.services import draft_exact_algebra_assessment as contract


def _wire_fraction(value: Fraction | int) -> str:
    value = Fraction(value)
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _wire_exact_real(value: contract.ExactReal) -> dict[str, object]:
    return {
        "rational": _wire_fraction(value.rational),
        "radical_coefficient": _wire_fraction(value.radical_coefficient),
        "radicand": value.radicand,
    }


def _wire_term(value: tuple[Fraction, int, int]) -> dict[str, object]:
    coefficient, x_exponent, y_exponent = value
    return {
        "coefficient": _wire_fraction(coefficient),
        "x_exponent": x_exponent,
        "y_exponent": y_exponent,
    }


def _wire_reconstruction(
    value: tuple[
        tuple[Fraction, int, int],
        tuple[Fraction, int, int],
        tuple[Fraction, int, int],
    ],
) -> dict[str, object]:
    quotient, divisor, product = value
    return {
        "quotient_term": _wire_term(quotient),
        "divisor_term": _wire_term(divisor),
        "product_term": _wire_term(product),
    }


def _correct_wire_response(variant: contract.HiddenExactVariant) -> dict[str, object]:
    oracle = variant.oracle
    if variant.kind == contract.ExactAlgebraKind.LINEAR_EQUATION:
        return {
            "classification": oracle["classification"],
            "solutions": [_wire_fraction(value) for value in oracle["solutions"]],
            "substitution_checks": [
                {
                    "solution": _wire_fraction(solution),
                    "left_value": _wire_fraction(left_value),
                    "right_value": _wire_fraction(right_value),
                }
                for solution, left_value, right_value in oracle["substitution_checks"]
            ],
        }
    if variant.kind == contract.ExactAlgebraKind.ROOT_EQUATION:
        return {
            "classification": oracle["classification"],
            "solutions": [_wire_exact_real(value) for value in oracle["solutions"]],
            "substitution_checks": [
                {
                    "solution": _wire_exact_real(solution),
                    "left_value": _wire_exact_real(left_value),
                    "right_value": _wire_exact_real(right_value),
                }
                for solution, left_value, right_value in oracle["substitution_checks"]
            ],
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
            "terms": [_wire_term(term) for term in oracle["terms"]],
            "domain_restrictions": list(oracle["domain_restrictions"]),
            "coefficient_reason": oracle["coefficient_reason"],
            "exponent_reason": oracle["exponent_reason"],
            "reconstruction": [_wire_reconstruction(record) for record in oracle["reconstruction"]],
        }
    if variant.kind == contract.ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER:
        return {
            "width_terms": [_wire_term(term) for term in oracle["width_terms"]],
            "total_width_terms": [_wire_term(term) for term in oracle["total_width_terms"]],
            "domain_restrictions": list(oracle["domain_restrictions"]),
            "multiplication_checks": [
                _wire_reconstruction(record) for record in oracle["multiplication_checks"]
            ],
            "units": {"width": oracle["units"][0], "area": oracle["units"][1]},
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
        assert variant.oracle["substitution_checks"] == ((solution, left, right),)
        assert parameters["left_coefficient"] != parameters["right_coefficient"]


def test_equation_substitution_is_exact_evidence_not_a_client_truth_flag() -> None:
    variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.LINEAR_EQUATION, 11)
    response = _correct_wire_response(variant)
    assert "substitution_check" not in response
    response["substitution_checks"][0]["left_value"] = "999"
    assert contract.score_exact_response(variant, response).is_correct is False

    boolean_claim = _correct_wire_response(variant)
    boolean_claim["substitution_checks"] = True
    with pytest.raises(ValueError, match="substitution_checks"):
        contract.score_exact_response(variant, boolean_claim)


def test_root_oracle_is_complete_or_correctly_reports_no_real_solutions() -> None:
    observed: set[str] = set()
    root_outcomes: set[str] = set()
    for seed in range(200):
        variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.ROOT_EQUATION, seed)
        parameters = variant.parameters
        classification = variant.oracle["classification"]
        observed.add(classification)
        root_outcomes.add(parameters["root_outcome"])
        solutions = variant.oracle["solutions"]
        if parameters["radicand"] < 0:
            assert classification == "NO_REAL_SOLUTIONS"
            assert solutions == ()
        elif parameters["radicand"] == 0:
            assert classification == "ONE_REAL_SOLUTION"
            assert solutions == (
                contract.ExactReal(Fraction(-parameters["shift"], parameters["coefficient"])),
            )
        else:
            assert classification == "TWO_REAL_SOLUTIONS"
            assert len(solutions) == 2
        for solution, left_value, right_value in variant.oracle["substitution_checks"]:
            affine_rational = (
                parameters["coefficient"] * solution.rational + parameters["shift"]
            )
            affine_radical = parameters["coefficient"] * solution.radical_coefficient
            independently_squared = contract.ExactReal(
                affine_rational**2 + affine_radical**2 * solution.radicand,
                2 * affine_rational * affine_radical,
                solution.radicand if affine_rational and affine_radical else 0,
            )
            assert left_value == independently_squared
            assert right_value == contract.ExactReal(Fraction(parameters["radicand"]))
            assert left_value == right_value
    assert observed == {
        "NO_REAL_SOLUTIONS",
        "ONE_REAL_SOLUTION",
        "TWO_REAL_SOLUTIONS",
    }
    assert root_outcomes == {
        "NEGATIVE",
        "ZERO",
        "POSITIVE_SQUARE",
        "POSITIVE_NONSQUARE",
    }


def test_principal_root_diagnostic_uses_positive_root_branch_for_negative_coefficients() -> None:
    checked = 0
    for seed in range(1, 200):
        variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.ROOT_EQUATION, seed)
        parameters = variant.parameters
        if parameters["radicand"] <= 0 or parameters["coefficient"] > 0:
            continue
        radicand = parameters["radicand"]
        square_root = math.isqrt(radicand)
        if square_root * square_root == radicand:
            expected = contract.ExactReal(
                Fraction(square_root - parameters["shift"], parameters["coefficient"])
            )
        else:
            expected = contract.ExactReal(
                Fraction(-parameters["shift"], parameters["coefficient"]),
                Fraction(1, parameters["coefficient"]),
                radicand,
            )
        alternative = variant.misconception_responses["ROOT.PRINCIPAL_ONLY"]
        assert alternative["solutions"] == (expected,)
        checked += 1
    assert checked > 10


def test_root_scoring_requires_canonical_exact_radicals() -> None:
    irrational = next(
        contract.generate_hidden_variant(contract.ExactAlgebraKind.ROOT_EQUATION, seed)
        for seed in range(100)
        if seed % 4 == 3
    )
    response = _correct_wire_response(irrational)
    response["solutions"][0]["radicand"] = 12
    with pytest.raises(ValueError, match="square-free"):
        contract.score_exact_response(irrational, response)

    zero = contract.generate_hidden_variant(contract.ExactAlgebraKind.ROOT_EQUATION, 1)
    zero_response = _correct_wire_response(zero)
    zero_response["solutions"][0]["radicand"] = 5
    with pytest.raises(ValueError, match="radicand zero"):
        contract.score_exact_response(zero, zero_response)


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


def test_polynomial_scoring_accepts_commuted_unlike_terms_and_rejects_duplicate_powers() -> None:
    variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT, 23)
    response = _correct_wire_response(variant)
    response["terms"].reverse()
    response["reconstruction"].reverse()
    response["domain_restrictions"].reverse()
    assert contract.score_exact_response(variant, response).is_correct is True

    duplicate = _correct_wire_response(variant)
    duplicate["terms"][1]["x_exponent"] = duplicate["terms"][0]["x_exponent"]
    duplicate["terms"][1]["y_exponent"] = duplicate["terms"][0]["y_exponent"]
    with pytest.raises(ValueError, match="unique exponent pairs"):
        contract.score_exact_response(variant, duplicate)


def test_polynomial_scoring_requires_typed_reasons_and_exact_reconstruction() -> None:
    variant = contract.generate_hidden_variant(contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT, 41)

    for code in (
        "POLY.DIV.COEFFICIENT_RECIPROCAL",
        "POLY.DIV.ADD_EXPONENTS",
        "POLY.DIV.ONE_TERM_ONLY",
        "POLY.DIV.DOMAIN_OMITTED",
    ):
        response = dict(variant.misconception_responses[code])
        wire = {
            "terms": [_wire_term(term) for term in response["terms"]],
            "domain_restrictions": list(response["domain_restrictions"]),
            "coefficient_reason": response["coefficient_reason"],
            "exponent_reason": response["exponent_reason"],
            "reconstruction": [
                _wire_reconstruction(record) for record in response["reconstruction"]
            ],
        }
        score = contract.score_exact_response(variant, wire)
        assert score == contract.ExactScore(False, code, assistance_level=0)

    malformed = _correct_wire_response(variant)
    malformed["reconstruction"][0]["product_term"]["x_exponent"] += 1
    with pytest.raises(ValueError, match="recomputed exactly"):
        contract.score_exact_response(variant, malformed)

    noncanonical = _correct_wire_response(variant)
    noncanonical["terms"][0]["coefficient"] += "/1"
    with pytest.raises(ValueError, match="canonical fractions"):
        contract.score_exact_response(variant, noncanonical)


def test_polynomial_area_transfer_is_exact_order_independent_and_dimension_typed() -> None:
    for seed in range(100):
        variant = contract.generate_hidden_variant(
            contract.ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER,
            seed,
        )
        height = variant.parameters["common_height"]
        for width, reconstruction in zip(
            variant.oracle["width_terms"],
            variant.oracle["multiplication_checks"],
            strict=True,
        ):
            assert reconstruction == (
                width,
                height,
                (
                    width[0] * height[0],
                    width[1] + height[1],
                    width[2] + height[2],
                ),
            )
        response = _correct_wire_response(variant)
        response["width_terms"].reverse()
        response["total_width_terms"].reverse()
        response["multiplication_checks"].reverse()
        response["domain_restrictions"].reverse()
        assert contract.score_exact_response(variant, response).is_correct is True

        wrong_units = _correct_wire_response(variant)
        wrong_units["units"]["area"] = "units"
        with pytest.raises(ValueError, match="width and area dimensions"):
            contract.score_exact_response(variant, wrong_units)


def test_exponent_oracle_covers_positive_zero_and_negative_results_exactly() -> None:
    outcomes: set[str] = set()
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
        assert parameters["base_nonzero"] is True
        outcomes.add(parameters["outcome"])
        if exponent == 0:
            assert expected == 1
            assert "EXP.ZERO_WRITTEN_AS_ZERO" in variant.misconception_responses
        elif exponent < 0:
            assert "EXP.NEGATIVE_IS_NEGATIVE_VALUE" in variant.misconception_responses
    assert outcomes == {"POSITIVE", "ZERO", "NEGATIVE"}


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
        misconception = variant.misconception_responses["EXP.GEOMETRY.POWER_NOT_DISTRIBUTED"]
        assert misconception["result_coefficient"] == (
            parameters["coefficient"] ** parameters["dimensional_power"]
        )
        assert misconception["result_exponent"] == parameters["exponent"]
        assert misconception["exact_value"] == (
            misconception["result_coefficient"]
            * parameters["base"] ** misconception["result_exponent"]
        )
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
                if kind == contract.ExactAlgebraKind.LINEAR_EQUATION:
                    wire = {
                        "classification": response["classification"],
                        "solutions": [_wire_fraction(value) for value in response["solutions"]],
                        "substitution_checks": [
                            {
                                "solution": _wire_fraction(solution),
                                "left_value": _wire_fraction(left_value),
                                "right_value": _wire_fraction(right_value),
                            }
                            for solution, left_value, right_value in response["substitution_checks"]
                        ],
                    }
                elif kind == contract.ExactAlgebraKind.ROOT_EQUATION:
                    wire = {
                        "classification": response["classification"],
                        "solutions": [
                            _wire_exact_real(value) for value in response["solutions"]
                        ],
                        "substitution_checks": [
                            {
                                "solution": _wire_exact_real(solution),
                                "left_value": _wire_exact_real(left_value),
                                "right_value": _wire_exact_real(right_value),
                            }
                            for solution, left_value, right_value in response[
                                "substitution_checks"
                            ]
                        ],
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
        "EXP.ZERO_WRITTEN_AS_ZERO",
        "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED",
    }


def test_quotient_dividends_remain_polynomials_across_seeded_variants() -> None:
    """Negative quotient powers must never turn the given dividend into a Laurent polynomial."""
    for kind in (
        contract.ExactAlgebraKind.MONOMIAL_QUOTIENT,
        contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT,
    ):
        negative_quotient_seen = False
        for seed in range(1000):
            variant = contract.generate_hidden_variant(kind, seed)
            dividend_terms = variant.parameters["dividend_terms"]
            assert all(x_exp >= 0 and y_exp >= 0 for _, x_exp, y_exp in dividend_terms), (
                kind, seed, dividend_terms
            )
            assert len({(x_exp, y_exp) for _, x_exp, y_exp in dividend_terms}) == len(
                dividend_terms
            ), (kind, seed)
            if kind == contract.ExactAlgebraKind.POLYNOMIAL_QUOTIENT:
                quotient_terms = variant.oracle["terms"]
            else:
                quotient_terms = ((
                    variant.oracle["coefficient"],
                    variant.oracle["x_exponent"],
                    variant.oracle["y_exponent"],
                ),)
            negative_quotient_seen |= any(x < 0 or y < 0 for _, x, y in quotient_terms)
            assert contract.score_exact_response(variant, _correct_wire_response(variant)).is_correct
        assert negative_quotient_seen, kind
