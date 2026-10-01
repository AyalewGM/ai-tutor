import random
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem


def _module_contextualizer():
    from app.services import problem_contextualizer

    return problem_contextualizer.contextualizer


@dataclass(frozen=True)
class GeneratedProblem:
    prompt: str
    canonical_answer: str
    difficulty: int
    problem_type: str
    context: dict | None = None
    parameters: dict | None = None


def _fmt_term(coefficient: int, variable: str) -> str:
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{coefficient}{variable}"


def _fmt_expr(coefficient: int, constant: int, variable: str = "x") -> str:
    lead = _fmt_term(coefficient, variable)
    if constant == 0:
        return lead
    return f"{lead}{constant:+d}"


def _generate_simplify_expression(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 3:
        a = rng.randint(2, 9)
        b = rng.randint(1, 12)
        sign = "+" if difficulty <= 2 or rng.random() < 0.5 else "-"
        prompt = f"{a}(x{sign}{b})"
        answer = _fmt_expr(a, a * b if sign == "+" else -a * b)
        parameters = {"a": a, "b": b, "sign": sign}
    else:
        a, c = rng.randint(2, 9), rng.randint(2, 9)
        b = rng.randint(-9, 9)
        d = rng.randint(-9, 9)
        prompt = f"{_fmt_expr(a, b)} + {_fmt_expr(c, d)}"
        prompt = prompt.replace("+ -", "- ")
        answer = _fmt_expr(a + c, b + d)
        parameters = {"a": a, "b": b, "c": c, "d": d}
    return GeneratedProblem(
        prompt, answer, difficulty, "SIMPLIFY_EXPRESSION", parameters=parameters
    )


def _generate_combine_like_terms(rng: random.Random, difficulty: int) -> GeneratedProblem:
    variable = rng.choice(["x", "y", "n"])
    a = rng.randint(-9, 9)
    b = rng.randint(-9, 9)
    while a == 0 or b == 0:
        a = rng.randint(-9, 9)
        b = rng.randint(-9, 9)
    constant = rng.randint(-9, 9) if difficulty >= 3 else 0
    terms = [f"{_fmt_term(a, variable)}", f"{_fmt_term(b, variable)}"]
    if constant:
        terms.append(str(constant))
    prompt = "Simplify " + " + ".join(terms).replace("+ -", "- ") + "."
    answer = _fmt_expr(a + b, constant, variable)
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "COMBINE_LIKE_TERMS",
        parameters={"a": a, "b": b, "constant": constant, "variable": variable},
    )


def _generate_polynomial_add_subtract(rng: random.Random, difficulty: int) -> GeneratedProblem:
    variable = rng.choice(["x", "y"])
    a, b = rng.randint(-6, 6), rng.randint(-9, 9)
    c, d = rng.randint(-6, 6), rng.randint(-9, 9)
    while a == 0 or c == 0:
        a, c = rng.randint(-6, 6), rng.randint(-6, 6)
    operation = "-" if difficulty >= 3 and rng.random() < 0.6 else "+"
    left = _fmt_expr(a, b, variable)
    right = _fmt_expr(c, d, variable)
    prompt = f"Simplify ({left}) {operation} ({right})."
    if operation == "+":
        coefficient, constant = a + c, b + d
    else:
        coefficient, constant = a - c, b - d
    answer = _fmt_expr(coefficient, constant, variable)
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "POLYNOMIAL_ADD_SUBTRACT",
        parameters={
            "a": a, "b": b, "c": c, "d": d,
            "operation": operation, "variable": variable,
        },
    )


def _generate_solve_equation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-12, 12) if difficulty >= 4 else rng.randint(1, 12)
    if difficulty <= 1:
        b = rng.randint(1, 20)
        prompt = f"x + {b} = {x + b}"
        parameters = {"tier": "add_inverse", "b": b, "x": x}
    elif difficulty == 2:
        a = rng.randint(2, 9)
        prompt = f"{a}x = {a * x}"
        parameters = {"tier": "coefficient", "a": a, "x": x}
    elif difficulty <= 4:
        a, b = rng.randint(2, 9), rng.randint(1, 15)
        prompt = f"{_fmt_expr(a, b)} = {a * x + b}"
        parameters = {"tier": "two_step", "a": a, "b": b, "x": x}
    else:
        a, b = rng.randint(2, 6), rng.randint(-9, 9)
        prompt = f"{a}({_fmt_expr(1, b)}) = {a * (x + b)}"
        parameters = {"tier": "distribute_equation", "a": a, "b": b, "x": x}
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION", parameters=parameters
    )


def _generate_linear_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        m = rng.randint(1, 8)
        b = rng.randint(-8, 8) if difficulty == 2 else rng.randint(0, 8)
        prompt = (
            f"A line has slope {m} and y-intercept {b}. "
            "Write its equation in slope-intercept form."
        )
        answer = f"y={_fmt_expr(m, b)}"
        parameters = {"tier": "write_slope_intercept", "m": m, "b": b}
    else:
        m = rng.randint(-8, 8)
        b = rng.randint(-9, 9)
        x = rng.randint(-6, 6)
        prompt = f"For y = {_fmt_expr(m, b)}, what is y when x = {x}?"
        answer = str(m * x + b)
        parameters = {"tier": "evaluate", "m": m, "b": b, "x": x}
    return GeneratedProblem(
        prompt, answer, difficulty, "LINEAR_FUNCTION", parameters=parameters
    )


