"""Canonical sampling, bivariate-data, and experimental-probability depth."""

from __future__ import annotations

import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str,
    name: str,
    skill: str,
    problem_type: str,
    lo: int,
    hi: int,
    *dimensions: str,
) -> ProblemFamilySpec:
    return ProblemFamilySpec(
        code,
        name,
        skill,
        problem_type,
        lo,
        hi,
        ALL_MODES,
        frozenset(dimensions),
    )


FAMILIES = {
    "MATH.DATA.SAMPLE.REPRESENTATIVE": _spec(
        "MATH.DATA.SAMPLE.REPRESENTATIVE",
        "Identify a representative sample",
        "MATH.DATA.SAMPLING",
        "REASONING",
        2,
        4,
        "reasoning",
        "conceptual_understanding",
    ),
    "MATH.DATA.SAMPLE.BIAS": _spec(
        "MATH.DATA.SAMPLE.BIAS",
        "Diagnose sampling bias",
        "MATH.DATA.SAMPLING",
        "ERROR_ANALYSIS",
        2,
        4,
        "error_analysis",
        "misconception_probe",
    ),
    "MATH.DATA.SCATTER.ASSOCIATION": _spec(
        "MATH.DATA.SCATTER.ASSOCIATION",
        "Classify bivariate association",
        "MATH.DATA.BIVARIATE",
        "DATA_REASONING",
        2,
        4,
        "representation",
        "reasoning",
    ),
    "MATH.DATA.SCATTER.PREDICT": _spec(
        "MATH.DATA.SCATTER.PREDICT",
        "Predict from a bivariate trend",
        "MATH.DATA.BIVARIATE",
        "MODELING",
        2,
        4,
        "modeling",
        "transfer",
    ),
    "MATH.DATA.LINEFIT.PREDICT": _spec(
        "MATH.DATA.LINEFIT.PREDICT",
        "Predict using a line of best fit",
        "MATH.DATA.LINEAR_MODEL",
        "MODELING",
        2,
        4,
        "modeling",
        "procedural_fluency",
    ),
    "MATH.DATA.LINEFIT.SLOPE": _spec(
        "MATH.DATA.LINEFIT.SLOPE",
        "Interpret slope in a data model",
        "MATH.DATA.LINEAR_MODEL",
        "REASONING",
        2,
        4,
        "reasoning",
        "modeling",
    ),
    "MATH.DATA.TWOWAY.RELATIVE": _spec(
        "MATH.DATA.TWOWAY.RELATIVE",
        "Compute a conditional relative frequency",
        "MATH.DATA.FREQUENCY",
        "DATA_TABLE",
        2,
        4,
        "representation",
        "procedural_fluency",
    ),
    "MATH.PROB.EXPERIMENTAL": _spec(
        "MATH.PROB.EXPERIMENTAL",
        "Compute experimental probability",
        "MATH.PROB.EXPERIMENTAL",
        "PROBABILITY",
        1,
        3,
        "procedural_fluency",
        "representation",
    ),
    "MATH.PROB.EXPECTED_COUNT": _spec(
        "MATH.PROB.EXPECTED_COUNT",
        "Use probability to predict an expected count",
        "MATH.PROB.EXPERIMENTAL",
        "MODELING",
        2,
        4,
        "modeling",
        "transfer",
    ),
    "MATH.PROB.THEORY.VS_EXPERIMENT": _spec(
        "MATH.PROB.THEORY.VS_EXPERIMENT",
        "Compare theoretical and experimental probability",
        "MATH.PROB.EXPERIMENTAL",
        "REASONING",
        2,
        4,
        "reasoning",
        "conceptual_understanding",
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.DATA.SAMPLE.REPRESENTATIVE":
        population = rng.choice(["school", "town recreation program", "district"])
        return (
            (
                f"A researcher wants to estimate preferences for the whole {population}. "
                "Which sample is most representative? "
                "(A) A random sample drawn from the full population. "
                "(B) Only volunteers from one club. "
                "(C) Only people present at one activity. "
                "(D) The researcher's friends."
            ),
            "A",
            (
                "A representative sample should give members of the population a fair chance.",
                "Convenience and volunteer-only samples can systematically overrepresent groups.",
            ),
            {"DATA.SAMPLE.CONVENIENCE": "B", "DATA.SAMPLE.LOCATION": "C"},
        )

    if family_code == "MATH.DATA.SAMPLE.BIAS":
        context = rng.choice(
            [
                ("school lunch", "students leaving the cafeteria"),
                ("after-school programs", "members of the robotics club"),
                ("community exercise", "people entering a fitness center"),
            ]
        )
        return (
            (
                f"A survey about {context[0]} is given only to {context[1]}. "
                "What is the main problem? "
                "(A) The sample may be biased because the selection favors one group. "
                "(B) Every sample must include the entire population. "
                "(C) Random samples are always smaller. "
                "(D) There is no possible bias."
            ),
            "A",
            (
                "Ask who had a chance to be selected.",
                "A selection method can bias results when it systematically favors a subgroup.",
            ),
            {"DATA.SAMPLE.BIAS.DENY": "D", "DATA.SAMPLE.CENSUS_REQUIRED": "B"},
        )

    if family_code == "MATH.DATA.SCATTER.ASSOCIATION":
        direction = rng.choice(["positive", "negative", "none"])
        if direction == "positive":
            description = "the points generally rise from left to right"
            wrong = "negative"
        elif direction == "negative":
            description = "the points generally fall from left to right"
            wrong = "positive"
        else:
            description = "the points show no consistent upward or downward trend"
            wrong = "positive"
        return (
            f"A scatter plot shows that {description}. What association is shown?",
            direction,
            (
                "Read the overall direction of the point cloud, not one individual point.",
                "Rising suggests positive, falling negative, and no clear direction no association.",
            ),
            {"DATA.SCATTER.REVERSE_DIRECTION": wrong},
        )

    if family_code == "MATH.DATA.SCATTER.PREDICT":
        rate = rng.randint(2, 8)
        intercept = rng.randint(1, 12)
        x_value = rng.randint(5, 15)
        prediction = rate * x_value + intercept
        return (
            (
                f"A bivariate data trend is modeled approximately by y = {rate}x + {intercept}. "
                f"Using the trend, predict y when x = {x_value}."
            ),
            str(prediction),
            (
                "A trend prediction uses the model rather than an individual data point.",
                f"Substitute x = {x_value} into the model.",
            ),
            {"DATA.SCATTER.IGNORE_INTERCEPT": str(rate * x_value)},
        )

    if family_code == "MATH.DATA.LINEFIT.PREDICT":
        slope = rng.randint(2, 9)
        intercept = rng.randint(3, 20)
        x_value = rng.randint(4, 14)
        answer = slope * x_value + intercept
        return (
            (
                f"A line of best fit is y = {slope}x + {intercept}. "
                f"What value does the model predict at x = {x_value}?"
            ),
            str(answer),
            (
                "A line of best fit gives an estimated response.",
                f"Compute {slope} × {x_value} + {intercept}.",
            ),
            {"DATA.LINEFIT.OMIT_INTERCEPT": str(slope * x_value)},
        )

    if family_code == "MATH.DATA.LINEFIT.SLOPE":
        slope = rng.randint(2, 12)
        context = rng.choice(
            [
                ("hours practiced", "points scored", "points"),
                ("weeks", "plant height", "centimeters"),
                ("hours traveled", "distance", "miles"),
            ]
        )
        return (
            (
                f"A model relating {context[0]} x to {context[1]} y is "
                f"y = {slope}x + 5. What does the slope {slope} mean?"
            ),
            f"y increases by about {slope} {context[2]} for each 1-unit increase in x",
            (
                "Slope is change in the response for a one-unit increase in the explanatory variable.",
                "Interpret the rate in the context and keep the direction of change.",
            ),
            {
                "DATA.LINEFIT.SLOPE_AS_INTERCEPT": "y starts at 5",
                "DATA.LINEFIT.REVERSE_RATE": f"x increases by {slope} for each 1-unit increase in y",
            },
        )

    if family_code == "MATH.DATA.TWOWAY.RELATIVE":
        yes = rng.randint(12, 40)
        no = rng.randint(8, 30)
        while no == yes:
            no = rng.randint(8, 30)
        total = yes + no
        fraction = Fraction(yes, total)
        return (
            (
                f"In one row of a two-way table, {yes} students answered yes and {no} answered no. "
                "What fraction of students in this row answered yes?"
            ),
            f"{fraction.numerator}/{fraction.denominator}",
            (
                "A conditional relative frequency uses the relevant row total as the denominator.",
                f"The row total is {yes} + {no} = {total}.",
            ),
            {"DATA.TWOWAY.USE_NO": f"{Fraction(no, total)}"},
        )

    if family_code == "MATH.PROB.EXPERIMENTAL":
        trials = rng.choice([20, 30, 40, 50, 60])
        successes = rng.randint(3, trials - 3)
        probability = Fraction(successes, trials)
        return (
            (
                f"An event occurred {successes} times in {trials} trials. "
                "What is the experimental probability?"
            ),
            f"{probability.numerator}/{probability.denominator}",
            (
                "Experimental probability is observed successes divided by total trials.",
                f"Use {successes}/{trials} and simplify.",
            ),
            {"PROB.EXPERIMENTAL.REVERSE": f"{Fraction(trials, successes)}"},
        )

    if family_code == "MATH.PROB.EXPECTED_COUNT":
        denominator = rng.choice([2, 4, 5, 10])
        numerator = rng.randint(1, denominator - 1)
        trials = denominator * rng.randint(8, 20)
        expected = trials * numerator // denominator
        return (
            (
                f"An event has probability {numerator}/{denominator}. "
                f"About how many times should it occur in {trials} trials?"
            ),
            str(expected),
            (
                "Expected count is probability multiplied by number of trials.",
                f"Compute {numerator}/{denominator} × {trials}.",
            ),
            {"PROB.EXPECTED.ADD_DENOMINATOR": str(expected + denominator)},
        )

    if family_code == "MATH.PROB.THEORY.VS_EXPERIMENT":
        theoretical = Fraction(1, rng.choice([2, 4, 5]))
        trials = theoretical.denominator * rng.randint(10, 20)
        expected = trials * theoretical.numerator // theoretical.denominator
        observed = expected + rng.choice([-2, -1, 1, 2])
        experimental = Fraction(observed, trials)
        return (
            (
                f"The theoretical probability is {theoretical}. In {trials} trials, "
                f"the event occurred {observed} times. Which statement is correct? "
                "(A) Experimental probability can differ from theoretical probability, "
                "especially in a finite sample. "
                "(B) The experiment is invalid unless the probabilities are exactly equal. "
                "(C) Theoretical probability must be replaced by the experimental result. "
                "(D) A probability model guarantees an exact count in every experiment."
            ),
            "A",
            (
                f"The experimental probability here is {experimental}.",
                "Random variation means observed relative frequency need not equal theory exactly.",
            ),
            {"PROB.THEORY.EXACT_COUNT": "D", "PROB.THEORY.REJECT_MODEL": "B"},
        )

    raise ValueError(f"No bivariate/sampling builder for family: {family_code}")
