"""CENTER_SPREAD generator: mean, median, mode, range, dot-plot
reading, reversing a mean to a missing score and choosing a measure
of centre under an outlier, plus the STAT6 misconception rules."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import MISCONCEPTION_RULES, _normalize
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int, which: str | None = None) -> object:
    for seed in range(2500):
        generated = GENERATORS["CENTER_SPREAD"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") != tier:
            continue
        if which is not None and generated.parameters.get("which") != which:
            continue
        return generated
    raise AssertionError(f"no CENTER_SPREAD/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _correct_text(generated) -> str:
    return next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer)


def test_tier_coverage() -> None:
    assert _gen("mean", difficulty=1).parameters["tier"] == "mean"
    assert _gen("median", difficulty=2)
    assert _gen("dot_count", difficulty=2)
    assert _gen("dot_center", difficulty=2)
    assert _gen("mean_reverse", difficulty=3)
    assert _gen("best_measure", difficulty=3)
    assert _gen("range_mode", difficulty=1, which="range")
    assert _gen("range_mode", difficulty=1, which="mode")


def test_mean_is_the_exact_average() -> None:
    generated = _gen("mean", difficulty=1)
    data = generated.parameters["data"]
    assert int(_correct_text(generated)) == sum(data) // len(data)
    assert sum(data) % len(data) == 0


def test_median_uses_sorted_data_but_displays_unsorted() -> None:
    generated = _gen("median", difficulty=2)
    data = generated.parameters["data"]
    display = generated.parameters["display"]
    assert data == sorted(data)
    assert sorted(display) == data
    s = sorted(display)
    n = len(s)
    mid = n // 2
    med = Fraction(s[mid]) if n % 2 else Fraction(s[mid - 1] + s[mid], 2)
    assert _correct_text(generated) == (
        str(med.numerator) if med.denominator == 1 else str(med))


def test_range_and_mode_correctness() -> None:
    ranged = _gen("range_mode", difficulty=1, which="range")
    data = ranged.parameters["data"]
    assert _correct_text(ranged) == str(data[-1] - data[0])
    moded = _gen("range_mode", difficulty=1, which="mode")
    data = moded.parameters["data"]
    counts = {v: data.count(v) for v in set(data)}
    assert int(_correct_text(moded)) == max(counts, key=counts.get)
    assert max(counts.values()) > 1


def test_dot_count_and_dot_center_render_dot_plots() -> None:
    counted = _gen("dot_count", difficulty=2)
    data, value = counted.parameters["data"], counted.parameters["value"]
    assert _correct_text(counted) == str(data.count(value))
    spec = visualization_for(_as_problem(counted))
    assert spec is not None and spec["type"] == "dot_plot"
    centered = _gen("dot_center", difficulty=2)
    spec = visualization_for(_as_problem(centered))
    assert spec is not None and spec["type"] == "dot_plot"


def test_list_and_reverse_tiers_have_no_visual() -> None:
    for tier in ("mean", "median", "mean_reverse", "best_measure"):
        difficulty = 3 if tier in {"mean_reverse", "best_measure"} else 2
        assert visualization_for(_as_problem(_gen(tier, difficulty=difficulty))) is None


def test_mean_reverse_is_integer_and_deterministic() -> None:
    generated = _gen("mean_reverse", difficulty=3)
    n, mean = generated.parameters["n"], generated.parameters["mean"]
    known = generated.parameters["known"]
    assert generated.answer_kind == "INTEGER"
    assert int(generated.canonical_answer) == n * mean - sum(known)


def test_mean_reverse_misconception_rule_catches_total() -> None:
    generated = _gen("mean_reverse", difficulty=3)
    n, mean = generated.parameters["n"], generated.parameters["mean"]
    rule = next(
        r for r in MISCONCEPTION_RULES if r.__name__ == "_center_spread_errors")
    prompt = _normalize(generated.prompt)
    match = rule(prompt, str(n * mean), generated.canonical_answer)
    assert match is not None and match.code == "STAT6_001"
    mean_restated = rule(prompt, str(mean), generated.canonical_answer)
    assert mean_restated is not None and mean_restated.code == "STAT6_001"


def test_distractors_carry_misconception_tags() -> None:
    generated = _gen("median", difficulty=2)
    tagged = {c["text"]: c.get("misconception_code") for c in generated.choices}
    assert tagged[_correct_text(generated)] is None
    assert "STAT6_002" in tagged.values()


def test_prompt_variety() -> None:
    prompts = {
        GENERATORS["CENTER_SPREAD"](random.Random(seed), 3).prompt
        for seed in range(60)
    }
    assert len(prompts) > 40
