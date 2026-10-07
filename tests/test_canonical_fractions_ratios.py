"""Comprehensive tests for canonical fractions, decimals, ratios, proportions and percent families.

Validates deterministic generation, independent mathematical correctness,
misconception classification, difficulty progression, diversity, curriculum
neutrality, learning modes, money semantics, structured assessment contracts,
registry compatibility, and the legacy-Problem materialization pathway.

Mathematical oracle tests recompute expected answers from parsed operands
using ``fractions.Fraction`` and ``decimal.Decimal``.  They do NOT rely on
``p.is_correct(p.canonical_answer)`` as proof of mathematical truth.
"""

import re
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

# ---------------------------------------------------------------------------
# Domain groupings
# ---------------------------------------------------------------------------

FRAC_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.FRAC.")]
DEC_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.DEC.")]
RATIO_FAMILIES = [c for c in FAMILIES if c.startswith(("MATH.RATIO.", "MATH.RATE."))]
PROP_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.PROP.")]
PCT_FAMILIES = [c for c in FAMILIES if c.startswith("MATH.PCT.")]

ALL_NEW = FRAC_FAMILIES + DEC_FAMILIES + RATIO_FAMILIES + PROP_FAMILIES + PCT_FAMILIES

_CENTS = Decimal("0.01")


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
        p = generate(family_code, seed=seed, difficulty=spec.min_difficulty)
        assert p.is_correct(p.canonical_answer), (
            f"{family_code} seed={seed}: canonical answer '{p.canonical_answer}' fails validation"
        )


@pytest.mark.parametrize("family_code", ALL_NEW)
def test_wrong_answer_does_not_validate(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=7, difficulty=spec.min_difficulty)
    assert not p.is_correct("DEFINITELY_WRONG_ANSWER_XYZ_123")


# ====================================================================
# 3. Misconception classification
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_misconception_answers_classified_deterministically(family_code):
    spec = FAMILIES[family_code]
    for seed in range(10):
        p = generate(family_code, seed=seed, difficulty=spec.min_difficulty)
        for mc_code, mc_answer in p.misconception_answers.items():
            classified = p.misconception_for(mc_answer)
            assert classified == mc_code, (
                f"{family_code} seed={seed}: expected {mc_code}, got {classified}"
            )


@pytest.mark.parametrize("family_code", ALL_NEW)
def test_misconceptions_never_match_correct_answer(family_code):
    spec = FAMILIES[family_code]
    for seed in range(30):
        for diff in range(spec.min_difficulty, spec.max_difficulty + 1):
            p = generate(family_code, seed=seed, difficulty=diff)
            for mc_code, mc_answer in p.misconception_answers.items():
                assert not p.is_correct(mc_answer), (
                    f"{family_code} seed={seed} d={diff}: "
                    f"misconception {mc_code} ({mc_answer}) matches correct ({p.canonical_answer})"
                )


# ====================================================================
# 4. Difficulty
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_out_of_range_difficulty_fails_closed(family_code):
    spec = FAMILIES[family_code]
    with pytest.raises(ValueError, match="difficulty outside family range"):
        generate(family_code, seed=1, difficulty=spec.max_difficulty + 1)
    if spec.min_difficulty > 1:
        with pytest.raises(ValueError, match="difficulty outside family range"):
            generate(family_code, seed=1, difficulty=spec.min_difficulty - 1)


# ====================================================================
# 5. Diversity
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_different_seeds_produce_diverse_variants(family_code):
    spec = FAMILIES[family_code]
    prompts = {
        generate(family_code, seed=s, difficulty=spec.min_difficulty).prompt
        for s in range(30)
    }
    assert len(prompts) >= 8, f"{family_code}: only {len(prompts)} unique prompts in 30 seeds"


@pytest.mark.parametrize("family_code", ALL_NEW)
def test_difficulty_changes_variant_space(family_code):
    spec = FAMILIES[family_code]
    if spec.max_difficulty == spec.min_difficulty:
        pytest.skip("single difficulty level")
    low = generate(family_code, seed=42, difficulty=spec.min_difficulty)
    high = generate(family_code, seed=42, difficulty=spec.max_difficulty)
    assert low.prompt != high.prompt or low.canonical_answer != high.canonical_answer


# ====================================================================
# 6. Curriculum neutrality
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_family_is_curriculum_neutral(family_code):
    spec = FAMILIES[family_code]
    assert spec.canonical_skill_code.startswith("MATH.")
    for code_str in (spec.code, spec.canonical_skill_code):
        first_segment = code_str.split(".")[0]
        assert first_segment not in ("CA", "MD", "VA", "NY", "NJ", "TX", "ON")


# ====================================================================
# 7. Provenance
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_provenance_is_mihur_authored(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=0, difficulty=spec.min_difficulty)
    assert p.provenance["origin"] == "MIHUR_AUTHORED"
    assert p.provenance["license"] == "proprietary"


