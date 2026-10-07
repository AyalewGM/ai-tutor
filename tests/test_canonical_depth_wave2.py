import re
from fractions import Fraction

from app.canonical_problem_families import FAMILIES, LearningMode, generate

WAVE2_PREFIXES = (
    "MATH.RAT.",
    "MATH.EXP.",
    "MATH.ROOT.",
    "MATH.SCI.",
    "MATH.INEQ.",
    "MATH.FUNC.SEQUENCE.",
    "MATH.FUNC.COMPARE.",
    "MATH.FUNC.DOMAIN.",
    "MATH.FUNC.NONLINEAR.",
    "MATH.FUNC.ERROR.CONSTANT_RATE",
    "MATH.GEO.CIRCLE.",
    "MATH.DATA.DOT.",
    "MATH.DATA.HISTOGRAM.",
    "MATH.DATA.FIVE_NUMBER",
    "MATH.DATA.IQR",
    "MATH.DATA.MAD",
)

WAVE2_CODES = sorted(
    code for code in FAMILIES if code.startswith(WAVE2_PREFIXES)
)


def test_wave2_adds_substantial_canonical_depth() -> None:
    assert len(WAVE2_CODES) == 35
    canonical_skills = {FAMILIES[code].canonical_skill_code for code in WAVE2_CODES}
    assert {
        "MATH.NS.RATIONAL.OPERATIONS",
        "MATH.NS.EXPONENTS",
        "MATH.NS.ROOTS",
        "MATH.NS.SCIENTIFIC_NOTATION",
        "MATH.EE.INEQUALITY.ONE",
        "MATH.EE.INEQUALITY.MULTISTEP",
        "MATH.F.FUNCTIONS",
        "MATH.GEO.CIRCLES",
        "MATH.DATA.REPRESENTATIONS",
    } <= canonical_skills


def test_wave2_generation_is_deterministic_and_supports_all_learning_modes() -> None:
    for code in WAVE2_CODES:
        first = generate(code, seed=20261007, difficulty=3)
        second = generate(code, seed=20261007, difficulty=3)
        assert first == second, code
        assert FAMILIES[code].modes == frozenset(LearningMode), code


def test_wave2_misconceptions_never_equal_truth() -> None:
    for code in WAVE2_CODES:
        for seed in range(12):
            problem = generate(code, seed=seed, difficulty=3)
            normalized_answer = "".join(problem.canonical_answer.lower().split())
            for misconception, candidate in problem.misconception_answers.items():
                normalized_candidate = "".join(candidate.lower().split())
                assert normalized_candidate != normalized_answer, (code, seed, misconception)


def test_rational_addition_matches_independent_fraction_oracle() -> None:
    for seed in range(20):
        problem = generate("MATH.RAT.ADD", seed=seed, difficulty=3)
        match = re.fullmatch(r"Compute ([-0-9/]+) \+ ([-0-9/]+)\. Give the simplified result\.", problem.prompt)
        assert match
        expected = Fraction(match.group(1)) + Fraction(match.group(2))
        assert Fraction(problem.canonical_answer) == expected


def test_rational_division_matches_independent_fraction_oracle() -> None:
    for seed in range(20):
        problem = generate("MATH.RAT.DIV", seed=seed, difficulty=3)
        match = re.fullmatch(r"Compute ([-0-9/]+) ÷ ([-0-9/]+)\. Give the simplified result\.", problem.prompt)
        assert match
        expected = Fraction(match.group(1)) / Fraction(match.group(2))
        assert Fraction(problem.canonical_answer) == expected


def test_exponent_evaluation_matches_python_integer_power() -> None:
    for seed in range(20):
        problem = generate("MATH.EXP.EVALUATE", seed=seed, difficulty=3)
        match = re.fullmatch(r"Evaluate (\d+)\^(\d+)\.", problem.prompt)
        assert match
        assert int(problem.canonical_answer) == int(match.group(1)) ** int(match.group(2))


def test_square_root_truth_is_exact() -> None:
    for seed in range(20):
        problem = generate("MATH.ROOT.SQUARE", seed=seed, difficulty=3)
        radicand = int(re.search(r"root of (\d+)\?", problem.prompt).group(1))
        root = int(problem.canonical_answer)
        assert root >= 0
        assert root * root == radicand


def test_negative_inequality_reverses_direction() -> None:
    for seed in range(20):
        problem = generate("MATH.INEQ.NEGATIVE.FLIP", seed=seed, difficulty=3)
        match = re.fullmatch(r"Solve (-\d+)x ([<>]) (-?\d+)\.", problem.prompt)
        assert match
        coefficient, original, total = int(match.group(1)), match.group(2), int(match.group(3))
        boundary = total // coefficient
        expected_op = ">" if original == "<" else "<"
        assert problem.canonical_answer == f"x{expected_op}{boundary}"


def test_linear_sequence_uses_n_minus_one_intervals() -> None:
    for seed in range(20):
        problem = generate("MATH.FUNC.SEQUENCE.LINEAR", seed=seed, difficulty=3)
        match = re.fullmatch(
            r"A sequence starts at (-?\d+) and changes by (-?\d+) each term\. What is term (\d+)\?",
            problem.prompt,
        )
        assert match
        start, rate, n = map(int, match.groups())
        assert int(problem.canonical_answer) == start + (n - 1) * rate


def test_circle_formulas_use_radius_consistently() -> None:
    for seed in range(20):
        circumference = generate("MATH.GEO.CIRCLE.CIRCUMFERENCE", seed=seed, difficulty=3)
        area = generate("MATH.GEO.CIRCLE.AREA", seed=seed, difficulty=3)
        radius_c = int(re.search(r"radius (\d+)", circumference.prompt).group(1))
        radius_a = int(re.search(r"radius (\d+)", area.prompt).group(1))
        assert circumference.canonical_answer == f"{2 * radius_c}pi"
        assert area.canonical_answer == f"{radius_a * radius_a}pi"


def test_iqr_matches_independent_quartile_oracle() -> None:
    for seed in range(20):
        problem = generate("MATH.DATA.IQR", seed=seed, difficulty=3)
        values = [int(x) for x in re.search(r"\[(.*)\]", problem.prompt).group(1).split(", ")]
        lower, upper = values[:4], values[4:]
        q1 = (lower[1] + lower[2]) / 2
        q3 = (upper[1] + upper[2]) / 2
        assert float(problem.canonical_answer) == q3 - q1


def test_wave2_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario", "alberta"}
    for code in WAVE2_CODES:
        spec = FAMILIES[code]
        text = f"{spec.code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(jurisdiction in text for jurisdiction in forbidden)
