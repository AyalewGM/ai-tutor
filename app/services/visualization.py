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


def visualization_for(problem: Problem) -> dict | None:
    """Return a declarative visual spec for a problem, or None."""
    if problem.problem_type == "SIMPLIFY_EXPRESSION":
        return _area_model(problem)
    if problem.problem_type == "INTEGER_OPERATIONS":
        return _number_line(problem)
    if problem.problem_type == "INTEGER_COMPARE":
        return _compare_points(problem)
    return None
