"""Canonical geometry and measurement problem families."""

from __future__ import annotations

import math
import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.GEO.SHAPE.CLASSIFY": _spec("MATH.GEO.SHAPE.CLASSIFY", "Classify quadrilaterals by properties", "MATH.GEO.SHAPES", "CLASSIFICATION", 1, 3, "conceptual_understanding", "properties"),
    "MATH.GEO.PERIM.RECT": _spec("MATH.GEO.PERIM.RECT", "Rectangle perimeter", "MATH.GEO.MEASURE.PERIMETER", "MEASUREMENT", 1, 3, "procedural_fluency", "measurement"),
    "MATH.GEO.AREA.RECT": _spec("MATH.GEO.AREA.RECT", "Rectangle area", "MATH.GEO.MEASURE.AREA", "MEASUREMENT", 1, 3, "procedural_fluency", "measurement"),
    "MATH.GEO.AREA.TRI": _spec("MATH.GEO.AREA.TRI", "Triangle area", "MATH.GEO.MEASURE.AREA", "MEASUREMENT", 2, 4, "procedural_fluency", "representation"),
    "MATH.GEO.AREA.PARALLELOGRAM": _spec("MATH.GEO.AREA.PARALLELOGRAM", "Parallelogram area", "MATH.GEO.MEASURE.AREA", "MEASUREMENT", 2, 4, "procedural_fluency", "representation"),
    "MATH.GEO.AREA.TRAPEZOID": _spec("MATH.GEO.AREA.TRAPEZOID", "Trapezoid area", "MATH.GEO.MEASURE.AREA", "MEASUREMENT", 3, 4, "procedural_fluency", "reasoning"),
    "MATH.GEO.AREA.COMPOSITE": _spec("MATH.GEO.AREA.COMPOSITE", "Composite rectilinear area", "MATH.GEO.MEASURE.AREA", "MEASUREMENT", 3, 4, "reasoning", "decomposition"),
    "MATH.GEO.VOLUME.PRISM": _spec("MATH.GEO.VOLUME.PRISM", "Rectangular-prism volume", "MATH.GEO.MEASURE.VOLUME", "MEASUREMENT", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.SURFACE.PRISM": _spec("MATH.GEO.SURFACE.PRISM", "Rectangular-prism surface area", "MATH.GEO.MEASURE.SURFACE_AREA", "MEASUREMENT", 3, 4, "procedural_fluency", "spatial_reasoning"),
    "MATH.GEO.ANGLE.CLASSIFY": _spec("MATH.GEO.ANGLE.CLASSIFY", "Classify an angle", "MATH.GEO.ANGLES", "CLASSIFICATION", 1, 3, "conceptual_understanding", "representation"),
    "MATH.GEO.ANGLE.COMPLEMENT": _spec("MATH.GEO.ANGLE.COMPLEMENT", "Complementary angle", "MATH.GEO.ANGLES", "ANGLE_REASONING", 2, 4, "reasoning", "inverse_operations"),
    "MATH.GEO.ANGLE.SUPPLEMENT": _spec("MATH.GEO.ANGLE.SUPPLEMENT", "Supplementary angle", "MATH.GEO.ANGLES", "ANGLE_REASONING", 2, 4, "reasoning", "inverse_operations"),
    "MATH.GEO.TRIANGLE.MISSING_ANGLE": _spec("MATH.GEO.TRIANGLE.MISSING_ANGLE", "Triangle missing angle", "MATH.GEO.TRIANGLES", "ANGLE_REASONING", 2, 4, "reasoning", "properties"),
    "MATH.GEO.COORD.AXIS_DISTANCE": _spec("MATH.GEO.COORD.AXIS_DISTANCE", "Axis-aligned coordinate distance", "MATH.GEO.COORDINATE", "COORDINATE_GEOMETRY", 2, 4, "representation", "reasoning"),
    "MATH.GEO.PYTHAGOREAN.HYPOTENUSE": _spec("MATH.GEO.PYTHAGOREAN.HYPOTENUSE", "Pythagorean hypotenuse", "MATH.GEO.PYTHAGOREAN", "RIGHT_TRIANGLE", 3, 4, "procedural_fluency", "reasoning"),
    "MATH.GEO.TRANSFORM.TRANSLATE_POINT": _spec("MATH.GEO.TRANSFORM.TRANSLATE_POINT", "Translate a coordinate point", "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4, "representation", "spatial_reasoning"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.GEO.SHAPE.CLASSIFY":
        shape, answer, wrong = rng.choice([
            ("four equal sides and four right angles", "square", "rectangle"),
            ("two pairs of parallel sides and four right angles", "rectangle", "rhombus"),
            ("four equal sides, with opposite angles equal", "rhombus", "square"),
            ("exactly one pair of parallel sides", "trapezoid", "parallelogram"),
        ])
        return f"Name the most specific quadrilateral described: {shape}.", answer, ("List the defining properties.", "Choose the most specific name that must be true."), {"GEO.CLASSIFY.OVERGENERALIZE": wrong}
    if family_code == "MATH.GEO.PERIM.RECT":
        l, w = rng.randint(3, 15), rng.randint(2, 12)
        return f"A rectangle is {l} units long and {w} units wide. What is its perimeter?", str(2 * (l + w)), ("Perimeter measures distance around the boundary.", "Add both lengths and both widths."), {"GEO.PERIM.AREA_CONFUSION": str(l * w)}
    if family_code == "MATH.GEO.AREA.RECT":
        l, w = rng.randint(3, 15), rng.randint(2, 12)
        return f"A rectangle is {l} units long and {w} units wide. What is its area?", str(l * w), ("Area measures the surface inside the boundary.", "Multiply length by width."), {"GEO.AREA.PERIM_CONFUSION": str(2 * (l + w))}
    if family_code == "MATH.GEO.AREA.TRI":
        b, h = rng.randint(4, 16), rng.randint(3, 12)
        if b * h % 2:
            b += 1
        return f"A triangle has base {b} units and perpendicular height {h} units. What is its area?", str(b * h // 2), ("Use the perpendicular height.", "Triangle area is one half of base times height."), {"GEO.AREA.TRI.NO_HALF": str(b * h)}
    if family_code == "MATH.GEO.AREA.PARALLELOGRAM":
        b, h = rng.randint(4, 15), rng.randint(3, 11)
        slant = h + rng.randint(1, 5)
        return f"A parallelogram has base {b}, perpendicular height {h}, and slant side {slant}. What is its area?", str(b * h), ("Use the perpendicular height, not the slant side.", "Multiply base by perpendicular height."), {"GEO.AREA.USE_SLANT": str(b * slant)}
    if family_code == "MATH.GEO.AREA.TRAPEZOID":
        a, b, h = rng.randint(3, 8), rng.randint(9, 16), rng.randint(2, 10)
        if (a + b) * h % 2:
            h += 1
        correct = (a + b) * h // 2
        return f"A trapezoid has parallel bases {a} and {b} and height {h}. What is its area?", str(correct), ("Add the parallel bases.", "Multiply their sum by the height, then divide by 2."), {"GEO.AREA.TRAP.NO_HALF": str((a + b) * h)}
    if family_code == "MATH.GEO.AREA.COMPOSITE":
        w, h = rng.randint(8, 15), rng.randint(7, 13)
        a, b = rng.randint(2, w - 3), rng.randint(2, h - 3)
        correct = w * h - a * b
        return f"An L-shaped region is formed from a {w} by {h} rectangle with a {a} by {b} rectangular corner removed. What is its area?", str(correct), ("Find the area of the full outer rectangle.", "Subtract the area of the removed corner."), {"GEO.AREA.COMPOSITE.IGNORE_CUTOUT": str(w * h)}
    if family_code == "MATH.GEO.VOLUME.PRISM":
        l, w, h = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
        return f"A rectangular prism has length {l}, width {w}, and height {h}. What is its volume?", str(l * w * h), ("Volume counts cubic units.", "Multiply length, width, and height."), {"GEO.VOLUME.OMIT_DIMENSION": str(l * w)}
    if family_code == "MATH.GEO.SURFACE.PRISM":
        l, w, h = rng.randint(2, 8), rng.randint(2, 8), rng.randint(2, 8)
        correct = 2 * (l * w + l * h + w * h)
        return f"A rectangular prism has length {l}, width {w}, and height {h}. What is its surface area?", str(correct), ("There are three pairs of congruent faces.", "Add lw, lh, and wh, then double the sum."), {"GEO.SURFACE.VOLUME_CONFUSION": str(l * w * h)}
    if family_code == "MATH.GEO.ANGLE.CLASSIFY":
        angle = rng.choice([25, 40, 65, 90, 105, 125, 150, 180])
        answer = "acute" if angle < 90 else "right" if angle == 90 else "obtuse" if angle < 180 else "straight"
        wrong = "obtuse" if answer == "acute" else "acute"
        return f"Classify a {angle} degree angle.", answer, ("Compare the angle with 90 and 180 degrees.", "Use acute, right, obtuse, or straight."), {"GEO.ANGLE.CLASSIFY": wrong}
    if family_code == "MATH.GEO.ANGLE.COMPLEMENT":
        a = rng.randint(15, 75)
        return f"Two angles are complementary. One angle measures {a} degrees. What is the other angle?", str(90 - a), ("Complementary angles total 90 degrees.", f"Subtract {a} from 90."), {"GEO.ANGLE.SUPPLEMENT_SWAP": str(180 - a)}
    if family_code == "MATH.GEO.ANGLE.SUPPLEMENT":
        a = rng.randint(20, 160)
        return f"Two angles are supplementary. One angle measures {a} degrees. What is the other angle?", str(180 - a), ("Supplementary angles total 180 degrees.", f"Subtract {a} from 180."), {"GEO.ANGLE.COMPLEMENT_SWAP": str(abs(90 - a))}
    if family_code == "MATH.GEO.TRIANGLE.MISSING_ANGLE":
        a, b = rng.randint(25, 80), rng.randint(25, 80)
        while a + b >= 155:
            b = rng.randint(25, 70)
        return f"A triangle has angles of {a} degrees and {b} degrees. What is the third angle?", str(180 - a - b), ("The interior angles of a triangle total 180 degrees.", "Subtract both known angles from 180."), {"GEO.TRIANGLE.USE_360": str(360 - a - b)}
    if family_code == "MATH.GEO.COORD.AXIS_DISTANCE":
        if rng.random() < 0.5:
            x = rng.randint(-6, 6)
            y1, y2 = rng.sample(range(-8, 9), 2)
            p1, p2 = (x, y1), (x, y2)
        else:
            y = rng.randint(-6, 6)
            x1, x2 = rng.sample(range(-8, 9), 2)
            p1, p2 = (x1, y), (x2, y)
        distance = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        wrong = abs(p1[0] + p2[0]) + abs(p1[1] + p2[1])
        return f"What is the distance between ({p1[0]}, {p1[1]}) and ({p2[0]}, {p2[1]})?", str(distance), ("The points share one coordinate.", "Find the absolute difference of the coordinate that changes."), {"GEO.COORD.ADD_COORDINATES": str(wrong)}
    if family_code == "MATH.GEO.PYTHAGOREAN.HYPOTENUSE":
        a, b, c = rng.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)])
        return f"A right triangle has legs {a} and {b}. What is the hypotenuse?", str(c), ("Use a squared plus b squared equals c squared.", "Take the square root after adding the squares."), {"GEO.PYTH.NO_ROOT": str(a * a + b * b)}
    if family_code == "MATH.GEO.TRANSFORM.TRANSLATE_POINT":
        x, y = rng.randint(-6, 6), rng.randint(-6, 6)
        dx, dy = rng.choice([-4, -3, -2, 2, 3, 4]), rng.choice([-4, -3, -2, 2, 3, 4])
        answer = f"({x + dx},{y + dy})"
        return f"Translate the point ({x}, {y}) by the vector <{dx}, {dy}>. Give the image point.", answer, ("Add the horizontal component to x.", "Add the vertical component to y."), {"GEO.TRANSFORM.SWAP_VECTOR": f"({x + dy},{y + dx})"}
    raise ValueError(f"No geometry/measurement builder for family: {family_code}")
