"""Synthetic fraction assessment contract regressions; no learner database writes."""

from fractions import Fraction

from app.answer_contracts import AnswerContract, AnswerKind
from app.services.fraction_assessment_registry import (
    AUTHORIZED_FAMILIES,
    AssessmentMode,
    is_registered_for_mode,
    score_fraction,
)


def test_reuses_existing_rational_contract() -> None:
    contract = AnswerContract(AnswerKind.RATIONAL)
    assert contract.equivalent("6/8", "3/4")
    assert score_fraction("6/8", "3/4")
    assert score_fraction("-6/8", "-3/4")
    assert score_fraction("3/-4", "-3/4")
    assert score_fraction("6/-8", "-3/4")
    assert score_fraction("2", "8/4")


def test_variable_value_equivalence() -> None:
    assert score_fraction("x = 6/8", "x=3/4", variable="x")
    assert score_fraction("X=3/-4", "x=-3/4", variable="x")
    assert not score_fraction("y=3/4", "x=3/4", variable="x")
    assert not score_fraction("x=3/4", "y=3/4", variable="x")


def test_malformed_near_miss_and_zero_denominator_fail_closed() -> None:
    for invalid in ("1/0", "1/-0", "0/0", "1//2", "1.5", "1+1/2",
                    "-(-3/4)", "eval(1)", "__import__('os')", "1/2/3", "nan", ""):
        assert not score_fraction(invalid, "3/4")
    assert not score_fraction("4/5", "3/4")
    assert not score_fraction("1/2", "3/4")
    assert not score_fraction("2/3", "3/4")
    assert not score_fraction("3/4", "0/0")


def test_unapproved_489_families_cannot_enter_any_mode() -> None:
    assert not AUTHORIZED_FAMILIES
    for mode in AssessmentMode:
        assert not is_registered_for_mode(
            "ONTARIO.SIGNED.TWO_STEP", "MATH.EE.EQUATION.TWO", "a" * 40, mode
        )
        assert not is_registered_for_mode("", "", "", mode)


def test_pure_scorer_does_not_create_or_change_history() -> None:
    expected = Fraction(3, 4)
    before = (expected.numerator, expected.denominator)
    for _ in range(10):
        assert score_fraction("9/12", str(expected))
    assert before == (expected.numerator, expected.denominator)


def test_adversarial_raw_inputs_are_bounded_before_parsing() -> None:
    # Exercise both CodeQL trigger shapes and both trust positions. No timing
    # threshold is needed: over-budget input must never reach either parser.
    from unittest.mock import patch

    for raw in ("0" * 100_000 + "!", "A=" + " " * 100_000 + "!",
                "A" + " " * 100_000 + "=1", " " * 100_000 + "1"):
        for variable in (None, "A"):
            expected = "1" if variable is None else "A=1"
            with patch("app.services.fraction_assessment_registry._fraction") as rational, \
                    patch("app.services.fraction_assessment_registry._variable_value") as assigned:
                assert not score_fraction(raw, expected, variable=variable)
                assert not score_fraction(expected, raw, variable=variable)
                rational.assert_not_called()
                assigned.assert_not_called()


def test_bounded_near_misses_and_variable_delimiters() -> None:
    for invalid in ("0" * 63 + "!", "1/" + "0" * 61 + "!", "+", "-", "1/", "1/++2", "²", "1 2"):
        assert not score_fraction(invalid, "1")
    for invalid in ("A=" + " " * 61, "AA=1", "A==1", "A=1=1", "Å=1", "A=\n1\n2"):
        assert not score_fraction(invalid, "A=1", variable="A")
    assert score_fraction("A\t=\t-6/-8", "a=3/4", variable="a")
    assert score_fraction("1" * 64, "1" * 64)
    assert not score_fraction("1" * 65, "1" * 65)


def test_signed_denominators_and_decimal_digit_semantics() -> None:
    for candidate, expected in (("-6/-8", "3/4"), ("+6/-8", "-3/4"),
                                ("6/+8", "3/4"), ("-0/-8", "0"),
                                ("٦/-٨", "-3/4")):
        assert score_fraction(candidate, expected)
        assert score_fraction("A=" + candidate, "a=" + expected, variable="A")
    for invalid in ("1/+0", "1/-0", "1/٠", "1/²"):
        assert not score_fraction(invalid, "1")
        assert not score_fraction("A=" + invalid, "A=1", variable="A")
