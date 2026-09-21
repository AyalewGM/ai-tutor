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
        problem = _problem(
            "SIMPLIFY_EXPRESSION", "Expand 3(x + 4).", parameters={"a": 3, "b": 4}
        )
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
        problem = _problem(
            "SIMPLIFY_EXPRESSION", "Expand 4(x + 7).", parameters={"a": 4, "b": 7}
        )
        spec = visualization_for(problem)
        # area-model cells are a·x and a·b — the constant term must match
        assert spec["a"] * spec["b"] == 28


class TestNumberLine:
    def test_integer_sum_from_parameters(self):
        problem = _problem(
            "INTEGER_OPERATIONS", "Evaluate -3 + 7.", parameters={"a": -3, "b": 7}
        )
        spec = visualization_for(problem)
        assert spec["type"] == "number_line"
        assert spec["a"] == -3
        assert spec["b"] == 7
        assert spec["result"] == 4

    def test_range_covers_all_hops(self):
        problem = _problem(
            "INTEGER_OPERATIONS", "Evaluate -5 + 2.", parameters={"a": -5, "b": 2}
        )
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
    problem = _problem(
        "SOLVE_EQUATION", "Solve 2x + 3 = 9.", parameters={"tier": "coefficient"}
    )
    assert visualization_for(problem) is None
