import random

import pytest

from app.services.problem_generation import (
    _generate_addition_within_100,
    _generate_compare_length,
    _generate_equation_balance,
    _generate_fraction_halves_thirds_fourths,
    _generate_geometry_shapes,
    _generate_money_count,
    _generate_number_pattern,
    _generate_place_value_base_ten,
    _generate_subtraction_within_100,
    _generate_time_to_5_minutes,
    _generate_word_problem_add_sub_100,
)

@pytest.mark.parametrize("seed", range(100))
def test_grade2_shared_generators(seed):
    x=_generate_addition_within_100(random.Random(seed),2); p=x.parameters
    assert p and p["a"]+p["b"]<=100 and x.canonical_answer==str(p["a"]+p["b"])
    x=_generate_subtraction_within_100(random.Random(seed),2); p=x.parameters
    assert p and 0<=p["b"]<=p["a"]<=100 and x.canonical_answer==str(p["a"]-p["b"])
    x=_generate_word_problem_add_sub_100(random.Random(seed),2); p=x.parameters
    expected=p["a"]+p["b"] if p["operation"]=="add" else p["a"]-p["b"]
    assert 0<=expected<=100 and p["answer"]==expected and x.canonical_answer==str(expected)
    x=_generate_place_value_base_ten(random.Random(seed),2); p=x.parameters
    assert p["number"]==p["hundreds"]*100+p["tens"]*10+p["ones"]
    x=_generate_number_pattern(random.Random(seed),2); p=x.parameters
    assert p["answer"]==p["start"]+p["step"]*p["missing_index"] and x.canonical_answer==str(p["answer"])
    x=_generate_equation_balance(random.Random(seed),2); p=x.parameters
    assert p["c"]==p["a"]+p["b"] and x.canonical_answer==str({"a":p["a"],"b":p["b"],"c":p["c"]}[p["unknown"]])
    x=_generate_compare_length(random.Random(seed),2); p=x.parameters
    assert p["difference"]==abs(p["a"]-p["b"]) and x.canonical_answer==str(p["difference"])
    x=_generate_time_to_5_minutes(random.Random(seed),2); p=x.parameters
    assert 1<=p["hour"]<=12 and p["minute"]%5==0 and x.canonical_answer==f'{p["hour"]}:{p["minute"]:02d}'
    x=_generate_money_count(random.Random(seed),2); p=x.parameters
    cents=p["quarters"]*25+p["dimes"]*10+p["nickels"]*5+p["pennies"]
    assert p["total_cents"]==cents and x.canonical_answer=="$"+format(cents/100,".2f")
    x=_generate_fraction_halves_thirds_fourths(random.Random(seed),2); p=x.parameters
    assert p["denominator"] in {2,3,4} and 1<=p["numerator"]<=p["denominator"]
    x=_generate_geometry_shapes(random.Random(seed),2); p=x.parameters
    sides={"triangle":3,"square":4,"rectangle":4,"circle":0,"hexagon":6}
    assert p["sides"]==sides[p["shape"]] and x.canonical_answer==str(p["sides"])

@pytest.mark.parametrize("generator", [
    _generate_addition_within_100,_generate_subtraction_within_100,_generate_word_problem_add_sub_100,
    _generate_place_value_base_ten,_generate_number_pattern,_generate_equation_balance,_generate_compare_length,
    _generate_time_to_5_minutes,_generate_money_count,_generate_fraction_halves_thirds_fourths,_generate_geometry_shapes,
])
def test_grade2_repeatable(generator):
    assert generator(random.Random(20260928),2)==generator(random.Random(20260928),2)
