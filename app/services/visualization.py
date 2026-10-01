"""Deterministic visualization specs (Issue #42, first slice).

Problem parameters → declarative spec → React SVG renderer. No LLM
involvement: coordinates and labels are computed here, so a diagram can
never misrepresent the math. Unknown problem shapes return None — the
renderer simply shows nothing.
"""

import re
from typing import Any

from app.models import Problem

_SIMPLIFY_PAREN = re.compile(r"(-?\d+)\s*\(\s*x\s*([+-])\s*(\d+)\s*\)")
_INTEGER_EVAL = re.compile(r"(-?\d+)\s*([+-])\s*(-?\d+)")


def _params(problem: Problem) -> dict[str, Any]:
    solution = problem.solution or {}
    params = solution.get("parameters")
    return params if isinstance(params, dict) else {}


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _area_model(problem: Problem) -> dict | None:
    params = _params(problem)
    a, b = _int(params.get("a")), _int(params.get("b"))
    if a is None or b is None:
        match = _SIMPLIFY_PAREN.search(problem.prompt)
        if not match:
            return None
        a = int(match.group(1))
        b = int(match.group(3)) * (1 if match.group(2) == "+" else -1)
    if a == 0:
        return None
    return {
        "type": "area_model",
        "a": a,
        "b": b,
        "aria_label": (
            f"Area model for {a} times (x plus {b}): a rectangle of height {a} "
            f"split into an {a}x part and a {a} times {b} part."
        ),
    }


def _number_line(problem: Problem) -> dict | None:
    params = _params(problem)
    a, b = _int(params.get("a")), _int(params.get("b"))
    if a is None or b is None:
        match = _INTEGER_EVAL.search(problem.prompt)
        if not match:
            return None
        a = int(match.group(1))
        b = int(match.group(3)) * (1 if match.group(2) == "+" else -1)
    total = a + b
    lo = min(0, a, total) - 1
    hi = max(0, a, total) + 1
    return {
        "type": "number_line",
        "a": a,
        "b": b,
        "result": total,
        "min": lo,
        "max": hi,
        "aria_label": (
            f"Number line from {lo} to {hi}: start at 0, move {a}, "
            f"then move {b}."
        ),
    }


def _compare_points(problem: Problem) -> dict | None:
    params = _params(problem)
    a, b = _int(params.get("a")), _int(params.get("b"))
    if a is None or b is None:
        match = re.search(r"(-?\d+)\s+or\s+(-?\d+)", problem.prompt)
        if not match:
            return None
        a, b = int(match.group(1)), int(match.group(2))
    lo = min(a, b) - 2
    hi = max(a, b) + 2
    return {
        "type": "number_line_compare",
        "a": a,
        "b": b,
        "min": lo,
        "max": hi,
        "aria_label": f"Number line from {lo} to {hi} with points at {a} and {b}.",
    }


def _array_model(problem: Problem) -> dict | None:
    params = _params(problem)
    rows, columns = _int(params.get("rows")), _int(params.get("columns"))
    if rows is None or columns is None or not (1 <= rows <= 10 and 1 <= columns <= 10):
        return None
    return {
        "type": "array_model",
        "rows": rows,
        "columns": columns,
        "mode": "squares" if problem.problem_type == "RECTANGLE_AREA" else "counters",
        "aria_label": (
            f"Array with {rows} rows and {columns} columns, "
            f"showing {rows * columns} items in all."
        ),
    }


def _fraction_bar(problem: Problem) -> dict | None:
    params = _params(problem)
    numerator = _int(params.get("numerator"))
    denominator = _int(params.get("denominator"))
    if (
        numerator is None
        or denominator is None
        or denominator < 2
        or denominator > 12
        or numerator < 0
        or numerator > denominator
    ):
        return None
    return {
        "type": "fraction_bar",
        "numerator": numerator,
        "denominator": denominator,
        "aria_label": (
            f"Fraction bar divided into {denominator} equal parts with "
            f"{numerator} part{'s' if numerator != 1 else ''} selected."
        ),
    }


