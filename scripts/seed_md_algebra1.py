from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumSkillMapping,
    EducationAuthority,
    Jurisdiction,
)
from app.models import Curriculum, Problem, Skill
from scripts.seed_algebra1 import seed as seed_legacy_algebra1

CURRICULUM_CODE = "MD_ALGEBRA_1_2026_27"
LEGACY_CODE = "MCPS_ALGEBRA_1_2026_27"
MSDE_SOURCE = "https://www.marylandpublicschools.org/about/Pages/DCAA/Math/index.aspx"
MCPS_CONTEXT = "https://www.montgomeryschoolsmd.org/curriculum/math/"


def _authority(db):
    us = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"))
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us)
        db.flush()
    md = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id == us.id, Jurisdiction.code == "MD"))
    if md is None:
        md = Jurisdiction(
            parent_id=us.id,
            code="MD",
            name="Maryland",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=MSDE_SOURCE,
        )
        db.add(md)
        db.flush()
    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == md.id,
            EducationAuthority.code == "MSDE",
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=md.id,
            code="MSDE",
            name="Maryland State Department of Education",
            authority_type="STATE_AGENCY",
            source_uri=MSDE_SOURCE,
            provenance_json={"role": "Maryland mathematics standards authority"},
        )
        db.add(authority)
        db.flush()
    return authority


def _canonical_code(skill_code: str) -> str:
    return "MATH.ALGEBRA1." + skill_code.removeprefix("A1.").replace(".", "_")


def seed() -> None:
    # Upgrade the accepted pilot once, then operate directly on the upgraded
    # curriculum on subsequent runs. Re-running the legacy seed after its code
    # has been renamed would create a second pilot row and violate the unique
    # authority/code/version identity when that row is upgraded.
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        legacy = db.scalar(select(Curriculum).where(Curriculum.code == LEGACY_CODE))
    finally:
        db.close()

    if curriculum is None and legacy is None:
        seed_legacy_algebra1()

    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = db.scalar(select(Curriculum).where(Curriculum.code == LEGACY_CODE))
        if curriculum is None:
            raise RuntimeError("Algebra I seed did not create or locate its curriculum")

        curriculum.code = CURRICULUM_CODE
        curriculum.name = "Maryland Algebra I — revised MCCRS — SY 2026-27"
        curriculum.jurisdiction = "Maryland"
        curriculum.grade_level = "Algebra I"
        curriculum.authority_id = authority.id
        curriculum.version = "MCCRS-revised-SY2026-27"
        curriculum.source_uri = MSDE_SOURCE

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        for skill in skills:
            code = _canonical_code(skill.code)
            canonical = db.scalar(select(CanonicalSkill).where(CanonicalSkill.code == code))
            if canonical is None:
                canonical = CanonicalSkill(
                    code=code,
                    name=skill.name,
                    description=skill.description,
                    subject="MATHEMATICS",
                )
                db.add(canonical)
                db.flush()
            mapping = db.scalar(
                select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id)
            )
            if mapping is None:
                db.add(
                    CurriculumSkillMapping(
                        canonical_skill_id=canonical.id,
                        skill_id=skill.id,
                        mapping_type="EQUIVALENT",
                        provenance_json={
                            "basis": "AI Tutor reviewed Maryland Algebra I mapping",
                            "standards_authority": "Maryland State Department of Education",
                            "standards_source": MSDE_SOURCE,
                            "local_implementation_context": MCPS_CONTEXT,
                            "curriculum_code": CURRICULUM_CODE,
                            "curriculum_version": curriculum.version,
                        },
                    )
                )

        # Problems remain AI Tutor-authored; standards authority is reference
        # provenance, not a claim that MSDE or MCPS authored these prompts.
        skill_ids = [skill.id for skill in skills]
        for problem in db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))):
            solution = dict(problem.solution or {})
            provenance = dict(solution.get("provenance") or {})
            provenance.update(
                {
                    "origin": "AUTHORED",
                    "author": "AI Tutor curriculum team",
                    "license": "proprietary",
                    "standards_authority": "Maryland State Department of Education",
                    "standards_source": MSDE_SOURCE,
                    "local_implementation_context": MCPS_CONTEXT,
                }
            )
            provenance.pop("source_uri", None)
            solution["provenance"] = provenance
            problem.solution = solution

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