# ====================================================================
# 8. Learning modes
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_supports_diagnostic_and_mastery(family_code):
    spec = FAMILIES[family_code]
    diag = generate(
        family_code, seed="diag", difficulty=spec.min_difficulty,
        mode=LearningMode.DIAGNOSTIC,
    )
    mastery = generate(
        family_code, seed="mastery", difficulty=spec.min_difficulty,
        mode=LearningMode.MASTERY,
    )
    assert diag.mode == LearningMode.DIAGNOSTIC
    assert mastery.mode == LearningMode.MASTERY
    assert diag.variant_id != mastery.variant_id


# ====================================================================
# 9. Hints — progressive scaffolding
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_hints_are_progressive(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=5, difficulty=spec.min_difficulty)
    assert len(p.hints) >= 1, f"{family_code}: no hints"
    for h in p.hints:
        assert isinstance(h, str) and len(h) > 5


def test_fraction_unlike_add_hints_progress():
    """Hints should progress: identify issue -> find LCD -> show converted sum."""
    p = generate("MATH.FRAC.ADD.UNLIKE", seed=7, difficulty=2)
    assert len(p.hints) >= 3
    assert "common denominator" in p.hints[0].lower() or "different" in p.hints[0].lower()
    assert "LCD" in p.hints[1] or "lcd" in p.hints[1].lower()


def test_discount_hints_progress():
    """Discount hints: find discount amount -> subtract."""
    p = generate("MATH.PCT.DISCOUNT", seed=5, difficulty=2)
    assert len(p.hints) >= 2
    assert "%" in p.hints[0] or "discount" in p.hints[0].lower()
    assert "subtract" in p.hints[1].lower() or "$" in p.hints[1]


def test_proportion_cross_multiply_hints_progress():
    """Cross-multiply explanation hints: LCD idea -> algebraic step -> property name."""
    p = generate("MATH.PROP.CROSS_MULTIPLY.WHY", seed=3, difficulty=2)
    assert len(p.hints) >= 2
    assert "LCD" in p.hints[0] or "multiply" in p.hints[0].lower()


def test_ratio_error_additive_hints_progress():
    """Additive error hints: ask about scale -> explain multiplication -> give answer."""
    p = generate("MATH.RATIO.ERROR.ADDITIVE", seed=3, difficulty=2)
    assert len(p.hints) >= 2
    assert "times" in p.hints[0].lower() or "larger" in p.hints[0].lower()
    assert "multipli" in p.hints[1].lower() or "addition" in p.hints[1].lower()


# ====================================================================
# 10. Evidence dimensions
# ====================================================================

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_evidence_dimensions_declared(family_code):
    spec = FAMILIES[family_code]
    assert spec.evidence_dimensions, f"{family_code}: no evidence dimensions"


# ====================================================================
# 11. INDEPENDENT MATHEMATICAL ORACLE TESTS
# ====================================================================

# ---------- Fractions ----------

@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_add_unlike(seed):
    """Independently verify fraction addition using fractions.Fraction."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.FRAC.ADD.UNLIKE"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.FRAC.ADD.UNLIKE", seed=seed, difficulty=diff)
        m = re.search(r"(\d+)/(\d+) \+ (\d+)/(\d+)", p.prompt)
        if not m:
            continue
        n1, d1, n2, d2 = (int(x) for x in m.groups())
        expected = Fraction(n1, d1) + Fraction(n2, d2)
        # Normalise the canonical answer
        ans = p.canonical_answer.strip()
        # Parse mixed number "W N/D" or simple "N/D" or integer "N"
        m2 = re.fullmatch(r"(\d+) (\d+)/(\d+)", ans)
        m3 = re.fullmatch(r"(\d+)/(\d+)", ans)
        m4 = re.fullmatch(r"(\d+)", ans)
        if m2:
            actual = Fraction(int(m2.group(1))) + Fraction(int(m2.group(2)), int(m2.group(3)))
        elif m3:
            actual = Fraction(int(m3.group(1)), int(m3.group(2)))
        elif m4:
            actual = Fraction(int(m4.group(1)))
        else:
            pytest.fail(f"Cannot parse answer: {ans}")
        assert actual == expected, (
            f"seed={seed} diff={diff}: {n1}/{d1}+{n2}/{d2} expected {expected} got {actual}"
        )


@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_subtract_unlike(seed):
    """Independently verify fraction subtraction."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.FRAC.SUB.UNLIKE"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.FRAC.SUB.UNLIKE", seed=seed, difficulty=diff)
        m = re.search(r"(\d+)/(\d+) [−\-] (\d+)/(\d+)", p.prompt)
        if not m:
            continue
        n1, d1, n2, d2 = (int(x) for x in m.groups())
        expected = Fraction(n1, d1) - Fraction(n2, d2)
        ans_m = re.fullmatch(r"(\d+)/(\d+)", p.canonical_answer.strip())
        ans_int = re.fullmatch(r"(\d+)", p.canonical_answer.strip())
        if ans_m:
            actual = Fraction(int(ans_m.group(1)), int(ans_m.group(2)))
        elif ans_int:
            actual = Fraction(int(ans_int.group(1)))
        else:
            pytest.fail(f"Cannot parse answer: {p.canonical_answer}")
        assert actual == expected, (
            f"seed={seed} diff={diff}: {n1}/{d1}-{n2}/{d2} expected {expected} got {actual}"
        )


