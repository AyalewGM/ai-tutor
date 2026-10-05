"""Deterministic visualization specs (Issue #42, first slice).

Problem parameters → declarative spec → React SVG renderer. No LLM
involvement: coordinates and labels are computed here, so a diagram can
never misrepresent the math. Unknown problem shapes return None — the
renderer simply shows nothing.
"""

import json
import math
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
        "aria_label": (f"Number line from {lo} to {hi}: start at 0, move {a}, then move {b}."),
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
            f"Array with {rows} rows and {columns} columns, showing {rows * columns} items in all."
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
            f"Base-ten blocks for {number}: {hundreds} hundreds, {tens} tens, and {ones} ones."
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
            f"Coins totaling {total} cents: {q} quarters, {d} dimes, {n} nickels, {p} pennies."
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
        # Classify tiers hide the degree label — it would hand over the answer.
        "labeled": bool(params.get("labeled", True)),
        "aria_label": f"Angle measuring {angle} degrees.",
    }


def _geometry_2d_model(problem: Problem) -> dict | None:
    params = _params(problem)
    tier = params.get("tier")
    if tier in {"complementary", "supplementary"}:
        angle = _int(params.get("angle"))
        if angle is None or not (0 < angle < 180):
            return None
        return {
            "type": "angle_pair",
            "kind": tier,
            "angle": angle,
            "aria_label": "Two adjacent angles forming a right angle." if tier == "complementary" else "Two adjacent angles forming a straight line.",
        }
    if tier in {"linear_pair", "vertical_angles"}:
        angle = _int(params.get("angle"))
        mark = params.get("mark")
        if angle is None or not (0 < angle < 180) or mark not in {"adjacent", "vertical"}:
            return None
        return {
            "type": "intersecting_lines",
            "angle": angle,
            "mark": mark,
            "aria_label": "Two intersecting lines with one angle labeled.",
        }
    if tier == "triangle_angle":
        a = _int(params.get("a"))
        b = _int(params.get("b"))
        if a is None or b is None or not (0 < a < 180 and 0 < b < 180 and a + b < 180):
            return None
        return {
            "type": "triangle_angles",
            "a": a,
            "b": b,
            "aria_label": "A triangle with two labeled angles and one unknown.",
        }
    if tier in {"circle_area", "circle_circumference"}:
        r = _int(params.get("r"))
        if r is None or r <= 0:
            return None
        return {
            "type": "circle_measure",
            "r": r,
            "aria_label": f"A circle with radius {r}.",
        }
    if tier == "composite_area":
        w = _int(params.get("w"))
        h = _int(params.get("h"))
        a = _int(params.get("a"))
        b = _int(params.get("b"))
        if None in (w, h, a, b) or not (0 < a < w and 0 < b < h):
            return None
        return {
            "type": "composite_figure",
            "w": w,
            "h": h,
            "a": a,
            "b": b,
            "aria_label": "An L-shaped figure with labeled side lengths.",
        }
    return None


def _transformation_model(problem: Problem) -> dict | None:
    params = _params(problem)
    preimage = params.get("preimage")
    if (
        not isinstance(preimage, list)
        or not preimage
        or not all(isinstance(p, list) and len(p) == 2 for p in preimage)
    ):
        return None
    model: dict = {
        "type": "transformation",
        "preimage": preimage,
        "aria_label": "A coordinate plane showing a figure to transform.",
    }
    image = params.get("image")
    if isinstance(image, list) and image:
        model["image"] = image
        model["aria_label"] = "A coordinate plane showing a triangle and its image."
    if isinstance(params.get("labels"), list):
        model["labels"] = params["labels"]
    if isinstance(params.get("image_labels"), list):
        model["image_labels"] = params["image_labels"]
    return model


