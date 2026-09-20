from app.services.evaluation import evaluate_problem


def _misconception(prompt: str, answer: str, canonical: str) -> str | None:
    result = evaluate_problem(prompt, answer, canonical)
    assert result.correct is False
    return result.misconception_code


def test_correct_answers_never_flag_misconceptions() -> None:
    for prompt, canonical in [
        ("4(x-3)", "4x-12"),
        ("x + 5 = 12", "x=7"),
        ("2x + 3 = 11", "x=4"),
        ("A line has slope 2 and y-intercept -1. Write its equation.", "y=2x-1"),
        ("Evaluate -6 + 14.", "8"),
    ]:
        result = evaluate_problem(prompt, canonical, canonical)
        assert result.correct is True
        assert result.misconception_code is None


def test_partial_distribution_flagged() -> None:
    assert _misconception("3(x+4)", "3x+4", "3x+12") == "DIST_001"


def test_distribution_sign_error_flagged() -> None:
    assert _misconception("4(x-3)", "4x+12", "4x-12") == "DIST_002"
    assert _misconception("-2(x+6)", "-2x+12", "-2x-12") == "DIST_002"


def test_partial_distribution_takes_priority_over_sign_error() -> None:
    assert _misconception("4(x-3)", "4x-3", "4x-12") == "DIST_001"


def test_inverse_operation_wrong_direction_flagged() -> None:
    assert _misconception("x + 5 = 12", "x=17", "x=7") == "EQ_001"
    assert _misconception("x + 5 = 12", "x=-7", "x=7") == "EQ_001"
    assert _misconception("2x + 3 = 11", "x=7", "x=4") == "EQ_001"


def test_skipped_division_flagged() -> None:
    assert _misconception("2x + 3 = 11", "x=8", "x=4") == "EQ_002"
    assert _misconception("Solve 3x + 4 = 19.", "x=15", "x=5") == "EQ_002"


def test_slope_intercept_swap_flagged() -> None:
    assert (
        _misconception(
            "A line has slope 2 and y-intercept -1. Write its equation.",
            "y=-1x+2",
            "y=2x-1",
        )
        == "REL_001"
    )


def test_integer_sign_and_magnitude_errors_flagged() -> None:
    assert _misconception("Evaluate -6 + 14.", "-8", "8") == "NUM_001"
    assert _misconception("Evaluate -6 + 14.", "20", "8") == "NUM_002"
    assert _misconception("Evaluate -6 + 14.", "-20", "8") == "NUM_001"


def test_unlike_terms_combined_flagged() -> None:
    assert _misconception("Simplify 4x + 3 + 2x - 5.", "4x", "6x-2") == "ALG_001"
    assert _misconception("Simplify 2x + 5 + 3x - 1.", "9x", "5x+4") == "ALG_001"


def test_constant_sign_dropped_flagged() -> None:
    assert _misconception("Simplify 4x + 3 + 2x - 5.", "6x+8", "6x-2") == "ALG_002"
    assert _misconception("Simplify 2x + 5 + 3x - 1.", "5x+6", "5x+4") == "ALG_002"


def test_multiply_instead_of_divide_flagged() -> None:
    assert _misconception("Solve 4x = 20.", "x=80", "x=5") == "EQ_003"
    assert _misconception("Solve 3x = 12", "x=36", "x=4") == "EQ_003"


def test_fraction_added_across_flagged() -> None:
    assert _misconception("Evaluate 3/4 + 1/2.", "4/6", "5/4") == "NUM_003"


def test_coefficient_added_not_multiplied_flagged() -> None:
    assert (
        _misconception(
            "For y = 3x + 2, what is y when x = 4?", "9", "14"
        )
        == "REL_002"
    )


def test_percent_scaling_errors_flagged() -> None:
    assert (
        _misconception(
            "A $80 purchase has 13% tax. What is the tax amount?",
            "1040",
            "10.40",
        )
        == "FIN_001"
    )
    assert (
        _misconception(
            "A $120 item is discounted by 25%. What is the sale price before tax?",
            "95",
            "90",
        )
        == "FIN_001"
    )


def test_discount_amount_instead_of_price_flagged() -> None:
    assert (
        _misconception(
            "A $120 item is discounted by 25%. What is the sale price before tax?",
            "30",
            "90",
        )
        == "FIN_002"
    )


def test_unrecognized_errors_carry_no_misconception() -> None:
    assert _misconception("2x + 3 = 11", "x=1", "x=4") is None
    assert _misconception("3(x+4)", "7x", "3x+12") is None
