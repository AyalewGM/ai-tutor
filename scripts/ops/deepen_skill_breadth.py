"""Attach pedagogically-adjacent problem types to type-thin skills.

Generation variety is bounded by the set of problem types a skill already
carries: ``generate_problem`` draws only from types present on the skill.
Seeding one generated problem of each *companion* type therefore unlocks an
entire new shape of practice for that skill — and the normal warm pass
deepens it afterwards.

The companion map is deliberately conservative: only pairings that are
pedagogically adjacent at the skill's curriculum grade are attached
(``MIN_GRADE`` guards). Strands with no principled generator today
(data/probability, graphs) are left alone rather than padded with
off-target items. A secondary ``WORD_PROBLEM``-only skill gets companions
chosen by its strand code/name, not by the type alone.

Idempotent: a companion type already present on the skill is skipped.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import random

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill
from app.services.problem_generation import GENERATORS, generate_problem


class Companion(NamedTuple):
    problem_type: str
    min_grade: int


# existing type -> adjacent types at the same content grain.
COMPANION_TYPES: dict[str, list[Companion]] = {
    # Early arithmetic <-> same-range word problems.
    "ADDITION_WITHIN_20": [Companion("SUBTRACTION_WITHIN_20", 1), Companion("WORD_PROBLEM_ADD_SUB_20", 1)],
    "SUBTRACTION_WITHIN_20": [Companion("ADDITION_WITHIN_20", 1), Companion("WORD_PROBLEM_ADD_SUB_20", 1)],
    "ADDITION_WITHIN_100": [Companion("SUBTRACTION_WITHIN_100", 2), Companion("WORD_PROBLEM_ADD_SUB_100", 2)],
    "SUBTRACTION_WITHIN_100": [Companion("ADDITION_WITHIN_100", 2), Companion("WORD_PROBLEM_ADD_SUB_100", 2)],
    "WORD_PROBLEM_ADD_SUB_20": [Companion("ADDITION_WITHIN_20", 1), Companion("SUBTRACTION_WITHIN_20", 1)],
    "WORD_PROBLEM_ADD_SUB_100": [Companion("ADDITION_WITHIN_100", 2), Companion("SUBTRACTION_WITHIN_100", 2)],
    # Multiplication/division within 100.
    "MULTIPLICATION_WITHIN_100": [Companion("DIVISION_WITHIN_100", 3), Companion("WORD_PROBLEM_MULTIPLY_DIVIDE_100", 3)],
    "DIVISION_WITHIN_100": [Companion("MULTIPLICATION_WITHIN_100", 3), Companion("WORD_PROBLEM_MULTIPLY_DIVIDE_100", 3)],
    "WORD_PROBLEM_MULTIPLY_DIVIDE_100": [Companion("MULTIPLICATION_WITHIN_100", 3), Companion("DIVISION_WITHIN_100", 3)],
    "EQUAL_GROUPS": [Companion("EQUAL_SHARING", 2), Companion("WORD_PROBLEM_MULTIPLY_DIVIDE_100", 3)],
    "EQUAL_SHARING": [Companion("EQUAL_GROUPS", 2), Companion("WORD_PROBLEM_MULTIPLY_DIVIDE_100", 3)],
    "EQUATION_BALANCE": [Companion("ADDITION_WITHIN_20", 1), Companion("SUBTRACTION_WITHIN_20", 1)],
    "MONEY_COUNT": [Companion("WORD_PROBLEM_ADD_SUB_100", 2)],
    "COMPARE_LENGTH": [Companion("WORD_PROBLEM_ADD_SUB_20", 2)],
    "COMPARE_NUMBERS": [Companion("PLACE_VALUE_BASE_TEN", 1)],
    "PLACE_VALUE_BASE_TEN": [Companion("COMPARE_NUMBERS", 1), Companion("ROUNDING", 3)],
    # Time, shapes, patterns.
    "TIME_TO_HOUR_HALF_HOUR": [Companion("TIME_TO_5_MINUTES", 2), Companion("ELAPSED_TIME", 3)],
    "TIME_TO_5_MINUTES": [Companion("ELAPSED_TIME", 3)],
    "CLASSIFY_SHAPE": [Companion("GEOMETRY_SHAPES", 1)],
    "GEOMETRY_SHAPES": [Companion("CLASSIFY_SHAPE", 1)],
    "NUMBER_PATTERN": [Companion("NUMBER_SEQUENCE", 3)],
    "NUMBER_SEQUENCE": [Companion("NUMBER_PATTERN", 3)],
    "MULTI_DIGIT_MULTIPLICATION": [Companion("LONG_DIVISION", 4)],
    "LONG_DIVISION": [Companion("MULTI_DIGIT_MULTIPLICATION", 4)],
    "DECIMAL_PLACE_VALUE": [Companion("DECIMAL_OPERATIONS", 4)],
    "RECTANGLE_AREA": [Companion("AREA_PERIMETER_RECTANGLE", 4)],
    "VOLUME": [Companion("RECTANGLE_AREA", 5)],
    # Fractions.
    "FRACTION_HALVES_THIRDS_FOURTHS": [Companion("UNIT_FRACTION", 2), Companion("FRACTION_EQUIVALENCE", 3)],
    "UNIT_FRACTION": [Companion("FRACTION_EQUIVALENCE", 3), Companion("FRACTION_NUMBER_LINE", 3)],
    "FRACTION_EQUIVALENCE": [Companion("FRACTION_COMPARE", 3), Companion("FRACTION_NUMBER_LINE", 3)],
    "FRACTION_COMPARE": [Companion("FRACTION_EQUIVALENCE", 3)],
    "FRACTION_NUMBER_LINE": [Companion("FRACTION_EQUIVALENCE", 3)],
    "FRACTION_ADD_SUBTRACT_LIKE": [Companion("ADD_SUBTRACT_UNLIKE_FRACTIONS", 4)],
    "FRACTION_OPERATIONS": [Companion("ADD_SUBTRACT_UNLIKE_FRACTIONS", 5), Companion("MULTIPLY_FRACTIONS", 5), Companion("DIVIDE_FRACTIONS", 6)],
    "FRACTION_SUBTRACT": [Companion("FRACTION_OPERATIONS", 5)],
    "MULTIPLY_FRACTION_BY_WHOLE": [Companion("MULTIPLY_FRACTIONS", 4)],
    "MULTIPLY_FRACTIONS": [Companion("DIVIDE_FRACTIONS", 6)],
    # Secondary algebra / number.
    "SOLVE_EQUATION": [Companion("ALGEBRA_WORD_PROBLEM", 7)],
    "ALGEBRA_WORD_PROBLEM": [Companion("SOLVE_EQUATION", 7)],
    "SIMPLIFY_EXPRESSION": [Companion("COMBINE_LIKE_TERMS", 6)],
    "COMBINE_LIKE_TERMS": [Companion("SIMPLIFY_EXPRESSION", 6)],
    "LINEAR_RELATION": [Companion("LINEAR_FUNCTION", 8)],
    "LINEAR_FUNCTION": [Companion("LINEAR_RELATION", 8)],
    "ARITHMETIC": [Companion("INTEGER_OPERATIONS", 6), Companion("FRACTION_OPERATIONS", 6)],
    "INTEGER_OPERATIONS": [Companion("ARITHMETIC", 6)],
    "POLYNOMIAL_ADD_SUBTRACT": [Companion("COMBINE_LIKE_TERMS", 8)],
}

_EQUATION_STRANDS = re.compile(r"\.(EE|PFA|ALG|AT)\.|EQUATION|LINEAR")
_RATE_STRANDS = re.compile(r"\.RP\.|RATIO|PERCENT|PROPORTIONAL|RATE")
_NUMBER_STRANDS = re.compile(r"\.(NS|CE|NF)\.")
_GEOMETRY_STRANDS = re.compile(r"\.(MG|G)\.|GEOMETR", re.IGNORECASE)


def _grade_number(grade_level: str | None) -> int:
    """Curriculum grade as a number; high-school courses -> 9."""
    if not grade_level:
        return 1
    if grade_level.strip().isdigit():
        return int(grade_level.strip())
    return 9  # Algebra I / Integrated Algebra I / similar


def _word_problem_companions(skill: Skill, grade: int) -> list[str]:
    """Companion types for a secondary WORD_PROBLEM-only skill, by strand.

    Generic WORD_PROBLEM generation covers percent-of and unit-rate; the
    companion depends on what the skill actually teaches.
    """
    label = f"{skill.code} {(skill.name or '')}".upper()
    if _EQUATION_STRANDS.search(label):
        return [t for t, g in (("SOLVE_EQUATION", 6), ("ALGEBRA_WORD_PROBLEM", 7)) if grade >= g]
    if _RATE_STRANDS.search(label):
        # Unit-rate and percent word problems reduce to one-step equations.
        return ["SOLVE_EQUATION"] if grade >= 6 else []
    if _NUMBER_STRANDS.search(label):
        if "FRACTION" in label:
            return ["FRACTION_OPERATIONS"] if grade >= 5 else []
        return ["INTEGER_OPERATIONS"] if grade >= 6 else []
    if _GEOMETRY_STRANDS.search(label):
        return ["AREA_PERIMETER_RECTANGLE"] if grade >= 3 else []
    if ".FIN" in label:
        return ["DECIMAL_OPERATIONS"] if grade >= 4 else []
    return []  # DS/SP/probability strands: no principled generator today


def _companions_for(types: set[str], skill: Skill, grade: int) -> list[str]:
    out: list[str] = []
    for t in sorted(types):
        if t == "WORD_PROBLEM":
            out.extend(_word_problem_companions(skill, grade))
            continue
        for companion in COMPANION_TYPES.get(t, []):
            if grade >= companion.min_grade:
                out.append(companion.problem_type)
    seen: set[str] = set()
    return [t for t in out if t in GENERATORS and t not in types and not (t in seen or seen.add(t))]


def seed() -> None:
    """Attach companion types to skills carrying <= 2 distinct types."""
    rng = random.Random(20261002)
    with SessionLocal() as db:
        rows = db.execute(
            select(Skill, Curriculum)
            .join(Curriculum, Curriculum.id == Skill.curriculum_id)
            .where(~Curriculum.code.like("F009_%"), ~Skill.code.like("TEST.%"))
            .order_by(Curriculum.code, Skill.code)
        ).all()

        attached = skipped = 0
        for skill, curriculum in rows:
            types = set(
                db.scalars(
                    select(Problem.problem_type)
                    .where(Problem.primary_skill_id == skill.id)
                    .distinct()
                ).all()
            )
            if not types or len(types) > 2:
                continue
            grade = _grade_number(curriculum.grade_level)
            # Companions can chain (WORD_PROBLEM -> SOLVE_EQUATION ->
            # ALGEBRA_WORD_PROBLEM): iterate to a fixed point so a single
            # run reaches the full transitive closure and a second run is
            # a true no-op.
            difficulty = max(1, min(5, skill.difficulty_level or 2))
            companions = _companions_for(types, skill, grade)
            if not companions:
                skipped += 1
                continue
            for _ in range(4):
                added_any = False
                for companion in companions:
                    if generate_problem(
                        db, skill_id=skill.id, difficulty=difficulty,
                        problem_type=companion, rng=rng,
                    ) is not None:
                        types.add(companion)
                        attached += 1
                        added_any = True
                if not added_any:
                    break
                companions = _companions_for(types, skill, grade)
                if not companions:
                    break
        db.commit()
        print(
            f"[deepen] {attached} companion types attached; {skipped} "
            "type-thin skills had no principled companion (left untouched)"
        )


if __name__ == "__main__":
    seed()
