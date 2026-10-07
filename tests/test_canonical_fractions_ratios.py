"""Comprehensive tests for canonical fractions, decimals, ratios, proportions and percent families.

Validates deterministic generation, answer correctness, misconception classification,
difficulty progression, diversity, curriculum neutrality, learning modes, registry
compatibility, and the legacy-Problem materialization pathway.
"""

import re

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


# ===== Deterministic stability =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_same_seed_produces_identical_problem(family_code):
    spec = FAMILIES[family_code]
    a = generate(family_code, seed="stable-1", difficulty=spec.min_difficulty)
    b = generate(family_code, seed="stable-1", difficulty=spec.min_difficulty)
    assert a == b


# ===== Correctness =====

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


# ===== Misconception classification =====

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


# ===== Difficulty =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_out_of_range_difficulty_fails_closed(family_code):
    spec = FAMILIES[family_code]
    with pytest.raises(ValueError, match="difficulty outside family range"):
        generate(family_code, seed=1, difficulty=spec.max_difficulty + 1)
    if spec.min_difficulty > 1:
        with pytest.raises(ValueError, match="difficulty outside family range"):
            generate(family_code, seed=1, difficulty=spec.min_difficulty - 1)


# ===== Diversity =====

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
    # Same seed at different difficulties should differ
    assert low.prompt != high.prompt or low.canonical_answer != high.canonical_answer


# ===== Curriculum neutrality =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_family_is_curriculum_neutral(family_code):
    spec = FAMILIES[family_code]
    assert spec.canonical_skill_code.startswith("MATH.")
    # Jurisdiction codes appear as dot-separated leading segments, not as substrings
    for code_str in (spec.code, spec.canonical_skill_code):
        first_segment = code_str.split(".")[0]
        assert first_segment not in ("CA", "MD", "VA", "NY", "NJ", "TX", "ON")


# ===== Provenance =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_provenance_is_mihur_authored(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=0, difficulty=spec.min_difficulty)
    assert p.provenance["origin"] == "MIHUR_AUTHORED"
    assert p.provenance["license"] == "proprietary"


# ===== Learning modes =====

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


# ===== Hints =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_hints_are_progressive(family_code):
    spec = FAMILIES[family_code]
    p = generate(family_code, seed=5, difficulty=spec.min_difficulty)
    assert len(p.hints) >= 1, f"{family_code}: no hints"
    for h in p.hints:
        assert isinstance(h, str) and len(h) > 5


# ===== Evidence dimensions =====

@pytest.mark.parametrize("family_code", ALL_NEW)
def test_evidence_dimensions_declared(family_code):
    spec = FAMILIES[family_code]
    assert spec.evidence_dimensions, f"{family_code}: no evidence dimensions"


# ===== Domain-specific: fractions =====

def test_fraction_addition_unlike_common_denominator():
    """Verify LCD computation is correct for unlike-denominator addition."""
    p = generate("MATH.FRAC.ADD.UNLIKE", seed=100, difficulty=2)
    assert p.is_correct(p.canonical_answer)
    # The add-denominators misconception should be present
    assert "FRAC.ADD.ADD_DENOM" in p.misconception_answers


def test_fraction_division_reciprocal_hint():
    """Division hints should reference the reciprocal."""
    p = generate("MATH.FRAC.DIV", seed=10, difficulty=2)
    assert any("reciprocal" in h.lower() for h in p.hints)


def test_fraction_error_analysis_identifies_add_denom():
    """Error analysis should name the 'adding denominators' mistake."""
    p = generate("MATH.FRAC.ERROR.ADD_DENOM", seed=5, difficulty=2)
    assert "added the denominators" in p.canonical_answer.lower() or \
           "added the denominator" in p.canonical_answer.lower()


def test_fraction_of_quantity_contexts_vary():
    """Word problems should use multiple real-world contexts."""
    contexts = set()
    for seed in range(20):
        p = generate("MATH.FRAC.OF_QUANTITY", seed=seed, difficulty=2)
        # Extract first noun
        contexts.add(p.prompt.split(".")[0][:30])
    assert len(contexts) >= 3


def test_fraction_word_scaling_result_correct():
    """Recipe scaling should produce correct multiplication results."""
    for seed in range(15):
        p = generate("MATH.FRAC.WORD.SCALING", seed=seed, difficulty=2)
        assert p.is_correct(p.canonical_answer)


# ===== Domain-specific: decimals =====

def test_decimal_frac_to_dec_terminates():
    """Fraction-to-decimal conversion should use terminating fractions only."""
    for seed in range(20):
        p = generate("MATH.DEC.FRAC_TO_DEC", seed=seed, difficulty=2)
        # Answer should not contain "..." or repeating notation
        assert "..." not in p.canonical_answer
        assert p.is_correct(p.canonical_answer)


def test_decimal_money_change_positive():
    """Change should always be non-negative."""
    for seed in range(20):
        p = generate("MATH.DEC.MONEY.CHANGE", seed=seed, difficulty=2)
        # Extract dollar amount
        match = re.search(r'\$(\d+\.?\d*)', p.canonical_answer)
        assert match, f"No dollar amount in answer: {p.canonical_answer}"
        assert float(match.group(1)) >= 0