def _ten_frame(problem: Problem) -> dict | None:
    params = _params(problem)
    a, b = _int(params.get("a")), _int(params.get("b"))
    if a is None or b is None:
        return None
    total = a + b if params.get("operation") == "+" else a - b
    if not (0 <= total <= 20):
        return None
    return {
        "type": "ten_frame",
        "a": a,
        "b": b,
        "operation": params.get("operation", "+"),
        "total": total,
        "aria_label": (
            f"Ten frames showing {a} counters and {b} counters, "
            f"{params.get('operation', '+')} equals {total}."
        ),
    }


def _base_ten_model(problem: Problem) -> dict | None:
    params = _params(problem)
    number = _int(params.get("number"))
    if number is None:
        return None
    hundreds = _int(params.get("hundreds")) or 0
    tens = _int(params.get("tens")) or 0
    ones = _int(params.get("ones")) or 0
    return {
        "type": "base_ten",
        "number": number,
        "hundreds": hundreds,
        "tens": tens,
        "ones": ones,
        "aria_label": (
            f"Base-ten blocks for {number}: "
            f"{hundreds} hundreds, {tens} tens, and {ones} ones."
        ),
    }


def _money_model(problem: Problem) -> dict | None:
    params = _params(problem)
    q = _int(params.get("quarters")) or 0
    d = _int(params.get("dimes")) or 0
    n = _int(params.get("nickels")) or 0
    p = _int(params.get("pennies")) or 0
    total = _int(params.get("total_cents"))
    if total is None:
        return None
    return {
        "type": "money",
        "quarters": q,
        "dimes": d,
        "nickels": n,
        "pennies": p,
        "total_cents": total,
        "aria_label": (
            f"Coins totaling {total} cents: "
            f"{q} quarters, {d} dimes, {n} nickels, {p} pennies."
        ),
    }


def _clock_model(problem: Problem) -> dict | None:
    params = _params(problem)
    hour = _int(params.get("hour"))
    minute = _int(params.get("minute"))
    if hour is None or minute is None:
        return None
    return {
        "type": "clock",
        "hour": hour,
        "minute": minute,
        "aria_label": f"Analog clock showing {hour}:{minute:02d}.",
    }


def _angle_model(problem: Problem) -> dict | None:
    params = _params(problem)
    angle = _int(params.get("angle"))
    if angle is None or not (0 <= angle <= 180):
        return None
    return {
        "type": "angle",
        "angle": angle,
        "aria_label": f"Angle measuring {angle} degrees.",
    }


def _coordinate_model(problem: Problem) -> dict | None:
    params = _params(problem)
    x = _int(params.get("x"))
    y = _int(params.get("y"))
    if x is None or y is None:
        return None
    return {
        "type": "coordinate_plane",
        "x": x,
        "y": y,
        "max": max(x, y, 10) + 1,
        "aria_label": f"Coordinate plane with point at ({x}, {y}).",
    }


def _volume_model(problem: Problem) -> dict | None:
    params = _params(problem)
    l = _int(params.get("length"))
    w = _int(params.get("width"))
    h = _int(params.get("height"))
    if l is None or w is None or h is None:
        return None
    return {
        "type": "volume",
        "length": l,
        "width": w,
        "height": h,
        "aria_label": (
            f"Rectangular prism with length {l}, width {w}, height {h}, "
            f"volume {l * w * h}."
        ),
    }


def _ruler_model(problem: Problem) -> dict | None:
    params = _params(problem)
    a = _int(params.get("a"))
    b = _int(params.get("b"))
    if a is None or b is None:
        return None
    lo = 0
    hi = max(a, b) + 2
    return {
        "type": "ruler",
        "a": a,
        "b": b,
        "min": lo,
        "max": hi,
        "aria_label": f"Ruler showing lengths {a} and {b} units.",
    }


