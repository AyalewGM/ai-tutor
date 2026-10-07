"""Canonical statistics and probability problem families."""

from __future__ import annotations

import random
import statistics
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.DATA.MEAN": _spec("MATH.DATA.MEAN", "Mean of a data set", "MATH.DATA.CENTER", "DATA_ANALYSIS", 1, 4, "procedural_fluency", "data_reasoning"),
    "MATH.DATA.MEDIAN": _spec("MATH.DATA.MEDIAN", "Median of a data set", "MATH.DATA.CENTER", "DATA_ANALYSIS", 1, 4, "procedural_fluency", "data_reasoning"),
    "MATH.DATA.RANGE": _spec("MATH.DATA.RANGE", "Range of a data set", "MATH.DATA.SPREAD", "DATA_ANALYSIS", 1, 3, "procedural_fluency", "data_reasoning"),
    "MATH.DATA.MISSING_MEAN": _spec("MATH.DATA.MISSING_MEAN", "Missing value from a known mean", "MATH.DATA.CENTER", "DATA_REASONING", 2, 4, "reasoning", "inverse_operations"),
    "MATH.DATA.OUTLIER.CENTER": _spec("MATH.DATA.OUTLIER.CENTER", "Choose a resistant center with an outlier", "MATH.DATA.CENTER", "ERROR_ANALYSIS", 2, 4, "conceptual_understanding", "misconception_probe"),
    "MATH.DATA.FREQ.JOINT": _spec("MATH.DATA.FREQ.JOINT", "Joint relative frequency", "MATH.DATA.FREQUENCY", "TABLE_REASONING", 2, 4, "representation", "data_reasoning"),
    "MATH.DATA.FREQ.CONDITIONAL": _spec("MATH.DATA.FREQ.CONDITIONAL", "Conditional relative frequency", "MATH.DATA.FREQUENCY", "TABLE_REASONING", 3, 4, "reasoning", "data_reasoning"),
    "MATH.PROB.SIMPLE": _spec("MATH.PROB.SIMPLE", "Simple probability", "MATH.PROB.SIMPLE", "PROBABILITY", 1, 3, "procedural_fluency", "representation"),
    "MATH.PROB.COMPLEMENT": _spec("MATH.PROB.COMPLEMENT", "Complement probability", "MATH.PROB.SIMPLE", "PROBABILITY", 2, 4, "reasoning", "conceptual_understanding"),
    "MATH.PROB.SAMPLE_SPACE": _spec("MATH.PROB.SAMPLE_SPACE", "Count a compound sample space", "MATH.PROB.COMPOUND", "PROBABILITY", 2, 4, "reasoning", "combinatorial_reasoning"),
    "MATH.PROB.INDEPENDENT.AND": _spec("MATH.PROB.INDEPENDENT.AND", "Independent events both occur", "MATH.PROB.COMPOUND", "PROBABILITY", 3, 4, "procedural_fluency", "reasoning"),
    "MATH.PROB.DISJOINT.OR": _spec("MATH.PROB.DISJOINT.OR", "Disjoint events either occurs", "MATH.PROB.COMPOUND", "PROBABILITY", 3, 4, "procedural_fluency", "reasoning"),
}


