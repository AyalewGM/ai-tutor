from sqlalchemy import select

from app.content_models import CurriculumExpectation, ExpectationSkillMapping
from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_mth1w import AUTHORITY_CODE, CURRICULUM_CODE, seed
from scripts.seed_sprint1 import seed as seed_sprint1


def _seed_curricula():
    """Seed both jurisdictions so isolation tests do not depend on CI/test order."""
    seed_sprint1()
    seed()


def test_mth1w_seed_is_idempotent_and_jurisdiction_local():
    _seed_curricula()
    seed()

    db = SessionLocal()
    try:
        authority = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == AUTHORITY_CODE)
        )
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))

        assert authority is not None
        assert authority.name == "Ontario Ministry of Education"
        assert ontario is not None
        assert ontario.version == "2021"
        assert ontario.grade_level == "9"
        assert ontario.authority_id == authority.id
        assert grade8 is not None
        assert ontario.id != grade8.id

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == ontario.id)))
        seeded_skill_codes = {
            "MTH1W.B.NUM",
            "MTH1W.C.ALG",
            "MTH1W.C.REL",
            "MTH1W.F.FIN",
        }
        skills_by_code = {skill.code: skill for skill in skills}
        assert seeded_skill_codes <= skills_by_code.keys()
        seeded_skill_ids = {skills_by_code[code].id for code in seeded_skill_codes}

        expectations = list(
            db.scalars(
                select(CurriculumExpectation).where(
                    CurriculumExpectation.curriculum_id == ontario.id
                )
            )
        )
        assert {row.source_identifier for row in expectations} == {
            "MTH1W.B",
            "MTH1W.C",
            "MTH1W.F",
        }
        mappings = list(
            db.scalars(
                select(ExpectationSkillMapping).where(
                    ExpectationSkillMapping.curriculum_id == ontario.id
                )
            )
        )
        seeded_mappings = [row for row in mappings if row.skill_id in seeded_skill_ids]
        assert len(seeded_mappings) == 4
        assert {row.skill_id for row in seeded_mappings} == seeded_skill_ids

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id.in_(seeded_skill_ids)
                )
            )
        )
        assert len(edges) == 3
        assert all(edge.prerequisite_skill_id in seeded_skill_ids for edge in edges)

        problems = list(
            db.scalars(
                select(Problem).where(Problem.primary_skill_id.in_(seeded_skill_ids))
            )
        )
        assert len(problems) == 10
        assert all(problem.primary_skill_id in seeded_skill_ids for problem in problems)

        maryland_skill_ids = set(
            db.scalars(select(Skill.id).where(Skill.curriculum_id == grade8.id))
        )
        assert seeded_skill_ids.isdisjoint(maryland_skill_ids)
    finally:
        db.close()


def test_mth1w_prerequisite_guard_rejects_cross_curriculum_edge():
    _seed_curricula()
    db = SessionLocal()
    try:
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        ontario_skill = db.scalar(select(Skill).where(Skill.curriculum_id == ontario.id))
        maryland_skill = db.scalar(select(Skill).where(Skill.curriculum_id == grade8.id))

        from scripts.seed_mth1w import _prerequisite

        try:
            _prerequisite(db, ontario_skill, maryland_skill)
        except ValueError as exc:
            assert "cannot cross curriculum boundaries" in str(exc)
        else:
            raise AssertionError("Cross-curriculum prerequisite edge was not rejected")
    finally:
        db.rollback()
        db.close()


def test_mth1w_fine_grained_subskills_and_chains():
    _seed_curricula()

    db = SessionLocal()
    try:
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        skills = {
            skill.code: skill
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == ontario.id)
            )
        }
        subskills = {
            "MTH1W.B.NUM.INT", "MTH1W.B.NUM.FRAC",
            "MTH1W.C.ALG.EXPR", "MTH1W.C.ALG.EQ1", "MTH1W.C.ALG.EQ2",
            "MTH1W.C.REL.SLOPE", "MTH1W.C.REL.EVAL",
            "MTH1W.F.FIN.PCT", "MTH1W.F.FIN.APP",
        }
        assert subskills <= skills.keys()

        edges = set(
            db.execute(
                select(
                    SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_skill_id
                )
            ).all()
        )

        def edge(child: str, parent: str) -> bool:
            return (skills[child].id, skills[parent].id) in edges

        # Each strand anchor gates its chain head; chains descend atomically.
        assert edge("MTH1W.B.NUM.INT", "MTH1W.B.NUM")
        assert edge("MTH1W.B.NUM.FRAC", "MTH1W.B.NUM.INT")
        assert edge("MTH1W.C.ALG.EXPR", "MTH1W.C.ALG")
        assert edge("MTH1W.C.ALG.EQ1", "MTH1W.C.ALG.EXPR")
        assert edge("MTH1W.C.ALG.EQ2", "MTH1W.C.ALG.EQ1")
        assert edge("MTH1W.C.REL.SLOPE", "MTH1W.C.REL")
        assert edge("MTH1W.C.REL.SLOPE", "MTH1W.C.ALG.EQ2")
        assert edge("MTH1W.C.REL.EVAL", "MTH1W.C.REL.SLOPE")
        assert edge("MTH1W.F.FIN.PCT", "MTH1W.F.FIN")
        assert edge("MTH1W.F.FIN.APP", "MTH1W.F.FIN.PCT")

        # Every subskill has at least one curated problem of a generated-capable type.
        for code in subskills:
            types = {
                row[0]
                for row in db.execute(
                    select(Problem.problem_type).where(
                        Problem.primary_skill_id == skills[code].id
                    )
                )
            }
            assert types, code
    finally:
        db.close()
