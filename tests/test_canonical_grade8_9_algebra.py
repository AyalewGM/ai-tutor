import re

from app.canonical_problem_families import FAMILIES, LearningMode, generate

HS_PREFIXES = ("MATH.SYS.", "MATH.POLY.", "MATH.QUAD.", "MATH.EXPFUNC.")
HS_CODES = sorted(code for code in FAMILIES if code.startswith(HS_PREFIXES))


def test_grade8_9_algebra_batch_has_twenty_families() -> None:
    assert len(HS_CODES) == 20
    assert {
        "MATH.EE.SYSTEMS",
        "MATH.EE.POLYNOMIAL_OPERATIONS",
        "MATH.F.QUADRATIC.INTERPRET",
        "MATH.F.EXPONENTIAL",
    } <= {FAMILIES[code].canonical_skill_code for code in HS_CODES}


def test_grade8_9_algebra_is_deterministic_and_supports_all_modes() -> None:
    for code in HS_CODES:
        first = generate(code, seed=91, difficulty=3)
        second = generate(code, seed=91, difficulty=3)
        assert first == second, code
        assert FAMILIES[code].modes == frozenset(LearningMode), code


def test_grade8_9_misconceptions_do_not_collide_with_truth() -> None:
    for code in HS_CODES:
        for seed in range(10):
            problem = generate(code, seed=seed, difficulty=3)
            truth = "".join(problem.canonical_answer.lower().split())
            for candidate in problem.misconception_answers.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_elimination_system_solution_satisfies_both_equations() -> None:
    for seed in range(15):
        problem = generate("MATH.SYS.SOLVE.ELIMINATION", seed=seed, difficulty=3)
        match = re.fullmatch(
            r"Solve the system (\d+)x\+y=(-?\d+) and \1x-y=(-?\d+)\. Give x,y\.",
            problem.prompt,
        )
        assert match
        a, c1, c2 = map(int, match.groups())
        x, y = map(int, problem.canonical_answer.split(","))
        assert a * x + y == c1
        assert a * x - y == c2


def test_binomial_product_matches_independent_expansion() -> None:
    for seed in range(15):
        problem = generate("MATH.POLY.MULT.BINOMIAL", seed=seed, difficulty=3)
        match = re.fullmatch(r"Expand \(x\+(\d+)\)\(x\+(\d+)\)\.", problem.prompt)
        assert match
        a, b = map(int, match.groups())
        assert problem.canonical_answer == f"x^2+{a+b}x+{a*b}"


def test_quadratic_evaluation_matches_direct_oracle() -> None:
    for seed in range(15):
        problem = generate("MATH.QUAD.EVALUATE", seed=seed, difficulty=3)
        match = re.fullmatch(
            r"For f\(x\)=(\d+)x\^2\+\((-?\d+)\)x\+\((-?\d+)\), find f\((-?\d+)\)\.",
            problem.prompt,
        )
        assert match
        a, b, c, x = map(int, match.groups())
        assert int(problem.canonical_answer) == a * x * x + b * x + c


def test_exponential_evaluation_matches_direct_oracle() -> None:
    for seed in range(15):
        problem = generate("MATH.EXPFUNC.EVALUATE", seed=seed, difficulty=3)
        match = re.fullmatch(r"For f\(x\)=(\d+)\((\d+)\^x\), find f\((\d+)\)\.", problem.prompt)
        assert match
        initial, factor, x = map(int, match.groups())
        assert int(problem.canonical_answer) == initial * factor**x


def test_grade8_9_algebra_remains_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "new york", "maryland", "ontario"}
    for code in HS_CODES:
        spec = FAMILIES[code]
        metadata = f"{spec.code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
