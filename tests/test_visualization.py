"""Deterministic visualization specs (Issue #42)."""

from app.models import Problem
from app.services.visualization import visualization_for


def _problem(problem_type, prompt, parameters=None, canonical_answer=None):
    return Problem(
        primary_skill_id=None,
        problem_type=problem_type,
        difficulty=1,
        prompt=prompt,
        canonical_answer=canonical_answer,
        solution={"parameters": parameters} if parameters else {},
    )


class TestAreaModel:
    def test_simplify_from_parameters(self):
        problem = _problem("SIMPLIFY_EXPRESSION", "Expand 3(x + 4).", parameters={"a": 3, "b": 4})
        spec = visualization_for(problem)
        assert spec["type"] == "area_model"
        assert spec["a"] == 3
        assert spec["b"] == 4
        assert "area" in spec["aria_label"].lower()

    def test_simplify_parsed_from_curated_prompt(self):
        problem = _problem("SIMPLIFY_EXPRESSION", "Expand 2(x - 5).")
        spec = visualization_for(problem)
        assert spec["type"] == "area_model"
        assert spec["a"] == 2
        assert spec["b"] == -5

    def test_invariant_constant_term_matches_expansion(self):
        problem = _problem("SIMPLIFY_EXPRESSION", "Expand 4(x + 7).", parameters={"a": 4, "b": 7})
        spec = visualization_for(problem)
        # area-model cells are a·x and a·b — the constant term must match
        assert spec["a"] * spec["b"] == 28


class TestNumberLine:
    def test_integer_sum_from_parameters(self):
        problem = _problem("INTEGER_OPERATIONS", "Evaluate -3 + 7.", parameters={"a": -3, "b": 7})
        spec = visualization_for(problem)
        assert spec["type"] == "number_line"
        assert spec["a"] == -3
        assert spec["b"] == 7
        assert spec["result"] == 4

    def test_range_covers_all_hops(self):
        problem = _problem("INTEGER_OPERATIONS", "Evaluate -5 + 2.", parameters={"a": -5, "b": 2})
        spec = visualization_for(problem)
        assert spec["min"] <= min(0, spec["a"], spec["result"])
        assert spec["max"] >= max(0, spec["a"], spec["result"])

    def test_result_matches_canonical_answer(self):
        problem = _problem(
            "INTEGER_OPERATIONS",
            "Evaluate 4 - 9.",
            parameters={"a": 4, "b": -9},
            canonical_answer="-5",
        )
        spec = visualization_for(problem)
        # diagram result must equal the authoritative answer — never diverge
        assert spec["result"] == int(problem.canonical_answer)


class TestComparePoints:
    def test_compare_spec(self):
        problem = _problem(
            "INTEGER_COMPARE",
            "Which is greater, -4 or 2?",
            parameters={"a": -4, "b": 2},
        )
        spec = visualization_for(problem)
        assert spec["type"] == "number_line_compare"
        assert spec["min"] < min(spec["a"], spec["b"])
        assert spec["max"] > max(spec["a"], spec["b"])


def test_unsupported_type_returns_none():
    problem = _problem("LINEAR_RELATION", "For y = 3x + 2, what is y when x = 4?")
    assert visualization_for(problem) is None


def _family_problem(problem_type, prompt, family, parameters):
    return Problem(
        primary_skill_id=None,
        problem_type=problem_type,
        difficulty=1,
        prompt=prompt,
        canonical_answer=None,
        solution={"problem_family": family, "parameters": parameters},
    )


class TestBalanceScale:
    def test_two_step_equation_from_curated_prompt(self):
        spec = visualization_for(_problem("SOLVE_EQUATION", "Solve 3x + 12 = 30."))
        assert spec["type"] == "balance_scale"
        assert spec["left"] == {"x_count": 3, "units": 12}
        assert spec["right"] == {"x_count": 0, "units": 30}
        assert "balance" in spec["aria_label"].lower()

    def test_distributed_form_expands_onto_the_pan(self):
        spec = visualization_for(_problem("SOLVE_EQUATION", "Solve 2(x + 3) = 14."))
        assert spec["left"] == {"x_count": 2, "units": 6}

    def test_negative_constant_is_not_drawn_dishonestly(self):
        # Unit weights can't be negative on a pan — refuse rather than mislead.
        assert visualization_for(_problem("SOLVE_EQUATION", "Solve 3x - 5 = 16.")) is None

    def test_nonlinear_or_huge_equations_return_none(self):
        assert visualization_for(_problem("SOLVE_EQUATION", "x^2 - 4 = 0")) is None
        assert visualization_for(_problem("SOLVE_EQUATION", "Solve 9x + 50 = 95.")) is None


class TestFractionOperation:
    def test_unlike_denominators_share_a_common_grid(self):
        spec = visualization_for(_problem("FRACTION_OPERATIONS", "Evaluate 2/3 + 1/6."))
        assert spec["type"] == "fraction_operation"
        assert spec["operation"] == "+"
        assert spec["first"] == {"numerator": 2, "denominator": 3}
        assert spec["second"] == {"numerator": 1, "denominator": 6}
        assert spec["common_denominator"] == 6

    def test_subtract_family_from_parameters(self):
        spec = visualization_for(
            _problem(
                "FRACTION_SUBTRACT",
                "Evaluate 3/4 - 1/2.",
                parameters={"n1": 3, "d1": 4, "n2": 1, "d2": 2},
            )
        )
        assert spec["operation"] == "-"
        assert spec["common_denominator"] == 4

    def test_oversized_common_denominator_returns_none(self):
        assert visualization_for(_problem("FRACTION_OPERATIONS", "Evaluate 1/7 + 1/5.")) is None


class TestTapeDiagram:
    def test_percent_of_shades_the_percent(self):
        spec = visualization_for(
            _family_problem(
                "WORD_PROBLEM",
                "What is 20% of 60?",
                "WORD_PROBLEM:percent_of",
                {"percent": 20, "amount": 60},
            )
        )
        assert spec["type"] == "tape_diagram"
        assert spec["total_label"] == "60"
        assert spec["segments"][0] == {"label": "20%", "span": 20, "highlight": True}

    def test_flat_fee_does_not_leak_the_answer_count(self):
        # "How many miles?" — the number of rate segments IS the answer, so the
        # diagram must draw the rate part as a single unknown-length piece.
        spec = visualization_for(
            _family_problem(
                "ALGEBRA_WORD_PROBLEM",
                "taxi",
                "ALGEBRA_WORD_PROBLEM:flat_fee",
                {"fee": 3, "rate": 2, "miles": 7},
            )
        )
        assert spec["total_label"] == "$17"
        assert len(spec["segments"]) == 2
        assert "?" in spec["segments"][1]["label"]

    def test_number_trick_x_parts_have_fixed_width(self):
        spec = visualization_for(
            _family_problem(
                "ALGEBRA_WORD_PROBLEM",
                "n",
                "ALGEBRA_WORD_PROBLEM:number_trick",
                {"multiplier": 2, "added": 5, "value": 8},
            )
        )
        x_parts = [s for s in spec["segments"] if s["label"] == "x"]
        assert len(x_parts) == 2
        assert all(s["span"] == 4 for s in x_parts)  # not 8 — would reveal x

    def test_curated_word_problem_without_parameters_returns_none(self):
        assert visualization_for(_problem("WORD_PROBLEM", "A $80 purchase has 13% tax.")) is None
