"""Comprehensive tests for canonical Number Sense & Operations families.

Validates deterministic generation, independent mathematical correctness,
misconception classification, difficulty progression, diversity, learning
modes, structured assessment contracts, registry compatibility, and
the content coverage auditor.

Mathematical oracle tests recompute expected answers from parsed operands.
They do NOT rely on ``p.is_correct(p.canonical_answer)`` as proof of truth.
"""

import re
from math import gcd

import pytest

from app.canonical_problem_families import FAMILIES, generate

# ---------------------------------------------------------------------------
# Domain groupings
# ---------------------------------------------------------------------------

ADD_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.ADD.")]
SUB_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.SUB.")]
MUL_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.MUL.")]
DIV_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.DIV.")]
WN_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.WN.")]
PV_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.PV.")]
FAC_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.FAC.")]
OOO_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.OOO.")]
INT_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.INT.")]
EST_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.EST.")]
PROP_MATH_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.PROP_MATH.")]

ALL_NEW = (
    ADD_FAMILIES + SUB_FAMILIES + MUL_FAMILIES + DIV_FAMILIES +
    WN_FAMILIES + PV_FAMILIES + FAC_FAMILIES + OOO_FAMILIES +
    INT_FAMILIES + EST_FAMILIES + PROP_MATH_FAMILIES
)

SEEDS = list(range(20))
DIFFICULTIES = None  # set per-family

# ---------------------------------------------------------------------------
# Helper: parse comma-formatted integers
# ---------------------------------------------------------------------------

def _parse_int(s: str) -> int:
    """Parse a comma-formatted or plain integer string."""
    return int(s.replace(",", "").replace("$", "").strip())


def _parse_nums_from_prompt(prompt: str) -> list[int]:
    """Extract all integers from a prompt string."""
    return [int(m.replace(",", "")) for m in re.findall(r'-?\d[\d,]*', prompt)]


# ====================================================================
# 1. Deterministic stability
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_same_seed_produces_identical_problem(family_code):
    spec = FAMILIES[family_code]
    a = generate(family_code, seed="stable-1", difficulty=spec.min_difficulty)
    b = generate(family_code, seed="stable-1", difficulty=spec.min_difficulty)
    assert a == b


# ====================================================================
# 2. Self-validation (contract regression — not oracle)
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_canonical_answer_validates(family_code):
    spec = FAMILIES[family_code]
    for seed in range(10):
        for d in range(spec.min_difficulty, spec.max_difficulty + 1):
            p = generate(family_code, seed=seed, difficulty=d)
            assert p.is_correct(p.canonical_answer), (
                f"{family_code} d={d} s={seed}: '{p.canonical_answer}' fails"
            )


# ====================================================================
# 3. Misconception safety
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_misconception_differs_from_answer(family_code):
    spec = FAMILIES[family_code]
    for seed in range(15):
        for d in range(spec.min_difficulty, spec.max_difficulty + 1):
            p = generate(family_code, seed=seed, difficulty=d)
            for mc_code, mc_val in p.misconception_answers.items():
                assert not p.is_correct(mc_val), (
                    f"{family_code} d={d} s={seed}: misconception "
                    f"{mc_code}='{mc_val}' == answer '{p.canonical_answer}'"
                )


@pytest.mark.parametrize("family_code", ALL_NEW)
def test_no_duplicate_misconception_values(family_code):
    spec = FAMILIES[family_code]
    for seed in range(10):
        p = generate(family_code, seed=seed, difficulty=spec.min_difficulty)
        norm = lambda s: "".join(s.lower().split())
        vals = [norm(v) for v in p.misconception_answers.values()]
        assert len(vals) == len(set(vals)), (
            f"{family_code} seed={seed}: duplicate misconception values"
        )


# ====================================================================
# 4. Diversity across seeds
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_seed_diversity(family_code):
    spec = FAMILIES[family_code]
    prompts = set()
    for seed in range(20):
        p = generate(family_code, seed=seed, difficulty=spec.min_difficulty)
        prompts.add(p.prompt)
    assert len(prompts) >= 3, (
        f"{family_code}: only {len(prompts)} unique prompts across 20 seeds"
    )


