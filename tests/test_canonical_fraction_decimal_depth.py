import random
import re
from fractions import Fraction

from app.domains import fraction_decimal_depth as domain


CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 31):
    return domain.build(code, random.Random(seed), 3)


def test_fraction_decimal_depth_has_sixteen_families() -> None:
    assert len(CODES) == 16
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}\n    assert all({mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES)


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
        hundredths_digit = int(round(value * 100)) % 10
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
