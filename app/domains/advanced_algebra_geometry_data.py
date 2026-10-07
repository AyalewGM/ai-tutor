"""Canonical inequalities, richer functions, circle geometry, and data representations."""

from __future__ import annotations

import random
import statistics

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.INEQ.ONE.ADD": _spec("MATH.INEQ.ONE.ADD", "One-step additive inequalities", "MATH.EE.INEQUALITY.ONE", "SOLVE_INEQUALITY", 1, 3, "procedural_fluency", "inverse_operations"),
    "MATH.INEQ.ONE.MULT": _spec("MATH.INEQ.ONE.MULT", "One-step multiplicative inequalities", "MATH.EE.INEQUALITY.ONE", "SOLVE_INEQUALITY", 2, 4, "procedural_fluency", "inverse_operations"),
    "MATH.INEQ.NEGATIVE.FLIP": _spec("MATH.INEQ.NEGATIVE.FLIP", "Inequality reversal with a negative factor", "MATH.EE.INEQUALITY.MULTISTEP", "SOLVE_INEQUALITY", 2, 4, "reasoning", "misconception_probe"),
    "MATH.INEQ.TEST.SOLUTION": _spec("MATH.INEQ.TEST.SOLUTION", "Test an inequality solution", "MATH.EE.INEQUALITY.ONE", "REASONING", 1, 3, "reasoning", "substitution"),
    "MATH.INEQ.WORD.MINIMUM": _spec("MATH.INEQ.WORD.MINIMUM", "Model a minimum constraint", "MATH.EE.INEQUALITY.MULTISTEP", "WORD_PROBLEM", 2, 4, "modeling", "representation"),
    "MATH.INEQ.ERROR.NO_FLIP": _spec("MATH.INEQ.ERROR.NO_FLIP", "Diagnose missing inequality reversal", "MATH.EE.INEQUALITY.MULTISTEP", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.FUNC.SEQUENCE.LINEAR": _spec("MATH.FUNC.SEQUENCE.LINEAR", "Linear sequence rule", "MATH.F.LINEAR.SEQUENCE", "FUNCTION_REASONING", 1, 4, "representation", "pattern_reasoning"),
    "MATH.FUNC.COMPARE.RATE": _spec("MATH.FUNC.COMPARE.RATE", "Compare rates across linear representations", "MATH.F.LINEAR.COMPARE", "FUNCTION_REASONING", 2, 4, "reasoning", "representation"),
    "MATH.FUNC.DOMAIN.RANGE": _spec("MATH.FUNC.DOMAIN.RANGE", "Determine range from finite function values", "MATH.F.FUNCTIONS", "FUNCTION_REASONING", 2, 4, "conceptual_understanding", "representation"),
    "MATH.FUNC.NONLINEAR.CLASSIFY": _spec("MATH.FUNC.NONLINEAR.CLASSIFY", "Classify linear versus nonlinear patterns", "MATH.F.FUNCTIONS", "CLASSIFICATION", 2, 4, "conceptual_understanding", "pattern_reasoning"),
    "MATH.FUNC.ERROR.CONSTANT_RATE": _spec("MATH.FUNC.ERROR.CONSTANT_RATE", "Diagnose false constant-rate reasoning", "MATH.F.FUNCTIONS", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.GEO.CIRCLE.RADIUS_DIAMETER": _spec("MATH.GEO.CIRCLE.RADIUS_DIAMETER", "Radius and diameter relationship", "MATH.GEO.CIRCLES", "GEOMETRY", 1, 3, "conceptual_understanding", "measurement"),
    "MATH.GEO.CIRCLE.CIRCUMFERENCE": _spec("MATH.GEO.CIRCLE.CIRCUMFERENCE", "Circle circumference", "MATH.GEO.CIRCLES", "MEASUREMENT", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.CIRCLE.AREA": _spec("MATH.GEO.CIRCLE.AREA", "Circle area", "MATH.GEO.CIRCLES", "MEASUREMENT", 2, 4, "procedural_fluency", "measurement"),
    "MATH.GEO.CIRCLE.ERROR.RADIUS": _spec("MATH.GEO.CIRCLE.ERROR.RADIUS", "Diagnose radius/diameter confusion", "MATH.GEO.CIRCLES", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.DATA.DOT.FREQUENCY": _spec("MATH.DATA.DOT.FREQUENCY", "Read a dot-plot frequency", "MATH.DATA.REPRESENTATIONS", "DATA_REPRESENTATION", 1, 3, "representation", "data_reasoning"),
    "MATH.DATA.HISTOGRAM.BIN": _spec("MATH.DATA.HISTOGRAM.BIN", "Read a histogram interval", "MATH.DATA.REPRESENTATIONS", "DATA_REPRESENTATION", 2, 4, "representation", "data_reasoning"),
    "MATH.DATA.FIVE_NUMBER": _spec("MATH.DATA.FIVE_NUMBER", "Five-number summary", "MATH.DATA.SPREAD", "DATA_ANALYSIS", 2, 4, "procedural_fluency", "data_reasoning"),
    "MATH.DATA.IQR": _spec("MATH.DATA.IQR", "Interquartile range", "MATH.DATA.SPREAD", "DATA_ANALYSIS", 2, 4, "procedural_fluency", "data_reasoning"),
    "MATH.DATA.MAD": _spec("MATH.DATA.MAD", "Mean absolute deviation", "MATH.DATA.SPREAD", "DATA_ANALYSIS", 3, 4, "procedural_fluency", "data_reasoning"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.INEQ.ONE.ADD":
        boundary = rng.randint(-8, 15)
        offset = rng.randint(2, 9)
        total = boundary + offset
        op = rng.choice(["<", ">"])
        return (
            f"Solve x + {offset} {op} {total}.",
            f"x{op}{boundary}",
            ("Undo the addition on both sides.", "Adding or subtracting does not reverse the inequality."),
            {"INEQ.ADD.REVERSE_SIGN": f"x{('>' if op == '<' else '<')}{boundary}"},
        )
    if family_code == "MATH.INEQ.ONE.MULT":
        boundary = rng.randint(2, 12)
        coefficient = rng.randint(2, 7)
        total = boundary * coefficient
        op = rng.choice(["<", ">"])
        return (
            f"Solve {coefficient}x {op} {total}.",
            f"x{op}{boundary}",
            ("Divide both sides by the positive coefficient.", "A positive division keeps the inequality direction."),
            {"INEQ.POSITIVE.UNNECESSARY_FLIP": f"x{('>' if op == '<' else '<')}{boundary}"},
        )
    if family_code in {"MATH.INEQ.NEGATIVE.FLIP", "MATH.INEQ.ERROR.NO_FLIP"}:
        boundary = rng.randint(2, 10)
        coefficient = -rng.randint(2, 7)
        total = coefficient * boundary
        original = rng.choice(["<", ">"])
        solved = ">" if original == "<" else "<"
        if family_code == "MATH.INEQ.NEGATIVE.FLIP":
            return (
                f"Solve {coefficient}x {original} {total}.",
                f"x{solved}{boundary}",
                ("Divide both sides by the negative coefficient.", "Reverse the inequality when multiplying or dividing by a negative."),
                {"INEQ.NEGATIVE.NO_FLIP": f"x{original}{boundary}"},
            )
        return (
            f"A student solves {coefficient}x {original} {total} as x {original} {boundary}. "
            f"Which response is correct? (A) It should be x {solved} {boundary}. "
            "(B) The student is correct. (C) Change only the boundary sign. (D) Equality is required.",
            "A",
            ("The solving step divides by a negative number.", "That operation reverses the inequality direction."),
            {"INEQ.NEGATIVE.NO_FLIP": "B"},
        )
    if family_code == "MATH.INEQ.TEST.SOLUTION":
        boundary = rng.randint(-5, 10)
        candidate = boundary + rng.choice([-3, -2, 2, 3])
        op = rng.choice(["<", ">"])
        truth = candidate < boundary if op == "<" else candidate > boundary
        return (
            f"Is x={candidate} a solution of x {op} {boundary}? Answer yes or no.",
            "yes" if truth else "no",
            ("Substitute the candidate for x.", "Decide whether the resulting comparison is true."),
            {"INEQ.TEST.OPPOSITE": "no" if truth else "yes"},
        )
    if family_code == "MATH.INEQ.WORD.MINIMUM":
        rate = rng.randint(2, 8)
        fixed = rng.randint(1, 10)
        target = fixed + rate * rng.randint(4, 10)
        return (
            f"A fundraiser already has {fixed} dollars and earns {rate} dollars per item. "
            f"It needs at least {target} dollars. Which inequality models the number n of items?",
            f"{rate}n+{fixed}>={target}",
            ("'At least' includes equality.", "Combine the fixed amount and repeated earnings."),
            {"INEQ.WORD.STRICT_MINIMUM": f"{rate}n+{fixed}>{target}"},
        )
    if family_code == "MATH.FUNC.SEQUENCE.LINEAR":
        start = rng.randint(-5, 10)
        rate = rng.choice([-4, -3, 2, 3, 4, 5])
        n = rng.randint(5, 9)
        value = start + (n - 1) * rate
        return (
            f"A sequence starts at {start} and changes by {rate} each term. What is term {n}?",
            str(value),
            ("A constant difference makes a linear sequence.", f"Use {start} + ({n}-1)({rate})."),
            {"FUNC.SEQUENCE.OFF_BY_ONE": str(start + n * rate)},
        )
    if family_code == "MATH.FUNC.COMPARE.RATE":
        m1 = rng.randint(2, 8)
        m2 = rng.randint(2, 8)
        while m1 == m2:
            m2 = rng.randint(2, 8)
        answer = "A" if m1 > m2 else "B"
        return (
            f"Function A is y={m1}x+3. Function B has values (0,2), (1,{2+m2}), (2,{2+2*m2}). "
            "Which function has the greater rate of change? Answer A or B.",
            answer,
            ("For A, the x coefficient is the rate.", "For B, compare the change in y when x increases by 1."),
            {"FUNC.COMPARE.USE_INTERCEPT": "B" if answer == "A" else "A"},
        )
    if family_code == "MATH.FUNC.DOMAIN.RANGE":
        xs = rng.sample(range(-4, 6), 4)
        m, b = rng.choice([-3, -2, 2, 3]), rng.randint(-4, 4)
        ys = [m * x + b for x in xs]
        return (
            f"For the function pairs {list(zip(xs, ys, strict=True))}, give the range as sorted comma-separated values.",
            ",".join(map(str, sorted(set(ys)))),
            ("The range is the set of output values.", "Read the second coordinate of each ordered pair."),
            {"FUNC.DOMAIN_RANGE.SWAP": ",".join(map(str, sorted(set(xs))))},
        )
    if family_code == "MATH.FUNC.NONLINEAR.CLASSIFY":
        linear = rng.random() < 0.5
        xs = [0, 1, 2, 3]
        if linear:
            m, b = rng.randint(2, 5), rng.randint(0, 4)
            ys = [m * x + b for x in xs]
            answer = "linear"
        else:
            b = rng.randint(1, 4)
            ys = [x * x + b for x in xs]
            answer = "nonlinear"
        return (
            f"Classify the relationship with x-values {xs} and y-values {ys} as linear or nonlinear.",
            answer,
            ("Check first differences in y for equal changes in x.", "A linear relationship has a constant rate of change."),
            {"FUNC.LINEARITY.FIRST_DIFFERENCE": "nonlinear" if linear else "linear"},
        )
    if family_code == "MATH.FUNC.ERROR.CONSTANT_RATE":
        return (
            "A student says the table x=[1,2,3,4], y=[1,4,9,16] is linear because y always increases. "
            "Which response is correct? (A) It is nonlinear because first differences are not constant. "
            "(B) It is linear because all y-values increase. (C) It is linear because y is positive. "
            "(D) There is not enough information.",
            "A",
            ("Increasing is not the same as constant rate of change.", "Compare consecutive first differences."),
            {"FUNC.LINEARITY.INCREASING_MEANS_LINEAR": "B"},
        )
    if family_code == "MATH.GEO.CIRCLE.RADIUS_DIAMETER":
        radius = rng.randint(2, 15)
        return (
            f"A circle has radius {radius}. What is its diameter?",
            str(2 * radius),
            ("The radius goes from center to circle.", "The diameter is two radii."),
            {"GEO.CIRCLE.RADIUS_EQUALS_DIAMETER": str(radius)},
        )
    if family_code in {"MATH.GEO.CIRCLE.CIRCUMFERENCE", "MATH.GEO.CIRCLE.AREA"}:
        radius = rng.randint(2, 12)
        if family_code == "MATH.GEO.CIRCLE.CIRCUMFERENCE":
            return (
                f"A circle has radius {radius}. Give its circumference exactly in terms of pi.",
                f"{2*radius}pi",
                ("Circumference measures distance around the circle.", "Use C=2*pi*r."),
                {"GEO.CIRCLE.USE_AREA": f"{radius*radius}pi"},
            )
        return (
            f"A circle has radius {radius}. Give its area exactly in terms of pi.",
            f"{radius*radius}pi",
            ("Area measures the region inside the circle.", "Use A=pi*r^2."),
            {"GEO.CIRCLE.FORGET_SQUARE": f"{radius}pi"},
        )
    if family_code == "MATH.GEO.CIRCLE.ERROR.RADIUS":
        diameter = 2 * rng.randint(3, 12)
        correct = diameter // 2
        return (
            f"A circle has diameter {diameter}. A student uses {diameter} as r in A=pi*r^2. "
            f"Which response is correct? (A) The radius should be {correct}. "
            "(B) The student is correct. (C) The radius should be doubled. (D) Area uses no radius.",
            "A",
            ("Diameter spans two radii.", "Divide the diameter by 2 before using a radius formula."),
            {"GEO.CIRCLE.DIAMETER_AS_RADIUS": "B"},
        )
    if family_code == "MATH.DATA.DOT.FREQUENCY":
        values = [rng.randint(1, 6) for _ in range(12)]
        target = rng.choice(values)
        count = values.count(target)
        return (
            f"A dot plot represents the data {values}. How many dots should appear above {target}?",
            str(count),
            ("Each data value contributes one dot.", f"Count occurrences of {target}."),
            {"DATA.DOT.COUNT_DISTINCT": "1" if count != 1 else "2"},
        )
    if family_code == "MATH.DATA.HISTOGRAM.BIN":
        values = [rng.randint(0, 29) for _ in range(15)]
        lo = rng.choice([0, 10, 20])
        hi = lo + 10
        count = sum(lo <= value < hi for value in values)
        wrong = sum(lo <= value <= hi for value in values)
        if wrong == count:
            wrong = count + 1
        return (
            f"For data {values}, how many values belong in the histogram interval [{lo},{hi})?",
            str(count),
            ("A histogram bin includes values in its stated interval.", f"Count values at least {lo} and less than {hi}."),
            {"DATA.HISTOGRAM.INCLUDE_UPPER": str(wrong)},
        )
    if family_code in {"MATH.DATA.FIVE_NUMBER", "MATH.DATA.IQR"}:
        values = sorted(rng.sample(range(1, 40), 8))
        lower, upper = values[:4], values[4:]
        q1 = (lower[1] + lower[2]) / 2
        median = (values[3] + values[4]) / 2
        q3 = (upper[1] + upper[2]) / 2
        if family_code == "MATH.DATA.FIVE_NUMBER":
            answer = ",".join(f"{x:g}" for x in (values[0], q1, median, q3, values[-1]))
            return (
                f"Give the five-number summary min,Q1,median,Q3,max for {values}.",
                answer,
                ("Order the data first.", "Find the median, then the medians of the lower and upper halves."),
                {"DATA.FIVE_NUMBER.OMIT_QUARTILES": f"{values[0]},{median:g},{values[-1]}"},
            )
        return (
            f"Find the interquartile range of {values}.",
            f"{q3-q1:g}",
            ("Find Q1 and Q3 from the ordered data.", "IQR=Q3-Q1."),
            {"DATA.IQR.USE_RANGE": str(values[-1] - values[0])},
        )
    if family_code == "MATH.DATA.MAD":
        center = rng.randint(5, 15)
        values = [center - 4, center - 2, center, center + 2, center + 4]
        mean = statistics.mean(values)
        mad = statistics.mean(abs(value - mean) for value in values)
        return (
            f"Find the mean absolute deviation of {values}.",
            f"{mad:g}",
            ("Find the mean first.", "Average the absolute distances from the mean."),
            {"DATA.MAD.USE_SIGNED_DEVIATIONS": "0"},
        )
    raise ValueError(f"No advanced canonical builder for family: {family_code}")
