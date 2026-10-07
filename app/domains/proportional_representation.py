"""Canonical proportional-relationship representation depth."""

from __future__ import annotations

import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(code: str, name: str, skill: str, problem_type: str, *dimensions: str) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, 2, 4, ALL_MODES, frozenset(dimensions))


FAMILIES = {
    "MATH.PROP.CONSTANT.TABLE": _spec("MATH.PROP.CONSTANT.TABLE", "Find constant of proportionality from a table", "MATH.RP.PROPORTIONAL.REPRESENT", "RATIO_TABLE", "representation", "reasoning"),
    "MATH.PROP.EQUATION.FROM_RATE": _spec("MATH.PROP.EQUATION.FROM_RATE", "Write y = kx from a unit rate", "MATH.RP.PROPORTIONAL.REPRESENT", "MODEL_EQUATION", "modeling", "representation"),
    "MATH.PROP.GRAPH.ORIGIN": _spec("MATH.PROP.GRAPH.ORIGIN", "Reason about the origin in proportional graphs", "MATH.RP.PROPORTIONAL.REPRESENT", "GRAPH_REASONING", "reasoning", "conceptual_understanding"),
    "MATH.PROP.GRAPH.UNIT_POINT": _spec("MATH.PROP.GRAPH.UNIT_POINT", "Interpret the point (1,k) on a proportional graph", "MATH.RP.PROPORTIONAL.REPRESENT", "GRAPH_REASONING", "representation", "reasoning"),
    "MATH.PROP.COMPARE.TABLE_EQUATION": _spec("MATH.PROP.COMPARE.TABLE_EQUATION", "Compare proportional relationships across representations", "MATH.RP.PROPORTIONAL.COMPARE", "COMPARISON", "comparison", "representation"),
    "MATH.PROP.ERROR.INTERCEPT": _spec("MATH.PROP.ERROR.INTERCEPT", "Diagnose nonzero-intercept proportionality error", "MATH.RP.PROPORTIONAL.REPRESENT", "ERROR_ANALYSIS", "error_analysis", "misconception_probe"),
    "MATH.RATE.COMPLEX.UNIT": _spec("MATH.RATE.COMPLEX.UNIT", "Find a unit rate involving fractions", "MATH.RP.RATE.UNIT", "RATE", "procedural_fluency", "reasoning"),
    "MATH.PROP.POINT.INTERPRET": _spec("MATH.PROP.POINT.INTERPRET", "Interpret a point in a proportional context", "MATH.RP.PROPORTIONAL.REPRESENT", "GRAPH_REASONING", "modeling", "transfer"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.PROP.CONSTANT.TABLE":
        k = rng.randint(2, 12); xs = rng.sample(range(1, 9), 3); pairs = [(x, k * x) for x in xs]
        return (f"A proportional table contains the points {pairs}. What is the constant of proportionality k = y/x?", str(k), ("For a proportional relationship, y/x is constant.", "Divide any y-value by its matching x-value."), {"PROP.CONSTANT.USE_DIFFERENCE": str(pairs[0][1] - pairs[0][0])})
    if family_code == "MATH.PROP.EQUATION.FROM_RATE":
        k = rng.randint(2, 15); context = rng.choice(["miles traveled per hour", "dollars earned per hour", "items made per minute"])
        return (f"A proportional relationship has unit rate {k} {context}. If x is the number of input units and y is the output, write the equation.", f"y={k}x", ("A proportional relationship has the form y = kx.", f"Here the constant k is {k}."), {"PROP.EQUATION.ADD_RATE": f"y=x+{k}"})
    if family_code == "MATH.PROP.GRAPH.ORIGIN":
        return ("A relationship is proportional. Must its graph pass through (0,0)? Answer yes or no.", "yes", ("A proportional relationship has equation y = kx.", "When x = 0, y = 0 for every value of k."), {"PROP.GRAPH.NONZERO_INTERCEPT": "no"})
    if family_code == "MATH.PROP.GRAPH.UNIT_POINT":
        k = rng.randint(2, 15)
        return (f"A proportional graph contains the point (1,{k}). What does the y-coordinate represent?", f"unit rate {k}", ("The point with x = 1 describes one input unit.", "Its y-coordinate is the output per one input unit: the unit rate."), {"PROP.GRAPH.UNIT_POINT.AS_TOTAL": f"total {k}"})
    if family_code == "MATH.PROP.COMPARE.TABLE_EQUATION":
        k_table = rng.randint(2, 10); k_equation = k_table + rng.choice([-1, 1]) * rng.randint(1, 4)
        while k_equation <= 0: k_equation = k_table + rng.randint(1, 4)
        pairs = [(2, 2 * k_table), (4, 4 * k_table), (6, 6 * k_table)]; answer = "table" if k_table > k_equation else "equation"
        return (f"Relationship A is shown by table points {pairs}. Relationship B is y={k_equation}x. Which has the greater unit rate: table or equation?", answer, ("Find k = y/x for the table.", "In y = kx, the coefficient of x is the unit rate."), {"PROP.COMPARE.USE_LARGER_OUTPUT": "equation" if answer == "table" else "table"})
    if family_code == "MATH.PROP.ERROR.INTERCEPT":
        k, b = rng.randint(2, 9), rng.randint(1, 8)
        return (f"A student says y={k}x+{b} is proportional because y changes by {k} whenever x increases by 1. Which response is correct? (A) It is not proportional because the graph does not pass through the origin. (B) It is proportional because the rate of change is constant. (C) Every linear relationship is proportional. (D) The intercept does not matter.", "A", ("Constant rate of change makes a relationship linear, but not necessarily proportional.", "Proportional relationships require y = kx, so the y-intercept must be zero."), {"PROP.ERROR.CONSTANT_SLOPE_ONLY": "B"})
    if family_code == "MATH.RATE.COMPLEX.UNIT":
        denominator = rng.choice([2, 3, 4]); whole_units = rng.randint(2, 8); quantity = Fraction(whole_units, denominator); time = Fraction(1, denominator); rate = quantity / time
        return (f"A machine processes {quantity} units in {time} hour. How many units does it process per hour?", str(rate.numerator) if rate.denominator == 1 else f"{rate.numerator}/{rate.denominator}", ("A unit rate divides the output quantity by the input quantity.", f"Compute {quantity} ÷ {time}."), {"RATE.COMPLEX.MULTIPLY": str(quantity * time)})
    if family_code == "MATH.PROP.POINT.INTERPRET":
        x, k = rng.randint(2, 9), rng.randint(2, 12); y = x * k
        return (f"A graph relates hours x to miles y for a constant-speed trip and contains ({x},{y}). What does this point mean?", f"{y} miles in {x} hours", ("Coordinates are ordered as (input, output).", "Here x measures hours and y measures miles."), {"PROP.POINT.REVERSE_AXES": f"{x} miles in {y} hours"})
    raise ValueError(f"No proportional-representation builder for family: {family_code}")
