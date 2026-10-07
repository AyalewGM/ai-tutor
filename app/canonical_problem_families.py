"""Deterministic, curriculum-neutral Mihur mathematics problem families.

Mathematical truth lives here. Jurisdictions map standards to canonical skills;
they never fork generators, validators, hints, or misconception logic.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from enum import StrEnum


class LearningMode(StrEnum):
    DIAGNOSTIC = "DIAGNOSTIC"
    GUIDED = "GUIDED"
    INDEPENDENT = "INDEPENDENT"
    MASTERY = "MASTERY"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class GeneratedProblem:
    family_code: str
    canonical_skill_code: str
    variant_id: str
    difficulty: int
    mode: LearningMode
    problem_type: str
    prompt: str
    canonical_answer: str
    hints: tuple[str, ...]
    misconception_answers: dict[str, str]
    provenance: dict[str, str]

    def is_correct(self, answer: str) -> bool:
        return _normalize(answer) == _normalize(self.canonical_answer)

    def misconception_for(self, answer: str) -> str | None:
        normalized = _normalize(answer)
        for code, candidate in self.misconception_answers.items():
            if normalized == _normalize(candidate):
                return code
        return None


@dataclass(frozen=True)
class ProblemFamilySpec:
    code: str
    name: str
    canonical_skill_code: str
    problem_type: str
    min_difficulty: int
    max_difficulty: int
    modes: frozenset[LearningMode]
    evidence_dimensions: frozenset[str]


def _normalize(answer: str) -> str:
    return "".join(answer.lower().split()).replace("*", "")


def _rng(family_code: str, seed: str | int, difficulty: int) -> tuple[random.Random, str]:
    raw = f"{family_code}|{seed}|{difficulty}".encode()
    digest = hashlib.sha256(raw).hexdigest()
    return random.Random(int(digest[:16], 16)), digest[:16]


ALL_MODES = frozenset(LearningMode)

FAMILIES = {
    "MATH.EQ.ONE.ADD_DIRECT": ProblemFamilySpec(
        "MATH.EQ.ONE.ADD_DIRECT", "One-step additive equations",
        "MATH.EE.EQUATION.ONE", "SOLVE_EQUATION", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "inverse_operations"}),
    ),
    "MATH.EQ.TWO.DIRECT": ProblemFamilySpec(
        "MATH.EQ.TWO.DIRECT", "Two-step linear equations",
        "MATH.EE.EQUATION.TWO", "SOLVE_EQUATION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "operation_sequence"}),
    ),
    "MATH.EQ.TWO.WORD.FIXED_RATE": ProblemFamilySpec(
        "MATH.EQ.TWO.WORD.FIXED_RATE", "Fixed fee plus unit-rate modeling",
        "MATH.EE.EQUATION.TWO", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "operation_sequence"}),
    ),
    "MATH.EQ.TWO.WORD.UNKNOWN_START": ProblemFamilySpec(
        "MATH.EQ.TWO.WORD.UNKNOWN_START", "Unknown initial quantity modeling",
        "MATH.EE.EQUATION.TWO", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "representation", "inverse_operations"}),
    ),
    "MATH.EQ.TWO.WORD.COMPARISON": ProblemFamilySpec(
        "MATH.EQ.TWO.WORD.COMPARISON", "Multiplicative comparison modeling",
        "MATH.EE.EQUATION.TWO", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"reasoning", "modeling", "comparison_structure"}),
    ),
    "MATH.EQ.TWO.MODEL.FROM_CONTEXT": ProblemFamilySpec(
        "MATH.EQ.TWO.MODEL.FROM_CONTEXT", "Construct an equation from context",
        "MATH.EE.EQUATION.TWO", "MODEL_EQUATION", 2, 4, ALL_MODES,
        frozenset({"representation", "modeling", "structure_identification"}),
    ),
}


def _build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.EQ.ONE.ADD_DIRECT":
        x = rng.randint(2, 12 + difficulty * 4)
        offset = rng.randint(2, 8 + difficulty * 3)
        total = x + offset
        return (
            f"Solve x + {offset} = {total}.", f"x={x}",
            (f"Undo adding {offset} with the opposite operation.",
             f"Subtract {offset} from both sides."),
            {"EQ.INVERSE.WRONG_DIRECTION": f"x={total + offset}"},
        )
    if family_code == "MATH.EQ.TWO.DIRECT":
        x = rng.randint(2, 10 + difficulty * 3)
        coefficient = rng.randint(2, 4 + difficulty)
        offset = rng.randint(1, 5 + difficulty * 2)
        total = coefficient * x + offset
        return (
            f"Solve {coefficient}x + {offset} = {total}.", f"x={x}",
            (f"First undo the + {offset}.",
             f"Then divide both sides by {coefficient}."),
            {"EQ.SKIP.CONSTANT": f"x={total // coefficient}"},
        )
    if family_code == "MATH.EQ.TWO.WORD.FIXED_RATE":
        units = rng.randint(3, 8 + difficulty * 2)
        rate = rng.randint(2, 5 + difficulty)
        fee = rng.randint(2, 7 + difficulty)
        total = fee + rate * units
        return (
            f"A bike rental costs a fixed \${fee} fee plus \${rate} per hour. "
            f"The total bill is \${total}. How many hours was the bike rented?",
            str(units),
            (f"Represent the bill as {fee} + {rate}h = {total}.",
             f"Remove the fixed \${fee} first, then divide by {rate}."),
            {"EQ.WORD.IGNORE_FIXED_FEE": str(total // rate)},
        )
    if family_code == "MATH.EQ.TWO.WORD.UNKNOWN_START":
        start = rng.randint(4, 12 + difficulty * 3)
        groups = rng.randint(2, 5 + difficulty)
        added_each = rng.randint(2, 6 + difficulty)
        final = start + groups * added_each
        return (
            f"A reading challenge began with an unknown number of pages already read. "
            f"Then {added_each} pages were read on each of {groups} days, bringing "
            f"the total to {final} pages. How many pages had been read at the start?",
            str(start),
            (f"The unknown is the starting amount, not the daily amount.",
             f"Model it as s + {groups}({added_each}) = {final}."),
            {"EQ.WORD.CONFUSE_START_WITH_RATE": str(added_each)},
        )
    if family_code == "MATH.EQ.TWO.WORD.COMPARISON":
        base = rng.randint(3, 9 + difficulty)
        multiplier = rng.randint(2, 4 + difficulty)
        difference = rng.randint(1, 5 + difficulty)
        total = multiplier * base + difference
        return (
            f"Mina has \${difference} more than {multiplier} times the amount Kai has. "
            f"Mina has \${total}. How much money does Kai have?",
            str(base),
            (f"If Kai has k dollars, {multiplier} times that amount is {multiplier}k.",
             f"Model Mina's amount as {multiplier}k + {difference} = {total}."),
            {"EQ.WORD.ADD_BEFORE_DIVIDE": str(total // multiplier)},
        )
    coefficient = rng.randint(2, 4 + difficulty)
    fee = rng.randint(2, 7 + difficulty)
    units = rng.randint(3, 9 + difficulty)
    total = coefficient * units + fee
    return (
        f"A club charges a \${fee} registration fee and \${coefficient} for each "
        f"activity. Jordan paid \${total}. Write an equation using a for the "
        f"number of activities. Do not solve it.",
        f"{coefficient}a+{fee}={total}",
        ("Identify the repeated cost and multiply it by the unknown number of activities.",
         "Then add the one-time registration fee and set it equal to the total."),
        {
            "EQ.MODEL.SWAP_RATE_AND_FEE": f"{fee}a+{coefficient}={total}",
            "EQ.MODEL.OMIT_FIXED_FEE": f"{coefficient}a={total}",
        },
    )


def generate(
    family_code: str,
    *,
    seed: str | int,
    difficulty: int,
    mode: LearningMode = LearningMode.INDEPENDENT,
) -> GeneratedProblem:
    spec = FAMILIES[family_code]
    if not spec.min_difficulty <= difficulty <= spec.max_difficulty:
        raise ValueError("difficulty outside family range")
    if mode not in spec.modes:
        raise ValueError("learning mode is not eligible for family")
    rng, variant_id = _rng(family_code, seed, difficulty)
    prompt, answer, hints, misconceptions = _build(family_code, rng, difficulty)
    return GeneratedProblem(
        family_code=spec.code,
        canonical_skill_code=spec.canonical_skill_code,
        variant_id=variant_id,
        difficulty=difficulty,
        mode=mode,
        problem_type=spec.problem_type,
        prompt=prompt,
        canonical_answer=answer,
        hints=hints,
        misconception_answers=misconceptions,
        provenance={"origin": "MIHUR_AUTHORED", "license": "proprietary",
                    "generator": spec.code},
    )