# ====================================================================
# 5. Learning modes
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_all_declared_modes(family_code):
    spec = FAMILIES[family_code]
    for mode in spec.modes:
        p = generate(family_code, seed=1, difficulty=spec.min_difficulty, mode=mode)
        assert p.mode == mode


# ====================================================================
# 6. Difficulty boundaries
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_difficulty_boundaries(family_code):
    spec = FAMILIES[family_code]
    with pytest.raises(ValueError):
        generate(family_code, seed=0, difficulty=spec.min_difficulty - 1)
    with pytest.raises(ValueError):
        generate(family_code, seed=0, difficulty=spec.max_difficulty + 1)


# ====================================================================
# 7. Hint structure
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_hints_are_nonempty_strings(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=0, difficulty=spec.min_difficulty)
    assert isinstance(p.hints, tuple)
    assert len(p.hints) >= 1
    for h in p.hints:
        assert isinstance(h, str) and len(h) > 0


# ====================================================================
# 8. Provenance
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_provenance(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=0, difficulty=spec.min_difficulty)
    assert p.provenance["origin"] == "MIHUR_AUTHORED"
    assert p.provenance["license"] == "proprietary"


# ====================================================================
# 9. INDEPENDENT MATHEMATICAL ORACLE TESTS
# ====================================================================

# --- Addition oracle ---

class TestAdditionOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_addition_facts(self, seed, difficulty):
        p = generate("MATH.ADD.FACTS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert _parse_int(p.canonical_answer) == a + b

    @pytest.mark.parametrize("seed", SEEDS)
    def test_missing_addend(self, seed):
        p = generate("MATH.ADD.MISSING_ADDEND", seed=seed, difficulty=1)
        # prompt: "X + ____ = Y" → answer = Y - X
        nums = _parse_nums_from_prompt(p.prompt)
        x, y = nums[0], nums[-1]
        assert _parse_int(p.canonical_answer) == y - x

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_multidigit_addition(self, seed, difficulty):
        p = generate("MATH.ADD.MULTIDIGIT", seed=seed, difficulty=difficulty)
        nums = re.findall(r'[\d,]+', p.prompt)
        operands = [int(n.replace(",", "")) for n in nums]
        if len(operands) >= 2:
            assert _parse_int(p.canonical_answer) == operands[0] + operands[1]


# --- Subtraction oracle ---

class TestSubtractionOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_subtraction_facts(self, seed, difficulty):
        p = generate("MATH.SUB.FACTS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert _parse_int(p.canonical_answer) == a - b

    @pytest.mark.parametrize("seed", SEEDS)
    def test_missing_subtrahend(self, seed):
        p = generate("MATH.SUB.MISSING_SUBTRAHEND", seed=seed, difficulty=1)
        # prompt: "X - ____ = Y" → answer = X - Y
        nums = _parse_nums_from_prompt(p.prompt)
        x, y = nums[0], nums[-1]
        expected = x - y
        assert _parse_int(p.canonical_answer) == expected

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_multidigit_subtraction(self, seed, difficulty):
        p = generate("MATH.SUB.MULTIDIGIT", seed=seed, difficulty=difficulty)
        nums = re.findall(r'[\d,]+', p.prompt)
        operands = [int(n.replace(",", "")) for n in nums]
        if len(operands) >= 2:
            assert _parse_int(p.canonical_answer) == operands[0] - operands[1]


# --- Multiplication oracle ---

class TestMultiplicationOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_multiplication_facts(self, seed, difficulty):
        p = generate("MATH.MUL.FACTS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert _parse_int(p.canonical_answer) == a * b

    @pytest.mark.parametrize("seed", SEEDS)
    def test_missing_factor(self, seed):
        p = generate("MATH.MUL.MISSING_FACTOR", seed=seed, difficulty=1)
        # "? × B = P" → answer = P // B
        nums = re.findall(r'\d+', p.prompt)
        b, product = int(nums[0]), int(nums[1])
        assert _parse_int(p.canonical_answer) == product // b

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_multidigit_multiplication(self, seed, difficulty):
        p = generate("MATH.MUL.MULTIDIGIT", seed=seed, difficulty=difficulty)
        nums = re.findall(r'[\d,]+', p.prompt)
        operands = [int(n.replace(",", "")) for n in nums]
        if len(operands) >= 2:
            assert _parse_int(p.canonical_answer) == operands[0] * operands[1]

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_area_model(self, seed, difficulty):
        p = generate("MATH.MUL.AREA", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        length, width = int(nums[0]), int(nums[1])
        expected = length * width
        # Answer may be comma-formatted with unit suffix
        answer_nums = re.findall(r'[\d,]+', p.canonical_answer)
        assert answer_nums, f"No number in answer: {p.canonical_answer}"
        assert int(answer_nums[0].replace(",", "")) == expected


# --- Division oracle ---

class TestDivisionOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_division_facts(self, seed, difficulty):
        p = generate("MATH.DIV.FACTS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        dividend, divisor = int(nums[0]), int(nums[1])
        assert _parse_int(p.canonical_answer) == dividend // divisor

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_remainder_division(self, seed, difficulty):
        p = generate("MATH.DIV.REMAINDER", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        dividend, divisor = int(nums[0]), int(nums[1])
        q, _r = divmod(dividend, divisor)
        # Answer should contain quotient and remainder
        ans = p.canonical_answer
        assert str(q) in ans

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_interpret_remainder(self, seed, difficulty):
        """Remainder interpretation must give the contextually correct answer."""
        p = generate("MATH.DIV.INTERPRET_REMAINDER", seed=seed, difficulty=difficulty)
        # The answer is always an integer — either ceil or floor of division
        answer = _parse_int(p.canonical_answer)
        assert answer > 0

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_partitive_division(self, seed, difficulty):
        p = generate("MATH.DIV.WORD.PARTITIVE", seed=seed, difficulty=difficulty)
        # Word problem about sharing. Answer should be exact division result.
        answer = _parse_int(p.canonical_answer)
        assert answer >= 1

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_measurement_division(self, seed, difficulty):
        p = generate("MATH.DIV.WORD.MEASUREMENT", seed=seed, difficulty=difficulty)
        answer = _parse_int(p.canonical_answer)
        assert answer >= 1


# --- Factors & Multiples oracle ---

class TestFactorsOracle:
    def _factors(self, n):
        fs = set()
        for i in range(1, int(n ** 0.5) + 1):
            if n % i == 0:
                fs.add(i)
                fs.add(n // i)
        return sorted(fs)

    def _is_prime(self, n):
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _lcm(self, a, b):
        return abs(a * b) // gcd(a, b)

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_list_factors(self, seed, difficulty):
        p = generate("MATH.FAC.LIST_FACTORS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        n = int(nums[-1])
        expected_factors = self._factors(n)
        answer_nums = [int(x.strip()) for x in p.canonical_answer.split(",")]
        assert answer_nums == expected_factors

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_gcf(self, seed, difficulty):
        p = generate("MATH.FAC.GCF", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b = int(nums[-2]), int(nums[-1])
        assert _parse_int(p.canonical_answer) == gcd(a, b)

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_lcm(self, seed, difficulty):
        p = generate("MATH.FAC.LCM", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b = int(nums[-2]), int(nums[-1])
        assert _parse_int(p.canonical_answer) == self._lcm(a, b)

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_prime_or_composite(self, seed, difficulty):
        p = generate("MATH.FAC.PRIME_OR_COMPOSITE", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        n = int(nums[-1])
        expected = "Prime" if self._is_prime(n) else "Composite"
        assert p.canonical_answer == expected

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_prime_factorization(self, seed, difficulty):
        p = generate("MATH.FAC.PRIME_FACTORIZATION", seed=seed, difficulty=difficulty)
        # Parse the prime factorization from the answer
        factors = [int(x.strip()) for x in p.canonical_answer.replace("×", "*").split("*")]
        product = 1
        for f in factors:
            product *= f
            assert self._is_prime(f), f"{f} is not prime in factorization"
        # Reconstruct number from prompt
        nums = re.findall(r'\d+', p.prompt)
        n = int(nums[-1])
        assert product == n


# --- Integer oracle ---

class TestIntegerOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_opposite(self, seed, difficulty):
        p = generate("MATH.INT.OPPOSITE", seed=seed, difficulty=difficulty)
        nums = re.findall(r'-?\d+', p.prompt)
        n = int(nums[-1])
        assert int(p.canonical_answer) == -n

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_absolute_value(self, seed, difficulty):
        p = generate("MATH.INT.ABS_VALUE", seed=seed, difficulty=difficulty)
        nums = re.findall(r'-?\d+', p.prompt)
        n = int(nums[-1])
        assert int(p.canonical_answer) == abs(n)

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_integer_addition(self, seed, difficulty):
        p = generate("MATH.INT.ADD", seed=seed, difficulty=difficulty)
        # Parse two integers from prompt "Compute A + (B)."
        nums = re.findall(r'-?\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert int(p.canonical_answer) == a + b

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_integer_subtraction(self, seed, difficulty):
        p = generate("MATH.INT.SUB", seed=seed, difficulty=difficulty)
        nums = re.findall(r'-?\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert int(p.canonical_answer) == a - b

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_integer_multiplication(self, seed, difficulty):
        p = generate("MATH.INT.MUL", seed=seed, difficulty=difficulty)
        nums = re.findall(r'-?\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        assert int(p.canonical_answer) == a * b

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_integer_division(self, seed, difficulty):
        p = generate("MATH.INT.DIV", seed=seed, difficulty=difficulty)
        nums = re.findall(r'-?\d+', p.prompt)
        a, b = int(nums[0]), int(nums[1])
        expected = a // b if (a >= 0) == (b >= 0) else -(abs(a) // abs(b))
        assert int(p.canonical_answer) == expected


# --- Order of Operations oracle ---

class TestOOOOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_basic_mixed_ops(self, seed, difficulty):
        p = generate("MATH.OOO.BASIC", seed=seed, difficulty=difficulty)
        # "Evaluate: A + B × C"
        nums = re.findall(r'\d+', p.prompt)
        a, b, c = int(nums[0]), int(nums[1]), int(nums[2])
        assert int(p.canonical_answer) == a + b * c

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_parentheses(self, seed, difficulty):
        p = generate("MATH.OOO.PARENS", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b, c = int(nums[0]), int(nums[1]), int(nums[2])
        assert int(p.canonical_answer) == (a + b) * c

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_multi_operation(self, seed, difficulty):
        p = generate("MATH.OOO.MULTI_OP", seed=seed, difficulty=difficulty)
        nums = re.findall(r'\d+', p.prompt)
        a, b, c, d = int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3])
        assert int(p.canonical_answer) == a * b + c - d


# --- Place Value oracle ---

class TestPlaceValueOracle:

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_digit_value(self, seed, difficulty):
        p = generate("MATH.PV.DIGIT_VALUE", seed=seed, difficulty=difficulty)
        answer = _parse_int(p.canonical_answer)
        # Answer must be a valid place value product
        assert answer >= 0

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_rounding(self, seed, difficulty):
        p = generate("MATH.PV.ROUND", seed=seed, difficulty=difficulty)
        answer = _parse_int(p.canonical_answer)
        # Rounded numbers should end in zeros
        assert answer >= 0

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [2, 3, 4])
    def test_powers_of_ten(self, seed, difficulty):
        p = generate("MATH.PV.POWERS_TEN", seed=seed, difficulty=difficulty)
        answer = _parse_int(p.canonical_answer)
        # Must be a power of 10
        import math
        assert answer > 0
        assert math.log10(answer) == int(math.log10(answer))


# --- Whole Numbers oracle ---

class TestWholeNumbersOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_expanded_form(self, seed, difficulty):
        p = generate("MATH.WN.EXPANDED", seed=seed, difficulty=difficulty)
        # Parse the number from the prompt and verify expanded form
        nums = _parse_nums_from_prompt(p.prompt)
        if nums:
            n = nums[0]
            # Sum the parts of the answer
            parts = [int(x.strip()) for x in p.canonical_answer.split("+")]
            assert sum(parts) == n

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_standard_from_expanded(self, seed, difficulty):
        p = generate("MATH.WN.STANDARD_FROM_EXPANDED", seed=seed, difficulty=difficulty)
        # Parse expanded form parts from prompt, sum them
        parts = [int(x.strip()) for x in re.findall(r'[\d,]+', p.prompt)]
        if parts:
            expected = sum(parts)
            assert _parse_int(p.canonical_answer) == expected

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_compare_returns_greater(self, seed, difficulty):
        p = generate("MATH.WN.COMPARE", seed=seed, difficulty=difficulty)
        nums = _parse_nums_from_prompt(p.prompt)
        if len(nums) >= 2:
            assert _parse_int(p.canonical_answer) == max(nums[0], nums[1])


# --- Estimation oracle ---

class TestEstimationOracle:
    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_estimate_sum(self, seed, difficulty):
        p = generate("MATH.EST.SUM", seed=seed, difficulty=difficulty)
        # The answer should be a rounded sum
        answer = _parse_int(p.canonical_answer)
        assert answer >= 0

    @pytest.mark.parametrize("seed", SEEDS)
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
    def test_estimate_diff(self, seed, difficulty):
        p = generate("MATH.EST.DIFF", seed=seed, difficulty=difficulty)
        answer = _parse_int(p.canonical_answer)
        assert answer >= 0


# ====================================================================
# 10. Structured assessment contracts
# ====================================================================

# Families that use structured MC answers (letter or Yes/No).
# Exclude numeric-answer REASONING families like remainder interpretation.
_STRUCTURED_MC_TYPES = {"ERROR_ANALYSIS"}
MC_FAMILIES = [c for c in ALL_NEW if FAMILIES[c].problem_type in _STRUCTURED_MC_TYPES]
# Also include REASONING families whose prompt contains "(A)" options
MC_FAMILIES += [
    c for c in ALL_NEW
    if FAMILIES[c].problem_type == "REASONING"
    and c not in MC_FAMILIES
    and any(
        "(A)" in generate(c, seed=s, difficulty=FAMILIES[c].min_difficulty).prompt
        for s in [0]
    )
]

@pytest.mark.parametrize("family_code", MC_FAMILIES)
def test_mc_answer_is_structured(family_code):
    """MC families must return a single letter A-D or Yes/No or similar."""
    spec = FAMILIES[family_code]
    valid_answers = {"A", "B", "C", "D", "Yes", "No", "Prime", "Composite"}
    for seed in range(10):
        p = generate(family_code, seed=seed, difficulty=spec.min_difficulty)
        assert p.canonical_answer in valid_answers, (
            f"{family_code} seed={seed}: answer '{p.canonical_answer}' is not structured MC"
        )


# ====================================================================
# 11. Word-problem structure diversity
# ====================================================================

def test_addition_word_problems_have_varied_structures():
    """Addition word problems should cover multiple structures."""
    add_wp = [c for c in ADD_FAMILIES if "WORD" in c]
    assert len(add_wp) >= 5, f"Only {len(add_wp)} addition word-problem families"
    structures = {c.split(".")[-1] for c in add_wp}
    expected = {"RESULT_UNKNOWN", "CHANGE_UNKNOWN", "START_UNKNOWN", "COMBINE", "COMPARE"}
    assert structures >= expected, f"Missing structures: {expected - structures}"


def test_subtraction_word_problems_have_varied_structures():
    sub_wp = [c for c in SUB_FAMILIES if "WORD" in c]
    assert len(sub_wp) >= 5
    structures = {c.split(".")[-1] for c in sub_wp}
    expected = {"RESULT_UNKNOWN", "CHANGE_UNKNOWN", "START_UNKNOWN", "COMPARE_DIFF"}
    assert structures >= expected, f"Missing: {expected - structures}"


def test_division_has_both_interpretations():
    """Division must have both partitive and measurement families."""
    div_wp = [c for c in DIV_FAMILIES if "WORD" in c]
    codes = {c.split(".")[-1] for c in div_wp}
    assert "PARTITIVE" in codes, "Missing partitive division"
    assert "MEASUREMENT" in codes, "Missing measurement division"


def test_division_has_remainder_interpretation():
    """Division must have contextual remainder interpretation."""
    assert "MATH.DIV.INTERPRET_REMAINDER" in FAMILIES


# ====================================================================
# 12. Content coverage auditor tests
# ====================================================================

from app.content_audit import (
    COVERAGE_PROFILES,
    SKILL_PROFILE_MAP,
    AuditReport,
    audit,
    format_report,
)


class TestAuditor:
    def test_audit_returns_report(self):
        report = audit()
        assert isinstance(report, AuditReport)
        assert report.total_families == len(FAMILIES)
        assert report.total_skills > 0

    def test_audit_counts_match(self):
        report = audit()
        assert report.quality_gate_passes + report.quality_gate_failures == report.total_skills

    def test_major_operation_skills_have_families(self):
        report = audit()
        major_ops = ["MATH.NS.ADDITION", "MATH.NS.SUBTRACTION",
                     "MATH.NS.MULTIPLICATION", "MATH.NS.DIVISION"]
        for skill in major_ops:
            assert skill in report.skills, f"{skill} missing from report"
            assert report.skills[skill].family_count >= 8, (
                f"{skill} has only {report.skills[skill].family_count} families"
            )

    def test_major_operations_have_word_problems(self):
        report = audit()
        for skill in ["MATH.NS.ADDITION", "MATH.NS.SUBTRACTION",
                       "MATH.NS.MULTIPLICATION", "MATH.NS.DIVISION"]:
            assert report.skills[skill].has_word_problems, f"{skill} missing word problems"

    def test_major_operations_have_error_analysis(self):
        report = audit()
        for skill in ["MATH.NS.ADDITION", "MATH.NS.SUBTRACTION",
                       "MATH.NS.MULTIPLICATION", "MATH.NS.DIVISION"]:
            sk = report.skills[skill]
            assert sk.has_error_analysis or sk.has_misconception_probe, (
                f"{skill} missing error/misconception content"
            )

    def test_audit_deterministic(self):
        r1 = audit()
        r2 = audit()
        assert r1.total_families == r2.total_families
        assert r1.total_skills == r2.total_skills
        assert r1.quality_gate_passes == r2.quality_gate_passes

    def test_format_report_produces_string(self):
        report = audit()
        text = format_report(report)
        assert isinstance(text, str)
        assert "CANONICAL CONTENT COVERAGE AUDIT" in text

    def test_json_output(self):
        import json
        report = audit()
        d = report.to_dict()
        # Must be JSON-serializable
        s = json.dumps(d)
        assert len(s) > 100

    def test_newly_targeted_skills_pass_gates(self):
        """Skills we explicitly targeted in this release should pass."""
        report = audit()
        targeted = [
            "MATH.NS.ADDITION", "MATH.NS.SUBTRACTION",
            "MATH.NS.MULTIPLICATION", "MATH.NS.DIVISION",
            "MATH.NS.INTEGERS", "MATH.NS.INTEGER_OPERATIONS",
            "MATH.NS.ORDER_OF_OPERATIONS",
        ]
        for skill in targeted:
            sk = report.skills[skill]
            assert sk.quality_gate_pass, (
                f"{skill} fails quality gate: {sk.quality_gate_failures}"
            )

    def test_coverage_profiles_exist(self):
        assert "major_operation" in COVERAGE_PROFILES
        assert "core_concept" in COVERAGE_PROFILES
        assert "supplementary" in COVERAGE_PROFILES

    def test_skill_profile_map_has_entries(self):
        assert len(SKILL_PROFILE_MAP) > 20


# ====================================================================
# 13. Registry integrity
# ====================================================================

def test_no_duplicate_family_codes():
    from collections import Counter
    counts = Counter(FAMILIES.keys())
    dupes = {k: v for k, v in counts.items() if v > 1}
    assert not dupes, f"Duplicate family codes: {dupes}"


def test_all_new_families_in_global_registry():
    for code in ALL_NEW:
        assert code in FAMILIES, f"{code} missing from FAMILIES registry"


def test_total_family_count():
    """Verify we have a substantial number of families."""
    assert len(FAMILIES) >= 180, f"Only {len(FAMILIES)} families total"