def _similarity_model(problem: Problem) -> dict | None:
    params = _params(problem)
    preimage = params.get("preimage")
    image = params.get("image")
    if not (
        isinstance(preimage, list)
        and isinstance(image, list)
        and preimage
        and image
    ):
        return None
    model: dict = {
        "type": "similar_figures",
        "preimage": preimage,
        "image": image,
        "aria_label": "Two triangles drawn to scale.",
    }
    for key in ("pre_edge_labels", "image_edge_labels"):
        if isinstance(params.get(key), list):
            model[key] = params[key]
    return model


def _system_model(problem: Problem) -> dict | None:
    params = _params(problem)
    # The solve tier is deliberately diagram-free: rendering both lines
    # would hand the learner the intersection.
    if params.get("tier") == "solve":
        return None
    lines = params.get("lines")
    if not isinstance(lines, list) or len(lines) != 2:
        return None
    for line in lines:
        if not isinstance(line, dict) or any(
            line.get(k) is None
            for k in ("m_num", "m_den", "i_num", "i_den")
        ):
            return None
    return {
        "type": "linear_system",
        "lines": lines,
        "min": -9,
        "max": 9,
        "aria_label": "Two lines graphed on a coordinate plane.",
    }


def _scatterplot_model(problem: Problem) -> dict | None:
    params = _params(problem)
    points = params.get("points")
    if (
        not isinstance(points, list)
        or not points
        or not all(isinstance(p, list) and len(p) == 2 for p in points)
    ):
        return None
    model: dict = {
        "type": "scatterplot",
        "points": points,
        "x_max": 10,
        "y_max": 10,
        "aria_label": "A scatterplot of data points.",
    }
    # The best-fit line is part of the predict prompt; drawing it elsewhere
    # would answer the question.
    fit = params.get("fit")
    if isinstance(fit, dict) and all(
        fit.get(k) is not None for k in ("m_num", "m_den", "i_num", "i_den")
    ):
        model["fit"] = fit
        model["aria_label"] = "A scatterplot with its line of best fit."
    return model


def _frequency_table_model(problem: Problem) -> dict | None:
    params = _params(problem)
    rows = params.get("rows")
    cols = params.get("cols")
    cells = params.get("cells")
    if not (
        isinstance(rows, list) and len(rows) == 2
        and isinstance(cols, list) and len(cols) == 2
        and isinstance(cells, list) and len(cells) == 2
        and all(isinstance(r, list) and len(r) == 2 for r in cells)
    ):
        return None
    a, b = cells[0]
    c, d = cells[1]
    model: dict = {
        "type": "frequency_table",
        "row_labels": rows,
        "col_labels": cols,
        "cells": cells,
        "aria_label": "A two-way frequency table of survey results.",
    }
    # Totals are withheld on tiers that ask for them — the empty Total
    # row and column are the work the learner does.
    if params.get("show_totals"):
        model["row_totals"] = [a + b, c + d]
        model["col_totals"] = [a + c, b + d]
        model["grand_total"] = a + b + c + d
    return model


def _probability_model(problem: Problem) -> dict | None:
    params = _params(problem)
    kind = params.get("kind")
    if kind == "spinner":
        sections = params.get("sections")
        if not (isinstance(sections, list) and 2 <= len(sections) <= 8):
            return None
        return {
            "type": "spinner",
            "sections": sections,
            "aria_label": f"A spinner divided into {len(sections)} equal sections.",
        }
    if kind == "bag":
        marbles = params.get("marbles")
        if not (isinstance(marbles, list) and 1 <= len(marbles) <= 12):
            return None
        return {
            "type": "marble_bag",
            "marbles": marbles,
            "aria_label": f"A bag containing {len(marbles)} marbles.",
        }
    return None