def _generate_integer_sum(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
    elif difficulty <= 4:
        a, b = rng.randint(-15, 15), rng.randint(1, 15)
    else:
        a, b = rng.randint(-20, 20), rng.randint(-20, 20)
    prompt = f"Evaluate {a} + {b}." if b >= 0 else f"Evaluate {a} - {abs(b)}."
    return GeneratedProblem(
        prompt, str(a + b), difficulty, "INTEGER_OPERATIONS",
        parameters={"a": a, "b": b},
    )


def _generate_integer_compare(rng: random.Random, difficulty: int) -> GeneratedProblem:
    bound = 10 if difficulty <= 2 else 20
    a = rng.randint(-bound, bound)
    b = rng.randint(-bound, bound)
    while b == a:
        b = rng.randint(-bound, bound)
    prompt = f"Which is greater, {a} or {b}?"
    return GeneratedProblem(
        prompt, str(max(a, b)), difficulty, "INTEGER_COMPARE",
        parameters={"a": a, "b": b},
    )


def _generate_fraction_add(rng: random.Random, difficulty: int) -> GeneratedProblem:
    d1 = rng.choice([2, 3, 4, 5])
    d2 = rng.choice([2, 3, 4, 5, 6, 8])
    n1, n2 = rng.randint(1, d1 - 1), rng.randint(1, d2 - 1)
    result = Fraction(n1, d1) + Fraction(n2, d2)
    prompt = f"Evaluate {n1}/{d1} + {n2}/{d2}."
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt, answer, difficulty, "FRACTION_OPERATIONS",
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )


def _generate_fraction_subtract(rng: random.Random, difficulty: int) -> GeneratedProblem:
    f1 = Fraction(rng.randint(1, 4), rng.choice([2, 3, 4, 5]))
    f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    while f2 >= f1:
        f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    result = f1 - f2
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    prompt = (
        f"Evaluate {f1.numerator}/{f1.denominator} - "
        f"{f2.numerator}/{f2.denominator}."
    )
    return GeneratedProblem(
        prompt, answer, difficulty, "FRACTION_SUBTRACT",
        parameters={
            "n1": f1.numerator, "d1": f1.denominator,
            "n2": f2.numerator, "d2": f2.denominator,
        },
    )


