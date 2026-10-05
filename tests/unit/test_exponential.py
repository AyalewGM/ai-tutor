"""EXPONENTIAL_FUNCTION generator: f(x) = a·b^x evaluation, geometric
patterns, growth/decay reads, and the exponential_graph spec — plus the
product-first and linear-treatment misconception rules."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1200):
        generated = GENERATORS["EXPONENTIAL_FUNCTION"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no EXPONENTIAL_FUNCTION/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _fit(params: dict) -> tuple[int, Fraction]:
    return params["a"], Fraction(params["b_num"], params["b_den"])


def test_evaluate_matches_a_b_pow_x() -> None:
    for _ in range(100):
        generated = _gen("evaluate", difficulty=1)
        a, b = _fit(generated.parameters)
        x = generated.parameters["x"]
        assert int(generated.canonical_answer) == a * b**x
        assert generated.answer_kind == "INTEGER"


def test_next_value_extends_geometrically() -> None:
    for _ in range(60):
        generated = _gen("next_value", difficulty=1)
        a, b = _fit(generated.parameters)
        terms = generated.parameters["terms"]
        start = next(k for k in range(3) if int(a * b**k) == terms[0])
        assert terms == [int(a * b**k) for k in range(start, start + 4)]
        assert b > 1  # decay sequences would hit non-integer terms
        assert int(generated.canonical_answer) == terms[-1] * b


def test_growth_or_decay_matches_the_curve() -> None:
    for _ in range(100):
        generated = _gen("growth_or_decay", difficulty=2)
        _, b = _fit(generated.parameters)
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == ("exponential growth" if b > 1 else "exponential decay")
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        wrong_direction = "exponential decay" if b > 1 else "exponential growth"
        assert tags[wrong_direction] == "EXP_001"


def test_initial_value_answer_is_a() -> None:
    for _ in range(80):
        generated = _gen("initial_value", difficulty=2)
        a, _ = _fit(generated.parameters)
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == str(a)


def test_growth_factor_states_two_lattice_points() -> None:
    for _ in range(80):
        generated = _gen("growth_factor", difficulty=3)
        a, b = _fit(generated.parameters)
        assert f"(0, {a})" in generated.prompt
        assert f"(1, {a * b})" in generated.prompt
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == (str(b.numerator) if b.denominator == 1 else str(b))
        # Every option list still offers a reciprocal (EXP_001) and the
        # initial value (EXP_003) as tagged distractors.
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags.get(str(a)) == "EXP_003" or tags.get(str(a * b)) == "EXP_003"


def test_write_equation_marks_lattice_points_on_curve() -> None:
    for _ in range(60):
        generated = _gen("write_equation", difficulty=3)
        a, b = _fit(generated.parameters)
        for x, y in generated.parameters["mark_points"]:
            assert y == int(a * b**x)


def test_graph_tiers_emit_spec_and_text_tiers_do_not() -> None:
    for tier, difficulty in [
        ("growth_or_decay", 2),
        ("initial_value", 2),
        ("growth_factor", 3),
        ("write_equation", 3),
    ]:
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "exponential_graph"
    for tier, difficulty in [("evaluate", 1), ("next_value", 1)]:
        generated = _gen(tier, difficulty=difficulty)
        assert visualization_for(_as_problem(generated)) is None


def test_product_first_evaluation_flags_exp_003() -> None:
    prompt = "For f(x) = 2·3^x, what is f(2)?"
    # (2·3)^2 = 36 — multiplied a by b before exponentiating.
    assert evaluate_problem(prompt, "36", "18").misconception_code == "EXP_003"
    assert evaluate_problem(prompt, "18", "18").correct


def test_linear_treatment_flags_exp_004() -> None:
    prompt = "For f(x) = 3·2^x, what is f(3)?"
    # 3·2·3 = 18 (b·x, never exponentiated) and 3 + 2·3 = 9 (linear form).
    assert evaluate_problem(prompt, "18", "24").misconception_code == "EXP_004"
    assert evaluate_problem(prompt, "9", "24").misconception_code == "EXP_004"


def test_arithmetic_extrapolation_flags_exp_002() -> None:
    prompt = "An exponential pattern continues: 2, 6, 18, 54. What is the next term?"
    # Added the last difference (36) instead of multiplying by 3.
    assert evaluate_problem(prompt, "90", "162").misconception_code == "EXP_002"
    assert evaluate_problem(prompt, "162", "162").correct
