"""SYSTEM_OF_EQUATIONS generator: intersections, solution counts, and the
linear_system visual spec — plus the coordinate-swap misconception rule."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(800):
        generated = GENERATORS["SYSTEM_OF_EQUATIONS"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no SYSTEM_OF_EQUATIONS/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _line(line: dict) -> tuple[float, float]:
    return line["m_num"] / line["m_den"], line["i_num"] / line["i_den"]


def test_low_difficulty_only_reads_graphs() -> None:
    for seed in range(200):
        generated = GENERATORS["SYSTEM_OF_EQUATIONS"](random.Random(seed), 1)
        assert generated.parameters["tier"] == "graphical_solution"


def test_graphical_solution_is_the_intersection() -> None:
    for _ in range(80):
        generated = _gen("graphical_solution", difficulty=1)
        lines = generated.parameters["lines"]
        m1, b1 = _line(lines[0])
        m2, b2 = _line(lines[1])
        answer = generated.canonical_answer
        sx = float(answer.split(",")[0].strip("() "))
        sy = float(answer.split(",")[1].strip("() "))
        assert abs(m1 * sx + b1 - sy) < 1e-9
        assert abs(m2 * sx + b2 - sy) < 1e-9
        assert m1 != m2


def test_count_solutions_matches_the_lines() -> None:
    for _ in range(90):
        generated = _gen("count_solutions", difficulty=2)
        p = generated.parameters
        m1, b1 = _line(p["lines"][0])
        m2, b2 = _line(p["lines"][1])
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        if p["case"] == "one":
            assert correct == "one solution" and m1 != m2
        elif p["case"] == "none":
            assert correct == "no solution" and m1 == m2 and b1 != b2
        else:
            assert correct == "infinitely many solutions"
            assert m1 == m2 and b1 == b2


def test_count_solutions_tags_parallel_confusion() -> None:
    generated = _gen("count_solutions", difficulty=2)
    while generated.parameters["case"] != "none":
        generated = _gen("count_solutions", difficulty=2)
    tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
    assert tags["infinitely many solutions"] == "SYS_002"


def test_solve_tier_intersection_satisfies_both_equations() -> None:
    for _ in range(60):
        generated = _gen("solve", difficulty=3)
        p = generated.parameters
        answer = generated.canonical_answer
        sx = int(answer.split(",")[0].strip("() "))
        sy = int(answer.split(",")[1].strip("() "))
        assert p["a1"] * sx + p["b1"] * sy == p["c1"]
        assert p["a2"] * sx + p["b2"] * sy == p["c2"]


def test_solve_tier_has_no_diagram() -> None:
    # Rendering the lines would hand the intersection to the learner.
    generated = _gen("solve", difficulty=3)
    assert visualization_for(_as_problem(generated)) is None


def test_graph_tiers_emit_linear_system_spec() -> None:
    for tier, difficulty in [("graphical_solution", 1), ("count_solutions", 2)]:
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "linear_system"
        assert len(spec["lines"]) == 2


def test_swapped_intersection_flags_sys_001() -> None:
    prompt = (
        "The system of equations shown has exactly one solution. "
        "What are its coordinates?"
    )
    assert evaluate_problem(prompt, "(1, 2)", "(2, 1)").misconception_code == "SYS_001"