def _generate_word_problem(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        percent = rng.choice([10, 20, 25, 50])
        amount = rng.choice([40, 60, 80, 100, 120, 200])
        prompt = f"What is {percent}% of {amount}?"
        answer = str(percent * amount // 100)
        context = {
            "template": "percent_of",
            "parameters": {"percent": percent, "amount": amount},
        }
        parameters = dict(context["parameters"])
    else:
        total = rng.choice([60, 90, 120, 150, 240, 300])
        hours = rng.choice([2, 3, 4, 5, 6])
        prompt = (
            f"A car travels {total} miles in {hours} hours at a constant rate. "
            "What is the unit rate in miles per hour?"
        )
        answer = str(total // hours) if total % hours == 0 else f"{total}/{hours}"
        context = {
            "template": "unit_rate",
            "parameters": {"distance": total, "hours": hours},
        }
        parameters = dict(context["parameters"])
    return GeneratedProblem(
        prompt, answer, difficulty, "WORD_PROBLEM",
        context=context, parameters=parameters,
    )


def _generate_equal_groups(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 5 if difficulty <= 1 else 10
    rows, columns = rng.randint(2, limit), rng.randint(2, limit)
    return GeneratedProblem(
        prompt=(
            f"An array has {rows} rows with {columns} counters in each row. "
            "How many counters are there?"
        ),
        canonical_answer=str(rows * columns),
        difficulty=difficulty,
        problem_type="EQUAL_GROUPS",
        parameters={"rows": rows, "columns": columns, "representation": "array"},
    )


def _generate_equal_sharing(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 5 if difficulty <= 1 else 10
    groups, group_size = rng.randint(2, limit), rng.randint(2, limit)
    total = groups * group_size
    return GeneratedProblem(
        prompt=(
            f"{total} counters are shared equally among {groups} groups. "
            "How many counters are in each group?"
        ),
        canonical_answer=str(group_size),
        difficulty=difficulty,
        problem_type="EQUAL_SHARING",
        parameters={"total": total, "groups": groups, "group_size": group_size},
    )


def _generate_unit_fraction(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.randint(2, 6 if difficulty <= 1 else 10)
    numerator = 1 if difficulty <= 1 else rng.randint(1, denominator - 1)
    answer = f"{numerator}/{denominator}"
    prompt = (
        f"A whole is divided into {denominator} equal parts. "
        f"What fraction is {numerator} of those parts?"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "UNIT_FRACTION",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_rectangle_area(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 6 if difficulty <= 1 else 10
    rows, columns = rng.randint(2, limit), rng.randint(2, limit)
    return GeneratedProblem(
        prompt=(
            f"A rectangle has {rows} rows of {columns} unit squares. "
            "What is its area in square units?"
        ),
        canonical_answer=str(rows * columns),
        difficulty=difficulty,
        problem_type="RECTANGLE_AREA",
        parameters={"rows": rows, "columns": columns, "unit": "square units"},
    )


def _generate_addition_within_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(2, 9)
    b = rng.randint(2, min(9, 18 - a))
    return GeneratedProblem(
        prompt=f"What is {a} + {b}?",
        canonical_answer=str(a + b),
        difficulty=difficulty,
        problem_type="ADDITION_WITHIN_20",
        parameters={"a": a, "b": b, "operation": "+"},
    )


def _generate_subtraction_within_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(5, 18)
    b = rng.randint(2, min(a - 1, 9))
    return GeneratedProblem(
        prompt=f"What is {a} - {b}?",
        canonical_answer=str(a - b),
        difficulty=difficulty,
        problem_type="SUBTRACTION_WITHIN_20",
        parameters={"a": a, "b": b, "operation": "-"},
    )


def _generate_addition_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(10, 89)
    b = rng.randint(10, 99 - a)
    return GeneratedProblem(
        prompt=f"What is {a} + {b}?",
        canonical_answer=str(a + b),
        difficulty=difficulty,
        problem_type="ADDITION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "+"},
    )


def _generate_subtraction_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(20, 99)
    b = rng.randint(10, a - 1)
    return GeneratedProblem(
        prompt=f"What is {a} - {b}?",
        canonical_answer=str(a - b),
        difficulty=difficulty,
        problem_type="SUBTRACTION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "-"},
    )


def _generate_place_value_base_ten(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        tens = rng.randint(1, 9)
        ones = rng.randint(0, 9)
        number = tens * 10 + ones
        prompt = f"How many tens and ones make {number}?"
        answer = f"{tens} tens and {ones} ones"
        params = {"number": number, "tens": tens, "ones": ones, "place": "tens_and_ones"}
    else:
        hundreds = rng.randint(1, 9)
        tens = rng.randint(0, 9)
        ones = rng.randint(0, 9)
        number = hundreds * 100 + tens * 10 + ones
        prompt = f"How many hundreds, tens, and ones make {number}?"
        answer = f"{hundreds} hundreds, {tens} tens, and {ones} ones"
        params = {"number": number, "hundreds": hundreds, "tens": tens, "ones": ones, "place": "hundreds_tens_ones"}
    return GeneratedProblem(
        prompt, answer, difficulty, "PLACE_VALUE_BASE_TEN", parameters=params
    )


def _generate_money_count(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        q, d, n, p = rng.randint(0, 2), rng.randint(0, 2), rng.randint(0, 2), rng.randint(0, 4)
    else:
        q, d, n, p = rng.randint(0, 4), rng.randint(0, 5), rng.randint(0, 5), rng.randint(0, 9)
    total = q * 25 + d * 10 + n * 5 + p
    parts = []
    if q:
        parts.append(f"{q} quarter{'s' if q != 1 else ''}")
    if d:
        parts.append(f"{d} dime{'s' if d != 1 else ''}")
    if n:
        parts.append(f"{n} nickel{'s' if n != 1 else ''}")
    if p:
        parts.append(f"{p} penny{'s' if p != 1 else ''}")
    prompt = "What is the total value of " + ", ".join(parts) + "?"
    dollars = total // 100
    cents = total % 100
    if dollars:
        answer = f"${dollars}.{cents:02d}"
    else:
        answer = f"${cents / 100:.2f}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "MONEY_COUNT",
        parameters={"quarters": q, "dimes": d, "nickels": n, "pennies": p, "total_cents": total},
    )


def _generate_time_to_hour_half_hour(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        hour = rng.randint(1, 12)
        minute = rng.choice([0, 30])
    else:
        hour = rng.randint(1, 12)
        minute = rng.choice([0, 15, 30, 45])
    if minute == 0:
        answer = f"{hour}:00"
        prompt = f"What time is shown when the hour hand points to {hour} and the minute hand points to 12?"
    elif minute == 30:
        answer = f"{hour}:30"
        prompt = f"What time is shown when the hour hand is between {hour} and {(hour % 12) + 1} and the minute hand points to 6?"
    else:
        answer = f"{hour}:{minute:02d}"
        prompt = f"What time is shown when the minute hand points to {minute // 5} and the hour hand is near {hour}?"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "TIME_TO_HOUR_HALF_HOUR",
        parameters={"hour": hour, "minute": minute},
    )


def _generate_multi_digit_multiplication(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        a, b = rng.randint(10, 99), rng.randint(2, 9)
    else:
        a, b = rng.randint(100, 999), rng.randint(10, 99)
    return GeneratedProblem(
        prompt=f"What is {a} × {b}?",
        canonical_answer=str(a * b),
        difficulty=difficulty,
        problem_type="MULTI_DIGIT_MULTIPLICATION",
        parameters={"a": a, "b": b, "operation": "×"},
    )


def _generate_long_division(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        divisor = rng.randint(2, 9)
        quotient = rng.randint(10, 99)
    else:
        divisor = rng.randint(2, 12)
        quotient = rng.randint(10, 99)
    dividend = divisor * quotient
    return GeneratedProblem(
        prompt=f"What is {dividend} ÷ {divisor}?",
        canonical_answer=str(quotient),
        difficulty=difficulty,
        problem_type="LONG_DIVISION",
        parameters={"dividend": dividend, "divisor": divisor, "quotient": quotient, "operation": "÷"},
    )


def _generate_fraction_equivalence(rng: random.Random, difficulty: int) -> GeneratedProblem:
    target = Fraction(rng.randint(1, 3), rng.choice([2, 3, 4, 5, 6, 8]))
    multiplier = rng.randint(2, 4)
    equivalent = Fraction(target.numerator * multiplier, target.denominator * multiplier)
    prompt = f"What fraction is equivalent to {target.numerator}/{target.denominator} with denominator {equivalent.denominator}?"
    return GeneratedProblem(
        prompt,
        f"{equivalent.numerator}/{equivalent.denominator}",
        difficulty,
        "FRACTION_EQUIVALENCE",
        parameters={
            "original_numerator": target.numerator,
            "original_denominator": target.denominator,
            "multiplier": multiplier,
            "target_numerator": equivalent.numerator,
            "target_denominator": equivalent.denominator,
        },
    )


def _generate_fraction_add_subtract_like(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4, 5, 6, 8])
    n1 = rng.randint(1, denominator - 1)
    n2 = rng.randint(1, denominator - 1)
    if rng.random() < 0.5:
        result = Fraction(n1, denominator) + Fraction(n2, denominator)
        op = "+"
        prompt = f"What is {n1}/{denominator} + {n2}/{denominator}?"
    else:
        if n1 < n2:
            n1, n2 = n2, n1
        result = Fraction(n1, denominator) - Fraction(n2, denominator)
        op = "-"
        prompt = f"What is {n1}/{denominator} - {n2}/{denominator}?"
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_ADD_SUBTRACT_LIKE",
        parameters={"n1": n1, "n2": n2, "denominator": denominator, "operation": op},
    )


def _generate_fraction_multiply(rng: random.Random, difficulty: int) -> GeneratedProblem:
    n1 = rng.randint(1, 5)
    d1 = rng.randint(2, 6)
    n2 = rng.randint(1, 5)
    d2 = rng.randint(2, 6)
    result = Fraction(n1, d1) * Fraction(n2, d2)
    prompt = f"What is {n1}/{d1} × {n2}/{d2}?"
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_MULTIPLY",
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )


def _generate_decimal_place_value(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        value = round(rng.randint(1, 99) / 10, 1)
        prompt = f"What is the value of the digit in the tenths place of {value}?"
        answer = str(int((value * 10) % 10))
        params = {"number": value, "place": "tenths", "digit": int(answer)}
    else:
        value = round(rng.randint(1, 999) / 100, 2)
        prompt = f"What is the value of the digit in the hundredths place of {value}?"
        answer = str(int((value * 100) % 10))
        params = {"number": value, "place": "hundredths", "digit": int(answer)}
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "DECIMAL_PLACE_VALUE",
        parameters=params,
    )


def _generate_angle_measurement(rng: random.Random, difficulty: int) -> GeneratedProblem:
    angle = rng.choice([30, 45, 60, 90, 120, 135, 150])
    prompt = f"What is the measure of an angle that is {angle} degrees?"
    return GeneratedProblem(
        prompt,
        str(angle),
        difficulty,
        "ANGLE_MEASUREMENT",
        parameters={"angle": angle},
    )


def _generate_coordinate_plane(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(0, 10)
    y = rng.randint(0, 10)
    prompt = f"A point is located at ({x}, {y}) on a coordinate grid. What is the ordered pair?"
    return GeneratedProblem(
        prompt,
        f"({x}, {y})",
        difficulty,
        "COORDINATE_PLANE",
        parameters={"x": x, "y": y},
    )


def _generate_volume(rng: random.Random, difficulty: int) -> GeneratedProblem:
    l = rng.randint(2, 6)
    w = rng.randint(2, 6)
    h = rng.randint(2, 6)
    prompt = f"A rectangular prism has length {l}, width {w}, and height {h}. What is its volume?"
    return GeneratedProblem(
        prompt,
        str(l * w * h),
        difficulty,
        "VOLUME",
        parameters={"length": l, "width": w, "height": h},
    )


def _generate_number_sequence(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start = rng.randint(1, 100)
    step = rng.choice([1, 2, 5, 10])
    missing_index = rng.randint(1, 4)
    sequence = [start + step * i for i in range(5)]
    answer = sequence[missing_index]
    sequence[missing_index] = None
    prompt = "What number completes the sequence: " + ", ".join("?" if x is None else str(x) for x in sequence) + "?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "NUMBER_SEQUENCE",
        parameters={"start": start, "step": step, "missing_index": missing_index, "answer": answer},
    )


def _generate_compare_numbers(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 50 if difficulty <= 1 else 120
    a = rng.randint(1, limit)
    b = rng.randint(1, limit)
    if a == b:
        b = (b % limit) + 1
    if a > b:
        answer = ">"
    elif a < b:
        answer = "<"
    else:
        answer = "="
    prompt = f"Compare: {a} ___ {b}. Use >, <, or =."
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "COMPARE_NUMBERS",
        parameters={"a": a, "b": b, "operation": "compare"},
    )


def _generate_word_problem_add_sub_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    contexts = [
        ("add", "{a} crayons are on the table. {b} more are added. How many crayons are there?"),
        ("subtract", "{a} birds are on a branch. {b} fly away. How many birds are left?"),
        ("add", "There are {a} red blocks and {b} blue blocks. How many blocks are there in all?"),
        ("subtract", "A basket has {a} apples. {b} are eaten. How many apples remain?"),
    ]
    op, template = rng.choice(contexts)
    if op == "add":
        a = rng.randint(2, 12)
        b = rng.randint(2, min(9, 18 - a))
        answer = a + b
    else:
        a = rng.randint(5, 18)
        b = rng.randint(2, min(a - 1, 9))
        answer = a - b
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_ADD_SUB_20",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_word_problem_add_sub_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    contexts = [
        ("add", "A library has {a} fiction books and {b} nonfiction books. How many books are there?"),
        ("subtract", "There are {a} sheets of paper. {b} are used. How many are left?"),
        ("add", "A box has {a} red marbles and {b} blue marbles. How many marbles are there in all?"),
        ("subtract", "A school has {a} students. {b} leave for a field trip. How many remain?"),
    ]
    op, template = rng.choice(contexts)
    if op == "add":
        a = rng.randint(10, 80)
        b = rng.randint(10, 99 - a)
        answer = a + b
    else:
        a = rng.randint(20, 99)
        b = rng.randint(10, a - 1)
        answer = a - b
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_ADD_SUB_100",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_number_pattern(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start = rng.randint(1, 50)
    step = rng.choice([2, 5, 10])
    length = 5
    index = rng.randint(0, length - 1)
    pattern = [start + step * i for i in range(length)]
    answer = pattern[index]
    pattern[index] = None
    prompt = "What number completes the pattern: " + ", ".join("?" if x is None else str(x) for x in pattern) + "?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "NUMBER_PATTERN",
        parameters={"start": start, "step": step, "missing_index": index, "answer": answer},
    )


def _generate_equation_balance(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    c = a + b
    unknown = rng.choice(["a", "b", "c"])
    if unknown == "a":
        prompt = f"___ + {b} = {c}"
        answer = a
    elif unknown == "b":
        prompt = f"{a} + ___ = {c}"
        answer = b
    else:
        prompt = f"{a} + {b} = ___"
        answer = c
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "EQUATION_BALANCE",
        parameters={"a": a, "b": b, "c": c, "unknown": unknown},
    )


def _generate_compare_length(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    if a > b:
        answer = a - b
        prompt = f"One ribbon is {a} inches long. Another is {b} inches long. How much longer is the first ribbon?"
    else:
        answer = b - a
        prompt = f"One ribbon is {a} inches long. Another is {b} inches long. How much longer is the second ribbon?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "COMPARE_LENGTH",
        parameters={"a": a, "b": b, "difference": answer},
    )


def _generate_time_to_5_minutes(rng: random.Random, difficulty: int) -> GeneratedProblem:
    hour = rng.randint(1, 12)
    minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    prompt = f"What time is shown when the hour hand is near {hour} and the minute hand points to {minute // 5}?"
    answer = f"{hour}:{minute:02d}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "TIME_TO_5_MINUTES",
        parameters={"hour": hour, "minute": minute},
    )


def _generate_geometry_shapes(rng: random.Random, difficulty: int) -> GeneratedProblem:
    shapes = ["triangle", "square", "rectangle", "circle", "hexagon"]
    shape = rng.choice(shapes)
    prompt = f"How many sides does a {shape} have?"
    sides = {"triangle": 3, "square": 4, "rectangle": 4, "circle": 0, "hexagon": 6}
    return GeneratedProblem(
        prompt,
        str(sides[shape]),
        difficulty,
        "GEOMETRY_SHAPES",
        parameters={"shape": shape, "sides": sides[shape]},
    )


def _generate_fraction_halves_thirds_fourths(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4])
    numerator = rng.randint(1, denominator)
    prompt = f"A shape is divided into {denominator} equal parts. {numerator} part{'s' if numerator != 1 else ''} are shaded. What fraction is shaded?"
    answer = f"{numerator}/{denominator}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_HALVES_THIRDS_FOURTHS",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_bar_graph_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    categories = ["red", "blue", "green", "yellow"]
    values = [rng.randint(1, 10) for _ in categories]
    category = rng.choice(categories)
    answer = values[categories.index(category)]
    data = dict(zip(categories, values))
    prompt = f"A bar graph shows votes for favorite colors: {data}. How many votes did {category} receive?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "BAR_GRAPH_READ",
        parameters={"category": category, "value": answer, "total": sum(values)},
    )


def _generate_picture_graph_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    categories = ["dog", "cat", "bird", "fish"]
    values = [rng.randint(1, 8) for _ in categories]
    category = rng.choice(categories)
    answer = values[categories.index(category)]
    data = dict(zip(categories, values))
    prompt = f"A picture graph shows pets: {data}. How many {category}s are there?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "PICTURE_GRAPH_READ",
        parameters={"category": category, "value": answer, "total": sum(values)},
    )


def _generate_multiplication_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(2, 9) if difficulty <= 2 else rng.randint(2, 12)
    b = rng.randint(2, 9) if difficulty <= 2 else rng.randint(2, 12)
    return GeneratedProblem(
        prompt=f"What is {a} × {b}?",
        canonical_answer=str(a * b),
        difficulty=difficulty,
        problem_type="MULTIPLICATION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "×"},
    )


def _generate_division_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    b = rng.randint(2, 9)
    answer = rng.randint(2, 12 if difficulty <= 2 else 9)
    a = b * answer
    return GeneratedProblem(
        prompt=f"What is {a} ÷ {b}?",
        canonical_answer=str(answer),
        difficulty=difficulty,
        problem_type="DIVISION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "÷"},
    )


def _generate_word_problem_multiply_divide_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    templates = [
        ("multiply", "There are {a} boxes with {b} pencils in each box. How many pencils are there in all?"),
        ("divide", "{a} stickers are shared equally among {b} students. How many stickers does each student get?"),
    ]
    op, template = rng.choice(templates)
    if op == "multiply":
        a = rng.randint(2, 9)
        b = rng.randint(2, 12 if difficulty <= 2 else 9)
        answer = a * b
    else:
        b = rng.randint(2, 9)
        answer = rng.randint(2, 12 if difficulty <= 2 else 9)
        a = b * answer
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_MULTIPLY_DIVIDE_100",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_rounding(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        number = rng.randint(10, 99)
        place = 10
        place_name = "ten"
    else:
        number = rng.randint(100, 999)
        place = 100
        place_name = "hundred"
    rounded = round(number / place) * place
    return GeneratedProblem(
        prompt=f"Round {number} to the nearest {place_name}.",
        canonical_answer=str(rounded),
        difficulty=difficulty,
        problem_type="ROUNDING",
        parameters={"number": number, "place": place_name, "rounded": rounded},
    )


def _generate_fraction_compare(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominators = [2, 3, 4, 6, 8]
    d1, d2 = rng.sample(denominators, 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    from fractions import Fraction
    f1 = Fraction(n1, d1)
    f2 = Fraction(n2, d2)
    if f1 > f2:
        answer = ">"
    elif f1 < f2:
        answer = "<"
    else:
        answer = "="
    return GeneratedProblem(
        prompt=f"Compare: {n1}/{d1} ___ {n2}/{d2}. Use >, <, or =.",
        canonical_answer=answer,
        difficulty=difficulty,
        problem_type="FRACTION_COMPARE",
        parameters={"numerator1": n1, "denominator1": d1, "numerator2": n2, "denominator2": d2},
    )


def _generate_fraction_on_number_line(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4, 6, 8])
    numerator = rng.randint(1, denominator - 1)
    return GeneratedProblem(
        prompt=f"Where is the fraction {numerator}/{denominator} located on a number line from 0 to 1?",
        canonical_answer=f"{numerator}/{denominator}",
        difficulty=difficulty,
        problem_type="FRACTION_NUMBER_LINE",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_area_perimeter_rectangle(rng: random.Random, difficulty: int) -> GeneratedProblem:
    length = rng.randint(2, 10)
    width = rng.randint(2, 10)
    op = rng.choice(["area", "perimeter"])
    if op == "area":
        answer = length * width
        prompt = f"A rectangle has length {length} units and width {width} units. What is its area?"
    else:
        answer = 2 * (length + width)
        prompt = f"A rectangle has length {length} units and width {width} units. What is its perimeter?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "AREA_PERIMETER_RECTANGLE",
        parameters={"length": length, "width": width, "measure": op},
    )


def _generate_elapsed_time(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start_hour = rng.randint(1, 11)
    start_minute = rng.choice([0, 15, 30, 45])
    elapsed = rng.choice([15, 30, 45, 60, 90])
    start_total = start_hour * 60 + start_minute
    end_total = start_total + elapsed
    end_hour = (end_total // 60) % 12
    if end_hour == 0:
        end_hour = 12
    end_minute = end_total % 60
    start_str = f"{start_hour}:{start_minute:02d}"
    end_str = f"{end_hour}:{end_minute:02d}"
    return GeneratedProblem(
        prompt=f"A movie starts at {start_str} and ends at {end_str}. How many minutes long is the movie?",
        canonical_answer=str(elapsed),
        difficulty=difficulty,
        problem_type="ELAPSED_TIME",
        parameters={"start": start_str, "end": end_str, "elapsed": elapsed},
    )


def _generate_line_plot_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    data_points = [rng.randint(1, 10) for _ in range(rng.randint(8, 15))]
    value = rng.choice(list(set(data_points)))
    answer = data_points.count(value)
    return GeneratedProblem(
        prompt=f"A line plot shows these measurements in inches: {data_points}. How many measurements are {value} inches?",
        canonical_answer=str(answer),
        difficulty=difficulty,
        problem_type="LINE_PLOT_READ",
        parameters={"data": data_points, "value": value, "count": answer},
    )


def _generate_classify_shape(rng: random.Random, difficulty: int) -> GeneratedProblem:
    shapes = ["quadrilateral", "parallelogram", "rectangle", "rhombus", "square", "trapezoid"]
    shape = rng.choice(shapes)
    attr_map = {
        "quadrilateral": "4 sides",
        "parallelogram": "2 pairs of parallel sides",
        "rectangle": "4 right angles",
        "rhombus": "4 equal sides",
        "square": "4 equal sides and 4 right angles",
        "trapezoid": "at least 1 pair of parallel sides",
    }
    answer = attr_map[shape]
    return GeneratedProblem(
        prompt=f"What is the defining attribute of a {shape}?",
        canonical_answer=answer,
        difficulty=difficulty,
        problem_type="CLASSIFY_SHAPE",
        parameters={"shape": shape, "attribute": answer},
    )


def _generate_lines_parallel_perpendicular(rng: random.Random, difficulty: int) -> GeneratedProblem:
    relation = rng.choice(["parallel", "perpendicular"])
    if relation == "parallel":
        answer = "parallel"
        prompt = "Two lines in the same plane never meet. What are they called?"
    else:
        answer = "perpendicular"
        prompt = "Two lines meet at a right angle. What are they called?"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "LINES_PARALLEL_PERPENDICULAR",
        parameters={"relation": relation},
    )


def _generate_multiply_by_whole(rng: random.Random, difficulty: int) -> GeneratedProblem:
    whole = rng.randint(2, 9)
    denominator = rng.randint(2, 8)
    numerator = rng.randint(1, denominator - 1)
    answer_num = whole * numerator
    return GeneratedProblem(
        prompt=f"What is {whole} × {numerator}/{denominator}?",
        canonical_answer=f"{answer_num}/{denominator}",
        difficulty=difficulty,
        problem_type="MULTIPLY_FRACTION_BY_WHOLE",
        parameters={"whole": whole, "numerator": numerator, "denominator": denominator},
    )


def _generate_add_subtract_unlike_fractions(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from fractions import Fraction
    d1, d2 = rng.sample([2, 3, 4, 5, 6, 8, 10], 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    op = rng.choice(["+", "-"])
    f1 = Fraction(n1, d1)
    f2 = Fraction(n2, d2)
    result = f1 + f2 if op == "+" else f1 - f2
    if result <= 0:
        result = f1 + f2
        op = "+"
    prompt = f"What is {n1}/{d1} {op} {n2}/{d2}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "ADD_SUBTRACT_UNLIKE_FRACTIONS",
        parameters={"numerator1": n1, "denominator1": d1, "numerator2": n2, "denominator2": d2, "operation": op},
    )


def _generate_multiply_fractions(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from fractions import Fraction
    denominators = [2, 3, 4, 5, 6, 8]
    d1, d2 = rng.sample(denominators, 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    result = Fraction(n1, d1) * Fraction(n2, d2)
    prompt = f"What is {n1}/{d1} × {n2}/{d2}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "MULTIPLY_FRACTIONS",
        parameters={"numerator1": n1, "denominator1": d1, "numerator2": n2, "denominator2": d2},
    )


def _generate_divide_fractions(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from fractions import Fraction
    d = rng.choice([2, 3, 4, 5, 6, 8])
    n = rng.randint(1, d - 1)
    whole = rng.randint(2, 9)
    fraction = Fraction(n, d)
    result = Fraction(whole) / fraction
    prompt = f"How many servings of {n}/{d} are in {whole}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "DIVIDE_FRACTIONS",
        parameters={"whole": whole, "numerator": n, "denominator": d},
    )


def _generate_powers_of_ten(rng: random.Random, difficulty: int) -> GeneratedProblem:
    exponent = rng.randint(1, 4)
    answer = 10 ** exponent
    prompt = f"What is 10^{exponent}?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "POWERS_OF_TEN",
        parameters={"exponent": exponent, "base": 10},
    )


def _generate_decimal_operations(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from decimal import Decimal
    op = rng.choice(["+", "-"])
    a = Decimal(rng.randint(1, 99)) / 10 if rng.random() < 0.5 else Decimal(rng.randint(1, 999)) / 100
    b = Decimal(rng.randint(1, 99)) / 10 if rng.random() < 0.5 else Decimal(rng.randint(1, 999)) / 100
    if op == "+":
        answer = a + b
        prompt = f"What is {a} + {b}?"
    else:
        if a < b:
            a, b = b, a
        answer = a - b
        prompt = f"What is {a} - {b}?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "DECIMAL_OPERATIONS",
        parameters={"a": str(a), "b": str(b), "operation": op},
    )


def _generate_measurement_conversion(rng: random.Random, difficulty: int) -> GeneratedProblem:
    conversions = [
        ("m", "cm", 100),
        ("km", "m", 1000),
        ("kg", "g", 1000),
        ("L", "mL", 1000),
        ("ft", "in", 12),
    ]
    from_unit, to_unit, factor = rng.choice(conversions)
    value = rng.randint(1, 9)
    answer = value * factor
    prompt = f"Convert {value} {from_unit} to {to_unit}."
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "MEASUREMENT_CONVERSION",
        parameters={"value": value, "from": from_unit, "to": to_unit, "factor": factor},
    )


def _generate_arithmetic(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = (
        _generate_fraction_add(rng, difficulty)
        if rng.random() < 0.5
        else _generate_integer_sum(rng, difficulty)
    )
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, difficulty, "ARITHMETIC",
        parameters=generated.parameters,
    )


def _generate_linear_relation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = _generate_linear_function(rng, difficulty)
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, difficulty, "LINEAR_RELATION",
        parameters=generated.parameters,
    )


GENERATORS: dict[str, Callable[[random.Random, int], GeneratedProblem]] = {
    "ARITHMETIC": _generate_arithmetic,
    "SIMPLIFY_EXPRESSION": _generate_simplify_expression,
    "COMBINE_LIKE_TERMS": _generate_combine_like_terms,
    "POLYNOMIAL_ADD_SUBTRACT": _generate_polynomial_add_subtract,
    "SOLVE_EQUATION": _generate_solve_equation,
    "LINEAR_FUNCTION": _generate_linear_function,
    "LINEAR_RELATION": _generate_linear_relation,
    "INTEGER_OPERATIONS": _generate_integer_sum,
    "INTEGER_COMPARE": _generate_integer_compare,
    "FRACTION_OPERATIONS": _generate_fraction_add,
    "FRACTION_SUBTRACT": _generate_fraction_subtract,
    "WORD_PROBLEM": _generate_word_problem,
    "EQUAL_GROUPS": _generate_equal_groups,
    "EQUAL_SHARING": _generate_equal_sharing,
    "UNIT_FRACTION": _generate_unit_fraction,
    "RECTANGLE_AREA": _generate_rectangle_area,
    "ADDITION_WITHIN_20": _generate_addition_within_20,
    "SUBTRACTION_WITHIN_20": _generate_subtraction_within_20,
    "ADDITION_WITHIN_100": _generate_addition_within_100,
    "SUBTRACTION_WITHIN_100": _generate_subtraction_within_100,
    "PLACE_VALUE_BASE_TEN": _generate_place_value_base_ten,
    "MONEY_COUNT": _generate_money_count,
    "TIME_TO_HOUR_HALF_HOUR": _generate_time_to_hour_half_hour,
    "MULTI_DIGIT_MULTIPLICATION": _generate_multi_digit_multiplication,
    "LONG_DIVISION": _generate_long_division,
    "FRACTION_EQUIVALENCE": _generate_fraction_equivalence,
    "FRACTION_ADD_SUBTRACT_LIKE": _generate_fraction_add_subtract_like,
    "FRACTION_MULTIPLY": _generate_fraction_multiply,
    "DECIMAL_PLACE_VALUE": _generate_decimal_place_value,
    "ANGLE_MEASUREMENT": _generate_angle_measurement,
    "COORDINATE_PLANE": _generate_coordinate_plane,
    "VOLUME": _generate_volume,
    "NUMBER_SEQUENCE": _generate_number_sequence,
    "COMPARE_NUMBERS": _generate_compare_numbers,
    "WORD_PROBLEM_ADD_SUB_20": _generate_word_problem_add_sub_20,
    "WORD_PROBLEM_ADD_SUB_100": _generate_word_problem_add_sub_100,
    "NUMBER_PATTERN": _generate_number_pattern,
    "EQUATION_BALANCE": _generate_equation_balance,
    "COMPARE_LENGTH": _generate_compare_length,
    "TIME_TO_5_MINUTES": _generate_time_to_5_minutes,
    "GEOMETRY_SHAPES": _generate_geometry_shapes,
    "FRACTION_HALVES_THIRDS_FOURTHS": _generate_fraction_halves_thirds_fourths,
    "BAR_GRAPH_READ": _generate_bar_graph_read,
    "PICTURE_GRAPH_READ": _generate_picture_graph_read,
    "MULTIPLICATION_WITHIN_100": _generate_multiplication_within_100,
    "DIVISION_WITHIN_100": _generate_division_within_100,
    "WORD_PROBLEM_MULTIPLY_DIVIDE_100": _generate_word_problem_multiply_divide_100,
    "ROUNDING": _generate_rounding,
    "FRACTION_COMPARE": _generate_fraction_compare,
    "FRACTION_NUMBER_LINE": _generate_fraction_on_number_line,
    "AREA_PERIMETER_RECTANGLE": _generate_area_perimeter_rectangle,
    "ELAPSED_TIME": _generate_elapsed_time,
    "LINE_PLOT_READ": _generate_line_plot_read,
    "CLASSIFY_SHAPE": _generate_classify_shape,
    "LINES_PARALLEL_PERPENDICULAR": _generate_lines_parallel_perpendicular,
    "MULTIPLY_FRACTION_BY_WHOLE": _generate_multiply_by_whole,
    "ADD_SUBTRACT_UNLIKE_FRACTIONS": _generate_add_subtract_unlike_fractions,
    "MULTIPLY_FRACTIONS": _generate_multiply_fractions,
    "DIVIDE_FRACTIONS": _generate_divide_fractions,
    "POWERS_OF_TEN": _generate_powers_of_ten,
    "DECIMAL_OPERATIONS": _generate_decimal_operations,
    "MEASUREMENT_CONVERSION": _generate_measurement_conversion,
}


def _family_metadata(generated: GeneratedProblem) -> tuple[str, dict]:
    """Return stable family identity and minimized deterministic parameters.

    Family identity is application-owned and independent of curriculum mapping.
    Word-problem templates are distinct families; other generators currently
    have one family per generator until their representations are split.
    """
    if generated.context is not None:
        template = generated.context.get("template")
        parameters = generated.context.get("parameters") or {}
        if template:
            return f"{generated.problem_type}:{template}", dict(parameters)
    return generated.problem_type, dict(generated.parameters or {})


def _fingerprint(family: str, parameters: dict) -> tuple:
    return (family, tuple(sorted(parameters.items())))


def _existing_generated_keys(db: Session, skill_id: uuid.UUID) -> tuple[set, set]:
    """(prompts, (problem_family, parameters) fingerprints) already in the pool."""
    rows = db.execute(
        select(Problem.prompt, Problem.solution).where(
            Problem.primary_skill_id == skill_id
        )
    ).all()
    prompts = {row[0] for row in rows}
    fingerprints = {
        _fingerprint(solution["problem_family"], solution.get("parameters") or {})
        for _, solution in rows
        if isinstance(solution, dict) and solution.get("problem_family")
    }
    return prompts, fingerprints


def _possible_families(problem_type: str) -> set[str]:
    if problem_type == "WORD_PROBLEM":
        return {"WORD_PROBLEM:percent_of", "WORD_PROBLEM:unit_rate"}
    return {problem_type}


def generate_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    difficulty: int,
    problem_type: str | None = None,
    family: str | None = None,
    avoid_family: str | None = None,
    rng: random.Random | None = None,
) -> Problem | None:
    rng = rng or random.Random()
    if problem_type is not None:
        supported = [problem_type] if problem_type in GENERATORS else []
    else:
        available = db.scalars(
            select(Problem.problem_type)
            .where(Problem.primary_skill_id == skill_id)
            .distinct()
        ).all()
        supported = [t for t in available if t in GENERATORS]
    if not supported:
        return None
    possible = {f for t in supported for f in _possible_families(t)}
    if family is not None:
        if family not in possible:
            return None
        supported = [t for t in supported if family in _possible_families(t)]
    can_avoid = avoid_family is not None and len(possible - {avoid_family}) >= 1
    existing_prompts, existing_keys = _existing_generated_keys(db, skill_id)
    generated = None
    for _ in range(8):
        candidate = GENERATORS[rng.choice(supported)](rng, difficulty)
        family_id, parameters = _family_metadata(candidate)
        if family is not None and family_id != family:
            continue
        if can_avoid and family_id == avoid_family:
            continue
        if (
            candidate.prompt not in existing_prompts
            and _fingerprint(family_id, parameters) not in existing_keys
        ):
            generated = candidate
            break
    if generated is None:
        return None
    prompt = generated.prompt
    contextualizer = _module_contextualizer()
    if generated.context is not None and contextualizer is not None:
        narrative = contextualizer.contextualize(
            template=generated.context["template"],
            parameters=generated.context["parameters"],
            canonical_answer=generated.canonical_answer,
        )
        if narrative:
            prompt = narrative
    family_id, parameters = _family_metadata(generated)
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=prompt,
        canonical_answer=generated.canonical_answer,
        solution={
            "generated": True,
            "generator": generated.problem_type,
            "problem_family": family_id,
            "parameters": parameters,
            "difficulty": difficulty,
        },
        source_type="GENERATED",
    )
    db.add(problem)
    db.flush()
    return problem


def regenerate_variant(
    db: Session,
    *,
    source_problem: Problem,
    rng: random.Random | None = None,
) -> Problem | None:
    """Re-serve a missed generated problem with fresh parameters (same template,
    same difficulty, different numbers). Returns None for curated problems or
    unsupported templates."""
    metadata = source_problem.solution or {}
    generator = metadata.get("generator")
    if source_problem.source_type != "GENERATED" or generator not in GENERATORS:
        return None
    return generate_problem(
        db,
        skill_id=source_problem.primary_skill_id,
        difficulty=int(metadata.get("difficulty") or source_problem.difficulty),
        problem_type=generator,
        family=metadata.get("problem_family"),
        rng=rng,
    )


@dataclass(frozen=True)
class SkillContentReport:
    skill_id: uuid.UUID
    problem_count: int
    families: tuple[str, ...]
    ready: bool


def content_readiness(
    db: Session, *, skill_id: uuid.UUID, min_families: int = 2
) -> SkillContentReport:
    """A skill is content-ready when it can sustain a session: at least one
    problem and either >= min_families distinct families or a generator-
    capable problem type that can produce fresh items."""
    rows = db.execute(
        select(Problem.problem_type).where(Problem.primary_skill_id == skill_id)
    ).all()
    types = {row[0] for row in rows}
    families: set[str] = set()
    for ptype in types:
        families.update(_possible_families(ptype))
    generatable = bool(types & GENERATORS.keys())
    ready = len(rows) >= 1 and (len(families) >= min_families or generatable)
    return SkillContentReport(
        skill_id=skill_id,
        problem_count=len(rows),
        families=tuple(sorted(families)),
        ready=ready,
    )
