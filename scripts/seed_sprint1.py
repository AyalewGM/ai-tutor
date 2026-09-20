from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import (
    Curriculum,
    Misconception,
    Problem,
    Skill,
    SkillPrerequisite,
)


def _skill(db, curriculum: Curriculum, code: str, name: str, description: str, level: int) -> Skill:
    skill = db.scalar(
        select(Skill).where(
            Skill.curriculum_id == curriculum.id,
            Skill.code == code,
        )
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


def _prerequisite(db, skill: Skill, prerequisite: Skill, weight: str = "1.000") -> None:
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {
        "skill_id": skill.id,
        "prerequisite_skill_id": prerequisite.id,
    }
    if db.get(SkillPrerequisite, key) is None:
        db.add(
            SkillPrerequisite(
                skill_id=skill.id,
                prerequisite_skill_id=prerequisite.id,
                importance_weight=Decimal(weight),
            )
        )


def _problem(
    db,
    *,
    skill: Skill,
    difficulty: int,
    prompt: str,
    answer: str,
    problem_type: str,
) -> None:
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    )
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type=problem_type,
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                solution={"answer": answer},
                source_type="CURATED",
            )
        )


def seed() -> None:
    db = SessionLocal()
    try:
        mcps_authority = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == "MCPS")
        )
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        if curriculum is None:
            curriculum = Curriculum(
                code="MCPS_MATH_8",
                name="MCPS Grade 8 Mathematics",
                jurisdiction="Montgomery County, Maryland",
                grade_level="8",
                authority_id=mcps_authority.id if mcps_authority else None,
                version="1",
                source_uri=(
                    "https://www.montgomeryschoolsmd.org/curriculum/middleschool/grade8/"
                ),
            )
            db.add(curriculum)
            db.flush()
        elif mcps_authority is not None and curriculum.authority_id is None:
            curriculum.authority_id = mcps_authority.id
            curriculum.version = curriculum.version or "1"
            curriculum.source_uri = curriculum.source_uri or (
                "https://www.montgomeryschoolsmd.org/curriculum/middleschool/grade8/"
            )
            db.flush()

        inverse = _skill(
            db,
            curriculum,
            "M8.ALG.INVERSE",
            "Inverse Operations",
            "Use inverse operations to isolate a variable.",
            1,
        )
        distributive = _skill(
            db,
            curriculum,
            "M8.ALG.DIST",
            "Distributive Property",
            "Apply multiplication to every term inside parentheses.",
            2,
        )
        two_step = _skill(
            db,
            curriculum,
            "M8.ALG.TWO_STEP",
            "Two-Step Equations",
            "Solve equations that require two inverse-operation steps.",
            3,
        )
        multi_step = _skill(
            db,
            curriculum,
            "M8.ALG.MULTI_STEP",
            "Multi-Step Equations",
            "Solve equations that combine distribution and inverse operations.",
            4,
        )

        _prerequisite(db, two_step, inverse)
        _prerequisite(db, multi_step, distributive, "1.000")
        _prerequisite(db, multi_step, two_step, "0.900")

        # Fine-grained subskills: anchor skills gate each chain head so
        # placement/remediation can descend to the atomic blocker.
        inv_add = _skill(
            db, curriculum, "M8.ALG.INVERSE.ADD",
            "One-Step Add/Subtract Equations",
            "Solve x + a = b and x - a = b by undoing addition or subtraction.",
            1,
        )
        inv_mult = _skill(
            db, curriculum, "M8.ALG.INVERSE.MULT",
            "One-Step Multiply/Divide Equations",
            "Solve ax = b by undoing multiplication or division.",
            1,
        )
        dist_pos = _skill(
            db, curriculum, "M8.ALG.DIST.POS",
            "Distribution with Positive Factors",
            "Distribute a positive multiplier across a sum inside parentheses.",
            2,
        )
        dist_neg = _skill(
            db, curriculum, "M8.ALG.DIST.NEG",
            "Distribution with Signed Factors",
            "Distribute negative multipliers and subtraction inside parentheses.",
            3,
        )
        combine_eq = _skill(
            db, curriculum, "M8.ALG.MULTI_STEP.COMBINE",
            "Combining Like Terms in Equations",
            "Simplify each side by combining like terms before isolating the variable.",
            4,
        )

        _prerequisite(db, inv_add, inverse)
        _prerequisite(db, inv_mult, inv_add)
        _prerequisite(db, dist_pos, distributive)
        _prerequisite(db, dist_neg, dist_pos)
        _prerequisite(db, combine_eq, multi_step)

        def _misconception(
            skill: Skill, code: str, name: str, description: str, strategy: str
        ) -> None:
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
            distributive,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            distributive,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
        )
        _misconception(
            two_step,
            "EQ_001",
            "Inverse operation in wrong direction",
            "The learner applies the inverse operation in the wrong direction, "
            "for example adding the constant instead of subtracting it.",
            "Identify the operation applied to the variable and undo it with "
            "the opposite operation on both sides.",
        )
        _misconception(
            inverse,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            two_step,
            "EQ_002",
            "Skipped or missequenced inverse step",
            "The learner undoes one operation but skips or reorders the other "
            "inverse step, such as forgetting to divide by the coefficient.",
            "Undo operations in reverse order: remove the added constant first, "
            "then divide by the coefficient.",
        )
        _misconception(
            inv_add,
            "EQ_001",
            "Inverse operation in wrong direction",
            "The learner applies the inverse operation in the wrong direction, "
            "for example adding the constant instead of subtracting it.",
            "Identify the operation applied to the variable and undo it with "
            "the opposite operation on both sides.",
        )
        _misconception(
            inv_mult,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            dist_pos,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            dist_neg,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
        )
        _misconception(
            combine_eq,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )

        for difficulty, prompt, answer in [
            (1, "3(x+4)", "3x+12"),
            (1, "2(x+5)", "2x+10"),
            (2, "4(x-3)", "4x-12"),
            (2, "5(x+2)", "5x+10"),
            (3, "-2(x+6)", "-2x-12"),
        ]:
            _problem(
                db,
                skill=distributive,
                difficulty=difficulty,
                prompt=prompt,
                answer=answer,
                problem_type="SIMPLIFY_EXPRESSION",
            )

        for difficulty, prompt, answer in [
            (1, "Solve 3x = 12", "x=4"),
            (2, "Solve 5x = 45", "x=9"),
        ]:
            _problem(
                db,
                skill=inverse,
                difficulty=difficulty,
                prompt=prompt,
                answer=answer,
                problem_type="SOLVE_EQUATION",
            )

        for difficulty, prompt, answer in [
            (1, "x + 5 = 12", "x=7"),
            (2, "2x + 3 = 11", "x=4"),
        ]:
            _problem(
                db,
                skill=two_step,
                difficulty=difficulty,
                prompt=prompt,
                answer=answer,
                problem_type="SOLVE_EQUATION",
            )

        for difficulty, prompt, answer in [
            (2, "3(x+4)=24", "x=4"),
            (3, "4(x-2)+3=19", "x=6"),
            (4, "2(x+5)-4=18", "x=6"),
        ]:
            _problem(
                db,
                skill=multi_step,
                difficulty=difficulty,
                prompt=prompt,
                answer=answer,
                problem_type="SOLVE_EQUATION",
            )

        for skill, difficulty, prompt, answer, problem_type in [
            (inv_add, 1, "Solve x + 7 = 15.", "x=8", "SOLVE_EQUATION"),
            (inv_add, 1, "Solve x - 4 = 9.", "x=13", "SOLVE_EQUATION"),
            (inv_mult, 1, "Solve 6x = 42.", "x=7", "SOLVE_EQUATION"),
            (inv_mult, 1, "Solve 8x = 56.", "x=7", "SOLVE_EQUATION"),
            (dist_pos, 1, "Simplify 2(x + 6).", "2x+12", "SIMPLIFY_EXPRESSION"),
            (dist_pos, 2, "Simplify 5(x + 3).", "5x+15", "SIMPLIFY_EXPRESSION"),
            (dist_neg, 2, "Simplify -3(x + 4).", "-3x-12", "SIMPLIFY_EXPRESSION"),
            (dist_neg, 3, "Simplify -2(x - 5).", "-2x+10", "SIMPLIFY_EXPRESSION"),
            (combine_eq, 3, "Solve 3x + 2x = 20.", "x=4", "SOLVE_EQUATION"),
            (combine_eq, 4, "Solve 4x + 3x - 5 = 16.", "x=3", "SOLVE_EQUATION"),
        ]:
            _problem(
                db,
                skill=skill,
                difficulty=difficulty,
                prompt=prompt,
                answer=answer,
                problem_type=problem_type,
            )

        db.commit()
        print(
            "Seed complete. "
            f"Curriculum={curriculum.id} "
            f"Distributive={distributive.id} MultiStep={multi_step.id}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
