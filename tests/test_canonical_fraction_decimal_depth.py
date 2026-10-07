import random
import re
from fractions import Fraction

from app.domains import fraction_decimal_depth as domain

CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 31):
    return domain.build(code, random.Random(seed), 3)[:4]


def test_fraction_decimal_depth_has_sixteen_families() -> None:
    assert len(CODES) == 16
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}
    assert all(
        {mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES
    )


def test_fraction_decimal_depth_is_deterministic() -> None:
    for code in CODES:
        assert _build(code, 47) == _build(code, 47), code


def test_misconceptions_do_not_equal_truth() -> None:
    for code in CODES:
        for seed in range(15):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_improper_to_mixed_preserves_fraction_value() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.FRAC.IMPROPER.TO_MIXED", seed)
        n, d = map(int, re.search(r"Convert (\d+)/(\d+)", prompt).groups())
        whole, fraction = answer.split()
        rn, rd = map(int, fraction.split("/"))
        assert Fraction(n, d) == int(whole) + Fraction(rn, rd)


def test_mixed_to_improper_preserves_fraction_value() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.FRAC.MIXED.TO_IMPROPER", seed)
        whole, n, d = map(int, re.search(r"Convert (\d+) (\d+)/(\d+)", prompt).groups())
        an, ad = map(int, answer.split("/"))
        assert Fraction(an, ad) == whole + Fraction(n, d)



def _mixed_value(text: str) -> Fraction:
    if " " not in text:
        return Fraction(int(text), 1)
    whole, fraction = text.split()
    return Fraction(int(whole), 1) + Fraction(fraction)


def test_mixed_addition_matches_fraction_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.FRAC.MIXED.ADD", seed)
        match = re.fullmatch(
            r"Add (\d+) (\d+)/(\d+) \+ (\d+) (\d+)/(\d+)\.",
            prompt,
        )
        assert match
        w1, n1, d1, w2, n2, d2 = map(int, match.groups())
        expected = Fraction(w1, 1) + Fraction(n1, d1) + Fraction(w2, 1) + Fraction(n2, d2)
        assert _mixed_value(answer) == expected


def test_mixed_subtraction_matches_fraction_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.FRAC.MIXED.SUB", seed)
        match = re.fullmatch(
            r"Subtract (\d+) (\d+)/(\d+) - (\d+) (\d+)/(\d+)\.",
            prompt,
        )
        assert match
        w1, n1, d1, w2, n2, d2 = map(int, match.groups())
        expected = Fraction(w1, 1) + Fraction(n1, d1) - Fraction(w2, 1) - Fraction(n2, d2)
        assert _mixed_value(answer) == expected


def test_same_numerator_comparison_prefers_smaller_denominator() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.FRAC.COMPARE.SAME_NUMERATOR", seed)
        n1, d1, n2, d2 = map(int, re.fullmatch(r"Which is greater: (\d+)/(\d+) or (\d+)/(\d+)\?", prompt).groups())
        assert n1 == n2
        assert Fraction(answer) == max(Fraction(n1, d1), Fraction(n2, d2))


def test_decimal_rounding_matches_half_up_for_positive_values() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DEC.ROUND", seed)
        value = float(re.search(r"Round ([0-9.]+)", prompt).group(1))
        hundredths_digit = round(value * 100) % 10
        truncated = int(value * 10) / 10
        expected = truncated + (0.1 if hundredths_digit >= 5 else 0)
        assert abs(float(answer) - expected) < 1e-9


def test_power_of_ten_reasoning_is_exact() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DEC.POWER10", seed)
        value = float(re.search(r"What is ([0-9.]+)", prompt).group(1))
        assert abs(float(answer) - 10 * value) < 1e-9


def test_decimal_division_context_matches_equal_sharing() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DEC.WORD.DIV", seed)
        total, groups = re.fullmatch(
            r"([0-9.]+) liters are shared equally among (\d+) containers\. "
            r"How many liters go in each container\?",
            prompt,
        ).groups()
        assert abs(float(answer) - float(total) / int(groups)) < 1e-9


def test_fraction_decimal_depth_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario", "alberta"}
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)


def test_conceptual_fraction_decimal_visual_specs_are_deterministic() -> None:
    for code in (
        "MATH.FRAC.UNIT.MEANING",
        "MATH.DEC.FRACTION.TENTHS",
        "MATH.DEC.FRACTION.HUNDREDTHS",
    ):
        first = domain.build(code, random.Random(83), 2)
        second = domain.build(code, random.Random(83), 2)
        assert len(first) == 5
        assert first[4] == second[4]
        assert isinstance(first[4].get("type"), str)
        assert isinstance(first[4].get("aria_label"), str)
