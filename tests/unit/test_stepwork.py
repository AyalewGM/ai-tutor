from fractions import Fraction

from app.services.stepwork import (
    check_step,
    parse_equation,
    parse_expression,
    starting_equation,
    supports_steps,
)


def test_parse_expression_linear_forms() -> None:
    assert parse_expression("3x + 12") == {1: Fraction(3), 0: Fraction(12)}
    assert parse_expression("x") == {1: Fraction(1)}
    assert parse_expression("-x") == {1: Fraction(-1)}
    assert parse_expression("42") == {0: Fraction(42)}
    assert parse_expression("2(x + 3)") == {1: Fraction(2), 0: Fraction(6)}
    assert parse_expression("x/2") == {1: Fraction(1, 2)}
    assert parse_expression("-2(x - 7)") == {1: Fraction(-2), 0: Fraction(14)}


def test_parse_expression_rejects_non_x_variables_and_junk() -> None:
    assert parse_expression("2y + 1") is None
    assert parse_expression("hello") is None
    assert parse_expression("x +") is None
    assert parse_expression("3x = 9") is None  # not an expression


def test_parse_equation() -> None:
    assert parse_equation("3(x + 4) = 30") == (
        {1: Fraction(3), 0: Fraction(12)},
        {0: Fraction(30)},
    )
    assert parse_equation("3x + 12") is None  # not an equation
    assert parse_equation("a = b = c") is None


def test_starting_equation_strips_prompt_prefix() -> None:
    assert starting_equation("Solve 2x + 3 = 9.") == "2x + 3 = 9"
    assert starting_equation("3(x + 4) = 30") == "3(x + 4) = 30"
    assert starting_equation("What is the area?") is None


def test_equivalent_routes_are_all_legal() -> None:
    start = "3(x + 4) = 30"
    # Distribute first.
    assert check_step(start, [], "3x + 12 = 30", 0).status == "valid"
    # Divide first — a different but equally legal route.
    assert check_step(start, [], "x + 4 = 10", 0).status == "valid"


def test_canonical_path_to_solution() -> None:
    start = "3(x + 4) = 30"
    assert check_step(start, ["3x + 12 = 30"], "3x = 18", 0).status == "valid"
    result = check_step(start, ["3x + 12 = 30", "3x = 18"], "x = 6", 0)
    assert result.status == "solved"
    assert result.normalized_line == "x = 6"


def test_direct_answer_counts_as_solved() -> None:
    start = "3(x + 4) = 30"
    assert check_step(start, [], "x = 6", 0).status == "solved"
    assert check_step(start, [], "6", 0).status == "solved"
    assert check_step(start, [], "6 = x", 0).status == "solved"


def test_wrong_answer_is_invalid_not_solved() -> None:
    assert check_step("3(x + 4) = 30", [], "x = 8", 0).status == "invalid"


def test_inverse_direction_misconception() -> None:
    # 3x + 12 = 30 -> 3x = 42 (added 12 to the right instead of subtracting).
    result = check_step("3(x + 4) = 30", ["3x + 12 = 30"], "3x = 42", 0)
    assert result.status == "invalid"
    assert result.misconception_code == "EQ_001"


def test_one_sided_operation_misconception() -> None:
    # 3(x + 4) = 30 -> x + 4 = 30 (divided only the left side by 3).
    result = check_step("3(x + 4) = 30", [], "x + 4 = 30", 0)
    assert result.status == "invalid"
    assert result.misconception_code == "EQ_002"


def test_unclassified_wrong_step_is_still_invalid() -> None:
    result = check_step("3(x + 4) = 30", [], "2x + 4 = 9", 0)
    assert result.status == "invalid"
    assert result.misconception_code is None


def test_unparseable_lines_get_guidance_not_grading() -> None:
    assert check_step("3x = 9", [], "hello", 0).status == "unparseable"
    assert check_step("3x = 9", [], "x + 4", 0).status == "unparseable"
    assert check_step("3x = 9", [], "", 0).status == "unparseable"


def test_duplicate_line_flagged() -> None:
    assert check_step("3x = 9", [], "3x = 9", 0).status == "duplicate"


def test_intervention_escalates_to_reveal_after_repeated_failure() -> None:
    start = "3(x + 4) = 30"
    first = check_step(start, [], "x + 4 = 30", 0)
    assert first.status == "invalid" and first.revealed_line is None
    second = check_step(start, [], "x + 4 = 30", 1)
    assert second.status == "invalid" and second.revealed_line is None
    third = check_step(start, [], "x + 4 = 30", 2)
    assert third.status == "invalid"
    assert third.revealed_line is not None
    # The revealed line is itself a legal move.
    assert check_step(start, [], third.revealed_line, 0).status == "valid"


def test_multi_step_full_path_with_detour() -> None:
    start = "5x - 3 = 12"
    assert check_step(start, [], "5x = 15", 0).status == "valid"
    assert check_step(start, ["5x = 15"], "x = 3", 0).status == "solved"


def test_supports_steps_scoping() -> None:
    assert supports_steps("SOLVE_EQUATION")
    assert not supports_steps("ARITHMETIC_20")
    assert not supports_steps(None)
