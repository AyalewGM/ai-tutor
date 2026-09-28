import random
from decimal import Decimal
from fractions import Fraction

import pytest

from app.services.problem_generation import (
    _generate_add_subtract_unlike_fractions, _generate_angle_measurement,
    _generate_area_perimeter_rectangle, _generate_coordinate_plane,
    _generate_decimal_operations, _generate_decimal_place_value,
    _generate_divide_fractions, _generate_division_within_100,
    _generate_elapsed_time, _generate_equal_groups, _generate_equal_sharing,
    _generate_fraction_add_subtract_like, _generate_fraction_compare,
    _generate_fraction_equivalence, _generate_fraction_on_number_line,
    _generate_long_division, _generate_measurement_conversion,
    _generate_multi_digit_multiplication, _generate_multiplication_within_100,
    _generate_multiply_by_whole, _generate_multiply_fractions,
    _generate_powers_of_ten, _generate_rectangle_area, _generate_unit_fraction,
    _generate_volume, _generate_word_problem_multiply_divide_100,
)

@pytest.mark.parametrize("seed", range(100))
def test_grade3_core_arithmetic(seed):
    for gen in (_generate_equal_groups,_generate_equal_sharing,_generate_multiplication_within_100,_generate_division_within_100):
        x=gen(random.Random(seed),3); p=x.parameters
        if "rows" in p: expected=p["rows"]*p["columns"]
        elif "groups" in p: expected=p["group_size"]
        elif p.get("operation")=="×": expected=p["a"]*p["b"]
        else: expected=p["a"]//p["b"]
        assert x.canonical_answer==str(expected)
    x=_generate_word_problem_multiply_divide_100(random.Random(seed),3); p=x.parameters
    expected=p["a"]*p["b"] if p["operation"]=="multiply" else p["a"]//p["b"]
    assert p["answer"]==expected and x.canonical_answer==str(expected)
    x=_generate_unit_fraction(random.Random(seed),3); p=x.parameters
    assert p["denominator"]>1 and 1<=p["numerator"]<p["denominator"]
    x=_generate_rectangle_area(random.Random(seed),3); p=x.parameters
    assert x.canonical_answer==str(p["rows"]*p["columns"])
    x=_generate_elapsed_time(random.Random(seed),3); p=x.parameters
    assert p["elapsed"] in {15,30,45,60,90} and x.canonical_answer==str(p["elapsed"])

@pytest.mark.parametrize("seed", range(100))
def test_grade4_fraction_geometry_measurement(seed):
    x=_generate_fraction_equivalence(random.Random(seed),4); p=x.parameters
    assert Fraction(p["original_numerator"],p["original_denominator"])==Fraction(p["target_numerator"],p["target_denominator"])
    x=_generate_fraction_compare(random.Random(seed),4); p=x.parameters
    a=Fraction(p["numerator1"],p["denominator1"]); b=Fraction(p["numerator2"],p["denominator2"])
    assert x.canonical_answer==(">" if a>b else "<" if a<b else "=")
    x=_generate_fraction_on_number_line(random.Random(seed),4); p=x.parameters
    assert 0<Fraction(p["numerator"],p["denominator"])<1
    x=_generate_fraction_add_subtract_like(random.Random(seed),4); p=x.parameters
    a=Fraction(p["n1"],p["denominator"]); b=Fraction(p["n2"],p["denominator"])
    expected=a+b if p["operation"]=="+" else a-b
    assert x.canonical_answer==(str(expected.numerator) if expected.denominator==1 else f"{expected.numerator}/{expected.denominator}")
    x=_generate_area_perimeter_rectangle(random.Random(seed),4); p=x.parameters
    expected=p["length"]*p["width"] if p["measure"]=="area" else 2*(p["length"]+p["width"])
    assert x.canonical_answer==str(expected)
    x=_generate_angle_measurement(random.Random(seed),4); p=x.parameters
    assert 0<p["angle"]<180 and x.canonical_answer==str(p["angle"])
    x=_generate_measurement_conversion(random.Random(seed),4); p=x.parameters
    assert x.canonical_answer==str(p["value"]*p["factor"])

@pytest.mark.parametrize("seed", range(100))
def test_grade5_fraction_decimal_volume_coordinate(seed):
    x=_generate_multi_digit_multiplication(random.Random(seed),5); p=x.parameters
    assert x.canonical_answer==str(p["a"]*p["b"])
    x=_generate_long_division(random.Random(seed),5); p=x.parameters
    assert p["dividend"]==p["divisor"]*p["quotient"] and x.canonical_answer==str(p["quotient"])
    x=_generate_multiply_by_whole(random.Random(seed),5); p=x.parameters
    assert Fraction(x.canonical_answer)==p["whole"]*Fraction(p["numerator"],p["denominator"])
    x=_generate_add_subtract_unlike_fractions(random.Random(seed),5); p=x.parameters
    a=Fraction(p["numerator1"],p["denominator1"]); b=Fraction(p["numerator2"],p["denominator2"])
    expected=a+b if p["operation"]=="+" else a-b
    assert Fraction(x.canonical_answer)==expected and expected>0
    x=_generate_multiply_fractions(random.Random(seed),5); p=x.parameters
    assert Fraction(x.canonical_answer)==Fraction(p["numerator1"],p["denominator1"])*Fraction(p["numerator2"],p["denominator2"])
    x=_generate_divide_fractions(random.Random(seed),5); p=x.parameters
    assert Fraction(x.canonical_answer)==Fraction(p["whole"])/Fraction(p["numerator"],p["denominator"])
    x=_generate_decimal_place_value(random.Random(seed),5); p=x.parameters
    assert p["place"] in {"tenths","hundredths"} and 0<=p["digit"]<=9
    x=_generate_decimal_operations(random.Random(seed),5); p=x.parameters
    a=Decimal(p["a"]); b=Decimal(p["b"]); expected=a+b if p["operation"]=="+" else a-b
    assert Decimal(x.canonical_answer)==expected
    x=_generate_powers_of_ten(random.Random(seed),5); p=x.parameters
    assert x.canonical_answer==str(10**p["exponent"])
    x=_generate_volume(random.Random(seed),5); p=x.parameters
    assert x.canonical_answer==str(p["length"]*p["width"]*p["height"])
    x=_generate_coordinate_plane(random.Random(seed),5); p=x.parameters
    assert 0<=p["x"]<=10 and 0<=p["y"]<=10 and x.canonical_answer==f'({p["x"]}, {p["y"]})'

@pytest.mark.parametrize("generator,difficulty", [
    (_generate_equal_groups,3),(_generate_equal_sharing,3),(_generate_multiplication_within_100,3),
    (_generate_fraction_equivalence,4),(_generate_fraction_compare,4),(_generate_area_perimeter_rectangle,4),
    (_generate_multi_digit_multiplication,5),(_generate_long_division,5),(_generate_decimal_operations,5),
    (_generate_volume,5),(_generate_coordinate_plane,5),
])
def test_grades3_5_generators_repeatable(generator,difficulty):
    assert generator(random.Random(20260928),difficulty)==generator(random.Random(20260928),difficulty)
