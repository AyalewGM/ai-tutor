from decimal import Decimal

from sqlalchemy import select

from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.core.database import SessionLocal
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MTH1W"
AUTHORITY_CODE = "ON_MIN_ED"
SOURCE_URI = "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w"


def _skill(db, curriculum, code, name, description, level):
    skill = db.scalar(
        select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code)
    )
    if skill is None:
        skill = Skill(
            curriculum_id=curriculum.id,
            code=code,
            name=name,
            description=description,
            difficulty_level=level,
            mastery_threshold=Decimal("0.850"),
        )
        db.add(skill)
        db.flush()
    return skill


def _prerequisite(db, skill, prerequisite):
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(db, skill, difficulty, prompt, answer, problem_type):
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    )
    provenance = {
        "origin": "AUTHORED",
        "author": "AI Tutor curriculum team",
        "license": "proprietary",
        "source_uri": SOURCE_URI,
    }
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type=problem_type,
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                solution={"answer": answer, "provenance": provenance},
                source_type="CURATED",
            )
        )
    elif "provenance" not in (existing.solution or {}):
        existing.solution = {**(existing.solution or {}), "provenance": provenance}


def _expectation_pack() -> ContentPackInput:
    expectations = (
        ExpectationInput(
            source_identifier="MTH1W.B",
            title="Number",
            strand="B. Number",
            source_uri=SOURCE_URI,
        ),
        ExpectationInput(
            source_identifier="MTH1W.C",
            title="Algebra",
            strand="C. Algebra",
            source_uri=SOURCE_URI,
        ),
        ExpectationInput(
            source_identifier="MTH1W.F",
            title="Financial Literacy",
            strand="F. Financial Literacy",
            source_uri=SOURCE_URI,
        ),
    )
    mappings = (
        ExpectationSkillMappingInput("MTH1W.B", "MTH1W.B.NUM"),
        ExpectationSkillMappingInput("MTH1W.B", "MTH1W.B.NUM.INT"),
        ExpectationSkillMappingInput("MTH1W.B", "MTH1W.B.NUM.FRAC"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.ALG"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.ALG.EXPR"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.ALG.EQ1"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.ALG.EQ2"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.REL"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.REL.SLOPE"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.REL.EVAL"),
        ExpectationSkillMappingInput("MTH1W.F", "MTH1W.F.FIN"),
        ExpectationSkillMappingInput("MTH1W.F", "MTH1W.F.FIN.PCT"),
        ExpectationSkillMappingInput("MTH1W.F", "MTH1W.F.FIN.APP"),
    )
    return ContentPackInput(
        curriculum_code=CURRICULUM_CODE,
        curriculum_version="2021",
        expectations=expectations,
        mappings=mappings,
    )


def seed():
    db = SessionLocal()
    try:
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.code == CURRICULUM_CODE,
                Curriculum.version == "2021",
                Curriculum.active.is_(True),
            )
        )
        if curriculum is None:
            raise RuntimeError(
                "Active MTH1W 2021 curriculum registry entry is required; run migrations first"
            )

        number = _skill(
            db,
            curriculum,
            "MTH1W.B.NUM",
            "Number Sense and Operations",
            "Represent and operate with numbers in Grade 9 mathematical contexts.",
            1,
        )
        algebra = _skill(
            db,
            curriculum,
            "MTH1W.C.ALG",
            "Algebraic Expressions and Equations",
            "Represent relationships algebraically and solve equations.",
            2,
        )
        relations = _skill(
            db,
            curriculum,
            "MTH1W.C.REL",
            "Linear Relations",
            "Represent and reason about linear relationships in multiple forms.",
            3,
        )
        financial = _skill(
            db,
            curriculum,
            "MTH1W.F.FIN",
            "Financial Literacy",
            "Apply mathematical reasoning to practical financial decisions.",
            2,
        )

        _prerequisite(db, algebra, number)
        _prerequisite(db, relations, algebra)
        _prerequisite(db, financial, number)

        # Fine-grained subskills. Anchor skills stay in the graph; each strand's
        # anchor gates the head of its subskill chain so placement can descend
        # from a broad strand into the exact atomic skill blocking progress.
        num_int = _skill(
            db, curriculum, "MTH1W.B.NUM.INT",
            "Integer Operations",
            "Add, subtract, multiply, and divide integers with signed results.",
            1,
        )
        num_frac = _skill(
            db, curriculum, "MTH1W.B.NUM.FRAC",
            "Fraction Operations",
            "Add and subtract fractions using common denominators.",
            2,
        )
        alg_expr = _skill(
            db, curriculum, "MTH1W.C.ALG.EXPR",
            "Simplifying Algebraic Expressions",
            "Apply distribution and combine like terms to simplify expressions.",
            2,
        )
        alg_eq1 = _skill(
            db, curriculum, "MTH1W.C.ALG.EQ1",
            "One-Step Equations",
            "Solve equations of the form x + a = b and ax = b using inverse operations.",
            2,
        )
        alg_eq2 = _skill(
            db, curriculum, "MTH1W.C.ALG.EQ2",
            "Two-Step and Multi-Step Equations",
            "Solve ax + b = c and a(x + b) = c by undoing operations in reverse order.",
            3,
        )
        rel_slope = _skill(
            db, curriculum, "MTH1W.C.REL.SLOPE",
            "Slope-Intercept Form",
            "Identify slope and y-intercept and write equations in y = mx + b form.",
            3,
        )
        rel_eval = _skill(
            db, curriculum, "MTH1W.C.REL.EVAL",
            "Evaluating Linear Relations",
            "Evaluate a linear relation for a given input value.",
            3,
        )
        fin_pct = _skill(
            db, curriculum, "MTH1W.F.FIN.PCT",
            "Percent Computations",
            "Compute a percent of an amount using decimal conversion.",
            2,
        )
        fin_app = _skill(
            db, curriculum, "MTH1W.F.FIN.APP",
            "Discount and Tax Applications",
            "Apply percent reasoning to discounts, sale prices, and tax amounts.",
            3,
        )

        _prerequisite(db, num_int, number)
        _prerequisite(db, num_frac, num_int)
        _prerequisite(db, alg_expr, algebra)
        _prerequisite(db, alg_expr, num_int)
        _prerequisite(db, alg_eq1, alg_expr)
        _prerequisite(db, alg_eq2, alg_eq1)
        _prerequisite(db, rel_slope, relations)
        _prerequisite(db, rel_slope, alg_eq2)
        _prerequisite(db, rel_eval, rel_slope)
        _prerequisite(db, fin_pct, financial)
        _prerequisite(db, fin_pct, num_frac)
        _prerequisite(db, fin_app, fin_pct)

        def _misconception(skill, code, name, description, strategy):
            existing = db.scalar(
                select(Misconception).where(
                    Misconception.skill_id == skill.id,
                    Misconception.code == code,
                )
            )
            if existing is None:
                db.add(
                    Misconception(
                        skill_id=skill.id,
                        code=code,
                        name=name,
                        description=description,
                        remediation_strategy=strategy,
                    )
                )

        _misconception(
            number,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            number,
            "NUM_001",
            "Integer sum sign error",
            "The learner computes the correct magnitude for an integer sum but "
            "assigns the wrong sign to the result.",
            "Locate both addends on a number line and determine the sign of the "
            "result from the addend with the larger absolute value.",
        )
        _misconception(
            number,
            "NUM_002",
            "Integer magnitudes added instead of signed sum",
            "The learner adds the absolute values of the addends and ignores "
            "their signs.",
            "Treat the negative addend as movement left on the number line "
            "rather than as another positive amount.",
        )
        _misconception(
            algebra,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
        )
        _misconception(
            algebra,
            "EQ_001",
            "Inverse operation in wrong direction",
            "The learner applies the inverse operation in the wrong direction, "
            "for example adding the constant instead of subtracting it.",
            "Identify the operation applied to the variable and undo it with "
            "the opposite operation on both sides.",
        )
        _misconception(
            number,
            "NUM_003",
            "Fractions added across",
            "The learner adds numerators together and denominators together "
            "instead of finding a common denominator.",
            "Rewrite both fractions with a common denominator before adding "
            "the numerators.",
        )
        _misconception(
            algebra,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            algebra,
            "ALG_002",
            "Constant sign dropped",
            "The learner combines constants but drops the sign of a negative "
            "term.",
            "Attach each constant's sign to the term and combine signed "
            "constants carefully.",
        )
        _misconception(
            algebra,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            algebra,
            "EQ_002",
            "Skipped or missequenced inverse step",
            "The learner undoes one operation but skips or reorders the other "
            "inverse step, such as forgetting to divide by the coefficient.",
            "Undo operations in reverse order: remove the added constant first, "
            "then divide by the coefficient.",
        )
        _misconception(
            relations,
            "REL_001",
            "Slope and intercept swapped",
            "The learner writes the linear equation with the slope and "
            "y-intercept exchanged.",
            "Anchor the equation as y = mx + b and check which given value "
            "multiplies x and which stands alone.",
        )
        _misconception(
            relations,
            "REL_002",
            "Coefficient added to variable",
            "The learner evaluates mx as m + x instead of multiplying the "
            "slope by the input value.",
            "Substitute the input into mx as multiplication: m times x, "
            "then add b.",
        )
        _misconception(
            financial,
            "FIN_001",
            "Percent treated as a whole-number amount",
            "The learner uses the percent as a dollar amount or forgets to "
            "divide by 100.",
            "Convert the percent to a decimal by dividing by 100 before "
            "multiplying by the amount.",
        )
        _misconception(
            financial,
            "FIN_002",
            "Discount amount returned instead of final price",
            "The learner computes the discount but does not subtract it "
            "from the original price.",
            "After finding the discount amount, subtract it from the "
            "original price to get the price paid.",
        )
        _misconception(
            num_int,
            "NUM_001",
            "Integer sum sign error",
            "The learner computes the correct magnitude for an integer sum but "
            "assigns the wrong sign to the result.",
            "Locate both addends on a number line and determine the sign of the "
            "result from the addend with the larger absolute value.",
        )
        _misconception(
            num_frac,
            "NUM_003",
            "Fractions added across",
            "The learner adds numerators together and denominators together "
            "instead of finding a common denominator.",
            "Rewrite both fractions with a common denominator before adding "
            "the numerators.",
        )
        _misconception(
            alg_expr,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            alg_expr,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
        )
        _misconception(
            alg_eq1,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            alg_eq2,
            "EQ_002",
            "Skipped or missequenced inverse step",
            "The learner undoes one operation but skips or reorders the other "
            "inverse step, such as forgetting to divide by the coefficient.",
            "Undo operations in reverse order: remove the added constant first, "
            "then divide by the coefficient.",
        )
        _misconception(
            rel_slope,
            "REL_001",
            "Slope and intercept swapped",
            "The learner writes the linear equation with the slope and "
            "y-intercept exchanged.",
            "Anchor the equation as y = mx + b and check which given value "
            "multiplies x and which stands alone.",
        )
        _misconception(
            rel_eval,
            "REL_002",
            "Coefficient added to variable",
            "The learner evaluates mx as m + x instead of multiplying the "
            "slope by the input value.",
            "Substitute the input into mx as multiplication: m times x, "
            "then add b.",
        )
        _misconception(
            fin_app,
            "FIN_002",
            "Discount amount returned instead of final price",
            "The learner computes the discount but does not subtract it "
            "from the original price.",
            "After finding the discount amount, subtract it from the "
            "original price to get the price paid.",
        )

        problems = [
            (number, 1, "Evaluate -6 + 14.", "8", "ARITHMETIC"),
            (number, 2, "Evaluate 3/4 + 1/2.", "5/4", "ARITHMETIC"),
            (algebra, 1, "Simplify 4x + 3 + 2x - 5.", "6x-2", "SIMPLIFY_EXPRESSION"),
            (algebra, 1, "Solve 4x = 20.", "x=5", "SOLVE_EQUATION"),
            (algebra, 2, "Solve 3x + 4 = 19.", "x=5", "SOLVE_EQUATION"),
            (algebra, 2, "Simplify 4(x + 3).", "4x+12", "SIMPLIFY_EXPRESSION"),
            (relations, 2, "For y = 3x + 2, what is y when x = 4?", "14", "LINEAR_RELATION"),
            (relations, 3, "A line has slope 2 and y-intercept -1. Write its equation.", "y=2x-1", "LINEAR_RELATION"),
            (financial, 1, "A $80 purchase has 13% tax. What is the tax amount?", "10.40", "WORD_PROBLEM"),
            (financial, 2, "A $120 item is discounted by 25%. What is the sale price before tax?", "90", "WORD_PROBLEM"),
            # Fine-grained subskill problems, each typed to a registered generator.
            (num_int, 1, "Evaluate -8 + 15.", "7", "INTEGER_OPERATIONS"),
            (num_int, 2, "Evaluate -4 - 9.", "-13", "INTEGER_OPERATIONS"),
            (num_int, 1, "Which is greater, -4 or -9?", "-4", "INTEGER_COMPARE"),
            (num_int, 2, "Which is greater, -12 or -7?", "-7", "INTEGER_COMPARE"),
            (num_frac, 2, "Evaluate 2/3 + 1/6.", "5/6", "FRACTION_OPERATIONS"),
            (num_frac, 3, "Evaluate 5/8 + 1/4.", "7/8", "FRACTION_OPERATIONS"),
            (num_frac, 3, "Evaluate 3/4 - 1/2.", "1/4", "FRACTION_SUBTRACT"),
            (num_frac, 4, "Evaluate 5/6 - 1/3.", "1/2", "FRACTION_SUBTRACT"),
            (alg_expr, 1, "Simplify 3(x + 2).", "3x+6", "SIMPLIFY_EXPRESSION"),
            (alg_expr, 2, "Simplify 5x + 2 - 3x + 7.", "2x+9", "SIMPLIFY_EXPRESSION"),
            (alg_eq1, 1, "Solve x + 6 = 14.", "x=8", "SOLVE_EQUATION"),
            (alg_eq1, 1, "Solve 3x = 21.", "x=7", "SOLVE_EQUATION"),
            (alg_eq2, 2, "Solve 2x + 5 = 17.", "x=6", "SOLVE_EQUATION"),
            (alg_eq2, 3, "Solve 3(x - 2) = 12.", "x=6", "SOLVE_EQUATION"),
            (rel_slope, 2, "A line has slope 4 and y-intercept 3. Write its equation.", "y=4x+3", "LINEAR_FUNCTION"),
            (rel_slope, 3, "A line has slope -2 and y-intercept 5. Write its equation.", "y=-2x+5", "LINEAR_FUNCTION"),
            (rel_eval, 2, "For y = 2x + 1, what is y when x = 5?", "11", "LINEAR_FUNCTION"),
            (rel_eval, 3, "For y = -3x + 4, what is y when x = 2?", "-2", "LINEAR_FUNCTION"),
            (fin_pct, 1, "What is 15% of 80?", "12", "WORD_PROBLEM"),
            (fin_pct, 2, "What is 30% of 150?", "45", "WORD_PROBLEM"),
            (fin_app, 2, "A $60 item is discounted by 20%. What is the sale price?", "48", "WORD_PROBLEM"),
            (fin_app, 3, "A $45 meal has 13% tax. What is the tax amount?", "5.85", "WORD_PROBLEM"),
        ]
        for args in problems:
            _problem(db, *args)

        persist_expectation_pack(db, _expectation_pack())

        db.commit()
        print(f"MTH1W seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