def _shape_model(problem: Problem) -> dict | None:
    params = _params(problem)
    shape = params.get("shape")
    sides = _int(params.get("sides"))
    if shape is None:
        return None
    return {
        "type": "shape",
        "shape": shape,
        "sides": sides,
        "aria_label": f"A {shape} with {sides} sides.",
    }


def _bar_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    category = params.get("category")
    value = _int(params.get("value"))
    if category is None or value is None:
        return None
    return {
        "type": "bar_graph",
        "category": category,
        "value": value,
        "aria_label": f"Bar graph highlighting category {category} with value {value}.",
    }


def _picture_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    category = params.get("category")
    value = _int(params.get("value"))
    if category is None or value is None:
        return None
    return {
        "type": "picture_graph",
        "category": category,
        "value": value,
        "aria_label": f"Picture graph highlighting category {category} with value {value}.",
    }


def _number_line_model(problem: Problem) -> dict | None:
    params = _params(problem)
    if "numerator" in params and "denominator" in params:
        numerator = _int(params.get("numerator"))
        denominator = _int(params.get("denominator"))
        if numerator is None or denominator is None or denominator == 0:
            return None
        return {
            "type": "number_line",
            "min": 0,
            "max": 1,
            "tick_count": denominator,
            "mark_value": numerator / denominator,
            "aria_label": f"Number line from 0 to 1 showing {numerator}/{denominator}.",
        }
    return None


def _line_plot_model(problem: Problem) -> dict | None:
    params = _params(problem)
    data = params.get("data")
    value = _int(params.get("value"))
    if not isinstance(data, list) or value is None:
        return None
    return {
        "type": "line_plot",
        "data": data,
        "highlight": value,
        "aria_label": f"Line plot of measurements. Count how many are {value}.",
    }


def _place_value_disks(problem: Problem) -> dict | None:
    """Hundreds/tens/ones disks for multi-digit place value."""
    params = _params(problem)
    number = _int(params.get("number"))
    if number is None or number < 0 or number > 9999:
        return None
    digits = str(number).zfill(4)[-4:]
    thousands, hundreds, tens, ones = (
        int(digits[0]),
        int(digits[1]),
        int(digits[2]),
        int(digits[3]),
    )
    return {
        "type": "place_value_disks",
        "thousands": thousands,
        "hundreds": hundreds,
        "tens": tens,
        "ones": ones,
        "value": number,
        "aria_label": (
            f"Place value disks for {number}: "
            f"{thousands} thousand disks, {hundreds} hundred disks, "
            f"{tens} ten disks, {ones} one disks."
        ),
    }


def _decimal_place_value(problem: Problem) -> dict | None:
    """Decimal place-value chart for tenths/hundredths."""
    params = _params(problem)
    decimal_str = params.get("decimal")
    if decimal_str is None:
        return None
    try:
        value = float(decimal_str)
    except (TypeError, ValueError):
        return None
    # Split into whole and decimal parts
    whole = int(value)
    frac = value - whole
    tenths = int(frac * 10)
    hundredths = int(frac * 100) % 10
    return {
        "type": "decimal_place_value",
        "whole": whole,
        "tenths": tenths,
        "hundredths": hundredths,
        "value": value,
        "aria_label": (
            f"Decimal place value for {value}: "
            f"{whole} ones, {tenths} tenths, {hundredths} hundredths."
        ),
    }


def _comparison_bar(problem: Problem) -> dict | None:
    """Side-by-side comparison bars for comparing numbers."""
    params = _params(problem)
    a = _int(params.get("a"))
    b = _int(params.get("b"))
    if a is None or b is None:
        return None
    return {
        "type": "comparison_bars",
        "a": a,
        "b": b,
        "aria_label": f"Two bars: one for {a} and one for {b}. Compare their lengths.",
    }