@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_multiply(seed):
    """Independently verify fraction multiplication."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.FRAC.MUL"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.FRAC.MUL", seed=seed, difficulty=diff)
        m = re.search(r"(\d+)/(\d+) × (\d+)/(\d+)", p.prompt)
        if not m:
            continue
        n1, d1, n2, d2 = (int(x) for x in m.groups())
        expected = Fraction(n1, d1) * Fraction(n2, d2)
        ans = p.canonical_answer.strip()
        ans_m = re.fullmatch(r"(\d+)/(\d+)", ans)
        ans_int = re.fullmatch(r"(\d+)", ans)
        if ans_m:
            actual = Fraction(int(ans_m.group(1)), int(ans_m.group(2)))
        elif ans_int:
            actual = Fraction(int(ans_int.group(1)))
        else:
            pytest.fail(f"Cannot parse answer: {ans}")
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_divide(seed):
    """Independently verify fraction division."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.FRAC.DIV"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.FRAC.DIV", seed=seed, difficulty=diff)
        m = re.search(r"(\d+)/(\d+) ÷ (\d+)/(\d+)", p.prompt)
        if not m:
            continue
        n1, d1, n2, d2 = (int(x) for x in m.groups())
        expected = Fraction(n1, d1) / Fraction(n2, d2)
        ans = p.canonical_answer.strip()
        m2 = re.fullmatch(r"(\d+) (\d+)/(\d+)", ans)
        m3 = re.fullmatch(r"(\d+)/(\d+)", ans)
        m4 = re.fullmatch(r"(\d+)", ans)
        if m2:
            actual = Fraction(int(m2.group(1))) + Fraction(int(m2.group(2)), int(m2.group(3)))
        elif m3:
            actual = Fraction(int(m3.group(1)), int(m3.group(2)))
        elif m4:
            actual = Fraction(int(m4.group(1)))
        else:
            pytest.fail(f"Cannot parse answer: {ans}")
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_of_quantity(seed):
    """Independently verify fraction-of-quantity."""
    p = generate("MATH.FRAC.OF_QUANTITY", seed=seed, difficulty=2)
    m = re.search(r"(\d+)/(\d+) of (?:them|the)", p.prompt)
    total_m = re.search(r"has (\d+)|made (\d+)|holds (\d+)", p.prompt)
    if m and total_m:
        n, d = int(m.group(1)), int(m.group(2))
        total = int(next(g for g in total_m.groups() if g))
        expected = Fraction(n, d) * total
        assert expected == int(expected)  # must be exact integer
        assert int(expected) == int(p.canonical_answer)


@pytest.mark.parametrize("seed", range(20))
def test_oracle_fraction_simplify(seed):
    """Independently verify fraction simplification."""
    p = generate("MATH.FRAC.SIMPLIFY", seed=seed, difficulty=2)
    m = re.search(r"Simplify (\d+)/(\d+)", p.prompt)
    if not m:
        return
    n, d = int(m.group(1)), int(m.group(2))
    expected = Fraction(n, d)
    ans = p.canonical_answer.strip()
    ans_m = re.fullmatch(r"(\d+)/(\d+)", ans)
    ans_int = re.fullmatch(r"(\d+)", ans)
    if ans_m:
        actual = Fraction(int(ans_m.group(1)), int(ans_m.group(2)))
    elif ans_int:
        actual = Fraction(int(ans_int.group(1)))
    else:
        pytest.fail(f"Cannot parse: {ans}")
    assert actual == expected
    # Must be fully reduced
    if ans_m:
        from math import gcd
        assert gcd(int(ans_m.group(1)), int(ans_m.group(2))) == 1


# ---------- Decimals ----------

