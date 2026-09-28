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


def visualization_for(problem: Problem) -> dict | None:
    """Return a declarative visual spec for a problem, or None."""
    if problem.problem_type == "SIMPLIFY_EXPRESSION":
        return _area_model(problem)
    if problem.problem_type == "INTEGER_OPERATIONS":
        return _number_line(problem)
    if problem.problem_type == "INTEGER_COMPARE":
        return _compare_points(problem)
    if problem.problem_type in {"EQUAL_GROUPS", "RECTANGLE_AREA"}:
        return _array_model(problem)
    if problem.problem_type == "UNIT_FRACTION":
        return _fraction_bar(problem)
    if problem.problem_type in {"ADDITION_WITHIN_20", "SUBTRACTION_WITHIN_20"}:
        return _ten_frame(problem)
    if problem.problem_type == "PLACE_VALUE_BASE_TEN":
        return _base_ten_model(problem)
    if problem.problem_type == "MONEY_COUNT":
        return _money_model(problem)
    if problem.problem_type == "TIME_TO_HOUR_HALF_HOUR":
        return _clock_model(problem)
    if problem.problem_type in {
        "ADDITION_WITHIN_100",
        "SUBTRACTION_WITHIN_100",
        "MULTI_DIGIT_MULTIPLICATION",
        "LONG_DIVISION",
    }:
        return None
    if problem.problem_type == "FRACTION_EQUIVALENCE":
        return _fraction_bar(problem)
    if problem.problem_type in {"FRACTION_ADD_SUBTRACT_LIKE", "FRACTION_MULTIPLY"}:
        return _fraction_bar(problem)
    if problem.problem_type == "DECIMAL_PLACE_VALUE":
        return None
    if problem.problem_type == "ANGLE_MEASUREMENT":
        return _angle_model(problem)
    if problem.problem_type == "COORDINATE_PLANE":
        return _coordinate_model(problem)
    if problem.problem_type == "VOLUME":
        return _volume_model(problem)
    return None
