"""Original canonical triangle-congruence reasoning families.

These tasks address a shared high-school geometry content gap. They are not
claims that any jurisdiction's standards have been fully mapped or reviewed.
Mathematical decisions are deterministic; no learner or jurisdiction data.
"""

from __future__ import annotations

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(code: str, name: str, *dimensions: str) -> ProblemFamilySpec:
    return ProblemFamilySpec(
        code,
        name,
        "MATH.GEO.CONGRUENCE",
        "GEOMETRY_REASONING",
        2,
        4,
        ALL_MODES,
        frozenset(dimensions),
    )


FAMILIES = {
    "MATH.GEO.CONGRUENCE.SSS": _spec(
        "MATH.GEO.CONGRUENCE.SSS",
        "Determine whether three corresponding side lengths prove congruence",
        "reasoning", "congruence_criteria", "misconception_probe",
    ),
    "MATH.GEO.CONGRUENCE.SAS": _spec(
        "MATH.GEO.CONGRUENCE.SAS",
        "Distinguish included and nonincluded angles in congruence",
        "reasoning", "congruence_criteria", "representation",
    ),
    "MATH.GEO.CONGRUENCE.ASA_AAS": _spec(
        "MATH.GEO.CONGRUENCE.ASA_AAS",
        "Identify ASA versus AAS from the position of a known side",
        "reasoning", "congruence_criteria", "representation",
    ),
    "MATH.GEO.CONGRUENCE.HL": _spec(
        "MATH.GEO.CONGRUENCE.HL",
        "Use hypotenuse-leg reasoning for right triangles",
        "reasoning", "congruence_criteria", "misconception_probe",
    ),
    "MATH.GEO.CONGRUENCE.SSA": _spec(
        "MATH.GEO.CONGRUENCE.SSA",
        "Recognize that SSA generally does not guarantee congruence",
        "reasoning", "counterexample", "congruence_criteria",
    ),
    "MATH.GEO.CONGRUENCE.CPCTC": _spec(
        "MATH.GEO.CONGRUENCE.CPCTC",
        "Infer a corresponding side from a stated triangle congruence",
        "reasoning", "correspondence", "transfer",
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.GEO.CONGRUENCE.SSS":
        a = rng.randint(4, 8 + difficulty)
        b = rng.randint(5, 9 + difficulty)
        c = rng.randint(abs(a - b) + 2, a + b - 2)
        all_three = rng.choice((True, False))
        other_c = c if all_three else c + 1
        return (
            (
                f"Triangle A has side lengths {a}, {b}, {c}. Triangle B has "
                f"corresponding side lengths {a}, {b}, {other_c}. "
                "Do these corresponding side lengths prove the triangles congruent by SSS? "
                "Answer yes or no."
            ),
            "yes" if all_three else "no",
            (
                "SSS requires equality of all three pairs of corresponding sides.",
                "Check the third side, not just the first two.",
            ),
            {
                "GEO.CONGRUENCE.SSS.TWO_SIDES_SUFFICE": "no" if all_three else "yes",
            },
        )
    if family_code == "MATH.GEO.CONGRUENCE.SAS":
        a = rng.randint(5, 8 + difficulty)
        b = a + rng.randint(1, 3)
        angle = rng.choice((25, 30, 35))
        included = rng.choice((True, False))
        position = (
            f"the {angle} degree angle between those two sides"
            if included
            else f"a {angle} degree angle opposite the side of length {a}"
        )
        return (
            (
                f"Two triangles each have corresponding sides of lengths {a} and {b}, "
                f"and each has {position}. Does the stated information guarantee "
                "congruence by SAS? Answer yes or no."
            ),
            "yes" if included else "no",
            (
                "SAS requires the known angle to lie between the two known sides.",
                "An angle opposite one of the known sides gives SSA, not SAS.",
            ),
            {"GEO.CONGRUENCE.SAS.IGNORE_INCLUDED": "no" if included else "yes"},
        )
    if family_code == "MATH.GEO.CONGRUENCE.ASA_AAS":
        angle1 = rng.randint(35, 55)
        angle2 = rng.randint(45, 65)
        side = rng.randint(4, 9 + difficulty)
        included = rng.choice((True, False))
        location = (
            "the side joining the vertices of the two given angles"
            if included
            else "a side that is not between the two given angles"
        )
        return (
            (
                f"Two triangles have matching corresponding angles of {angle1} and "
                f"{angle2} degrees and a matching corresponding side of length {side}. "
                f"The known side is {location}. Is the congruence criterion ASA or AAS?"
            ),
            "ASA" if included else "AAS",
            (
                "Both ASA and AAS guarantee triangle congruence.",
                "ASA uses the included side; AAS uses a nonincluded side.",
            ),
            {"GEO.CONGRUENCE.ASA_AAS.CONFUSE_POSITION": "AAS" if included else "ASA"},
        )
    if family_code == "MATH.GEO.CONGRUENCE.HL":
        leg = rng.randint(3, 7 + difficulty)
        hyp = leg + rng.randint(2, 7)
        same_hyp = rng.choice((True, False))
        other_hyp = hyp if same_hyp else hyp + 1
        return (
            (
                "Two right triangles have corresponding legs of length "
                f"{leg}. Their hypotenuses measure {hyp} and {other_hyp}. "
                "Does the hypotenuse-leg (HL) criterion prove them congruent? "
                "Answer yes or no."
            ),
            "yes" if same_hyp else "no",
            (
                "HL applies only to right triangles.",
                "Both the hypotenuse and one corresponding leg must match.",
            ),
            {"GEO.CONGRUENCE.HL.IGNORE_HYPOTENUSE": "no" if same_hyp else "yes"},
        )
    if family_code == "MATH.GEO.CONGRUENCE.SSA":
        a = rng.randint(7, 12 + difficulty)
        b = a + rng.randint(1, 3)
        angle = rng.choice((20, 25, 30))
        return (
            (
                f"Two triangles each have sides of length {a} and {b}, plus "
                f"a {angle} degree angle opposite the side of length {a}. "
                "Must the triangles be congruent? Answer yes or no."
            ),
            "no",
            (
                "The given angle is not included between the two sides.",
                "SSA can produce two different triangles; it is not a general congruence criterion.",
            ),
            {"GEO.CONGRUENCE.SSA.TREAT_AS_SAS": "yes"},
        )
    if family_code == "MATH.GEO.CONGRUENCE.CPCTC":
        length = rng.randint(4, 12 + difficulty * 2)
        side = rng.choice(("AB", "BC", "AC"))
        matching = {"AB": "DE", "BC": "EF", "AC": "DF"}[side]
        other = length + rng.randint(1, 4)
        return (
            (
                f"Triangle ABC is congruent to triangle DEF, in that vertex order. "
                f"If side {side} is {length} cm, how long is side {matching}? "
                "Answer with a number of centimeters."
            ),
            str(length),
            (
                "The order ABC congruent to DEF means A corresponds to D, B to E, and C to F.",
                "Corresponding parts of congruent triangles have equal measures.",
            ),
            {"GEO.CONGRUENCE.CPCTC.ADD_UNRELATED_LENGTH": str(other)},
        )
    raise ValueError(f"No triangle-congruence builder for {family_code}")
