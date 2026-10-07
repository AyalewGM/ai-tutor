from fractions import Fraction
import random
import re

from app.domains import bivariate_sampling as domain


CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 37):
    return domain.build(code, random.Random(seed), 3)[:4]


def test_bivariate_sampling_batch_has_ten_families() -> None:
    assert len(CODES) == 10
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}
    assert all(
        {mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES
    )


def test_bivariate_sampling_is_deterministic() -> None:
    for code in CODES:
        assert _build(code, 61) == _build(code, 61), code


def test_misconceptions_do_not_collide_with_truth() -> None:
    for code in CODES:
        for seed in range(12):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_line_fit_prediction_matches_linear_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DATA.LINEFIT.PREDICT", seed)
        match = re.fullmatch(
            r"A line of best fit is y = (\d+)x \+ (\d+)\. "
            r"What value does the model predict at x = (\d+)\?",
            prompt,
        )
        assert match
        slope, intercept, x_value = map(int, match.groups())
        assert int(answer) == slope * x_value + intercept


def test_scatter_prediction_matches_linear_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DATA.SCATTER.PREDICT", seed)
        match = re.fullmatch(
            r"A bivariate data trend is modeled approximately by y = (\d+)x \+ (\d+)\. "
            r"Using the trend, predict y when x = (\d+)\.",
            prompt,
        )
        assert match
        slope, intercept, x_value = map(int, match.groups())
        assert int(answer) == slope * x_value + intercept


def test_two_way_relative_frequency_uses_row_total() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.DATA.TWOWAY.RELATIVE", seed)
        match = re.fullmatch(
            r"In one row of a two-way table, (\d+) students answered yes and (\d+) "
            r"answered no\. What fraction of students in this row answered yes\?",
            prompt,
        )
        assert match
        yes, no = map(int, match.groups())
        assert Fraction(answer) == Fraction(yes, yes + no)


def test_experimental_probability_matches_observed_frequency() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.PROB.EXPERIMENTAL", seed)
        match = re.fullmatch(
            r"An event occurred (\d+) times in (\d+) trials\. "
            r"What is the experimental probability\?",
            prompt,
        )
        assert match
        successes, trials = map(int, match.groups())
        assert Fraction(answer) == Fraction(successes, trials)


def test_expected_count_matches_probability_times_trials() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.PROB.EXPECTED_COUNT", seed)
        match = re.fullmatch(
            r"An event has probability (\d+)/(\d+)\. "
            r"About how many times should it occur in (\d+) trials\?",
            prompt,
        )
        assert match
        numerator, denominator, trials = map(int, match.groups())
        assert int(answer) == Fraction(numerator, denominator) * trials


def test_sampling_and_probability_depth_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario"}
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