def _pythagorean_model(problem: Problem) -> dict | None:
    params = _params(problem)
    tier = params.get("tier")
    if tier == "distance":
        points = params.get("points")
        if not (
            isinstance(points, list) and len(points) == 2
            and all(isinstance(p, list) and len(p) == 2 for p in points)
        ):
            return None
        return {
            "type": "distance_segment",
            "points": points,
            "labels": ["A", "B"],
            "aria_label": "Two points on a coordinate plane joined by a segment.",
        }
    if tier in {"hypotenuse", "leg", "radical_hypotenuse"}:
        a, b = _int(params.get("a")), _int(params.get("b"))
        if a is None or b is None:
            return None
        labels = {"leg_a": str(a), "leg_b": str(b), "hyp": "?"}
        if tier == "leg":
            c = _int(params.get("c"))
            if c is None:
                return None
            labels = {"leg_a": str(a), "leg_b": "?", "hyp": str(c)}
        return {
            "type": "right_triangle",
            "a": a,
            "b": b,
            **labels,
            "aria_label": "A right triangle with labeled sides.",
        }
    # Converse items stay text-only: a drawn right triangle would answer
    # the question.
    return None


def _coordinate_model(problem: Problem) -> dict | None:
    params = _params(problem)
    x = _int(params.get("x"))
    y = _int(params.get("y"))
    if x is None or y is None:
        return None
    labeled = params.get("labeled", True)
    return {
        "type": "coordinate_plane",
        "x": x,
        "y": y,
        "labeled": bool(labeled),
        "min": min(-10, min(x, y) - 2),
        "max": max(10, max(x, y) + 2),
        "aria_label": (
            f"Coordinate plane with a point at ({x}, {y})."
            if labeled
            else "Coordinate plane with a point plotted — read its coordinates."
        ),
    }


def _linear_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    m_num = _int(params.get("m_num"))
    m_den = _int(params.get("m_den"))
    b = _int(params.get("b"))
    if m_num is None or m_den is None or b is None or m_den == 0:
        return None
    return {
        "type": "linear_graph",
        "m_num": m_num,
        "m_den": m_den,
        "b": b,
        "min": -10,
        "max": 10,
        # Marking the intercept's lattice neighbours is the low-difficulty
        # scaffold — it turns the slope read into a rise-over-run count.
        "mark_lattice": bool(params.get("tier") in {"read_slope", "read_intercept"})
        and problem.difficulty <= 2,
        "aria_label": "A line graphed on a coordinate plane.",
    }


def _parabola_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    a_num = _int(params.get("a_num"))
    a_den = _int(params.get("a_den"))
    h = _int(params.get("h"))
    k = _int(params.get("k"))
    if a_num is None or a_den is None or h is None or k is None or a_den == 0:
        return None
    return {
        "type": "parabola_graph",
        "a_num": a_num,
        "a_den": a_den,
        "h": h,
        "k": k,
        "min": -10,
        "max": 10,
        "aria_label": "A parabola graphed on a coordinate plane.",
    }


def _polynomial_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    if params.get("tier") not in {"count_roots", "write_equation"}:
        return None
    coeffs = params.get("coeffs")
    if not isinstance(coeffs, list) or len(coeffs) < 2 or not all(
        isinstance(c, (int, float)) for c in coeffs
    ):
        return None
    roots = params.get("roots")
    return {
        "type": "polynomial_graph",
        "coeffs": coeffs,
        # Marked crossings are the read scaffold for equation matching —
        # they must stay hidden when the question is counting them.
        "roots": roots if isinstance(roots, list) else [],
        "mark_roots": params.get("tier") == "write_equation",
        "min": -10,
        "max": 10,
        "aria_label": "A polynomial curve graphed on a coordinate plane.",
    }


def _exponential_graph_model(problem: Problem) -> dict | None:
    params = _params(problem)
    if params.get("tier") in {"evaluate", "next_value"}:
        return None
    a = _int(params.get("a"))
    b_num = _int(params.get("b_num"))
    b_den = _int(params.get("b_den"))
    if a is None or b_num is None or b_den is None or b_den == 0:
        return None
    model: dict = {
        "type": "exponential_graph",
        "a": a,
        "b_num": b_num,
        "b_den": b_den,
        "x_min": -6,
        "x_max": 6,
        "y_min": -1,
        "y_max": 16,
        "aria_label": "An exponential curve graphed on a coordinate plane.",
    }
    # Marked lattice points scaffold the growth_factor and write_equation
    # reads; the classify/intercept tiers leave the curve unmarked.
    mark = params.get("mark_points")
    if isinstance(mark, list) and mark:
        model["mark_points"] = mark
    return model


