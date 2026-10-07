"""Canonical geometry reasoning and solid-measurement depth."""

from __future__ import annotations

import math
import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dimensions: str) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dimensions))


FAMILIES = {
    "MATH.GEO.TRIANGLE.INEQUALITY": _spec("MATH.GEO.TRIANGLE.INEQUALITY", "Apply the triangle inequality", "MATH.GEO.TRIANGLE.REASONING", "GEOMETRY_REASONING", 2, 4, "reasoning", "conceptual_understanding"),
    "MATH.GEO.PYTHAGOREAN.LEG": _spec("MATH.GEO.PYTHAGOREAN.LEG", "Find a missing right-triangle leg", "MATH.GEO.PYTHAGOREAN", "GEOMETRY", 2, 4, "procedural_fluency", "reasoning"),
    "MATH.GEO.PYTHAGOREAN.CONVERSE": _spec("MATH.GEO.PYTHAGOREAN.CONVERSE", "Use the converse of the Pythagorean theorem", "MATH.GEO.PYTHAGOREAN", "GEOMETRY_REASONING", 2, 4, "reasoning", "classification"),
    "MATH.GEO.CONGRUENCE.RIGID": _spec("MATH.GEO.CONGRUENCE.RIGID", "Reason about rigid transformations and congruence", "MATH.GEO.CONGRUENCE", "TRANSFORMATION_REASONING", 2, 4, "reasoning", "conceptual_understanding"),
    "MATH.GEO.SIMILAR.TRANSFORM": _spec("MATH.GEO.SIMILAR.TRANSFORM", "Reason about transformations and similarity", "MATH.GEO.SIMILARITY", "TRANSFORMATION_REASONING", 2, 4, "reasoning", "conceptual_understanding"),
    "MATH.GEO.TRANSFORM.COMPOSE": _spec("MATH.GEO.TRANSFORM.COMPOSE", "Compose coordinate translations", "MATH.GEO.TRANSFORMATIONS", "COORDINATE_GEOMETRY", 2, 4, "procedural_fluency", "representation"),
    "MATH.GEO.SYMMETRY.REFLECTION": _spec("MATH.GEO.SYMMETRY.REFLECTION", "Identify reflection symmetry", "MATH.GEO.TRANSFORMATIONS", "GEOMETRY_REASONING", 1, 3, "reasoning", "representation"),
    "MATH.GEO.SIMILAR.AREA_SCALE": _spec("MATH.GEO.SIMILAR.AREA_SCALE", "Relate linear and area scale factors", "MATH.GEO.SIMILARITY", "GEOMETRY_REASONING", 2, 4, "reasoning", "multiplicative_reasoning"),
    "MATH.GEO.NET.CUBE.SURFACE": _spec("MATH.GEO.NET.CUBE.SURFACE", "Use a cube net to determine surface area", "MATH.GEO.SURFACE_AREA", "GEOMETRY", 1, 3, "representation", "procedural_fluency"),
    "MATH.GEO.VOLUME.CYLINDER": _spec("MATH.GEO.VOLUME.CYLINDER", "Find cylinder volume", "MATH.GEO.SOLID_VOLUME", "GEOMETRY", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.VOLUME.CONE": _spec("MATH.GEO.VOLUME.CONE", "Find cone volume", "MATH.GEO.SOLID_VOLUME", "GEOMETRY", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.VOLUME.SPHERE": _spec("MATH.GEO.VOLUME.SPHERE", "Find sphere volume", "MATH.GEO.SOLID_VOLUME", "GEOMETRY", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.SURFACE.CYLINDER": _spec("MATH.GEO.SURFACE.CYLINDER", "Find total cylinder surface area", "MATH.GEO.SURFACE_AREA", "GEOMETRY", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.VOLUME.COMPOSITE_PRISMS": _spec("MATH.GEO.VOLUME.COMPOSITE_PRISMS", "Find volume of joined rectangular prisms", "MATH.GEO.SOLID_VOLUME", "GEOMETRY", 2, 4, "modeling", "decomposition"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.GEO.TRIANGLE.INEQUALITY":
        a, b = rng.randint(3, 12), rng.randint(3, 12)
        valid = rng.choice([True, False])
        c = rng.randint(abs(a - b) + 1, a + b - 1) if valid else a + b + rng.randint(0, 3)
        answer = "yes" if valid else "no"
        return (f"Can side lengths {a}, {b}, and {c} form a triangle? Answer yes or no.", answer, ("For a triangle, the sum of any two side lengths must exceed the third.", "It is enough to check the two shorter sides against the longest side."), {"GEO.TRIANGLE.IGNORE_INEQUALITY": "no" if valid else "yes"})
    if family_code == "MATH.GEO.PYTHAGOREAN.LEG":
        a, b, c = rng.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)])
        missing, known = rng.choice([(a, b), (b, a)])
        return (f"A right triangle has hypotenuse {c} and one leg {known}. Find the other leg.", str(missing), ("Use a² + b² = c² with c as the hypotenuse.", f"The missing leg squared is {c}² - {known}²."), {"GEO.PYTHAGOREAN.ADD_FOR_LEG": str(math.isqrt(c * c + known * known))})
    if family_code == "MATH.GEO.PYTHAGOREAN.CONVERSE":
        right = rng.choice([True, False])
        sides = rng.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17)]) if right else rng.choice([(4, 5, 7), (5, 6, 8), (6, 8, 11)])
        return (f"Do side lengths {sides[0]}, {sides[1]}, and {sides[2]} form a right triangle? Answer yes or no.", "yes" if right else "no", ("Square the two shorter sides and add them.", "Compare that sum with the square of the longest side."), {"GEO.PYTHAGOREAN.ASSUME_RIGHT": "no" if right else "yes"})
    if family_code == "MATH.GEO.CONGRUENCE.RIGID":
        transformation = rng.choice(["translation", "rotation", "reflection"])
        return (f"Figure B is obtained from Figure A by a {transformation}. Are the figures necessarily congruent? Answer yes or no.", "yes", ("Translations, rotations, and reflections are rigid transformations.", "Rigid transformations preserve distances and angle measures."), {"GEO.CONGRUENCE.CONFUSE_SIMILARITY": "no"})
    if family_code == "MATH.GEO.SIMILAR.TRANSFORM":
        factor = rng.choice([2, 3, 4])
        return (f"Figure B is obtained by dilating Figure A by scale factor {factor}, then translating it. Are A and B necessarily similar? Answer yes or no.", "yes", ("A dilation preserves angle measures and scales all lengths proportionally.", "A following rigid transformation does not change shape."), {"GEO.SIMILAR.REQUIRE_CONGRUENCE": "no"})
    if family_code == "MATH.GEO.TRANSFORM.COMPOSE":
        x, y = rng.randint(-8, 8), rng.randint(-8, 8); dx1, dy1 = rng.randint(-5, 5), rng.randint(-5, 5); dx2, dy2 = rng.randint(-5, 5), rng.randint(-5, 5)
        return (f"Point ({x},{y}) is translated by ({dx1},{dy1}) and then by ({dx2},{dy2}). Give the final point as x,y.", f"{x + dx1 + dx2},{y + dy1 + dy2}", ("Apply both translations to the coordinates.", "Translation vectors combine by adding their x-components and y-components."), {"GEO.TRANSFORM.ONLY_FIRST": f"{x + dx1},{y + dy1}"})
    if family_code == "MATH.GEO.SYMMETRY.REFLECTION":
        shape = rng.choice(["square", "rectangle", "equilateral triangle"]); axes = {"square": 4, "rectangle": 2, "equilateral triangle": 3}
        return (f"How many lines of reflection symmetry does a {shape} have?", str(axes[shape]), ("A line of symmetry divides a figure into mirror-image halves.", "Count distinct lines that reflect the figure onto itself."), {"GEO.SYMMETRY.COUNT_ROTATIONS": str(axes[shape] + 1)})
    if family_code == "MATH.GEO.SIMILAR.AREA_SCALE":
        factor, area = rng.randint(2, 5), rng.randint(3, 20)
        return (f"Two similar figures have linear scale factor {factor}. If the smaller figure has area {area}, what is the larger area?", str(area * factor * factor), ("Area is two-dimensional.", "A linear scale factor k produces an area scale factor k²."), {"GEO.SIMILAR.USE_LINEAR_FOR_AREA": str(area * factor)})
    if family_code == "MATH.GEO.NET.CUBE.SURFACE":
        side = rng.randint(2, 12)
        return (f"A cube net has six square faces, each with side length {side}. What is the cube's surface area?", str(6 * side * side), ("A cube has six congruent square faces.", "Find one face area, then multiply by six."), {"GEO.NET.USE_EDGE_TOTAL": str(6 * side)})
    if family_code == "MATH.GEO.VOLUME.CYLINDER":
        radius, height = rng.randint(2, 8), rng.randint(3, 12); coefficient = radius * radius * height
        return (f"A cylinder has radius {radius} and height {height}. Give its volume in terms of pi.", f"{coefficient}pi", ("Cylinder volume is base area times height.", "Use V = πr²h."), {"GEO.CYLINDER.OMIT_SQUARE": f"{radius * height}pi"})
    if family_code == "MATH.GEO.VOLUME.CONE":
        radius, height = rng.randint(2, 7), 3 * rng.randint(2, 8); coefficient = radius * radius * height // 3
        return (f"A cone has radius {radius} and height {height}. Give its volume in terms of pi.", f"{coefficient}pi", ("A cone with the same base and height has one-third the cylinder's volume.", "Use V = (1/3)πr²h."), {"GEO.CONE.USE_CYLINDER": f"{radius * radius * height}pi"})
    if family_code == "MATH.GEO.VOLUME.SPHERE":
        radius = 3 * rng.randint(1, 4); coefficient = 4 * radius**3 // 3
        return (f"A sphere has radius {radius}. Give its volume in terms of pi.", f"{coefficient}pi", ("Sphere volume depends on the cube of the radius.", "Use V = (4/3)πr³."), {"GEO.SPHERE.USE_SQUARE": f"{4 * radius * radius // 3}pi"})
    if family_code == "MATH.GEO.SURFACE.CYLINDER":
        radius, height = rng.randint(2, 8), rng.randint(3, 12); coefficient = 2 * radius * radius + 2 * radius * height
        return (f"A closed cylinder has radius {radius} and height {height}. Give its total surface area in terms of pi.", f"{coefficient}pi", ("Include two circular bases and the curved lateral surface.", "Use SA = 2πr² + 2πrh."), {"GEO.CYLINDER.SURFACE.ONE_BASE": f"{radius * radius + 2 * radius * height}pi"})
    if family_code == "MATH.GEO.VOLUME.COMPOSITE_PRISMS":
        a = (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6)); b = (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6)); v1, v2 = math.prod(a), math.prod(b)
        return (f"A solid is made by joining non-overlapping rectangular prisms with dimensions {a[0]}×{a[1]}×{a[2]} and {b[0]}×{b[1]}×{b[2]}. What is the total volume?", str(v1 + v2), ("Decompose the solid into the two non-overlapping prisms.", "Find each prism's volume and add the volumes."), {"GEO.COMPOSITE.MULTIPLY_VOLUMES": str(v1 * v2)})
    raise ValueError(f"No geometry-reasoning builder for family: {family_code}")
