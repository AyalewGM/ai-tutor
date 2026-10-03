"""Seed authored multiple-choice problems with misconception-coded distractors.

Each distractor maps to a real misconception code from the curriculum's
misconception catalog, so a wrong click lands directly in the remediation
pipeline instead of just scoring "incorrect."

Idempotent: skips problems whose prompt already exists for the skill.

    docker compose exec tutor-api python /app/scripts/seed_mc_problems.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Problem, Skill


def _choices(*entries: tuple[str, str | None]) -> list[dict]:
    """entries: (text, misconception_code | None). Returns a–d keyed choices."""
    return [
        {"id": chr(ord("a") + i), "text": text, **({"misconception_code": code} if code else {})}
        for i, (text, code) in enumerate(entries)
    ]


# (skill_code, problem_type, difficulty, prompt, correct_id, choices)
MC_PROBLEMS: list[tuple[str, str, int, str, str, list[dict]]] = [
    # --- Distributive property ---
    (
        "M8.ALG.DIST", "DISTRIBUTE_EXPRESSION", 1, "Expand 3(x + 4).", "b",
        _choices(
            ("3x + 4", "DIST_001"),   # distributed to first term only
            ("3x + 12", None),
            ("12x", "ALG_001"),       # multiplied both parts together
            ("3x + 7", "EQ_003"),     # added instead of multiplying
        ),
    ),
    (
        "M8.ALG.DIST", "DISTRIBUTE_EXPRESSION", 2, "Expand 5(2x - 3).", "a",
        _choices(
            ("10x - 15", None),
            ("10x - 3", "DIST_001"),
            ("10x + 15", "DIST_002"),
            ("7x - 15", "ALG_001"),
        ),
    ),
    (
        "M8.ALG.DIST.POS", "DISTRIBUTE_EXPRESSION", 1, "Expand 4(x + 2).", "c",
        _choices(
            ("4x + 2", "DIST_001"),
            ("8x", "ALG_001"),
            ("4x + 8", None),
            ("x + 8", "EQ_003"),
        ),
    ),
    (
        "M8.ALG.DIST.NEG", "DISTRIBUTE_EXPRESSION", 2, "Expand -2(x + 5).", "d",
        _choices(
            ("-2x + 10", "DIST_002"),  # missed the sign flip
            ("-2x + 5", "DIST_001"),
            ("2x - 10", "DIST_002"),
            ("-2x - 10", None),
        ),
    ),
    (
        "M8.ALG.DIST.NEG", "DISTRIBUTE_EXPRESSION", 3, "Expand -(x - 7).", "a",
        _choices(
            ("-x + 7", None),
            ("-x - 7", "DIST_002"),
            ("x + 7", "DIST_002"),
            ("-x - 1", "DIST_001"),
        ),
    ),
    (
        "A1.EXPR.DIST", "DISTRIBUTE_EXPRESSION", 1, "Expand 2(x + 6).", "b",
        _choices(
            ("2x + 6", "DIST_001"),
            ("2x + 12", None),
            ("12x", "ALG_001"),
            ("x + 12", "EQ_003"),
        ),
    ),
    (
        "M7.EE.EXPR.DIST", "DISTRIBUTE_EXPRESSION", 1, "Expand 6(x + 1).", "a",
        _choices(
            ("6x + 6", None),
            ("6x + 1", "DIST_001"),
            ("7x", "ALG_001"),
            ("6x - 6", "DIST_002"),
        ),
    ),
    # --- One-step equations ---
    (
        "M8.ALG.INVERSE.ADD", "SOLVE_EQUATION", 1, "Solve x + 7 = 15.", "c",
        _choices(
            ("x = 22", "EQ_001"),     # added to both sides instead of undoing
            ("x = 9", "EQ_003"),
            ("x = 8", None),
            ("x = 2", "EQ_002"),
        ),
    ),
    (
        "M8.ALG.INVERSE.ADD", "SOLVE_EQUATION", 1, "Solve x - 4 = 9.", "a",
        _choices(
            ("x = 13", None),
            ("x = 5", "EQ_001"),
            ("x = -5", "EQ_001"),
            ("x = 36", "EQ_003"),
        ),
    ),
    (
        "M8.ALG.INVERSE.MULT", "SOLVE_EQUATION", 1, "Solve 6x = 42.", "b",
        _choices(
            ("x = 252", "EQ_003"),    # multiplied instead of dividing
            ("x = 7", None),
            ("x = 36", "EQ_001"),
            ("x = 48", "EQ_001"),
        ),
    ),
    (
        "M8.ALG.INVERSE.MULT", "SOLVE_EQUATION", 2, "Solve x ÷ 3 = 5.", "d",
        _choices(
            ("x = 2", "EQ_001"),
            ("x = 8", "EQ_001"),
            ("x = 5/3", "EQ_003"),
            ("x = 15", None),
        ),
    ),
    (
        "M7.EE.EQUATION.ONE", "SOLVE_EQUATION", 1, "Solve x + 9 = 20.", "a",
        _choices(
            ("x = 11", None),
            ("x = 29", "EQ_001"),
            ("x = 180", "EQ_003"),
            ("x = 9", "EQ_002"),
        ),
    ),
    (
        "MTH1W.C.ALG.EQ1", "SOLVE_EQUATION", 1, "Solve 5x = 35.", "c",
        _choices(
            ("x = 30", "EQ_001"),
            ("x = 175", "EQ_003"),
            ("x = 7", None),
            ("x = 40", "EQ_001"),
        ),
    ),
    (
        "A1.LINEAR.EQ.ONE", "SOLVE_EQUATION", 1, "Solve x - 8 = 6.", "b",
        _choices(
            ("x = 2", "EQ_001"),
            ("x = 14", None),
            ("x = -14", "EQ_001"),
            ("x = 48", "EQ_003"),
        ),
    ),
    # --- Two-step equations ---
    (
        "M8.ALG.TWO_STEP", "SOLVE_EQUATION", 2, "Solve 2x + 3 = 11.", "a",
        _choices(
            ("x = 4", None),
            ("x = 7", "EQ_001"),      # added 3 instead of subtracting
            ("x = 5.5", "EQ_002"),    # divided before subtracting
            ("x = 14", "EQ_001"),
        ),
    ),
    (
        "M7.EE.EQUATION.TWO", "SOLVE_EQUATION", 2, "Solve 5x - 7 = 18.", "d",
        _choices(
            ("x = 2.2", "EQ_001"),    # subtracted 7 instead of adding
            ("x = 11", "EQ_002"),     # stopped after 18 - 7, never divided
            ("x = 25", "EQ_002"),     # stopped after 18 + 7, never divided
            ("x = 5", None),
        ),
    ),
    (
        "MTH1W.C.ALG.EQ2", "SOLVE_EQUATION", 2, "Solve 3x + 4 = 19.", "b",
        _choices(
            ("x = 23/3", "EQ_001"),   # added 4 instead of subtracting
            ("x = 5", None),
            ("x = 15", "EQ_002"),     # stopped after 19 - 4, never divided
            ("x = 45", "EQ_003"),     # multiplied 15 by 3
        ),
    ),
    (
        "A1.LINEAR.EQ.TWO", "SOLVE_EQUATION", 2, "Solve 4x - 5 = 15.", "a",
        _choices(
            ("x = 5", None),
            ("x = 2.5", "EQ_002"),
            ("x = 10", "EQ_001"),
            ("x = 20", "EQ_001"),
        ),
    ),
    # --- Multi-step ---
    (
        "M8.ALG.MULTI_STEP", "SOLVE_EQUATION", 3, "Solve 2(x + 3) = 14.", "c",
        _choices(
            ("x = 10", "DIST_001"),   # 2x + 3 = 14 → forgot to distribute 3
            ("x = 11", "EQ_001"),
            ("x = 4", None),
            ("x = 7", "EQ_002"),
        ),
    ),
    # --- Combining like terms ---
    (
        "M8.ALG.MULTI_STEP.COMBINE", "COMBINE_LIKE_TERMS", 2, "Solve 3x + 2x = 20.", "b",
        _choices(
            ("x = 10", "EQ_002"),
            ("x = 4", None),
            ("x = 20/3", "EQ_003"),
            ("x = 5", "ALG_001"),
        ),
    ),
    (
        "M7.EE.EXPR.COMBINE", "COMBINE_LIKE_TERMS", 1, "Simplify 3x + 5x - 2.", "a",
        _choices(
            ("8x - 2", None),
            ("6x", "ALG_001"),        # folded the constant into the x terms
            ("8x + 2", "ALG_002"),
            ("15x - 2", "ALG_001"),
        ),
    ),
    (
        "A1.EXPR.COMBINE", "COMBINE_LIKE_TERMS", 1, "Simplify 4a + 2b - a + 6.", "d",
        _choices(
            ("11ab", "ALG_001"),
            ("4a + 2b + 5", "ALG_002"),
            ("3a + 2b - 6", "ALG_002"),
            ("3a + 2b + 6", None),
        ),
    ),
    (
        "MTH1W.C.ALG.EXPR", "COMBINE_LIKE_TERMS", 2, "Simplify 2(x + 3) + 4x.", "c",
        _choices(
            ("6x + 3", "DIST_001"),
            ("2x + 7", "ALG_001"),
            ("6x + 6", None),
            ("8x + 6", "ALG_001"),
        ),
    ),
    # --- Fractions ---
    (
        "MTH1W.B.NUM.FRAC", "FRACTION_OPERATIONS", 2, "Evaluate 1/3 + 2/8.", "b",
        _choices(
            ("3/11", "NUM_003"),      # added across numerator and denominator
            ("7/12", None),
            ("3/8", "NUM_003"),
            ("14/24", "NUM_003"),
        ),
    ),
    (
        "MTH1W.B.NUM.FRAC", "FRACTION_OPERATIONS", 2, "Evaluate 3/4 - 1/6.", "a",
        _choices(
            ("7/12", None),
            ("2/2", "NUM_003"),
            ("2/10", "NUM_003"),
            ("4/10", "NUM_003"),
        ),
    ),
    # --- Integers ---
    (
        "MTH1W.B.NUM.INT", "INTEGER_OPERATIONS", 1, "Evaluate -6 + 14.", "a",
        _choices(
            ("8", None),
            ("-8", "NUM_001"),
            ("20", "NUM_002"),        # added magnitudes ignoring sign
            ("-20", "NUM_002"),
        ),
    ),
    (
        "MTH1W.B.NUM.INT", "INTEGER_OPERATIONS", 2, "Evaluate (-3) × (-4).", "c",
        _choices(
            ("-12", "NUM_001"),
            ("-7", "NUM_002"),
            ("12", None),
            ("7", "NUM_002"),
        ),
    ),
    # --- Percent & financial ---
    (
        "M7.RP.PERCENT.OF", "WORD_PROBLEM", 2, "Find 15% of 80.", "d",
        _choices(
            ("15", "FIN_001"),        # treated % as the amount
            ("5.33", "FIN_001"),
            ("8", "FIN_001"),
            ("12", None),
        ),
    ),
    (
        "MTH1W.F.FIN.PCT", "WORD_PROBLEM", 2, "Find 40% of 250.", "a",
        _choices(
            ("100", None),
            ("40", "FIN_001"),
            ("625", "FIN_001"),
            ("10", "FIN_001"),
        ),
    ),
    (
        "MTH1W.F.FIN.APP", "WORD_PROBLEM", 3, "A $60 jacket is 25% off. What is the sale price?", "b",
        _choices(
            ("$15", "FIN_002"),       # returned the discount, not the price
            ("$45", None),
            ("$35", "FIN_001"),
            ("$75", "FIN_001"),
        ),
    ),
    # --- Unit rates ---
    (
        "M7.RP.PROP.RATE", "WORD_PROBLEM", 2, "8 granola bars cost $6. What is the unit price?", "c",
        _choices(
            ("$1.33 per bar", "DIV_SMALLER_FROM_LARGER"),
            ("$48", "EQ_003"),
            ("$0.75 per bar", None),
            ("$14 per bar", "EQ_001"),
        ),
    ),
    # --- Linear relations ---
    (
        "MTH1W.C.REL.SLOPE", "LINEAR_RELATION", 2,
        "Identify the slope and y-intercept of y = -3x + 5.", "a",
        _choices(
            ("slope = -3, intercept = 5", None),
            ("slope = 5, intercept = -3", "REL_001"),
            ("slope = 3, intercept = 5", "NUM_001"),
            ("slope = -3x, intercept = 5", "REL_002"),
        ),
    ),
    (
        "A1.LINEAR.FN.SLOPE", "LINEAR_FUNCTION", 2,
        "Write the equation of a line with slope 2 and y-intercept -1.", "d",
        _choices(
            ("y = -x + 2", "REL_001"),
            ("y = 2x + 1", "NUM_001"),
            ("x = 2y - 1", "REL_002"),
            ("y = 2x - 1", None),
        ),
    ),
    (
        "MTH1W.C.REL.EVAL", "LINEAR_RELATION", 1, "For y = 3x - 2, find y when x = 4.", "b",
        _choices(
            ("y = 14", "EQ_001"),
            ("y = 10", None),
            ("y = 34", "ALG_001"),
            ("y = 5", "EQ_002"),
        ),
    ),
    (
        "A1.LINEAR.FN.EVAL", "LINEAR_FUNCTION", 1, "Evaluate f(x) = -2x + 7 when x = -3.", "a",
        _choices(
            ("f(-3) = 13", None),
            ("f(-3) = 1", "NUM_001"),
            ("f(-3) = -1", "NUM_002"),
            ("f(-3) = -13", "NUM_001"),
        ),
    ),
]


def seed() -> None:
    with SessionLocal() as db:
        skills = db.scalars(
            select(Skill).where(Skill.code.in_({row[0] for row in MC_PROBLEMS}))
        ).all()
        by_code: dict[str, list[Skill]] = {}
        for skill in skills:
            by_code.setdefault(skill.code, []).append(skill)

        provenance = {
            "origin": "AUTHORED",
            "author": "AI Tutor curriculum team",
            "license": "proprietary",
            "source_uri": "https://www.montgomeryschoolsmd.org/curriculum/math/",
        }
        created = skipped = backfilled = 0
        for code, ptype, difficulty, prompt, correct_id, choices in MC_PROBLEMS:
            for skill in by_code.get(code, []):
                # A (skill, prompt) can hold more than one row — an authored
                # free-text problem and an MC twin — so backfill every match,
                # not just the first.
                existing = db.scalars(
                    select(Problem).where(
                        Problem.primary_skill_id == skill.id,
                        Problem.prompt == prompt,
                    )
                ).all()
                if existing:
                    for row in existing:
                        if "provenance" not in (row.solution or {}):
                            row.solution = {
                                **(row.solution or {}),
                                "provenance": provenance,
                            }
                            backfilled += 1
                    skipped += 1
                    continue
                db.add(
                    Problem(
                        primary_skill_id=skill.id,
                        problem_type=ptype,
                        difficulty=difficulty,
                        prompt=prompt,
                        canonical_answer=correct_id,
                        answer_kind="MULTIPLE_CHOICE",
                        choices=choices,
                        source_type="CURATED",
                        solution={
                            "answer": correct_id,
                            "format": "multiple_choice",
                            "provenance": provenance,
                        },
                    )
                )
                created += 1
        db.commit()
        missing = {row[0] for row in MC_PROBLEMS} - set(by_code)
        print(
            f"created {created} MC problems, skipped {skipped} existing, "
            f"backfilled provenance on {backfilled}"
        )
        if missing:
            print(f"no skills found for codes: {sorted(missing)}")


if __name__ == "__main__":
    seed()