def _volume_model(problem: Problem) -> dict | None:
    params = _params(problem)
    l = _int(params.get("length"))
    w = _int(params.get("width"))
    h = _int(params.get("height"))
    if l is None or w is None or h is None:
        return None
    return {
        "type": "solid",
        "solid": "rectangular_prism",
        "l": l,
        "w": w,
        "h": h,
        "aria_label": f"Rectangular prism with length {l}, width {w}, height {h}.",
    }


_SOLID_DIM_KEYS = {
    "rectangular_prism": ("l", "w", "h"),
    "square_pyramid": ("b", "h"),
    "cylinder": ("r", "h"),
    "cone": ("r", "h"),
}


def _solid_model(problem: Problem) -> dict | None:
    params = _params(problem)
    solid = params.get("solid")
    keys = _SOLID_DIM_KEYS.get(solid)
    if keys is None:
        return None
    spec = {"type": "solid", "solid": solid}
    # Property-counting tiers render the same solids unlabelled; every
    # other tier must carry the dimensions its prompt references.
    dims_optional = params.get("tier") in {"count_faces", "count_edges"}
    for key in keys:
        value = _int(params.get(key))
        if value is None:
            if not dims_optional:
                return None
        else:
            spec[key] = value
    names = {
        "rectangular_prism": "rectangular prism",
        "square_pyramid": "square pyramid",
        "cylinder": "cylinder",
        "cone": "cone",
    }
    dims = ", ".join(f"{key} = {spec[key]}" for key in keys if key in spec)
    spec["aria_label"] = f"A {names[solid]}." if not dims else f"A {names[solid]} with {dims}."
    return spec


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
            terms.append({"coefficient": value, "variable": None, "degree": 0, "label": str(value)})
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
            + (
                "Every term in the subtracted group changes sign before like terms are combined."
                if operation == "-"
                else "The second polynomial keeps its signs before like terms are combined."
            )
        ),
    }


def _parse_int(text: str) -> int | None:
    if not text:
        return None
    sign = -1 if text[0] == "-" else 1
    digits = text[1:] if text[0] in "+-" else text
    if not digits or not digits.isdigit():
        return None
    return sign * int(digits)


def _linear_side(text: str) -> tuple[int, int] | None:
    """Parse a small linear side without regex backtracking on learner input."""
    value = "".join(text.replace("−", "-").split())
    if not value or len(value) > 64:
        return None

    # Bare constant.
    constant = _parse_int(value)
    if constant is not None:
        return 0, constant

    # Distributed form: a(x+b) or a(x-b).
    if value.endswith(")") and "(" in value:
        coeff_text, inner = value.split("(", 1)
        if not inner.endswith(")"):
            return None
        inner = inner[:-1]
        if not inner.startswith("x") or len(inner) < 3 or inner[1] not in "+-":
            return None
        a = -1 if coeff_text == "-" else (1 if coeff_text in ("", "+") else _parse_int(coeff_text))
        b = _parse_int(inner[1:])
        if a is None or b is None:
            return None
        return a, a * b

    # ax, ax+b, or ax-b.
    if "x" not in value or value.count("x") != 1:
        return None
    coeff_text, tail = value.split("x", 1)
    a = -1 if coeff_text == "-" else (1 if coeff_text in ("", "+") else _parse_int(coeff_text))
    if a is None:
        return None
    if not tail:
        return a, 0
    if tail[0] not in "+-":
        return None
    b = _parse_int(tail)
    if b is None:
        return None
    return a, b


