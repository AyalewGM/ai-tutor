"""Canonical elementary data-representation and pattern-reasoning families."""

from __future__ import annotations

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.DATA.BAR.READ": _spec("MATH.DATA.BAR.READ", "Read a bar graph value", "MATH.DATA.ELEMENTARY.REPRESENT", "DATA_REPRESENTATION", 1, 2, "representation", "data_reasoning"),
    "MATH.DATA.BAR.COMPARE": _spec("MATH.DATA.BAR.COMPARE", "Compare bar graph categories", "MATH.DATA.ELEMENTARY.COMPARE", "DATA_REASONING", 1, 3, "reasoning", "comparison"),
    "MATH.DATA.BAR.TOTAL": _spec("MATH.DATA.BAR.TOTAL", "Find a total from a bar graph", "MATH.DATA.ELEMENTARY.COMPARE", "DATA_REASONING", 1, 3, "reasoning", "addition"),
    "MATH.DATA.PICTURE.SCALE": _spec("MATH.DATA.PICTURE.SCALE", "Read a scaled picture graph", "MATH.DATA.ELEMENTARY.REPRESENT", "DATA_REPRESENTATION", 1, 3, "representation", "multiplicative_reasoning"),
    "MATH.DATA.TALLY.READ": _spec("MATH.DATA.TALLY.READ", "Read tally marks", "MATH.DATA.ELEMENTARY.REPRESENT", "DATA_REPRESENTATION", 1, 2, "representation", "counting"),
    "MATH.DATA.FREQ.MODE": _spec("MATH.DATA.FREQ.MODE", "Identify the most frequent category", "MATH.DATA.ELEMENTARY.COMPARE", "DATA_REASONING", 1, 3, "reasoning", "comparison"),
    "MATH.DATA.LINEPLOT.FREQUENCY": _spec("MATH.DATA.LINEPLOT.FREQUENCY", "Read a line-plot frequency", "MATH.DATA.ELEMENTARY.REPRESENT", "DATA_REPRESENTATION", 1, 3, "representation", "data_reasoning"),
    "MATH.DATA.LINEPLOT.DIFFERENCE": _spec("MATH.DATA.LINEPLOT.DIFFERENCE", "Compare line-plot frequencies", "MATH.DATA.ELEMENTARY.COMPARE", "DATA_REASONING", 2, 3, "reasoning", "subtraction"),
    "MATH.PATTERN.ADDITIVE.NEXT": _spec("MATH.PATTERN.ADDITIVE.NEXT", "Continue an additive number pattern", "MATH.PATTERN.NUMERIC", "PATTERN", 1, 3, "pattern_reasoning", "number_sense"),
    "MATH.PATTERN.MULTIPLICATIVE.NEXT": _spec("MATH.PATTERN.MULTIPLICATIVE.NEXT", "Continue a multiplicative number pattern", "MATH.PATTERN.NUMERIC", "PATTERN", 2, 4, "pattern_reasoning", "multiplicative_reasoning"),
    "MATH.PATTERN.RULE.INPUT_OUTPUT": _spec("MATH.PATTERN.RULE.INPUT_OUTPUT", "Apply an input-output rule", "MATH.PATTERN.FUNCTION_RULE", "FUNCTION_REASONING", 1, 3, "representation", "pattern_reasoning"),
    "MATH.PATTERN.ERROR.DIFFERENCE": _spec("MATH.PATTERN.ERROR.DIFFERENCE", "Diagnose an incorrect pattern rule", "MATH.PATTERN.NUMERIC", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
}