def _fraction_circle(problem: Problem) -> dict | None:
    """Circular fraction model as an alternative to fraction bar."""
    params = _params(problem)
    numerator = _int(params.get("numerator"))
    denominator = _int(params.get("denominator"))
    if (
        numerator is None
        or denominator is None
        or denominator < 2
        or denominator > 12
        or numerator < 0
        or numerator > denominator
    ):
        return None
    return {
        "type": "fraction_circle",
        "numerator": numerator,
        "denominator": denominator,
        "aria_label": f"Circle divided into {denominator} equal parts, {numerator} shaded.",
    }



_LINEAR_TERM = re.compile(r"([+-]?\s*\d*)\s*([a-zA-Z])(?:\^(\d+))?")
_POLY_GROUPS = re.compile(r"\(([^()]*)\)\s*([+-])\s*\(([^()]*)\)")


def _algebra_terms(expression: str) -> list[dict[str, Any]]:
    """Parse the simple authored polynomial forms used by deterministic visuals."""
    normalized = expression.replace("−", "-").replace(" ", "")
    terms: list[dict[str, Any]] = []
    for token in re.findall(r"[+-]?[^+-]+", normalized):
        variable_match = re.fullmatch(r"([+-]?\d*)([a-zA-Z])(?:\^(\d+))?", token)
        if variable_match:
            raw, variable, degree_raw = variable_match.groups()
            if raw in {"", "+"}:
                coefficient = 1
            elif raw == "-":
                coefficient = -1
            else:
                coefficient = int(raw)
            terms.append(
                {
                    "coefficient": coefficient,
                    "variable": variable,
                    "degree": int(degree_raw or "1"),
                    "label": token.lstrip("+"),
                }
            )
            continue
        if re.fullmatch(r"[+-]?\d+", token):
            value = int(token)
            terms.append(
                {"coefficient": value, "variable": None, "degree": 0, "label": str(value)}
            )
    return terms

def _like_term_visual(problem: Problem) -> dict | None:
    expression = problem.prompt.removeprefix("Simplify ").rstrip(".")
    terms = _algebra_terms(expression)
    if len(terms) < 2:
        return None
    groups: dict[str, list[dict[str, Any]]] = {}
    for term in terms:
        key = f"{term['variable'] or 'constant'}^{term['degree']}"
        groups.setdefault(key, []).append(term)
    return {
        "type": "algebra_tiles",
        "terms": terms,
        "groups": [{"key": key, "terms": grouped} for key, grouped in groups.items()],
        "aria_label": (
            "Algebra tiles grouped by matching variable and exponent structure. "
            "Only terms in the same group are like terms."
        ),
    }


def _polynomial_sign_visual(problem: Problem) -> dict | None:
    expression = problem.prompt.removeprefix("Simplify ").rstrip(".")
    match = _POLY_GROUPS.search(expression)
    if not match:
        return None
    left, operation, right = match.groups()
    left_terms = _algebra_terms(left)
    right_terms = _algebra_terms(right)
    if not left_terms or not right_terms:
        return None
    transformed = [
        {**term, "coefficient": -term["coefficient"], "sign_changed": True}
        if operation == "-"
        else {**term, "sign_changed": False}
        for term in right_terms
    ]
    return {
        "type": "polynomial_sign_change",
        "operation": operation,
        "left_terms": left_terms,
        "right_terms": right_terms,
        "transformed_right_terms": transformed,
        "aria_label": (
            "Polynomial subtraction sign-change model. "
            + ("Every term in the subtracted group changes sign before like terms are combined."
               if operation == "-"
               else "The second polynomial keeps its signs before like terms are combined.")
        ),
    }


