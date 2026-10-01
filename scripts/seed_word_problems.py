"""Seed authored word problems for algebra/equation pilot skills.

Each is a short narrative whose solution exercises the skill's core move.
FREE_TEXT answers match the canonical form the misconception rules expect.

    docker compose exec tutor-api python /app/scripts/seed_word_problems.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Problem, Skill

# (skill_code, difficulty, prompt, canonical_answer)
WORD_PROBLEMS: list[tuple[str, int, str, str]] = [
    # One-step add/subtract
    ("M8.ALG.INVERSE.ADD", 1,
     "Maya had some stickers. She bought 7 more and now has 15. How many did she start with? "
     "Write and solve x + 7 = 15.",
     "x = 8"),
    ("M8.ALG.INVERSE.ADD", 2,
     "After spending $9 on lunch, Leo has $23 left. Write and solve x - 9 = 23.",
     "x = 32"),
    ("A1.LINEAR.EQ.ONE", 1,
     "After a discount of $8, a ticket costs $6. Solve x - 8 = 6 for the original price.",
     "x = 14"),
    ("MTH1W.C.ALG.EQ1", 1,
     "A tank holds some water. After draining 12 litres, 28 litres remain. Solve x - 12 = 28.",
     "x = 40"),
    # One-step multiply/divide
    ("M8.ALG.INVERSE.MULT", 1,
     "Six friends split a $42 pizza bill equally. Solve 6x = 42 for each share.",
     "x = 7"),
    ("M8.ALG.INVERSE.MULT", 2,
     "Each row holds the same number of chairs. With x chairs per row and 3 rows filling 15 seats, "
     "solve 3x = 15.",
     "x = 5"),
    ("MTH1W.C.ALG.EQ1", 2,
     "Five identical boxes weigh 35 kg together. Solve 5x = 35 for the weight of one box.",
     "x = 7"),
    # Two-step
    ("M8.ALG.TWO_STEP", 2,
     "A gym charges a $3 sign-up fee plus $2 per week. If Sam paid $11 total, solve 2x + 3 = 11 "
     "for the number of weeks.",
     "x = 4"),
    ("M7.EE.EQUATION.TWO", 2,
     "A taxi charges a $7 pickup fee plus $5 per km. A ride cost $22 total. Solve 5x + 7 = 22 "
     "for the number of km.",
     "x = 3"),
    ("MTH1W.C.ALG.EQ2", 2,
     "A tutoring club has a $4 materials fee and charges $3 per session. Priya paid $19. "
     "Solve 3x + 4 = 19.",
     "x = 5"),
    ("A1.LINEAR.EQ.TWO", 2,
     "A phone repair costs $15 plus $4 per hour of labor. The bill was $35. Solve 4x + 15 = 35.",
     "x = 5"),
    # Distribution in context
    ("M8.ALG.DIST", 1,
     "Three gift bags each hold x candies plus 4 bonus candies. Write the total as an expression: "
     "expand 3(x + 4).",
     "3x + 12"),
    ("M8.ALG.DIST.POS", 1,
     "Four planters each grow x seedlings plus 2 spares. Expand 4(x + 2).",
     "4x + 8"),
    ("A1.EXPR.DIST", 1,
     "Each of 2 shelves holds x books plus 6 magazines. Expand 2(x + 6).",
     "2x + 12"),
    ("M7.EE.EXPR.DIST", 1,
     "Six teammates each score x points plus 1 bonus point. Expand 6(x + 1).",
     "6x + 6"),
    # Combining like terms in context
    ("M7.EE.EXPR.COMBINE", 1,
     "Jordan earned 3x points on Monday and 5x on Tuesday, then lost 2. Write 3x + 5x - 2 in "
     "simplest form.",
     "8x - 2"),
    ("A1.EXPR.COMBINE", 2,
     "A rectangle's sides are 4a and 2b; moving a hedge trims a from one side and adds 6 metres of "
     "fencing. Simplify 4a + 2b - a + 6.",
     "3a + 2b + 6"),
    ("M8.ALG.MULTI_STEP.COMBINE", 3,
     "Two pockets hold 3x and 2x marbles, totaling 20. Solve 3x + 2x = 20.",
     "x = 4"),
    # Multi-step
    ("M8.ALG.MULTI_STEP", 3,
     "Two identical bundles each contain x pencils plus 3 extras, for 14 pencils total. "
     "Solve 2(x + 3) = 14.",
     "x = 4"),
    # Slope-intercept in context
    ("MTH1W.C.REL.SLOPE", 2,
     "A plant starts 5 cm tall and shrinks 3 cm each week in winter — y = -3x + 5. "
     "Which number is the slope?",
     "-3"),
    ("A1.LINEAR.FN.SLOPE", 2,
     "A rewards card gives a $1 starting credit and earns $2 per visit. Write its balance rule "
     "in y = mx + b form (slope 2, intercept -1).",
     "y = 2x - 1"),
    # Evaluating relations
    ("MTH1W.C.REL.EVAL", 1,
     "A ride costs $3 per km minus a $2 discount: y = 3x - 2. Find the cost of a 4 km ride.",
     "y = 10"),
    ("A1.LINEAR.FN.EVAL", 1,
     "Temperature drops 2 degrees per hour from 7: f(x) = -2x + 7. Find f(-3).",
     "f(-3) = 13"),
]


def seed() -> None:
    with SessionLocal() as db:
        skills = db.scalars(
            select(Skill).where(Skill.code.in_({row[0] for row in WORD_PROBLEMS}))
        ).all()
        by_code: dict[str, list[Skill]] = {}
        for skill in skills:
            by_code.setdefault(skill.code, []).append(skill)

        created = skipped = 0
        for code, difficulty, prompt, answer in WORD_PROBLEMS:
            for skill in by_code.get(code, []):
                exists = db.scalar(
                    select(Problem.id).where(
                        Problem.primary_skill_id == skill.id,
                        Problem.prompt == prompt,
                    )
                )
                if exists:
                    skipped += 1
                    continue
                db.add(
                    Problem(
                        primary_skill_id=skill.id,
                        problem_type="WORD_PROBLEM",
                        difficulty=difficulty,
                        prompt=prompt,
                        canonical_answer=answer,
                        source_type="CURATED",
                        solution={"answer": answer, "format": "word_problem"},
                    )
                )
                created += 1
        db.commit()
        missing = {row[0] for row in WORD_PROBLEMS} - set(by_code)
        print(f"created {created} word problems, skipped {skipped} existing")
        if missing:
            print(f"no skills found for codes: {sorted(missing)}")


if __name__ == "__main__":
    seed()