def _balance_scale(problem: Problem) -> dict | None:
    """Two-pan balance for a linear equation: x-blocks and unit weights per side.

    Honest for ax + b = c with 0 < a <= 6 and small constants; anything else
    (negatives on the pans, big numbers) returns None rather than a misleading
    picture.
    """
    from app.services.stepwork import starting_equation

    equation = starting_equation(problem.prompt)
    if equation is None:
        return None
    return _balance_scale_for_equation(equation)


def _balance_scale_for_equation(equation: str) -> dict | None:
    """Balance-scale spec for any 'lhs = rhs' text, e.g. a learner's line."""
    lhs_text, _, rhs_text = equation.partition("=")
    lhs, rhs = _linear_side(lhs_text), _linear_side(rhs_text)
    if lhs is None or rhs is None:
        return None
    a_l, b_l = lhs
    a_r, b_r = rhs
    if a_l < 0 or a_r < 0 or b_l < 0 or b_r < 0 or max(a_l, a_r) > 6 or max(b_l, b_r) > 30:
        return None
    if a_l == 0 and a_r == 0:
        return None
    return {
        "type": "balance_scale",
        "left": {"x_count": a_l, "units": b_l},
        "right": {"x_count": a_r, "units": b_r},
        "aria_label": (
            f"A balance scale. Left pan: {a_l} x-block{'s' if a_l != 1 else ''} and "
            f"{b_l} unit weight{'s' if b_l != 1 else ''}. Right pan: {a_r} x-block"
            f"{'s' if a_r != 1 else ''} and {b_r} unit weight{'s' if b_r != 1 else ''}. "
            "The pans balance, so both sides are equal."
        ),
    }


_FRACTION_OP = re.compile(r"(\d+)\s*/\s*(\d+)\s*([+\-−])\s*(\d+)\s*/\s*(\d+)")


def _fraction_operation_bars(problem: Problem) -> dict | None:
    """Two fraction bars drawn on a common-denominator grid for + / −."""
    params = _params(problem)
    n1, d1, n2, d2 = (_int(params.get(k)) for k in ("n1", "d1", "n2", "d2"))
    operation = "+" if problem.problem_type != "FRACTION_SUBTRACT" else "-"
    if None in (n1, d1, n2, d2):
        match = _FRACTION_OP.search(problem.prompt.replace("−", "-"))
        if not match:
            return None
        n1, d1, n2, d2 = (int(match.group(i)) for i in (1, 2, 4, 5))
        operation = "-" if match.group(3) in "-−" else "+"
    if min(d1, d2) < 2 or n1 > d1 or n2 > d2 or n1 < 0 or n2 < 0:
        return None
    common = d1 * d2 // math.gcd(d1, d2)
    if common > 24:
        return None
    return {
        "type": "fraction_operation",
        "operation": operation,
        "first": {"numerator": n1, "denominator": d1},
        "second": {"numerator": n2, "denominator": d2},
        "common_denominator": common,
        "aria_label": (
            f"Two fraction bars: {n1}/{d1} and {n2}/{d2}, both divided into "
            f"{common} equal parts so the pieces match before "
            f"{'adding' if operation == '+' else 'subtracting'}."
        ),
    }