def visualization_for(problem: Problem) -> dict | None:
    """Return a declarative visual spec for a problem, or None."""
    if problem.problem_type == "SIMPLIFY_EXPRESSION":
        return _area_model(problem)
    if problem.problem_type == "COMBINE_LIKE_TERMS":
        return _like_term_visual(problem)
    if problem.problem_type == "POLYNOMIAL_ADD_SUBTRACT":
        return _polynomial_sign_visual(problem)
    if problem.problem_type == "INTEGER_OPERATIONS":
        return _number_line(problem)
    if problem.problem_type == "INTEGER_COMPARE":
        return _compare_points(problem)
    if problem.problem_type in {"EQUAL_GROUPS", "RECTANGLE_AREA"}:
        return _array_model(problem)
    if problem.problem_type == "UNIT_FRACTION":
        return _fraction_bar(problem)
    if problem.problem_type in {"ADDITION_WITHIN_20", "SUBTRACTION_WITHIN_20", "WORD_PROBLEM_ADD_SUB_20"}:
        return _ten_frame(problem)
    if problem.problem_type == "PLACE_VALUE_BASE_TEN":
        params = _params(problem)
        number = _int(params.get("number"))
        if number is not None and number > 999:
            return _place_value_disks(problem)
        return _base_ten_model(problem)
    if problem.problem_type == "MONEY_COUNT":
        return _money_model(problem)
    if problem.problem_type == "TIME_TO_HOUR_HALF_HOUR":
        return _clock_model(problem)
    if problem.problem_type == "TIME_TO_5_MINUTES":
        return _clock_model(problem)
    if problem.problem_type in {
        "ADDITION_WITHIN_100",
        "SUBTRACTION_WITHIN_100",
        "WORD_PROBLEM_ADD_SUB_100",
        "MULTI_DIGIT_MULTIPLICATION",
        "LONG_DIVISION",
        "NUMBER_SEQUENCE",
        "NUMBER_PATTERN",
        "EQUATION_BALANCE",
    }:
        return None
    if problem.problem_type == "DECIMAL_PLACE_VALUE":
        return _decimal_place_value(problem)
    if problem.problem_type == "COMPARE_NUMBERS":
        return _comparison_bar(problem)
    if problem.problem_type == "FRACTION_EQUIVALENCE":
        return _fraction_bar(problem)
    if problem.problem_type in {"FRACTION_ADD_SUBTRACT_LIKE", "FRACTION_MULTIPLY"}:
        return _fraction_bar(problem)
    if problem.problem_type == "FRACTION_HALVES_THIRDS_FOURTHS":
        return _fraction_circle(problem)
    if problem.problem_type == "FRACTION_COMPARE":
        return _fraction_bar(problem)
    if problem.problem_type == "FRACTION_CIRCLE":
        return _fraction_circle(problem)
    if problem.problem_type == "FRACTION_NUMBER_LINE":
        return _number_line_model(problem)
    if problem.problem_type == "COMPARE_LENGTH":
        return _ruler_model(problem)
    if problem.problem_type in {"AREA_PERIMETER_RECTANGLE"}:
        return None
    if problem.problem_type == "VOLUME":
        return _volume_model(problem)
    if problem.problem_type == "GEOMETRY_SHAPES":
        return _shape_model(problem)
    if problem.problem_type == "BAR_GRAPH_READ":
        return _bar_graph_model(problem)
    if problem.problem_type == "PICTURE_GRAPH_READ":
        return _picture_graph_model(problem)
    if problem.problem_type == "LINE_PLOT_READ":
        return _line_plot_model(problem)
    if problem.problem_type in {"CLASSIFY_SHAPE", "LINES_PARALLEL_PERPENDICULAR"}:
        return _shape_model(problem)
    if problem.problem_type == "ELAPSED_TIME":
        return _clock_model(problem)
    if problem.problem_type in {
        "ROUNDING",
        "WORD_PROBLEM_MULTIPLY_DIVIDE_100",
        "ADD_SUBTRACT_UNLIKE_FRACTIONS",
        "MULTIPLY_FRACTIONS",
        "DIVIDE_FRACTIONS",
        "DECIMAL_OPERATIONS",
        "POWERS_OF_TEN",
        "MEASUREMENT_CONVERSION",
    }:
        return None
    if problem.problem_type == "ANGLE_MEASUREMENT":
        return _angle_model(problem)
    if problem.problem_type == "COORDINATE_PLANE":
        return _coordinate_model(problem)
    return None
