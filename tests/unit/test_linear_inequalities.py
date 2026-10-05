"""LINEAR_INEQUALITIES generator: solve ax + b ⊙ c, sign flips,
number-line graphs, context inequalities, compound forms and the
no-solution/all-reals cases, plus distractor misconception tags."""

import random
from types import SimpleNamespace

from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for

_FLIP = {"<": ">", ">": "<", "≤": "≥", "≥": "≤"}


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(2500):
        generated = GENERATORS["LINEAR_INEQUALITIES"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no LINEAR_INEQUALITIES/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _correct_text(generated) -> str:
    return next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
    )


def test_solve_flips_only_when_the_coefficient_is_negative() -> None:
    for _ in range(200):
        generated = _gen("solve", difficulty=1)
        p = generated.parameters
        a, b, c, op = p["a"], p["b"], p["c"], p["op"]
        k = (c - b) // a
        assert a * k + b == c  # clean integer boundary
        expected = _FLIP[op] if a < 0 else op
        correct = _correct_text(generated)
        assert correct == f"x {expected} {k}"
        tags = {c_["text"]: c_.get("misconception_code") for c_ in generated.choices}
        if a < 0:
            assert tags[f"x {op} {k}"] == "INEQ_001"
        else:
            assert tags[f"x {_FLIP[op]} {k}"] == "INEQ_002"
        assert visualization_for(_as_problem(generated)) is None


def test_flip_or_not_always_flips_for_negative_coefficients() -> None:
    for _ in range(120):
        generated = _gen("flip_or_not", difficulty=1)
        p = generated.parameters
        assert p["a"] < 0
        assert p["c"] % p["a"] == 0
        correct = _correct_text(generated)
        assert _FLIP[p["op"]] in correct


def test_graph_spec_matches_the_stated_inequality() -> None:
    for _ in range(120):
        generated = _gen("graph", difficulty=2)
        p = generated.parameters
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "inequality_line"
        assert spec["point"] == p["point"]
        assert spec["direction"] == p["direction"]
        assert spec["closed"] == p["closed"]
        correct = _correct_text(generated)
        op = correct.split()[1]
        assert (op in {"<", "≤"}) == (p["direction"] == "left")
        assert (op in {"≤", "≥"}) == p["closed"]
        tags = {c_.get("misconception_code") for c_ in generated.choices}
        assert "INEQ_003" in tags and "INEQ_004" in tags


def test_word_boundary_matches_the_context_language() -> None:
    for _ in range(120):
        generated = _gen("word", difficulty=2)
        p = generated.parameters
        assert (p["c"] - p["b"]) % p["r"] == 0
        k = (p["c"] - p["b"]) // p["r"]
        correct = _correct_text(generated)
        assert correct == f"{p['var']} {p['op']} {k}"
        strict = "more than" in generated.prompt
        assert (p["op"] == ">") == strict


def test_compound_solves_both_bounds() -> None:
    for _ in range(120):
        generated = _gen("compound", difficulty=3)
        p = generated.parameters
        a, b = p["a"], p["b"]
        k1 = (p["c1"] - b) // a
        k2 = (p["c2"] - b) // a
        assert k1 < k2
        correct = _correct_text(generated)
        assert correct == f"{k1} {p['op1']} x {p['op2']} {k2}"


def test_special_truthiness_matches_the_constants() -> None:
    for _ in range(120):
        generated = _gen("special", difficulty=4)
        p = generated.parameters
        gap = p["b1"] - p["b2"]
        holds = gap > 0  # x cancels for both > and ≥
        correct = _correct_text(generated)
        assert correct == ("all real numbers" if holds else "no solution")


def test_distractor_tags_cover_the_flip_and_boundary_errors() -> None:
    for _ in range(200):
        generated = _gen("solve", difficulty=1)
        codes = {c.get("misconception_code") for c in generated.choices}
        codes.discard(None)
        assert codes <= {"INEQ_001", "INEQ_002", "INEQ_003"}
        assert len(codes) >= 2
