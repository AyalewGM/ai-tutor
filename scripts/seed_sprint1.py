from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
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
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        if curriculum is None:
            curriculum = Curriculum(
                code="MCPS_MATH_8",
                name="MCPS Grade 8 Mathematics",
                jurisdiction="Montgomery County, Maryland",
                grade_level="8",
            )
            db.add(curriculum)
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

        misconception = db.scalar(
            select(Misconception).where(Misconception.code == "DIST_001")
        )
        if misconception is None:
            db.add(
                Misconception(
                    skill_id=distributive.id,
                    code="DIST_001",
                    name="Partial distribution",
                    description=(
                        "The learner multiplies the outside factor by only one term "
                        "inside parentheses."
                    ),
                    remediation_strategy=(
                        "Represent the outside factor as multiplying each term separately "
                        "before simplifying."
                    ),
                )
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