def _frac(n: int, d: int) -> str:
    return str(Fraction(n, d))


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.DATA.MEAN":
        n = rng.choice([4, 5, 6])
        target = rng.randint(4, 20)
        values = [rng.randint(2, 20) for _ in range(n - 1)]
        values.append(n * target - sum(values))
        while values[-1] < 0:
            values = [rng.randint(2, target + 3) for _ in range(n - 1)]
            values.append(n * target - sum(values))
        rng.shuffle(values)
        return f"Find the mean of: {', '.join(map(str, values))}.", str(target), ("Add all values.", f"Divide the total by the {n} values."), {"DATA.MEAN.DIVIDE_BY_WRONG_COUNT": str(sum(values) // max(1, n - 1))}, {"type": "dot_plot", "data": values, "aria_label": "Dot plot of the data values used to find the mean."}
    if family_code == "MATH.DATA.MEDIAN":
        n = rng.choice([5, 7])
        values = rng.sample(range(2, 30), n)
        answer = int(statistics.median(values))
        wrong = values[n // 2]
        return f"Find the median of: {', '.join(map(str, values))}.", str(answer), ("Order the data from least to greatest.", "Choose the middle value after ordering."), {"DATA.MEDIAN.NO_SORT": str(wrong)}, {"type": "dot_plot", "data": values, "aria_label": "Dot plot of the data values used to find the median."}
    if family_code == "MATH.DATA.RANGE":
        values = rng.sample(range(1, 35), rng.choice([5, 6, 7]))
        answer = max(values) - min(values)
        return f"Find the range of: {', '.join(map(str, values))}.", str(answer), ("Identify the greatest and least values.", "Subtract the least from the greatest."), {"DATA.RANGE.USE_MAX": str(max(values))}, {"type": "dot_plot", "data": values, "aria_label": "Dot plot showing the spread of the data values."}
    if family_code == "MATH.DATA.MISSING_MEAN":
        n = rng.choice([4, 5, 6])
        mean = rng.randint(6, 18)
        known = [rng.randint(2, 18) for _ in range(n - 1)]
        missing = n * mean - sum(known)
        while missing < 1 or missing > 30:
            known = [rng.randint(3, mean + 2) for _ in range(n - 1)]
            missing = n * mean - sum(known)
        return f"The mean of {n} values is {mean}. The known values are {', '.join(map(str, known))}. What is the missing value?", str(missing), (f"The total of all {n} values must be {n * mean}.", "Subtract the sum of the known values."), {"DATA.MEAN.SUBTRACT_FROM_MEAN": str(abs(mean - sum(known)))}
    if family_code == "MATH.DATA.OUTLIER.CENTER":
        core = sorted(rng.sample(range(6, 16), 5))
        outlier = rng.randint(35, 50)
        return f"The data are {', '.join(map(str, core + [outlier]))}. Which measure of center is less affected by the outlier: mean or median?", "median", ("An outlier pulls some measures toward an extreme.", "The median depends on position rather than the size of every value."), {"DATA.OUTLIER.MEAN": "mean"}, {"type": "dot_plot", "data": core + [outlier], "highlight": outlier, "aria_label": "Dot plot with one value far from the main cluster."}
    if family_code in {"MATH.DATA.FREQ.JOINT", "MATH.DATA.FREQ.CONDITIONAL"}:
        a, b, c, d = [rng.randint(4, 18) for _ in range(4)]
        total = a + b + c + d
        if family_code == "MATH.DATA.FREQ.JOINT":
            return f"A two-way table has counts [[{a},{b}],[{c},{d}]]. What fraction of all observations are in the first-row, first-column cell?", _frac(a, total), ("Joint relative frequency uses the grand total.", f"Divide the cell count {a} by {total}."), {"DATA.FREQ.USE_ROW_TOTAL": _frac(a, a + b)}, {"type": "frequency_table", "row_labels": ["Group 1", "Group 2"], "col_labels": ["Category 1", "Category 2"], "cells": [[a, b], [c, d]], "row_totals": [a + b, c + d], "col_totals": [a + c, b + d], "grand_total": total, "aria_label": "Two-way frequency table with two groups and two categories."}
        return f"A two-way table has counts [[{a},{b}],[{c},{d}]]. Among observations in the first row, what fraction are in the first column?", _frac(a, a + b), ("Conditional frequency uses the total of the given group.", f"Use first-row total {a + b} as the denominator."), {"DATA.FREQ.USE_GRAND_TOTAL": _frac(a, total)}, {"type": "frequency_table", "row_labels": ["Group 1", "Group 2"], "col_labels": ["Category 1", "Category 2"], "cells": [[a, b], [c, d]], "row_totals": [a + b, c + d], "col_totals": [a + c, b + d], "grand_total": total, "aria_label": "Two-way frequency table for conditional relative-frequency reasoning."}
    if family_code in {"MATH.PROB.SIMPLE", "MATH.PROB.COMPLEMENT"}:
        total = rng.randint(5, 12)
        favorable = rng.randint(1, total - 1)
        if family_code == "MATH.PROB.SIMPLE":
            return f"A bag has {total} equally likely marbles, {favorable} of them blue. What is the probability of drawing blue?", _frac(favorable, total), ("Probability is favorable outcomes over all equally likely outcomes.", f"Use {favorable} over {total} and simplify."), {"PROB.SIMPLE.INVERT": _frac(total, favorable)}, {"type": "marble_bag", "marbles": ["blue"] * favorable + ["red"] * (total - favorable), "aria_label": f"Bag containing {favorable} blue and {total - favorable} red marbles."}
        return f"A bag has {total} equally likely marbles, {favorable} of them blue. What is the probability of drawing a marble that is not blue?", _frac(total - favorable, total), ("A complement includes every outcome outside the event.", "Subtract the event probability from 1."), {"PROB.COMPLEMENT.EVENT_ITSELF": _frac(favorable, total)}, {"type": "marble_bag", "marbles": ["blue"] * favorable + ["red"] * (total - favorable), "aria_label": f"Bag containing {favorable} blue and {total - favorable} non-blue marbles."}
    if family_code == "MATH.PROB.SAMPLE_SPACE":
        spinner = rng.randint(3, 8)
        die = rng.choice([4, 6, 8])
        return f"A spinner has {spinner} possible outcomes and a die has {die} possible outcomes. How many ordered outcomes are possible when both are used once?", str(spinner * die), ("Use the multiplication principle.", f"There are {spinner} choices followed by {die} choices."), {"PROB.SAMPLE_SPACE.ADD": str(spinner + die)}
    if family_code == "MATH.PROB.INDEPENDENT.AND":
        a, b = rng.randint(1, 4), rng.randint(2, 6)
        c, d = rng.randint(1, 4), rng.randint(2, 6)
        while a >= b or c >= d:
            a, b = rng.randint(1, 4), rng.randint(2, 6)
            c, d = rng.randint(1, 4), rng.randint(2, 6)
        correct = Fraction(a, b) * Fraction(c, d)
        wrong = Fraction(a, b) + Fraction(c, d)
        return f"Independent events A and B have probabilities {Fraction(a, b)} and {Fraction(c, d)}. What is P(A and B)?", str(correct), ("For independent events joined by 'and', multiply.", "Multiply the two probabilities and simplify."), {"PROB.AND.ADD": str(wrong)}
    if family_code == "MATH.PROB.DISJOINT.OR":
        den = rng.choice([6, 8, 10, 12])
        a = rng.randint(1, den // 3)
        b = rng.randint(1, den // 3)
        return f"Disjoint events A and B have probabilities {Fraction(a, den)} and {Fraction(b, den)}. What is P(A or B)?", str(Fraction(a + b, den)), ("Disjoint events cannot happen together.", "For disjoint events joined by 'or', add their probabilities."), {"PROB.OR.MULTIPLY": str(Fraction(a * b, den * den))}
    raise ValueError(f"No statistics/probability builder for family: {family_code}")
