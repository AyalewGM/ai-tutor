from decimal import Decimal

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import Curriculum, Misconception, Problem, Skill


def seed() -> None:
    Base.metadata.create_all(bind=engine)
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

        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        if skill is None:
            skill = Skill(
                curriculum_id=curriculum.id,
                code="M8.ALG.DIST",
                name="Distributive Property",
                description="Apply multiplication to every term inside parentheses.",
                difficulty_level=2,
                mastery_threshold=Decimal("0.850"),
            )
            db.add(skill)
            db.flush()

        misconception = db.scalar(select(Misconception).where(Misconception.code == "DIST_001"))
        if misconception is None:
            db.add(
                Misconception(
                    skill_id=skill.id,
                    code="DIST_001",
                    name="Partial distribution",
                    description="The learner multiplies the outside factor by only one term inside parentheses.",
                    remediation_strategy="Represent the outside factor as multiplying each term separately before simplifying.",
                )
            )

        existing_problem = db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id))
        if existing_problem is None:
            problems = [
                (1, "3(x+4)", "3x+12"),
                (1, "2(x+5)", "2x+10"),
                (2, "4(x-3)", "4x-12"),
                (2, "5(x+2)", "5x+10"),
                (3, "-2(x+6)", "-2x-12"),
            ]
            for difficulty, prompt, answer in problems:
                db.add(
                    Problem(
                        primary_skill_id=skill.id,
                        problem_type="SIMPLIFY_EXPRESSION",
                        difficulty=difficulty,
                        prompt=prompt,
                        canonical_answer=answer,
                        solution={"answer": answer},
                        source_type="CURATED",
                    )
                )

        db.commit()
        print(f"Seed complete. Curriculum={curriculum.id} Skill={skill.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