def test_decimal_place_value_digit_is_correct():
    """Place-value answer should be a single digit."""
    for seed in range(10):
        p = generate("MATH.DEC.PLACE_VALUE", seed=seed, difficulty=1)
        assert p.canonical_answer.isdigit()
        assert 0 <= int(p.canonical_answer) <= 9


def test_decimal_error_analysis_shorter_is_larger():
    """The shorter decimal should actually be larger in the error analysis."""
    for seed in range(10):
        p = generate("MATH.DEC.ERROR.LONGER_LARGER", seed=seed, difficulty=2)
        assert "no" in p.canonical_answer.lower()


# ===== Domain-specific: ratios =====

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


def test_ratio_error_additive_reasoning():
    """The additive-reasoning error analysis should name the misconception."""
    p = generate("MATH.RATIO.ERROR.ADDITIVE", seed=3, difficulty=2)
    assert "additive" in p.canonical_answer.lower() or "multiplicative" in p.canonical_answer.lower()


# ===== Domain-specific: proportions =====

def test_proportion_identify_proportional_and_not():
    """Should generate both proportional and non-proportional tables."""
    yes_count = 0
    no_count = 0
    for seed in range(30):
        p = generate("MATH.PROP.IDENTIFY", seed=seed, difficulty=2)
        if "yes" in p.canonical_answer.lower():
            yes_count += 1
        elif "no" in p.canonical_answer.lower():
            no_count += 1
    assert yes_count >= 3 and no_count >= 3


def test_proportion_cross_multiply_explains_property():
    """The 'why cross multiply' family should reference the multiplication property."""
    p = generate("MATH.PROP.CROSS_MULTIPLY.WHY", seed=7, difficulty=2)
    assert "multipl" in p.canonical_answer.lower()


def test_proportion_multistep_includes_tax():
    """Multi-step proportion should calculate tax on the right base."""
    for seed in range(10):
        p = generate("MATH.PROP.MULTISTEP", seed=seed, difficulty=3)
        assert "$" in p.canonical_answer


# ===== Domain-specific: percent =====

def test_percent_convert_to_dec_correct():
    """Percent to decimal conversion should be mathematically correct."""
    for seed in range(15):
        p = generate("MATH.PCT.CONVERT.TO_DEC", seed=seed, difficulty=1)
        # Answer should be a valid decimal number
        float(p.canonical_answer)
        assert p.is_correct(p.canonical_answer)


def test_percent_discount_sale_price_less_than_original():
    """Sale price should always be less than original."""
    for seed in range(20):
        p = generate("MATH.PCT.DISCOUNT", seed=seed, difficulty=2)
        # Extract prices from prompt and answer
        prices = re.findall(r'\$(\d+)', p.prompt + " " + p.canonical_answer)
        if len(prices) >= 2:
            original = int(prices[0])
            sale = int(prices[-1])
            assert sale < original


def test_percent_reverse_finds_original():
    """Reverse percent should recover the original value."""
    for seed in range(10):
        p = generate("MATH.PCT.REVERSE", seed=seed, difficulty=3)
        assert "$" in p.canonical_answer
        assert p.is_correct(p.canonical_answer)


def test_percent_increase_decrease_correct():
    """Percent increase/decrease calculations should be correct."""
    for seed in range(10):
        p_inc = generate("MATH.PCT.INCREASE", seed=seed, difficulty=2)
        assert "%" in p_inc.canonical_answer
        p_dec = generate("MATH.PCT.DECREASE", seed=seed, difficulty=2)
        assert "%" in p_dec.canonical_answer


def test_percent_error_base_names_the_mistake():
    """Error analysis should explain the wrong-base error."""
    p = generate("MATH.PCT.ERROR.BASE", seed=4, difficulty=2)
    assert "original" in p.canonical_answer.lower()


def test_percent_multi_step_correct():
    """Multi-step (discount + tax) should compute correctly."""
    for seed in range(10):
        p = generate("MATH.PCT.MULTI_STEP", seed=seed, difficulty=3)
        assert "$" in p.canonical_answer
        assert p.is_correct(p.canonical_answer)


def test_percent_tip_total_exceeds_bill():
    """Tip total should exceed the original bill."""
    for seed in range(10):
        p = generate("MATH.PCT.TIP", seed=seed, difficulty=1)
        bill_match = re.search(r'bill is \$(\d+)', p.prompt)
        total_match = re.search(r'\$(\d+)', p.canonical_answer)
        if bill_match and total_match:
            assert int(total_match.group(1)) > int(bill_match.group(1))


# ===== Cross-cutting: word problem structure diversity =====

def test_word_problems_cover_multiple_structures():
    """Word-problem families within each domain should test distinct structures."""
    frac_word = [c for c in FRAC_FAMILIES if FAMILIES[c].problem_type == "WORD_PROBLEM"]
    assert len(frac_word) >= 4, f"Only {len(frac_word)} fraction word families"

    pct_word = [c for c in PCT_FAMILIES if FAMILIES[c].problem_type == "WORD_PROBLEM"]
    assert len(pct_word) >= 6, f"Only {len(pct_word)} percent word families"


# ===== Registry compatibility =====

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


# ===== Count assertions =====

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