def _tape_diagram(problem: Problem) -> dict | None:
    """Bar model for a word problem: segments whose lengths follow the parameters."""
    params = _params(problem)
    solution = problem.solution or {}
    family = str(solution.get("problem_family") or "")
    template = family.split(":", 1)[1] if ":" in family else params.get("template")
    if template == "percent_of":
        percent, amount = _int(params.get("percent")), _int(params.get("amount"))
        if percent is None or amount is None or not (0 < percent <= 100):
            return None
        return {
            "type": "tape_diagram",
            "total_label": str(amount),
            "segments": [
                {"label": f"{percent}%", "span": percent, "highlight": True},
                {"label": "", "span": 100 - percent, "highlight": False},
            ],
            "aria_label": f"A bar representing {amount}, with {percent} percent of it shaded.",
        }
    if template == "unit_rate":
        distance, hours = _int(params.get("distance")), _int(params.get("hours"))
        if not distance or not hours or hours > 8:
            return None
        return {
            "type": "tape_diagram",
            "total_label": f"{distance} miles",
            "segments": [{"label": "?", "span": 1, "highlight": i == 0} for i in range(hours)],
            "aria_label": f"A bar for {distance} miles split into {hours} equal hours; one hour is highlighted.",
        }
    if template in {"flat_fee", "savings"}:
        fixed = _int(params.get("fee") if template == "flat_fee" else params.get("saved"))
        rate = _int(params.get("rate") if template == "flat_fee" else params.get("weekly"))
        count = _int(params.get("miles") if template == "flat_fee" else params.get("weeks"))
        if fixed is None or rate is None or count is None or count > 15:
            return None
        unit = "mile" if template == "flat_fee" else "week"
        # The count of rate parts is the answer, so it is drawn as a single
        # unknown-length part rather than N visible segments.
        return {
            "type": "tape_diagram",
            "total_label": f"${fixed + rate * count}",
            "segments": [
                {"label": f"${fixed}", "span": 2, "highlight": True},
                {"label": f"${rate} × ?", "span": 5, "highlight": False},
            ],
            "aria_label": (
                f"A bar for the total: a fixed ${fixed} part followed by an unknown "
                f"number of ${rate} parts, one per {unit}."
            ),
        }
    if template == "number_trick":
        a, b, x = (
            _int(params.get("multiplier")),
            _int(params.get("added")),
            _int(params.get("value")),
        )
        if a is None or b is None or x is None or a > 9:
            return None
        # Unknown parts get a fixed width — the diagram must not leak x's size.
        return {
            "type": "tape_diagram",
            "total_label": str(a * x + b),
            "segments": [{"label": "x", "span": 4, "highlight": True} for _ in range(a)]
            + [{"label": str(b), "span": 3, "highlight": False}],
            "aria_label": f"A bar made of {a} equal x parts plus {b}, totaling {a * x + b}.",
        }
    if template == "shared_total":
        k, x = _int(params.get("ratio")), _int(params.get("leo"))
        if k is None or x is None or k > 6:
            return None
        return {
            "type": "tape_diagram",
            "total_label": str((k + 1) * x),
            "segments": [{"label": "Leo", "span": 1, "highlight": True}]
            + [{"label": "Mia", "span": 1, "highlight": False} for _ in range(k)],
            "aria_label": f"A bar split into {k + 1} equal parts: 1 for Leo and {k} for Mia, totaling {(k + 1) * x}.",
        }
    return None


def step_visual(problem: Problem, line: str | None) -> dict | None:
    """Visual anchored at the learner's *current* line, not the problem start.

    CPA PICTORIAL/CONCRETE presentation: render the last accepted line (or the
    problem's starting point) so the picture tracks where the learner actually
    is. Equation lines become a balance scale of that line; other strands fall
    back to the problem-level spec. Returns None when nothing honest exists.
    """
    anchor = line or None
    if anchor is None:
        from app.services.stepwork import starting_point

        anchor = starting_point(problem)
    if anchor and "=" in anchor:
        spec = _balance_scale_for_equation(anchor)
        if spec is not None:
            return spec
    return visualization_for(problem)


def _pan_text(pan: dict) -> str:
    """'3x + 12' / 'x' / '12' from a balance pan spec."""
    x_count, units = int(pan.get("x_count", 0)), int(pan.get("units", 0))
    parts = []
    if x_count:
        parts.append("x" if x_count == 1 else f"{x_count}x")
    if units:
        parts.append(str(units))
    return " + ".join(parts) or "0"