@pytest.mark.parametrize("seed", range(20))
def test_oracle_decimal_add(seed):
    """Independently verify decimal addition using Decimal."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.DEC.ADD"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.DEC.ADD", seed=seed, difficulty=diff)
        m = re.search(r"Add (\d+(?:\.\d+)?) \+ (\d+(?:\.\d+)?)", p.prompt)
        if not m:
            continue
        a, b = Decimal(m.group(1)), Decimal(m.group(2))
        expected = a + b
        actual = Decimal(p.canonical_answer.strip())
        assert actual == expected, f"seed={seed} d={diff}: {a}+{b} expected {expected} got {actual}"


@pytest.mark.parametrize("seed", range(20))
def test_oracle_decimal_subtract(seed):
    """Independently verify decimal subtraction."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.DEC.SUB"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.DEC.SUB", seed=seed, difficulty=diff)
        m = re.search(r"Subtract (\d+(?:\.\d+)?) [−\-] (\d+(?:\.\d+)?)", p.prompt)
        if not m:
            continue
        a, b = Decimal(m.group(1)), Decimal(m.group(2))
        expected = a - b
        actual = Decimal(p.canonical_answer.strip())
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_decimal_multiply(seed):
    """Independently verify decimal multiplication."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.DEC.MUL"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.DEC.MUL", seed=seed, difficulty=diff)
        m = re.search(r"Multiply (\d+(?:\.\d+)?) × (\d+(?:\.\d+)?)", p.prompt)
        if not m:
            continue
        a, b = Decimal(m.group(1)), Decimal(m.group(2))
        expected = a * b
        actual = Decimal(p.canonical_answer.strip())
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_decimal_frac_to_dec(seed):
    """Independently verify fraction-to-decimal conversion."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.DEC.FRAC_TO_DEC"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.DEC.FRAC_TO_DEC", seed=seed, difficulty=diff)
        m = re.search(r"Convert (\d+)/(\d+)", p.prompt)
        if not m:
            continue
        n, d = int(m.group(1)), int(m.group(2))
        expected = Decimal(n) / Decimal(d)
        expected = expected.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
        actual = Decimal(p.canonical_answer.strip())
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_decimal_money_change(seed):
    """Independently verify money change calculations using Decimal."""
    p = generate("MATH.DEC.MONEY.CHANGE", seed=seed, difficulty=2)
    paid_m = re.search(r"\$(\d+(?:\.\d+)?)\s+bill", p.prompt)
    price_m = re.search(r"costs \$(\d+(?:\.\d+)?)", p.prompt)
    if paid_m and price_m:
        paid = Decimal(paid_m.group(1))
        price = Decimal(price_m.group(1))
        expected = paid - price
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected


# ---------- Ratios ----------