def _categories(rng: random.Random) -> dict[str, int]:
    names = ["red", "blue", "green", "yellow"]
    values = rng.sample(range(3, 13), 4)
    return dict(zip(names, values, strict=True))


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code in {"MATH.DATA.BAR.READ", "MATH.DATA.BAR.COMPARE", "MATH.DATA.BAR.TOTAL"}:
        data = _categories(rng)
        if family_code == "MATH.DATA.BAR.READ":
            category = rng.choice(list(data))
            return (
                f"A bar graph has counts {data}. What is the count for {category}?",
                str(data[category]),
                ("Find the named category.", "Read its bar height."),
                {"DATA.BAR.READ.WRONG_CATEGORY": str(next(value for key, value in data.items() if key != category))},
            )
        if family_code == "MATH.DATA.BAR.COMPARE":
            first, second = rng.sample(list(data), 2)
            difference = abs(data[first] - data[second])
            return (
                f"A bar graph has counts {data}. What is the difference between {first} and {second}?",
                str(difference),
                ("Read both bar heights.", "Subtract the smaller count from the larger count."),
                {"DATA.BAR.COMPARE.ADD": str(data[first] + data[second])},
            )
        first, second = rng.sample(list(data), 2)
        return (
            f"A bar graph has counts {data}. What is the combined count for {first} and {second}?",
            str(data[first] + data[second]),
            ("Read both bar heights.", "Add the two category counts."),
            {"DATA.BAR.TOTAL.SUBTRACT": str(abs(data[first] - data[second]))},
        )
    if family_code == "MATH.DATA.PICTURE.SCALE":
        symbols = rng.randint(3, 8)
        scale = rng.choice([2, 5, 10])
        return (
            f"In a picture graph, each symbol represents {scale} students. A category has {symbols} symbols. How many students does it represent?",
            str(symbols * scale),
            ("Each symbol stands for more than one student.", "Multiply the number of symbols by the key value."),
            {"DATA.PICTURE.IGNORE_KEY": str(symbols)},
        )
    if family_code == "MATH.DATA.TALLY.READ":
        groups = rng.randint(1, 4)
        extras = rng.randint(1, 4)
        total = groups * 5 + extras
        return (
            f"A tally table shows {groups} complete groups of five marks and {extras} extra marks. What count does it represent?",
            str(total),
            ("Each complete tally group is 5.", "Multiply the complete groups by 5, then add the extra marks."),
            {"DATA.TALLY.COUNT_GROUPS_ONLY": str(groups + extras)},
        )
    if family_code == "MATH.DATA.FREQ.MODE":
        data = _categories(rng)
        category = max(data, key=data.get)
        return (
            f"A frequency table has counts {data}. Which category occurs most often?",
            category,
            ("Compare the category counts.", "The greatest frequency identifies the most common category."),
            {"DATA.MODE.CHOOSE_SMALLEST": min(data, key=data.get)},
        )
    if family_code in {"MATH.DATA.LINEPLOT.FREQUENCY", "MATH.DATA.LINEPLOT.DIFFERENCE"}:
        values = [rng.randint(1, 6) for _ in range(16)]
        present = sorted(set(values))
        if family_code == "MATH.DATA.LINEPLOT.FREQUENCY":
            target = rng.choice(present)
            count = values.count(target)
            return (
                f"A line plot represents the data {values}. How many marks should appear above {target}?",
                str(count),
                ("Each observation contributes one mark.", f"Count how many times {target} appears."),
                {"DATA.LINEPLOT.COUNT_DISTINCT": str(len(present)) if len(present) != count else str(count + 1)},
            )
        first, second = rng.sample(present, 2)
        difference = abs(values.count(first) - values.count(second))
        wrong = values.count(first) + values.count(second)
        if wrong == difference:
            wrong += 1
        return (
            f"A line plot represents the data {values}. What is the difference between the frequencies of {first} and {second}?",
            str(difference),
            ("Count the marks above each requested value.", "Subtract the smaller frequency from the larger frequency."),
            {"DATA.LINEPLOT.ADD_FREQUENCIES": str(wrong)},
        )
    if family_code == "MATH.PATTERN.ADDITIVE.NEXT":
        start = rng.randint(1, 20)
        step = rng.randint(2, 9)
        terms = [start + step * i for i in range(4)]
        return (
            f"Continue the pattern {terms}. What is the next term?",
            str(terms[-1] + step),
            ("Find the amount added each time.", "Add the same amount to the last term."),
            {"PATTERN.ADD.DOUBLE_STEP": str(terms[-1] + 2 * step)},
        )
    if family_code == "MATH.PATTERN.MULTIPLICATIVE.NEXT":
        start = rng.randint(1, 5)
        factor = rng.choice([2, 3, 4])
        terms = [start * factor**i for i in range(4)]
        return (
            f"Continue the pattern {terms}. What is the next term?",
            str(terms[-1] * factor),
            ("Find the constant multiplicative factor.", "Multiply the last term by that same factor."),
            {"PATTERN.MULTIPLICATIVE.USE_DIFFERENCE": str(terms[-1] + (terms[1] - terms[0]))},
        )
    if family_code == "MATH.PATTERN.RULE.INPUT_OUTPUT":
        multiplier = rng.randint(2, 6)
        addend = rng.randint(1, 8)
        value = rng.randint(2, 12)
        return (
            f"A rule multiplies an input by {multiplier}, then adds {addend}. What is the output for input {value}?",
            str(multiplier * value + addend),
            ("Apply the operations in the stated order.", "Multiply first, then add."),
            {"PATTERN.RULE.ADD_THEN_MULTIPLY": str((value + addend) * multiplier)},
        )
    if family_code == "MATH.PATTERN.ERROR.DIFFERENCE":
        start = rng.randint(2, 12)
        step = rng.randint(2, 7)
        terms = [start + step * i for i in range(4)]
        wrong_step = step + 1
        prompt = (
            f"A student says the pattern {terms} increases by {wrong_step} each time. "
            f"Which response is correct? (A) It increases by {step}. "
            "(B) The student is correct. (C) It doubles each time. (D) There is no rule."
        )
        return (
            prompt,
            "A",
            ("Compare consecutive terms.", "Subtract each term from the next to find the repeated difference."),
            {"PATTERN.ERROR.ACCEPT_WRONG_DIFFERENCE": "B"},
        )
    raise ValueError(f"No elementary data/pattern builder for family: {family_code}")
