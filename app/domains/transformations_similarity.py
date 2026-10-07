"""Canonical transformation, congruence, and similarity depth families."""

from __future__ import annotations

import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


def _point(x: int | Fraction, y: int | Fraction) -> str:
    return f"{x},{y}"


FAMILIES = {
    "MATH.GEO.TRANSFORM.REFLECT_Y_EQ_X": _spec(
        "MATH.GEO.TRANSFORM.REFLECT_Y_EQ_X", "Reflect across y equals x",
        "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4,
        "representation", "spatial_reasoning",
    ),
    "MATH.GEO.TRANSFORM.ROTATE_90_CW": _spec(
        "MATH.GEO.TRANSFORM.ROTATE_90_CW", "Rotate 90 degrees clockwise",
        "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4,
        "representation", "spatial_reasoning",
    ),
    "MATH.GEO.TRANSFORM.ROTATE_180": _spec(
        "MATH.GEO.TRANSFORM.ROTATE_180", "Rotate 180 degrees",
        "MATH.GEO.TRANSFORMATIONS", "TRANSFORMATION", 2, 4,
        "representation", "spatial_reasoning",
    ),
    "MATH.GEO.RIGID.DISTANCE": _spec(
        "MATH.GEO.RIGID.DISTANCE", "Reason about distance under rigid motions",
        "MATH.GEO.CONGRUENCE", "GEOMETRIC_REASONING", 2, 4,
        "conceptual_understanding", "reasoning",
    ),
    "MATH.GEO.SIMILAR.REVERSE_SCALE": _spec(
        "MATH.GEO.SIMILAR.REVERSE_SCALE", "Recover an original similar-figure length",
        "MATH.GEO.SIMILARITY", "SIMILARITY", 2, 4,
        "proportional_reasoning", "inverse_operations",
    ),
    "MATH.GEO.SIMILAR.PERIMETER_SCALE": _spec(
        "MATH.GEO.SIMILAR.PERIMETER_SCALE", "Scale perimeter under dilation",
        "MATH.GEO.SIMILARITY", "SIMILARITY", 2, 4,
        "proportional_reasoning", "measurement",
    ),
    "MATH.GEO.SIMILAR.VOLUME_SCALE": _spec(
        "MATH.GEO.SIMILAR.VOLUME_SCALE", "Scale volume under dilation",
        "MATH.GEO.SIMILARITY", "SIMILARITY", 3, 4,
        "proportional_reasoning", "reasoning", "measurement",
    ),
    "MATH.GEO.SIMILAR.ANGLE_INVARIANT": _spec(
        "MATH.GEO.SIMILAR.ANGLE_INVARIANT", "Reason about angles under dilation",
        "MATH.GEO.SIMILARITY", "GEOMETRIC_REASONING", 2, 4,
        "conceptual_understanding", "properties",
    ),
    "MATH.GEO.SIMILAR.AA": _spec(
        "MATH.GEO.SIMILAR.AA", "Establish triangle similarity by AA",
        "MATH.GEO.SIMILARITY", "GEOMETRIC_REASONING", 3, 4,
        "conceptual_understanding", "reasoning",
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.GEO.TRANSFORM.REFLECT_Y_EQ_X":
        x, y = rng.randint(-8, 8), rng.randint(-8, 8)
        while x == y:
            y = rng.randint(-8, 8)
        return (
            f"Reflect ({x},{y}) across the line y=x. Give x,y.",
            _point(y, x),
            ("Reflection across y=x exchanges the coordinate roles.", "Swap x and y."),
            {"GEO.REFLECT.LEAVE_UNCHANGED": _point(x, y)},
            {
                "type": "coordinate_point", "x": x, "y": y, "min": -10, "max": 10,
                "aria_label": f"Coordinate plane with preimage point at ({x}, {y}); reflect it across y equals x.",
            },
        )
    if family_code == "MATH.GEO.TRANSFORM.ROTATE_90_CW":
        x, y = rng.randint(-8, 8), rng.randint(-8, 8)
        if x == 0 and y == 0:
            x = 3
        return (
            f"Rotate ({x},{y}) 90 degrees clockwise about the origin. Give x,y.",
            _point(y, -x),
            ("A clockwise quarter-turn swaps the coordinate positions.", "After swapping, negate the new y-coordinate."),
            {"GEO.ROTATE.CCW_CONFUSION": _point(-y, x)},
            {
                "type": "coordinate_point", "x": x, "y": y, "min": -10, "max": 10,
                "aria_label": f"Coordinate plane with preimage point at ({x}, {y}) for a 90 degree clockwise rotation.",
            },
        )
    if family_code == "MATH.GEO.TRANSFORM.ROTATE_180":
        x, y = rng.randint(-8, 8), rng.randint(-8, 8)
        if x == 0 and y == 0:
            y = 4
        return (
            f"Rotate ({x},{y}) 180 degrees about the origin. Give x,y.",
            _point(-x, -y),
            ("A half-turn sends each coordinate to its opposite.", "Negate both x and y."),
            {"GEO.ROTATE.NEGATE_ONE": _point(-x, y)},
            {
                "type": "coordinate_point", "x": x, "y": y, "min": -10, "max": 10,
                "aria_label": f"Coordinate plane with preimage point at ({x}, {y}) for a 180 degree rotation.",
            },
        )
    if family_code == "MATH.GEO.RIGID.DISTANCE":
        length = rng.randint(3, 18)
        motion = rng.choice(["translation", "reflection", "rotation"])
        return (
            f"A segment has length {length}. After a {motion}, what is the image segment's length?",
            str(length),
            ("Translations, reflections, and rotations are rigid motions.", "Rigid motions preserve distance."),
            {"GEO.RIGID.CHANGE_LENGTH": str(length + rng.choice([1, 2, 3]))},
        )
    if family_code == "MATH.GEO.SIMILAR.REVERSE_SCALE":
        original = rng.randint(3, 12)
        scale = rng.choice([2, 3, 4])
        image = original * scale
        return (
            f"A dilation with scale factor {scale} produces a side of length {image}. What was the original side length?",
            str(original),
            ("The image length equals scale factor times original length.", "Undo the dilation by dividing by the scale factor."),
            {"GEO.SIMILAR.MULTIPLY_REVERSE": str(image * scale)},
        )
    if family_code == "MATH.GEO.SIMILAR.PERIMETER_SCALE":
        perimeter = rng.randint(12, 50)
        scale = rng.choice([2, 3, 4])
        return (
            f"A polygon has perimeter {perimeter}. It is dilated by scale factor {scale}. What is the image perimeter?",
            str(perimeter * scale),
            ("Every side length is multiplied by the scale factor.", "Perimeter is a sum of side lengths, so it scales by the same factor."),
            {"GEO.SIMILAR.PERIMETER.SQUARE_SCALE": str(perimeter * scale * scale)},
        )
    if family_code == "MATH.GEO.SIMILAR.VOLUME_SCALE":
        volume = rng.randint(4, 25)
        scale = rng.choice([2, 3])
        return (
            f"A solid has volume {volume} cubic units. A similar solid uses scale factor {scale}. What is the image volume?",
            str(volume * scale**3),
            ("Three independent linear dimensions scale in a solid.", "Volume scales by the cube of the linear scale factor."),
            {"GEO.SIMILAR.VOLUME.SQUARE_SCALE": str(volume * scale * scale)},
        )
    if family_code == "MATH.GEO.SIMILAR.ANGLE_INVARIANT":
        angle = rng.randint(25, 145)
        scale = rng.choice([2, 3, 4])
        return (
            f"An angle measures {angle} degrees. Its figure is dilated by scale factor {scale}. What is the image angle measure?",
            str(angle),
            ("A dilation changes lengths but preserves angle measures.", "Keep the angle measure unchanged."),
            {"GEO.SIMILAR.ANGLE.SCALE": str(angle * scale)},
        )
    if family_code == "MATH.GEO.SIMILAR.AA":
        a = rng.randint(25, 70)
        b = rng.randint(25, 70)
        while a + b >= 150:
            b = rng.randint(25, 65)
        return (
            (
                f"Triangle P has angles {a} and {b} degrees. "
                f"Triangle Q has angles {a} and {b} degrees. "
                "Which conclusion is guaranteed? (A) similar by AA "
                "(B) congruent (C) not similar (D) equal area"
            ),
            "A",
            ("Two matching angle pairs determine triangle similarity.", "AA establishes similarity, not necessarily congruence."),
            {"GEO.SIMILAR.AA.CONGRUENT": "B"},
        )
    raise ValueError(f"No transformation/similarity builder for family: {family_code}")
