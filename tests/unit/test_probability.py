"""PROBABILITY generator: likelihood classification, simple and
complementary probabilities, sample-space counts, and compound events —
plus the spinner and marble-bag visual specs."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(2000):
        generated = GENERATORS["PROBABILITY"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no PROBABILITY/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _items(params: dict) -> list[str]:
    return params.get("sections") or params["marbles"]


def _correct_text(generated) -> str:
    return next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
    )


def test_low_difficulty_only_likelihood_and_simple() -> None:
    for seed in range(200):
        generated = GENERATORS["PROBABILITY"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"likelihood", "simple"}


def test_likelihood_matches_the_share() -> None:
    bands = {
        "impossible": lambda p: p == 0,
        "unlikely": lambda p: 0 < p < Fraction(1, 2),
        "equally likely": lambda p: p == Fraction(1, 2),
        "likely": lambda p: Fraction(1, 2) < p < 1,
        "certain": lambda p: p == 1,
    }
    seen = set()
    for seed in range(2000):
        generated = GENERATORS["PROBABILITY"](random.Random(seed), 1)
        params = generated.parameters
        if params["tier"] != "likelihood":
            continue
        outcome = params["likelihood"]
        seen.add(outcome)
        items = _items(params)
        p = Fraction(items.count(params["target"]), len(items))
        assert bands[outcome](p)
        assert _correct_text(generated).startswith(outcome)
        for choice in generated.choices:
            if choice["id"] != generated.canonical_answer:
                assert choice["misconception_code"] == "PROB_004"
    assert seen == {"impossible", "unlikely", "equally likely", "likely", "certain"}


def test_simple_probability_is_favourable_over_total() -> None:
    for _ in range(120):
        generated = _gen("simple", difficulty=1)
        params = generated.parameters
        items = _items(params)
        assert _correct_text(generated) == str(
            Fraction(items.count(params["target"]), len(items))
        )


def test_complement_is_one_minus_the_event() -> None:
    for _ in range(120):
        generated = _gen("complement", difficulty=2)
        params = generated.parameters
        items = _items(params)
        n = len(items)
        c = items.count(params["target"])
        assert _correct_text(generated) == str(Fraction(n - c, n))
        # The signature distractor — the event itself — is always offered.
        tagged = [c2 for c2 in generated.choices if c2.get("misconception_code") == "PROB_003"]
        assert str(Fraction(c, n)) in {c2["text"] for c2 in tagged}


def test_count_outcomes_is_spinner_times_coin() -> None:
    for _ in range(100):
        generated = _gen("count_outcomes", difficulty=2)
        params = generated.parameters
        n = len(params["sections"])
        assert _correct_text(generated) == str(2 * n)
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags.get(str(n + 2)) == "PROB_002"
        assert tags.get(str(n)) == "PROB_002"


def test_compound_twice_squares_the_probability() -> None:
    for _ in range(120):
        generated = _gen("compound_twice", difficulty=3)
        params = generated.parameters
        items = params["sections"]
        c, n = items.count(params["target"]), len(items)
        assert _correct_text(generated) == str(Fraction(c * c, n * n))
        tagged = {c2["text"] for c2 in generated.choices
                  if c2.get("misconception_code") == "PROB_002"}
        assert str(Fraction(2 * c, n)) in tagged


def test_compound_or_adds_the_counts() -> None:
    for _ in range(120):
        generated = _gen("compound_or", difficulty=3)
        params = generated.parameters
        items = _items(params)
        n = len(items)
        c = items.count(params["target"])
        c2 = items.count(params["target_b"])
        assert _correct_text(generated) == str(Fraction(c + c2, n))
        tagged = {c2_["text"] for c2_ in generated.choices
                  if c2_.get("misconception_code") == "PROB_002"}
        assert str(Fraction(c * c2, n * n)) in tagged


def test_visuals_match_the_kind() -> None:
    for tier, difficulty in (("likelihood", 1), ("simple", 1), ("complement", 2),
                             ("compound_or", 3)):
        spinner_item = bag_item = None
        for seed in range(2000):
            generated = GENERATORS["PROBABILITY"](random.Random(seed), difficulty)
            if generated.parameters.get("tier") != tier:
                continue
            if generated.parameters["kind"] == "spinner" and spinner_item is None:
                spinner_item = generated
            if generated.parameters["kind"] == "bag" and bag_item is None:
                bag_item = generated
        assert spinner_item is not None and bag_item is not None
        assert visualization_for(_as_problem(spinner_item))["type"] == "spinner"
        assert visualization_for(_as_problem(bag_item))["type"] == "marble_bag"


def test_every_item_offers_four_distinct_choices() -> None:
    seen_tiers = set()
    for seed in range(1500):
        for difficulty in (1, 2, 3):
            generated = GENERATORS["PROBABILITY"](random.Random(seed), difficulty)
            seen_tiers.add(generated.parameters["tier"])
            texts = [c["text"] for c in generated.choices]
            assert len(texts) == 4
            assert len(set(texts)) == 4
    assert seen_tiers == {
        "likelihood", "simple", "complement",
        "count_outcomes", "compound_twice", "compound_or",
    }