@pytest.mark.parametrize("seed", range(20))
def test_oracle_unit_rate(seed):
    """Independently verify unit rate computation."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.RATE.UNIT"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.RATE.UNIT", seed=seed, difficulty=diff)
        m = re.search(r"(\d+) (?:widgets|miles|apples) in (\d+)|(\d+) (?:widgets|miles|apples) for \$(\d+)", p.prompt)
        if m:
            total = int(m.group(1) or m.group(3))
            qty = int(m.group(2) or m.group(4))
            expected = total // qty
            assert expected == int(p.canonical_answer), (
                f"seed={seed}: {total}/{qty} expected {expected} got {p.canonical_answer}"
            )


@pytest.mark.parametrize("seed", range(20))
def test_oracle_drt(seed):
    """Independently verify distance-rate-time using d=r*t."""
    for diff in range(2, 5):
        spec = FAMILIES["MATH.RATE.DRT"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.RATE.DRT", seed=seed, difficulty=diff)
        ans = p.canonical_answer
        if "how far" in p.prompt.lower():
            rate_m = re.search(r"at (\d+) miles per hour", p.prompt)
            time_m = re.search(r"for (\d+) hours", p.prompt)
            if rate_m and time_m:
                expected = int(rate_m.group(1)) * int(time_m.group(1))
                actual = int(re.search(r"\d+", ans).group())
                assert actual == expected
        elif "speed" in p.prompt.lower():
            dist_m = re.search(r"(\d+) miles", p.prompt)
            time_m = re.search(r"in (\d+) hours", p.prompt)
            if dist_m and time_m:
                expected = int(dist_m.group(1)) // int(time_m.group(1))
                actual = int(re.search(r"\d+", ans).group())
                assert actual == expected
        elif "how long" in p.prompt.lower():
            dist_m = re.search(r"(\d+) miles", p.prompt)
            rate_m = re.search(r"at (\d+) miles per hour", p.prompt)
            if dist_m and rate_m:
                expected = int(dist_m.group(1)) // int(rate_m.group(1))
                actual = int(re.search(r"\d+", ans).group())
                assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_recipe_scaling(seed):
    """Independently verify recipe scaling uses multiplicative ratio."""
    p = generate("MATH.RATIO.RECIPE", seed=seed, difficulty=2)
    m = re.search(r"uses (\d+) .+ for every (\d+) .+\. If you use (\d+)", p.prompt)
    if m:
        base_a, base_b, target_a = (int(x) for x in m.groups())
        assert target_a % base_a == 0, "target should be clean multiple"
        scale = target_a // base_a
        expected = base_b * scale
        assert int(p.canonical_answer) == expected


# ---------- Proportions ----------

@pytest.mark.parametrize("seed", range(20))
def test_oracle_proportion_missing_value(seed):
    """Independently verify proportional missing values: a/b = c/d => a*d == b*c."""
    for diff in range(1, 5):
        spec = FAMILIES["MATH.PROP.MISSING_VALUE"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PROP.MISSING_VALUE", seed=seed, difficulty=diff)
        # Format: "Solve A/B = C/?." or "Solve A/B = ?/D."
        m = re.search(r"Solve (\d+)/(\d+) = (\d+|\?)/(\d+|\?)", p.prompt)
        if not m:
            continue
        parts = list(m.groups())
        ans = int(p.canonical_answer)
        # Replace ? with the answer
        vals = [ans if x == "?" else int(x) for x in parts]
        a, b, c, d = vals
        # Cross-product must be equal
        assert a * d == b * c, (
            f"seed={seed} d={diff}: {a}/{b} != {c}/{d} (cross: {a*d} vs {b*c})"
        )


@pytest.mark.parametrize("seed", range(20))
def test_oracle_proportion_scale_factor(seed):
    """Independently verify scale factor: large = small * factor."""
    p = generate("MATH.PROP.SCALE_FACTOR", seed=seed, difficulty=2)
    m = re.search(r"(\d+) cm.*?(\d+) cm", p.prompt)
    if m:
        small, large = sorted([int(m.group(1)), int(m.group(2))])
        factor = int(p.canonical_answer)
        assert large == small * factor


@pytest.mark.parametrize("seed", range(20))
def test_oracle_proportion_identify(seed):
    """Verify proportional identification: parse table, check y/x constancy."""
    p = generate("MATH.PROP.IDENTIFY", seed=seed, difficulty=2)
    pairs = re.findall(r"\((\d+), (\d+)\)", p.prompt)
    if len(pairs) < 2:
        return
    ratios = [Fraction(int(y), int(x)) for x, y in pairs]
    is_proportional = len(set(ratios)) == 1
    ans = p.canonical_answer.strip()
    if is_proportional:
        assert ans == "Yes", f"Table is proportional but answer is {ans}"
    else:
        assert ans == "No", f"Table is not proportional but answer is {ans}"


# ---------- Percent (independent oracle) ----------

@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_of_quantity(seed):
    """Independently verify: X% of W == answer."""
    p = generate("MATH.PCT.OF_QUANTITY", seed=seed, difficulty=2)
    m = re.search(r"(\d+)% of (\d+)", p.prompt)
    if not m:
        m = re.search(r"has (\d+) .+\. (\d+)%", p.prompt)
        if m:
            total, pct = int(m.group(1)), int(m.group(2))
        else:
            return
    else:
        pct, total = int(m.group(1)), int(m.group(2))
    expected = Fraction(total * pct, 100)
    assert expected == int(expected)  # must be exact
    assert int(expected) == int(p.canonical_answer)


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_find_whole(seed):
    """Independently verify: part / (pct/100) == whole."""
    p = generate("MATH.PCT.FIND_WHOLE", seed=seed, difficulty=2)
    m = re.search(r"(\d+) is (\d+)% of what", p.prompt)
    if not m:
        return
    part, pct = int(m.group(1)), int(m.group(2))
    expected = Fraction(part * 100, pct)
    assert expected == int(expected)
    assert int(expected) == int(p.canonical_answer)


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_find_percent(seed):
    """Independently verify: part / whole * 100 == percent."""
    for diff in range(2, 5):
        spec = FAMILIES["MATH.PCT.FIND_PERCENT"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PCT.FIND_PERCENT", seed=seed, difficulty=diff)
        m = re.search(r"(\d+) is what percent of (\d+)", p.prompt)
        if not m:
            continue
        part, whole = int(m.group(1)), int(m.group(2))
        expected_pct = Fraction(part * 100, whole)
        stated = int(p.canonical_answer.rstrip("%"))
        assert expected_pct == stated, (
            f"seed={seed} d={diff}: {part}/{whole}*100 = {expected_pct} but stated {stated}%"
        )


@pytest.mark.parametrize("seed", range(30))
def test_oracle_pct_increase(seed):
    """Independently verify: (new-original)/original * 100 == stated percent."""
    for diff in range(2, 5):
        spec = FAMILIES["MATH.PCT.INCREASE"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PCT.INCREASE", seed=seed, difficulty=diff)
        m = re.search(r"from (\d+) to (\d+)", p.prompt)
        if not m:
            continue
        orig, new_v = int(m.group(1)), int(m.group(2))
        change = new_v - orig
        expected_pct = Fraction(change * 100, orig)
        stated = int(p.canonical_answer.rstrip("%"))
        assert expected_pct == stated, (
            f"seed={seed} d={diff}: ({new_v}-{orig})/{orig}*100 = {expected_pct} stated {stated}%"
        )


@pytest.mark.parametrize("seed", range(30))
def test_oracle_pct_decrease(seed):
    """Independently verify percent decrease."""
    for diff in range(2, 5):
        spec = FAMILIES["MATH.PCT.DECREASE"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PCT.DECREASE", seed=seed, difficulty=diff)
        m = re.search(r"from (\d+) to (\d+)", p.prompt)
        if not m:
            continue
        orig, new_v = int(m.group(1)), int(m.group(2))
        change = orig - new_v
        expected_pct = Fraction(change * 100, orig)
        stated = int(p.canonical_answer.rstrip("%"))
        assert expected_pct == stated


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_discount_money(seed):
    """Independently verify discount with Decimal: sale = price - price*pct/100."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.PCT.DISCOUNT"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PCT.DISCOUNT", seed=seed, difficulty=diff)
        price_m = re.search(r"costs \$(\d+(?:\.\d+)?)", p.prompt)
        pct_m = re.search(r"(\d+)% off", p.prompt)
        if not (price_m and pct_m):
            continue
        price = Decimal(price_m.group(1))
        pct = int(pct_m.group(1))
        savings = (price * pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        expected = price - savings
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected, (
            f"seed={seed} d={diff}: ${price} - {pct}% = ${expected} got ${actual}"
        )


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_tax_money(seed):
    """Independently verify tax with Decimal: total = price + price*tax_pct/100."""
    for diff in range(1, 4):
        spec = FAMILIES["MATH.PCT.TAX"]
        if not (spec.min_difficulty <= diff <= spec.max_difficulty):
            continue
        p = generate("MATH.PCT.TAX", seed=seed, difficulty=diff)
        price_m = re.search(r"costs \$(\d+(?:\.\d+)?)", p.prompt)
        pct_m = re.search(r"(\d+)%", p.prompt)
        if not (price_m and pct_m):
            continue
        price = Decimal(price_m.group(1))
        pct = int(pct_m.group(1))
        tax = (price * pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        expected = price + tax
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_tip_money(seed):
    """Independently verify tip: total = bill + bill*tip_pct/100."""
    p = generate("MATH.PCT.TIP", seed=seed, difficulty=1)
    bill_m = re.search(r"bill is \$(\d+(?:\.\d+)?)", p.prompt)
    pct_m = re.search(r"(\d+)% tip", p.prompt)
    if bill_m and pct_m:
        bill = Decimal(bill_m.group(1))
        pct = int(pct_m.group(1))
        tip = (bill * pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        expected = bill + tip
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_multi_step_money(seed):
    """Independently verify: final = (price - discount) + tax on discounted."""
    p = generate("MATH.PCT.MULTI_STEP", seed=seed, difficulty=3)
    price_m = re.search(r"costs \$(\d+(?:\.\d+)?)", p.prompt)
    disc_m = re.search(r"(\d+)% off", p.prompt)
    tax_m = re.search(r"(\d+)% sales tax", p.prompt)
    if price_m and disc_m and tax_m:
        price = Decimal(price_m.group(1))
        disc_pct = int(disc_m.group(1))
        tax_pct = int(tax_m.group(1))
        discount = (price * disc_pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        after = price - discount
        tax = (after * tax_pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        expected = after + tax
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected


@pytest.mark.parametrize("seed", range(20))
def test_oracle_pct_reverse(seed):
    """Independently verify reverse percent recovery."""
    p = generate("MATH.PCT.REVERSE", seed=seed, difficulty=3)
    ans_m = re.search(r"\$(\d+)", p.canonical_answer)
    if not ans_m:
        return
    original = int(ans_m.group(1))
    inc_m = re.search(r"(\d+)% increase.*?\$(\d+)", p.prompt)
    dec_m = re.search(r"(\d+)% discount.*?\$(\d+)", p.prompt)
    if inc_m:
        pct, final = int(inc_m.group(1)), int(inc_m.group(2))
        # original + original*pct/100 = final => original*(100+pct)/100 = final
        expected_orig = Fraction(final * 100, 100 + pct)
        assert expected_orig == original
    elif dec_m:
        pct, final = int(dec_m.group(1)), int(dec_m.group(2))
        expected_orig = Fraction(final * 100, 100 - pct)
        assert expected_orig == original


@pytest.mark.parametrize("seed", range(20))
def test_oracle_prop_multistep_money(seed):
    """Independently verify proportional multi-step with Decimal."""
    p = generate("MATH.PROP.MULTISTEP", seed=seed, difficulty=3)
    m = re.search(r"cost \$(\d+(?:\.\d+)?) each.*?(\d+) pens.*?(\d+)%", p.prompt)
    if m:
        price_per = Decimal(m.group(1))
        qty = int(m.group(2))
        tax_pct = int(m.group(3))
        subtotal = price_per * qty
        tax = (subtotal * tax_pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)
        expected = subtotal + tax
        actual = Decimal(p.canonical_answer.replace("$", ""))
        assert actual == expected


# ====================================================================
# 12. Money format — non-integer dollar amounts exist
# ====================================================================

def test_money_families_produce_cent_amounts():
    """At least some discount/tax/tip problems should have non-integer dollar answers."""
    non_integer_count = 0
    for fc in ["MATH.PCT.DISCOUNT", "MATH.PCT.TAX", "MATH.PCT.TIP", "MATH.PCT.MULTI_STEP"]:
        spec = FAMILIES[fc]
        for seed in range(30):
            p = generate(fc, seed=seed, difficulty=spec.min_difficulty)
            val = Decimal(p.canonical_answer.replace("$", ""))
            if val != val.to_integral_value():
                non_integer_count += 1
    assert non_integer_count >= 10, (
        f"Only {non_integer_count} non-integer-dollar answers — money families should produce "
        "realistic cent amounts"
    )


# ====================================================================
# 13. Structured deterministic assessment — error analysis / reasoning
# ====================================================================

def test_frac_error_add_denom_is_structured_mc():
    """Error analysis answer should be a single letter (A-D), not prose."""
    for seed in range(10):
        p = generate("MATH.FRAC.ERROR.ADD_DENOM", seed=seed, difficulty=2)
        assert p.canonical_answer in ("A", "B", "C", "D"), (
            f"Expected structured MC, got: {p.canonical_answer}"
        )
        assert "(A)" in p.prompt


def test_dec_error_longer_larger_is_structured_mc():
    """Decimal error analysis should be structured MC."""
    for seed in range(10):
        p = generate("MATH.DEC.ERROR.LONGER_LARGER", seed=seed, difficulty=2)
        assert p.canonical_answer in ("A", "B", "C"), (
            f"Expected structured MC, got: {p.canonical_answer}"
        )


def test_ratio_error_additive_is_structured_mc():
    """Additive reasoning error should be structured MC."""
    for seed in range(10):
        p = generate("MATH.RATIO.ERROR.ADDITIVE", seed=seed, difficulty=2)
        assert p.canonical_answer in ("A", "B", "C", "D"), (
            f"Expected structured MC, got: {p.canonical_answer}"
        )


def test_pct_error_base_is_structured_mc():
    """Wrong-base error analysis should be structured MC."""
    for seed in range(10):
        p = generate("MATH.PCT.ERROR.BASE", seed=seed, difficulty=2)
        assert p.canonical_answer in ("A", "B", "C", "D"), (
            f"Expected structured MC, got: {p.canonical_answer}"
        )


def test_prop_identify_is_yes_no():
    """Proportional identification should be Yes/No."""
    for seed in range(10):
        p = generate("MATH.PROP.IDENTIFY", seed=seed, difficulty=2)
        assert p.canonical_answer in ("Yes", "No")


def test_prop_nonproportional_is_yes_no():
    """Non-proportional should be Yes/No."""
    for seed in range(10):
        p = generate("MATH.PROP.NONPROPORTIONAL", seed=seed, difficulty=2)
        assert p.canonical_answer in ("Yes", "No")


def test_prop_cross_multiply_is_structured_mc():
    """Cross-multiply reasoning should be MC."""
    for seed in range(10):
        p = generate("MATH.PROP.CROSS_MULTIPLY.WHY", seed=seed, difficulty=2)
        assert p.canonical_answer in ("A", "B", "C", "D")


def test_frac_benchmark_is_structured_mc():
    """Benchmark estimation should produce one of the benchmark values."""
    for seed in range(10):
        p = generate("MATH.FRAC.ESTIMATE.BENCHMARK", seed=seed, difficulty=2)
        assert p.canonical_answer in ("0", "1/4", "1/2", "3/4", "1")


# ====================================================================
# 14. Domain-specific invariants
# ====================================================================

def test_fraction_division_reciprocal_hint():
    """Division hints should reference the reciprocal."""
    p = generate("MATH.FRAC.DIV", seed=10, difficulty=2)
    assert any("reciprocal" in h.lower() for h in p.hints)


def test_fraction_of_quantity_contexts_vary():
    """Word problems should use multiple real-world contexts."""
    contexts = set()
    for seed in range(20):
        p = generate("MATH.FRAC.OF_QUANTITY", seed=seed, difficulty=2)
        contexts.add(p.prompt.split(".")[0][:30])
    assert len(contexts) >= 3


def test_decimal_frac_to_dec_terminates():
    """Fraction-to-decimal conversion should use terminating fractions only."""
    for seed in range(20):
        p = generate("MATH.DEC.FRAC_TO_DEC", seed=seed, difficulty=2)
        assert "..." not in p.canonical_answer
        assert p.is_correct(p.canonical_answer)


def test_decimal_money_change_positive():
    """Change should always be non-negative."""
    for seed in range(20):
        p = generate("MATH.DEC.MONEY.CHANGE", seed=seed, difficulty=2)
        match = re.search(r'\$(\d+\.?\d*)', p.canonical_answer)
        assert match, f"No dollar amount in answer: {p.canonical_answer}"
        assert float(match.group(1)) >= 0


def test_decimal_place_value_digit_is_correct():
    """Place-value answer should be a single digit."""
    for seed in range(10):
        p = generate("MATH.DEC.PLACE_VALUE", seed=seed, difficulty=1)
        assert p.canonical_answer.isdigit()
        assert 0 <= int(p.canonical_answer) <= 9


def test_ratio_interpret_colon_format():
    """Ratio answers should use colon notation."""
    for seed in range(10):
        p = generate("MATH.RATIO.INTERPRET", seed=seed, difficulty=1)
        assert ":" in p.canonical_answer


def test_ratio_table_missing_value_integer():
    """Ratio table missing values should be positive integers."""
    for seed in range(15):
        p = generate("MATH.RATIO.TABLE.MISSING", seed=seed, difficulty=2)
        assert p.canonical_answer.isdigit()
        assert int(p.canonical_answer) > 0


def test_rate_compare_requires_unit_rate():
    """Rate comparison hints should reference unit rates."""
    p = generate("MATH.RATE.COMPARE", seed=5, difficulty=2)
    assert any("unit rate" in h.lower() for h in p.hints)


def test_drt_covers_all_unknowns():
    """Distance-rate-time should generate problems for all three unknowns."""
    unknowns = set()
    for seed in range(50):
        p = generate("MATH.RATE.DRT", seed=seed, difficulty=2)
        if "how far" in p.prompt.lower():
            unknowns.add("distance")
        elif "speed" in p.prompt.lower():
            unknowns.add("rate")
        elif "how long" in p.prompt.lower():
            unknowns.add("time")
    assert len(unknowns) >= 2, f"Only found unknowns: {unknowns}"


def test_proportion_identify_proportional_and_not():
    """Should generate both proportional and non-proportional tables."""
    yes_count = sum(
        1 for seed in range(30)
        if generate("MATH.PROP.IDENTIFY", seed=seed, difficulty=2).canonical_answer == "Yes"
    )
    assert 3 <= yes_count <= 27  # both outcomes exist


def test_percent_discount_sale_less_than_original():
    """Sale price should always be less than original."""
    for seed in range(20):
        p = generate("MATH.PCT.DISCOUNT", seed=seed, difficulty=2)
        price_m = re.search(r"costs \$(\d+(?:\.\d+)?)", p.prompt)
        sale = Decimal(p.canonical_answer.replace("$", ""))
        if price_m:
            assert sale < Decimal(price_m.group(1))


def test_percent_tip_total_exceeds_bill():
    """Tip total should exceed the original bill."""
    for seed in range(10):
        p = generate("MATH.PCT.TIP", seed=seed, difficulty=1)
        bill_m = re.search(r"bill is \$(\d+(?:\.\d+)?)", p.prompt)
        total = Decimal(p.canonical_answer.replace("$", ""))
        if bill_m:
            assert total > Decimal(bill_m.group(1))


# ====================================================================
# 15. Cross-cutting: word problem structure diversity
# ====================================================================

def test_word_problems_cover_multiple_structures():
    """Word-problem families within each domain should test distinct structures."""
    frac_word = [c for c in FRAC_FAMILIES if FAMILIES[c].problem_type == "WORD_PROBLEM"]
    assert len(frac_word) >= 4, f"Only {len(frac_word)} fraction word families"
    pct_word = [c for c in PCT_FAMILIES if FAMILIES[c].problem_type == "WORD_PROBLEM"]
    assert len(pct_word) >= 6, f"Only {len(pct_word)} percent word families"


# ====================================================================
# 16. Registry compatibility
# ====================================================================

def test_all_new_families_are_in_global_registry():
    """Every new domain family should appear in FAMILIES and have a valid spec."""
    for code in ALL_NEW:
        spec = FAMILIES[code]
        assert spec.code == code
        assert spec.canonical_skill_code.startswith("MATH.")
        assert spec.min_difficulty <= spec.max_difficulty
        assert spec.modes


def test_materialization_produces_correct_solution_dict():
    """GeneratedProblem should carry all data needed for legacy Problem.solution."""
    p = generate("MATH.FRAC.ADD.UNLIKE", seed=7, difficulty=2)
    assert p.family_code == "MATH.FRAC.ADD.UNLIKE"
    assert p.provenance["origin"] == "MIHUR_AUTHORED"
    assert p.canonical_skill_code.startswith("MATH.")
    assert isinstance(p.hints, tuple) and len(p.hints) >= 1
    assert isinstance(p.misconception_answers, dict)


# ====================================================================
# 17. Count assertions
# ====================================================================

def test_family_counts():
    """Verify expected family counts by domain."""
    assert len(FRAC_FAMILIES) >= 15
    assert len(DEC_FAMILIES) >= 10
    assert len(RATIO_FAMILIES) >= 8
    assert len(PROP_FAMILIES) >= 7
    assert len(PCT_FAMILIES) >= 14
    assert len(ALL_NEW) >= 55


def test_evidence_dimension_coverage():
    """Verify that evidence dimensions cover all required types."""
    all_dims = set()
    for code in ALL_NEW:
        all_dims.update(FAMILIES[code].evidence_dimensions)
    expected = {
        "procedural_fluency", "conceptual_understanding", "modeling",
        "transfer", "comparison", "estimation", "reasoning",
        "error_analysis", "misconception_probe", "representation",
        "number_sense",
    }
    missing = expected - all_dims
    assert not missing, f"Missing evidence dimensions: {missing}"


def test_problem_type_coverage():
    """Verify variety of problem types across domains."""
    types = {FAMILIES[c].problem_type for c in ALL_NEW}
    assert "WORD_PROBLEM" in types
    assert "ERROR_ANALYSIS" in types
    assert "COMPARISON" in types
    assert "ESTIMATION" in types
    assert "CONVERSION" in types
    assert "REASONING" in types