def chat_cpa_block(spec: dict | None) -> str | None:
    """Translate a declarative spec into a ```json:cpa fenced block.

    The chat CPAVisualizer renders payload types FRACTION_BARS and
    BALANCE_SCALE; spec types with no honest chat payload (tape diagrams,
    ten frames, …) return None and the tutor message goes out unadorned.
    Pure formatting — the spec is already the application-owned truth.
    """
    if not spec:
        return None
    kind = spec.get("type")
    payload: dict | None = None
    if kind == "balance_scale":
        payload = {
            "type": "BALANCE_SCALE",
            "title": "Balance scale",
            "balanceScale": {
                "leftExpr": _pan_text(spec.get("left") or {}),
                "rightExpr": _pan_text(spec.get("right") or {}),
            },
        }
    elif kind == "fraction_operation":
        common = spec.get("common_denominator")
        first, second = spec.get("first") or {}, spec.get("second") or {}
        n1, d1 = first.get("numerator"), first.get("denominator")
        n2, d2 = second.get("numerator"), second.get("denominator")
        if common and all(isinstance(v, int) for v in (n1, d1, n2, d2)):
            payload = {
                "type": "FRACTION_BARS",
                "title": "Same-size pieces",
                "fractionBars": [
                    {
                        "numerator": n1 * common // d1,
                        "denominator": common,
                        "label": f"{n1}/{d1} =",
                    },
                    {
                        "numerator": n2 * common // d2,
                        "denominator": common,
                        "label": f"{n2}/{d2} =",
                    },
                ],
            }
    elif kind in {"fraction_bar", "ratio_bar"}:
        numerator, denominator = spec.get("numerator"), spec.get("denominator")
        if isinstance(numerator, int) and isinstance(denominator, int):
            payload = {
                "type": "FRACTION_BARS",
                "title": "Fraction bar",
                "fractionBars": [{"numerator": numerator, "denominator": denominator}],
            }
    if payload is None:
        return None
    return "```json:cpa\n" + json.dumps(payload) + "\n```"


def visualization_for(problem: Problem) -> dict | None:
    """Return a declarative visual spec for a problem, or None."""
    if problem.problem_type == "SOLVE_EQUATION":
        return _balance_scale(problem)
    if problem.problem_type in {"FRACTION_OPERATIONS", "FRACTION_SUBTRACT"}:
        return _fraction_operation_bars(problem)
    if problem.problem_type in {"WORD_PROBLEM", "ALGEBRA_WORD_PROBLEM"}:
        return _tape_diagram(problem)
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
    if problem.problem_type in {
        "ADDITION_WITHIN_20",
        "SUBTRACTION_WITHIN_20",
        "WORD_PROBLEM_ADD_SUB_20",
    }:
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
    if problem.problem_type == "LINEAR_GRAPH":
        return _linear_graph_model(problem)
    if problem.problem_type == "QUADRATIC_FUNCTION":
        return _parabola_graph_model(problem)
    if problem.problem_type == "POLYNOMIAL_FUNCTION":
        return _polynomial_graph_model(problem)
    if problem.problem_type == "SOLID_VOLUME":
        return _solid_model(problem)
    if problem.problem_type == "GEOMETRY_2D":
        return _geometry_2d_model(problem)
    if problem.problem_type == "TRANSFORMATION":
        return _transformation_model(problem)
    if problem.problem_type == "SIMILARITY":
        return _similarity_model(problem)
    if problem.problem_type == "SYSTEM_OF_EQUATIONS":
        return _system_model(problem)
    if problem.problem_type == "STATISTICS":
        return _scatterplot_model(problem)
    if problem.problem_type == "FREQUENCY_TABLE":
        return _frequency_table_model(problem)
    if problem.problem_type == "PROBABILITY":
        return _probability_model(problem)
    if problem.problem_type == "PYTHAGOREAN":
        return _pythagorean_model(problem)
    if problem.problem_type == "EXPONENTIAL_FUNCTION":
        return _exponential_graph_model(problem)
    return None
