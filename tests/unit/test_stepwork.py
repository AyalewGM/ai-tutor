from fractions import Fraction

from app.services.stepwork import (
    check_step,
    check_word_step,
    parse_equation,
    parse_equation_lenient,
    parse_expression,
    parse_expression_lenient,
    problem_supports_steps,
    starting_equation,
    starting_expression,
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


def test_parse_expression_rejects_mixed_variables_and_junk() -> None:
    assert parse_expression("2y + 1") is not None  # any single variable is fine
    assert parse_expression("2x + y") is None  # mixed variables are not
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
    assert supports_steps("SIMPLIFY_EXPRESSION")
    assert supports_steps("FRACTION_OPERATIONS")
    assert not supports_steps("ARITHMETIC_20")
    assert not supports_steps(None)


def test_expression_steps_fraction_family() -> None:
    start = "1/2 + 1/3"
    result = check_step(start, [], "3/6 + 2/6", 0)
    assert result.status == "valid"
    assert check_step(start, ["3/6 + 2/6"], "5/6", 0).status == "solved"
    assert check_step(start, [], "5/6", 0).status == "solved"
    # Equal but not in lowest terms — a valid move, not the final answer.
    assert check_step(start, ["3/6 + 2/6"], "10/12", 0).status == "valid"


def test_expression_steps_simplify_family() -> None:
    start = "3(x + 4)"
    assert check_step(start, [], "3x + 12", 0).status == "solved"
    partial = check_step(start, [], "3x + 4", 0)
    assert partial.status == "invalid"
    assert partial.misconception_code == "DIST_001"


def test_expression_steps_combine_like_terms_family() -> None:
    start = "4y + 3y - 5"
    assert check_step(start, [], "7y - 5", 0).status == "solved"
    assert check_step(start, [], "7y + 5", 0).status == "invalid"
    eq = check_step(start, [], "4y + 3y = 5", 0)
    assert eq.status == "unparseable"


def test_fraction_adds_across_misconception() -> None:
    result = check_step("1/2 + 1/3", [], "2/5", 0)
    assert result.status == "invalid"
    assert result.misconception_code == "NUM_003"


def test_starting_expression_preserves_leading_sign() -> None:
    # "Simplify -2y - 5y." — the prefix stripper must not eat the minus.
    assert starting_expression("Simplify -2y - 5y.") == "-2y - 5y"
    assert starting_expression("Evaluate 1/2 + 1/3.") == "1/2 + 1/3"
    assert starting_expression("3(x + 4)") == "3(x + 4)"
    assert check_step("-2y - 5y", [], "-7y", 0).status == "solved"


def test_sympy_fallback_covers_syntax_the_native_parser_lacks() -> None:
    # ^ exponent syntax and implicit multiplication through parens
    assert parse_expression_lenient("x^2 - 5x + 6") == {
        2: Fraction(1), 1: Fraction(-5), 0: Fraction(6),
    }
    assert parse_expression_lenient("0.5x + 1/4") == {
        1: Fraction(1, 2), 0: Fraction(1, 4),
    }
    assert parse_equation_lenient("x^2 - 4 = 0") is not None


def test_sympy_fallback_rejects_out_of_scope_input() -> None:
    # Rational expressions, functions, and multi-variable input stay
    # honestly unparseable rather than being half-checked.
    assert parse_expression_lenient("(x+1)/(x-1)") is None
    assert parse_expression_lenient("sin(x)") is None
    assert parse_expression_lenient("x + y") is None
    assert parse_expression_lenient("hello") is None
    assert parse_expression_lenient("2**x") is None


def test_quadratic_equation_steps() -> None:
    # Factoring preserves the solution set — a legal step.
    result = check_step("x^2 - 5x + 6 = 0", [], "(x-2)(x-3) = 0", 0)
    assert result.status == "valid"
    # x = 2 alone drops a root — the solution set is NOT preserved.
    assert check_step("x^2 = 4", [], "x = 2", 0).status == "invalid"


def test_higher_degree_normalized_rendering() -> None:
    result = check_step("x^2 - 5x + 6 = 0", [], "(x-2)(x-3) = 0", 0)
    assert result.normalized_line == "x^2 - 5x + 6 = 0"


def test_word_problem_model_and_answer() -> None:
    # "A $80 purchase has 13% tax." — the model is a calculation whose
    # value must equal the canonical answer.
    c = Fraction("10.40")
    assert check_word_step("10.40", c, [], "0.13 * 80", 0).status == "valid"
    wrong_model = check_word_step("10.40", c, [], "0.13 * 50", 0)
    assert wrong_model.status == "invalid"
    # A bare correct answer is solved at any point — the structure is
    # scaffolding, not a gate.
    assert check_word_step("10.40", c, [], "10.40 dollars", 0).status == "solved"
    # Chained computation ending at the answer is solved.
    assert check_word_step(
        "10.40", c, ["0.13 * 80"], "0.13 * 80 = 10.4", 0
    ).status == "solved"
    # Off-value compute step is an arithmetic slip.
    slip = check_word_step("10.40", c, ["0.13 * 80"], "9.4", 0)
    assert slip.status == "invalid"
    assert slip.misconception_code == "NUM_003"


def test_word_problem_supports_steps_gate() -> None:
    from app.models import Problem

    problem = Problem(
        problem_type="WORD_PROBLEM",
        answer_kind="INTEGER",
        prompt="What is 20% of 60?",
        canonical_answer="12",
    )
    assert problem_supports_steps(problem)
    # No parseable numeric answer → step mode stays off.
    bad = Problem(
        problem_type="WORD_PROBLEM",
        answer_kind="FREE_TEXT",
        prompt="Explain the pattern.",
        canonical_answer="it doubles",
    )
    assert not problem_supports_steps(bad)
