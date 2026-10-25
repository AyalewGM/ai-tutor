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
