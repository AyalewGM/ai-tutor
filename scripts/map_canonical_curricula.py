from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Skill

# Explicit, reviewed mathematical equivalences. This mapping never transfers
# learner evidence; StudentSkill remains keyed to the curriculum-local Skill.
EQUIVALENCES = {
    ("MTH1W", "2021", "MTH1W.C.ALG.EXPR"): "MATH.EE.EXPR",
    ("MTH1W", "2021", "MTH1W.C.ALG.EQ1"): "MATH.EE.EQUATION.ONE",
    ("MTH1W", "2021", "MTH1W.C.ALG.EQ2"): "MATH.EE.EQUATION.TWO",
    ("MTH1W", "2021", "MTH1W.F.FIN.PCT"): "MATH.RP.PERCENT.OF",
}


def map_existing_skills(db) -> int:
    created = 0
    for (curriculum_code, version, skill_code), canonical_code in EQUIVALENCES.items():
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.code == curriculum_code,
                Curriculum.version == version,
            )
        )
        if curriculum is None:
            continue
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == skill_code,
            )
        )
        if skill is None:
            continue
        canonical = db.scalar(
            select(CanonicalSkill).where(CanonicalSkill.code == canonical_code)
        )
        if canonical is None:
            canonical = CanonicalSkill(
                code=canonical_code,
                name=skill.name,
                description=skill.description,
                subject="MATHEMATICS",
            )
            db.add(canonical)
            db.flush()
        mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == skill.id
            )
        )
        if mapping is None:
            db.add(
                CurriculumSkillMapping(
                    canonical_skill_id=canonical.id,
                    skill_id=skill.id,
                    mapping_type="EQUIVALENT",
                    provenance_json={
                        "basis": "AI Tutor reviewed mathematical equivalence",
                        "curriculum_code": curriculum.code,
                        "curriculum_version": curriculum.version,
                    },
                )
            )
            created += 1
    return created


def seed() -> None:
    db = SessionLocal()
    try:
        created = map_existing_skills(db)
        db.commit()
        print(f"Canonical cross-curriculum mappings complete. Created={created}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
