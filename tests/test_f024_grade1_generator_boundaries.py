import random

import pytest

from app.services.problem_generation import (
    _generate_addition_within_20,
    _generate_compare_numbers,
    _generate_equation_balance,
    _generate_fraction_halves_thirds_fourths,
    _generate_geometry_shapes,
    _generate_number_sequence,
    _generate_place_value_base_ten,
    _generate_subtraction_within_20,
    _generate_time_to_hour_half_hour,
    _generate_word_problem_add_sub_20,
)


@pytest.mark.parametrize("seed", range(100))
@pytest.mark.parametrize("difficulty", [1, 2])
def test_grade1_addition_generator_stays_within_domain(seed, difficulty):
    problem = _generate_addition_within_20(random.Random(seed), difficulty)
    p = problem.parameters
    assert p is not None
    assert 0 <= p["a"] <= 20
    assert 0 <= p["b"] <= 20
    assert p["a"] + p["b"] <= 20
    assert problem.canonical_answer == str(p["a"] + p["b"])


@pytest.mark.parametrize("seed", range(100))
@pytest.mark.parametrize("difficulty", [1, 2])
def test_grade1_subtraction_generator_is_nonnegative_and_correct(seed, difficulty):
    problem = _generate_subtraction_within_20(random.Random(seed), difficulty)
    p = problem.parameters
    assert p is not None
    assert 0 <= p["b"] <= p["a"] <= 20
    assert problem.canonical_answer == str(p["a"] - p["b"])


@pytest.mark.parametrize("seed", range(100))
def test_grade1_word_problem_arithmetic_matches_parameters(seed):
    problem = _generate_word_problem_add_sub_20(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    expected = p["a"] + p["b"] if p["operation"] == "add" else p["a"] - p["b"]
    assert 0 <= expected <= 20
    assert p["answer"] == expected
    assert problem.canonical_answer == str(expected)


@pytest.mark.parametrize("seed", range(100))
def test_grade1_place_value_round_trips_number(seed):
    problem = _generate_place_value_base_ten(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert p["place"] == "tens_and_ones"
    assert p["number"] == p["tens"] * 10 + p["ones"]
    assert 10 <= p["number"] <= 99
    assert problem.canonical_answer == f'{p["tens"]} tens and {p["ones"]} ones'


@pytest.mark.parametrize("seed", range(100))
def test_grade1_fraction_parts_are_valid(seed):
    problem = _generate_fraction_halves_thirds_fourths(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert p["denominator"] in {2, 3, 4}
    assert 1 <= p["numerator"] <= p["denominator"]
    assert problem.canonical_answer == f'{p["numerator"]}/{p["denominator"]}'


@pytest.mark.parametrize("seed", range(100))
def test_grade1_time_is_hour_or_half_hour_and_correct(seed):
    problem = _generate_time_to_hour_half_hour(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert 1 <= p["hour"] <= 12
    assert p["minute"] in {0, 30}
    assert problem.canonical_answer == f'{p["hour"]}:{p["minute"]:02d}'


@pytest.mark.parametrize("seed", range(100))
def test_grade1_number_sequence_answer_matches_progression(seed):
    problem = _generate_number_sequence(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert p["step"] in {1, 2, 5, 10}
    assert 1 <= p["missing_index"] <= 4
    assert p["answer"] == p["start"] + p["step"] * p["missing_index"]
    assert problem.canonical_answer == str(p["answer"])


@pytest.mark.parametrize("seed", range(100))
def test_grade1_compare_numbers_never_accidentally_equal(seed):
    problem = _generate_compare_numbers(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert 1 <= p["a"] <= 50
    assert 1 <= p["b"] <= 50
    assert p["a"] != p["b"]
    expected = ">" if p["a"] > p["b"] else "<"
    assert problem.canonical_answer == expected


@pytest.mark.parametrize("seed", range(100))
def test_grade1_equation_balance_is_algebraically_correct(seed):
    problem = _generate_equation_balance(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    assert p["c"] == p["a"] + p["b"]
    expected = {"a": p["a"], "b": p["b"], "c": p["c"]}[p["unknown"]]
    assert problem.canonical_answer == str(expected)


@pytest.mark.parametrize("seed", range(100))
def test_grade1_geometry_shape_answer_matches_shape(seed):
    problem = _generate_geometry_shapes(random.Random(seed), 1)
    p = problem.parameters
    assert p is not None
    sides = {"triangle": 3, "square": 4, "rectangle": 4, "circle": 0, "hexagon": 6}
    assert p["shape"] in sides
    assert p["sides"] == sides[p["shape"]]
    assert problem.canonical_answer == str(sides[p["shape"]])


@pytest.mark.parametrize(
    "generator",
    [
        _generate_addition_within_20,
        _generate_subtraction_within_20,
        _generate_word_problem_add_sub_20,
        _generate_place_value_base_ten,
        _generate_fraction_halves_thirds_fourths,
        _generate_time_to_hour_half_hour,
        _generate_number_sequence,
        _generate_compare_numbers,
        _generate_equation_balance,
        _generate_geometry_shapes,
    ],
)
def test_grade1_generators_are_repeatable_for_same_seed(generator):
    first = generator(random.Random(20260928), 1)
    second = generator(random.Random(20260928), 1)
    assert first == second
