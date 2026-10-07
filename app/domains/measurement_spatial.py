"""Canonical measurement, coordinate, transformation, and similarity families."""

from __future__ import annotations

import math
import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.MEAS.LENGTH.METRIC": _spec("MATH.MEAS.LENGTH.METRIC", "Convert metric length", "MATH.MEAS.UNIT_CONVERSION", "MEASUREMENT", 1, 3, "procedural_fluency", "place_value"),
    "MATH.MEAS.LENGTH.CUSTOMARY": _spec("MATH.MEAS.LENGTH.CUSTOMARY", "Convert feet and inches", "MATH.MEAS.UNIT_CONVERSION", "MEASUREMENT", 1, 3, "procedural_fluency", "measurement"),
    "MATH.MEAS.MASS.METRIC": _spec("MATH.MEAS.MASS.METRIC", "Convert metric mass", "MATH.MEAS.UNIT_CONVERSION", "MEASUREMENT", 1, 3, "procedural_fluency", "place_value"),
    "MATH.MEAS.WEIGHT.CUSTOMARY": _spec("MATH.MEAS.WEIGHT.CUSTOMARY", "Convert pounds and ounces", "MATH.MEAS.UNIT_CONVERSION", "MEASUREMENT", 1, 3, "procedural_fluency", "measurement"),
    "MATH.MEAS.CAPACITY.METRIC": _spec("MATH.MEAS.CAPACITY.METRIC", "Convert liters and milliliters", "MATH.MEAS.UNIT_CONVERSION", "MEASUREMENT", 1, 3, "procedural_fluency", "place_value"),
    "MATH.MEAS.TIME.CONVERT": _spec("MATH.MEAS.TIME.CONVERT", "Convert hours and minutes", "MATH.MEAS.TIME", "MEASUREMENT", 1, 3, "procedural_fluency", "measurement"),
    "MATH.MEAS.TIME.ELAPSED": _spec("MATH.MEAS.TIME.ELAPSED", "Find elapsed time", "MATH.MEAS.TIME", "WORD_PROBLEM", 1, 4, "modeling", "procedural_fluency"),
    "MATH.MEAS.RATE.CONVERT": _spec("MATH.MEAS.RATE.CONVERT", "Convert a compound rate", "MATH.MEAS.DIMENSIONAL_ANALYSIS", "RATE", 3, 4, "reasoning", "unit_analysis"),
    "MATH.GEO.ANGLE.VERTICAL": _spec("MATH.GEO.ANGLE.VERTICAL", "Vertical angle reasoning", "MATH.GEO.ANGLES", "ANGLE_REASONING", 2, 4, "reasoning", "properties"),
    "MATH.GEO.ANGLE.PARALLEL": _spec("MATH.GEO.ANGLE.PARALLEL", "Parallel-line angle reasoning", "MATH.GEO.ANGLES", "ANGLE_REASONING", 2, 4, "reasoning", "properties"),
    "MATH.GEO.TRIANGLE.CLASSIFY_SIDES": _spec("MATH.GEO.TRIANGLE.CLASSIFY_SIDES", "Classify triangles by side lengths", "MATH.GEO.TRIANGLES", "CLASSIFICATION", 1, 3, "conceptual_understanding", "properties"),
    "MATH.GEO.POLYGON.INTERIOR_SUM": _spec("MATH.GEO.POLYGON.INTERIOR_SUM", "Polygon interior-angle sum", "MATH.GEO.POLYGONS", "ANGLE_REASONING", 3, 4, "procedural_fluency", "reasoning"),
    "MATH.GEO.COORD.MIDPOINT": _spec("MATH.GEO.COORD.MIDPOINT", "Coordinate midpoint", "MATH.GEO.COORDINATE", "COORDINATE_GEOMETRY", 2, 4, "procedural_fluency", "representation"),
    "MATH.GEO.COORD.DISTANCE": _spec("MATH.GEO.COORD.DISTANCE", "Coordinate distance", "MATH.GEO.COORDINATE", "COORDINATE_GEOMETRY", 3, 4, "procedural_fluency", "reasoning"),
    "MATH.GEO.TRANSFORM.REFLECT_X": _spec("MATH.GEO.TRANSFORM.REFLECT_X", "Reflect a point across the x-axis", "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4, "representation", "spatial_reasoning"),
    "MATH.GEO.TRANSFORM.REFLECT_Y": _spec("MATH.GEO.TRANSFORM.REFLECT_Y", "Reflect a point across the y-axis", "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4, "representation", "spatial_reasoning"),
    "MATH.GEO.TRANSFORM.ROTATE_90": _spec("MATH.GEO.TRANSFORM.ROTATE_90", "Rotate a point 90 degrees counterclockwise", "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4, "representation", "spatial_reasoning"),
    "MATH.GEO.TRANSFORM.DILATE": _spec("MATH.GEO.TRANSFORM.DILATE", "Dilate a point about the origin", "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4, "representation", "spatial_reasoning"),
    "MATH.GEO.SIMILAR.SCALE": _spec("MATH.GEO.SIMILAR.SCALE", "Find a missing similar-figure length", "MATH.GEO.SIMILARITY", "SIMILARITY", 2, 4, "reasoning", "proportional_reasoning"),
    "MATH.GEO.SCALE.DRAWING": _spec("MATH.GEO.SCALE.DRAWING", "Use a drawing scale", "MATH.GEO.SCALE_DRAWING", "WORD_PROBLEM", 2, 4, "modeling", "proportional_reasoning"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.MEAS.LENGTH.METRIC":
        meters = rng.randint(2, 40)
        return (
            f"Convert {meters} meters to centimeters.",
            str(meters * 100),
            ("One meter equals 100 centimeters.", "Multiply the number of meters by 100."),
            {"MEAS.METRIC.DIVIDE": str(meters / 100)},
        )
    if family_code == "MATH.MEAS.LENGTH.CUSTOMARY":
        feet = rng.randint(2, 15)
        return (
            f"Convert {feet} feet to inches.",
            str(feet * 12),
            ("One foot equals 12 inches.", "Multiply the number of feet by 12."),
            {"MEAS.LENGTH.USE_TEN": str(feet * 10)},
        )
    if family_code == "MATH.MEAS.MASS.METRIC":
        kilograms = rng.randint(2, 25)
        return (
            f"Convert {kilograms} kilograms to grams.",
            str(kilograms * 1000),
            ("One kilogram equals 1000 grams.", "Multiply by 1000."),
            {"MEAS.METRIC.USE_100": str(kilograms * 100)},
        )
    if family_code == "MATH.MEAS.WEIGHT.CUSTOMARY":
        pounds = rng.randint(2, 20)
        return (
            f"Convert {pounds} pounds to ounces.",
            str(pounds * 16),
            ("One pound equals 16 ounces.", "Multiply the number of pounds by 16."),
            {"MEAS.WEIGHT.USE_12": str(pounds * 12)},
        )
    if family_code == "MATH.MEAS.CAPACITY.METRIC":
        liters = rng.randint(2, 18)
        return (
            f"Convert {liters} liters to milliliters.",
            str(liters * 1000),
            ("One liter equals 1000 milliliters.", "Multiply by 1000."),
            {"MEAS.CAPACITY.USE_100": str(liters * 100)},
        )
    if family_code == "MATH.MEAS.TIME.CONVERT":
        hours = rng.randint(2, 12)
        return (
            f"Convert {hours} hours to minutes.",
            str(hours * 60),
            ("One hour equals 60 minutes.", "Multiply the hours by 60."),
            {"MEAS.TIME.USE_100": str(hours * 100)},
        )
    if family_code == "MATH.MEAS.TIME.ELAPSED":
        start_hour = rng.randint(7, 15)
        start_minute = rng.choice([0, 10, 15, 20, 30, 40, 45, 50])
        elapsed = rng.choice([35, 45, 50, 70, 80, 95, 110])
        start_total = start_hour * 60 + start_minute
        end_total = start_total + elapsed
        end_hour, end_minute = divmod(end_total, 60)
        prompt = (
            f"An activity starts at {start_hour}:{start_minute:02d} and ends at "
            f"{end_hour}:{end_minute:02d}. How many minutes does it last?"
        )
        return (
            prompt,
            str(elapsed),
            ("Convert both clock times to minutes after midnight.", "Subtract the start time from the end time."),
            {"MEAS.TIME.SUBTRACT_CLOCK_DIGITS": str(abs((end_hour - start_hour) * 100 + end_minute - start_minute))},
        )
    if family_code == "MATH.MEAS.RATE.CONVERT":
        mph = rng.choice([30, 45, 60, 75])
        minutes = rng.choice([20, 30, 40])
        miles = mph * minutes // 60
        return (
            f"A vehicle travels at {mph} miles per hour for {minutes} minutes. How many miles does it travel?",
            str(miles),
            ("Convert the minutes to a fraction of an hour.", "Multiply rate by time in hours."),
            {"MEAS.RATE.USE_MINUTES_AS_HOURS": str(mph * minutes)},
        )
    if family_code == "MATH.GEO.ANGLE.VERTICAL":
        angle = rng.randint(25, 155)
        return (
            f"Two lines intersect. One angle measures {angle} degrees. What is the measure of its vertical angle?",
            str(angle),
            ("Vertical angles are opposite angles formed by intersecting lines.", "Vertical angles are congruent."),
            {"GEO.VERTICAL.SUPPLEMENT": str(180 - angle)},
        )
    if family_code == "MATH.GEO.ANGLE.PARALLEL":
        angle = rng.randint(30, 150)
        return (
            f"Two parallel lines are cut by a transversal. One corresponding angle is {angle} degrees. What is the corresponding angle on the other line?",
            str(angle),
            ("Corresponding angles formed by a transversal of parallel lines are congruent.", "Keep the same measure."),
            {"GEO.PARALLEL.SUPPLEMENT": str(180 - angle)},
        )
    if family_code == "MATH.GEO.TRIANGLE.CLASSIFY_SIDES":
        case = rng.choice(["equilateral", "isosceles", "scalene"])
        if case == "equilateral":
            a = rng.randint(3, 12)
            sides = (a, a, a)
        elif case == "isosceles":
            a = rng.randint(4, 12)
            b = rng.randint(3, 2 * a - 1)
            while b == a:
                b = rng.randint(3, 2 * a - 1)
            sides = (a, a, b)
        else:
            sides = rng.choice([(4, 5, 6), (5, 6, 8), (6, 7, 9), (7, 8, 10)])
        return (
            f"Classify a triangle with side lengths {sides[0]}, {sides[1]}, and {sides[2]} as equilateral, isosceles, or scalene.",
            case,
            ("Compare the three side lengths.", "Three equal sides are equilateral; exactly two equal sides are isosceles."),
            {"GEO.TRIANGLE.CLASSIFY_BY_ANGLE": "right" if case != "equilateral" else "acute"},
        )
    if family_code == "MATH.GEO.POLYGON.INTERIOR_SUM":
        sides = rng.randint(4, 10)
        total = (sides - 2) * 180
        return (
            f"What is the sum of the interior angles of a {sides}-sided polygon?",
            str(total),
            ("A polygon can be partitioned into n-2 triangles from one vertex.", "Multiply n-2 by 180 degrees."),
            {"GEO.POLYGON.USE_N_TIMES_180": str(sides * 180)},
        )
    if family_code == "MATH.GEO.COORD.MIDPOINT":
        x1, y1 = rng.randint(-8, 8), rng.randint(-8, 8)
        dx, dy = 2 * rng.randint(-5, 5), 2 * rng.randint(-5, 5)
        if dx == 0 and dy == 0:
            dx = 2
        x2, y2 = x1 + dx, y1 + dy
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        return (
            f"Find the midpoint of ({x1},{y1}) and ({x2},{y2}). Give x,y.",
            f"{mx},{my}",
            ("Average the x-coordinates.", "Average the y-coordinates."),
            {"GEO.MIDPOINT.ADD_ONLY": f"{x1+x2},{y1+y2}"},
        )
    if family_code == "MATH.GEO.COORD.DISTANCE":
        triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)]
        dx, dy, distance = rng.choice(triples)
        x1, y1 = rng.randint(-6, 4), rng.randint(-6, 4)
        sx, sy = rng.choice([-1, 1]), rng.choice([-1, 1])
        x2, y2 = x1 + sx * dx, y1 + sy * dy
        return (
            f"Find the distance between ({x1},{y1}) and ({x2},{y2}).",
            str(distance),
            ("Find the horizontal and vertical changes.", "Use the Pythagorean theorem on those changes."),
            {"GEO.DISTANCE.MANHATTAN": str(dx + dy)},
        )
    if family_code in {"MATH.GEO.TRANSFORM.REFLECT_X", "MATH.GEO.TRANSFORM.REFLECT_Y"}:
        x, y = rng.randint(-8, 8), rng.randint(-8, 8)
        if x == 0:
            x = 3
        if y == 0:
            y = -4
        if family_code.endswith("REFLECT_X"):
            answer = f"{x},{-y}"
            wrong = f"{-x},{y}"
            axis = "x-axis"
        else:
            answer = f"{-x},{y}"
            wrong = f"{x},{-y}"
            axis = "y-axis"
        return (
            f"Reflect the point ({x},{y}) across the {axis}. Give x,y.",
            answer,
            ("A reflection keeps the coordinate parallel to the mirror axis.", "Negate the coordinate perpendicular to the mirror axis."),
            {"GEO.REFLECTION.WRONG_AXIS": wrong},
        )
    if family_code == "MATH.GEO.TRANSFORM.ROTATE_90":
        x, y = rng.randint(-8, 8), rng.randint(-8, 8)
        if x == 0 and y == 0:
            x = 2
        return (
            f"Rotate ({x},{y}) 90 degrees counterclockwise about the origin. Give x,y.",
            f"{-y},{x}",
            ("A 90-degree counterclockwise rotation swaps the coordinates.", "After swapping, negate the new x-coordinate."),
            {"GEO.ROTATE.SWAP_ONLY": f"{y},{x}"},
        )
    if family_code == "MATH.GEO.TRANSFORM.DILATE":
        x, y = rng.randint(-6, 6), rng.randint(-6, 6)
        scale = rng.choice([2, 3, 4])
        return (
            f"Dilate ({x},{y}) about the origin by scale factor {scale}. Give x,y.",
            f"{scale*x},{scale*y}",
            ("A dilation from the origin multiplies each coordinate by the scale factor.", "Apply the same scale factor to x and y."),
            {"GEO.DILATE.ADD_SCALE": f"{x+scale},{y+scale}"},
        )
    if family_code == "MATH.GEO.SIMILAR.SCALE":
        original = rng.randint(3, 12)
        scale = rng.choice([2, 3, 4])
        image = original * scale
        other = rng.randint(2, 10)
        return (
            f"Two figures are similar. A side of length {original} corresponds to {image}. If another original side is {other}, what is its corresponding length?",
            str(other * scale),
            ("Find the multiplicative scale factor from the known pair.", "Apply that same factor to every corresponding length."),
            {"GEO.SIMILAR.ADD_DIFFERENCE": str(other + (image - original))},
        )
    if family_code == "MATH.GEO.SCALE.DRAWING":
        scale = rng.choice([2, 3, 4, 5])
        drawing = rng.randint(3, 12)
        return (
            f"On a scale drawing, 1 centimeter represents {scale} meters. A segment is {drawing} centimeters long. What actual length does it represent in meters?",
            str(scale * drawing),
            ("Each drawing centimeter represents the stated number of real meters.", "Multiply drawing length by the scale."),
            {"GEO.SCALE.DIVIDE": str(drawing / scale)},
        )
    raise ValueError(f"No measurement/spatial builder for family: {family_code}")
