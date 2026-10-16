"""Seed extension (challenge-tier) problems for the middle-grade curricula.

Extension problems are opt-in stretch items: authored above each skill's
normal band, tagged extension_eligible so attempts stay out of mastery
evidence. Idempotent — keyed on (skill, prompt) like the other seeders.
"""

from sqlalchemy import select

from app.content_models import ProblemContentMetadata
from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill

MCPS_SOURCE = "https://www.montgomeryschoolsmd.org/curriculum/math/ms/"

# (skill_code, prompt, answer, difficulty, problem_type, answer_kind, objective)
EXTENSIONS: dict[str, dict[str, list[tuple[str, str, str, int, str, str, str]]]] = {
    "MCPS_MATH_6": {
        "M6.RP.RATIO": [
            (("A recipe uses flour to sugar in the ratio 5:2. You triple the recipe, "
             "then add 1 extra cup of flour for a total of 16 cups of flour. "
             "How many cups of sugar are in the recipe?"), "6", 7, "WORD_PROBLEM",
             "INTEGER", "Stretch: adjust a scaled ratio before reading the other part."),
            (("The ratio of cats to dogs at a shelter is 3:4. After 2 more cats arrive, "
             "the ratio becomes 7:8. How many cats were there at first?"), "12", 8,
             "WORD_PROBLEM", "INTEGER", "Stretch: ratio shift under an additive change."),
        ],
        "M6.RP.UNIT_RATE": [
            (("A 12-ounce juice costs $3.00 and a 20-ounce juice costs $4.60. "
             "How many cents per ounce cheaper is the larger juice?"), "2", 6,
             "WORD_PROBLEM", "INTEGER", "Stretch: compare two unit rates."),
            (("Car A travels 180 miles on 6 gallons. Car B travels 240 miles on "
             "10 gallons. How many more miles per gallon does Car A get?"), "6", 6,
             "WORD_PROBLEM", "INTEGER", "Stretch: unit-rate comparison of two cars."),
        ],
        "M6.NS.FRACTION": [
            ("How many 3/4-cup servings are in 5 1/4 cups of rice?", "7", 6,
             "WORD_PROBLEM", "INTEGER", "Stretch: divide by a fraction from a mixed number."),
            ("A rope is 8 1/4 feet long. How many 3/4-foot pieces can be cut from it?",
             "11", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: measurement division with a mixed number."),
        ],
        "M6.EE.EXPR": [
            ("Evaluate 2x^2 + 3x - 5 when x = 4.", "39", 6, "SIMPLIFY_EXPRESSION",
             "INTEGER", "Stretch: evaluate a quadratic-style expression."),
            ("The expression 3(2x + 4) - 2x simplifies to ax + b. What is a + b?",
             "16", 7, "SIMPLIFY_EXPRESSION", "INTEGER",
             "Stretch: simplify, then extract and combine coefficients."),
        ],
        "M6.EE.EQUATION": [
            ("Solve for x: 3x + 7 = 2x + 19.", "12", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: variable on both sides."),
            (("A rectangle's perimeter is 34 units and its length is 3 more than "
             "its width. What is the width?"), "7", 7, "WORD_PROBLEM",
             "INTEGER", "Stretch: build and solve an equation from perimeter."),
        ],
        "M6.SP.STAT": [
            (("Four numbers have a mean of 10. Three of them are 6, 9, and 14. "
             "What is the fourth number?"), "11", 6, "WORD_PROBLEM",
             "INTEGER", "Stretch: work backward from a mean."),
            (("A data set has 7 ordered numbers and a median of 12. If the three "
             "smallest values each increase by 2, does the median change? "
             "Answer yes or no."), "no", 7, "WORD_PROBLEM", "FREE_TEXT",
             "Stretch: reason about which order statistic the median protects."),
        ],
        "M6.G.GEO": [
            (("A triangle has base 10 units and area 35 square units. What is its "
             "height?"), "7", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: invert the area formula."),
            (("The distance between (2, 5) and (2, k) is 9 units. If k > 5, "
             "what is k?"), "14", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: solve for a coordinate from a distance."),
        ],
    },
    "MCPS_MATH_7": {
        "M7.RP.PROP.RATE": [
            (("Three identical printers together print 120 pages in 4 minutes. "
             "How many pages per minute does one printer print?"), "10", 6,
             "WORD_PROBLEM", "INTEGER", "Stretch: unit rate through a combined rate."),
            (("A proportional relationship y = kx passes through (6, 15). "
             "What is y when x = 10?"), "25", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: recover the constant, then evaluate."),
        ],
        "M7.RP.PERCENT.OF": [
            (("A jacket is discounted 30%, then the sale price is discounted "
             "another 20%. What is the final price of a $100 jacket in dollars?"),
             "56", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: successive percent changes multiply, not add."),
            (("A price is raised 10%, then lowered 10%. What is the final price "
             "of a $200 item in dollars?"), "198", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: symmetric percent changes do not cancel."),
        ],
        "M7.EE.EXPR.DIST": [
            ("Expand and simplify: 4(2x - 3) - (x - 7).", "7x - 5", 6,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: distribute across two grouped terms."),
            ("Factor completely: 12x + 18.", "6(2x + 3)", 6, "SIMPLIFY_EXPRESSION",
             "FREE_TEXT", "Stretch: extract the greatest common factor."),
        ],
        "M7.EE.EXPR.COMBINE": [
            ("Simplify: 5x - 2(x + 4) + 7.", "3x - 1", 6, "SIMPLIFY_EXPRESSION",
             "FREE_TEXT", "Stretch: combine like terms through a negative factor."),
            ("Simplify: -2(x - 5) + 3(2x - 1).", "4x + 7", 7, "SIMPLIFY_EXPRESSION",
             "FREE_TEXT", "Stretch: two distributions with sign care."),
        ],
        "M7.EE.EQUATION.ONE": [
            ("Solve for x: x/4 + 3 = 9.", "24", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: undo a quotient, then a sum."),
            ("Solve for x: -2x + 5 = -11.", "8", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: signed coefficients on both sides of the step."),
        ],
        "M7.EE.EQUATION.TWO": [
            ("Solve for x: 5x - 3 = 2x + 12.", "5", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: collect variable terms across the equals sign."),
            ("Solve for x: 2(x + 4) = 3x - 1.", "9", 8, "SOLVE_EQUATION", "INTEGER",
             "Stretch: distribute before collecting variable terms."),
        ],
        "M7.G.SOLID": [
            (("A cube has edge length 5 cm. What is its surface area in square "
             "centimeters?"), "150", 6, "SOLID_VOLUME", "INTEGER",
             "Stretch: surface area from a single edge."),
            (("A cylinder has volume 100π cubic cm and radius 5 cm. What is its "
             "height in cm?"), "4", 8, "SOLID_VOLUME", "INTEGER",
             "Stretch: invert V = πr^2h."),
        ],
        "M7.G.GEO": [
            (("A circle has circumference 20π units. What is its area? "
             "Write your answer like 100π."), "100π", 7, "WORD_PROBLEM", "FREE_TEXT",
             "Stretch: circumference to radius to area."),
            (("Two complementary angles are in the ratio 2:3. How many degrees is "
             "the larger angle?"), "54", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: split 90 degrees by a ratio."),
        ],
        "M7.SP.PROB": [
            (("A bag holds 4 red, 5 blue, and 3 green marbles. Two marbles are "
             "drawn without replacement. What is the probability both are blue? "
             "Write as a fraction."), "5/33", 8, "PROBABILITY", "FRACTION",
             "Stretch: compound probability without replacement."),
            (("Two fair dice are rolled. What is the probability the sum is 7? "
             "Write as a fraction."), "1/6", 6, "PROBABILITY", "FRACTION",
             "Stretch: enumerate the 36-outcome sample space."),
        ],
        "M7.RP.GRAPH": [
            ("A line passes through (0, 3) and (4, 11). What is its slope?",
             "2", 6, "PROPORTIONAL_GRAPH", "INTEGER",
             "Stretch: slope from two points."),
            (("Does the point (5, 13) lie on the line y = 3x - 2? "
             "Answer yes or no."), "yes", 6, "PROPORTIONAL_GRAPH", "FREE_TEXT",
             "Stretch: test a point against a linear rule."),
        ],
        "M7.NS.RAT": [
            ("Compute: (-3/4) / (9/8). Write as a fraction.", "-2/3", 7,
             "SIGNED_NUMBERS", "FRACTION",
             "Stretch: signed fraction division with reduction."),
            ("Evaluate: (-2)^3 + (-3)^2.", "1", 7, "SIGNED_NUMBERS", "INTEGER",
             "Stretch: signs and exponents together."),
        ],
    },
    "MCPS_MATH_8": {
        "M8.ALG.INVERSE.ADD": [
            ("Solve for x: x - (-7) = -3.", "-10", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: subtracting a negative flips the sign."),
            ("Solve for x: x + 9 = -14 + 3.", "-20", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: simplify the right side before undoing."),
        ],
        "M8.ALG.INVERSE.MULT": [
            ("Solve for x: (2/3)x = -8.", "-12", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: multiply by the reciprocal of a fraction coefficient."),
            ("Solve for x: -(3/4)x = 9.", "-12", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: reciprocal of a negated fraction coefficient."),
        ],
        "M8.ALG.DIST.POS": [
            ("Solve for x: 4(x + 3) - 2x = 30.", "9", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute, then combine like terms."),
            ("Solve for x: 2(3x - 1) + x = 5(x + 2).", "6", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute and collect on both sides."),
        ],
        "M8.ALG.DIST.NEG": [
            ("Solve for x: -2(3x - 4) = -10.", "3", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: distribute a negative factor."),
            ("Solve for x: -3(2x + 1) + 5x = -21.", "18", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: negative distribution leaves one clean term."),
        ],
        "M8.ALG.MULTI_STEP.COMBINE": [
            ("Solve for x: 3(x - 2) + 4 = 2(x + 5).", "12", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute on both sides, then collect."),
            ("Solve for x: 4(2x - 3) = 2(3x + 1) + 6.", "10", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: two distributions plus a stray constant."),
        ],
        "M8.PROB.MARBLE_QA": [
            (("A bag has 3 red and 2 blue marbles. You draw 2 without replacement. "
             "What is the probability they are the same color? Write as a fraction."),
             "2/5", 8, "PROBABILITY", "FRACTION",
             "Stretch: union of two compound paths."),
            (("A bag has 2 red, 3 blue, and 5 green marbles. Without replacement, "
             "what is P(blue first, then red)? Write as a fraction."), "1/15", 8,
             "PROBABILITY", "FRACTION",
             "Stretch: ordered compound path without replacement."),
        ],
    },
}


def _extension_problem(
    db,
    curriculum: Curriculum,
    skill: Skill,
    prompt: str,
    answer: str,
    difficulty: int,
    problem_type: str,
    answer_kind: str,
    objective: str,
    source_uri: str,
) -> None:
    provenance = {
        "origin": "AUTHORED",
        "author": "AI Tutor curriculum team",
        "license": "proprietary",
        "tier": "extension",
        "source_uri": source_uri,
    }
    problem = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    )
    if problem is None:
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type=problem_type,
            difficulty=difficulty,
            prompt=prompt,
            canonical_answer=answer,
            answer_kind=answer_kind,
            solution={"answer": answer, "provenance": provenance},
            source_type="CURATED",
        )
        db.add(problem)
        db.flush()
    else:
        prior = (problem.solution or {}).get("provenance") or {}
        if prior.get("tier") == "extension" and not prior.get("source_uri"):
            problem.solution = {
                **(problem.solution or {}),
                "provenance": {**prior, "source_uri": source_uri},
            }

    metadata = db.scalar(
        select(ProblemContentMetadata).where(
            ProblemContentMetadata.problem_id == problem.id
        )
    )
    if metadata is None:
        db.add(
            ProblemContentMetadata(
                problem_id=problem.id,
                curriculum_id=curriculum.id,
                objective=objective,
                evaluation_type="EXACT",
                extension_eligible=True,
            )
        )
    elif not metadata.extension_eligible:
        raise ValueError(
            f"Problem {problem.id} already exists with extension_eligible=False; "
            "refusing to quietly retag evidence content"
        )


def seed() -> None:
    written = 0
    with SessionLocal() as db:
        for curriculum_code, by_skill in EXTENSIONS.items():
            curriculum = db.scalar(
                select(Curriculum).where(Curriculum.code == curriculum_code)
            )
            if curriculum is None:
                raise ValueError(f"Curriculum {curriculum_code} not seeded")
            for skill_code, problems in by_skill.items():
                skill = db.scalar(
                    select(Skill).where(
                        Skill.curriculum_id == curriculum.id,
                        Skill.code == skill_code,
                    )
                )
                if skill is None:
                    raise ValueError(
                        f"Skill {skill_code} missing in {curriculum_code}"
                    )
                for prompt, answer, difficulty, ptype, akind, objective in problems:
                    _extension_problem(
                        db, curriculum, skill, prompt, answer, difficulty,
                        ptype, akind, objective, MCPS_SOURCE,
                    )
                    written += 1
        db.commit()
    print(f"Seeded {written} extension problems across {len(EXTENSIONS)} curricula")


if __name__ == "__main__":
    seed()
