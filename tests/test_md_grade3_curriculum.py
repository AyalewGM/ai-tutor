from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import (
    Curriculum,
    Problem,
    Skill,
    SkillPrerequisite,
    SkillStatus,
    Student,
    StudentSkill,
)
from app.services.problem_generation import content_readiness, generate_problem
from scripts.seed_md_grade3 import (
    CURRICULUM_CODE,
    CURRICULUM_VERSION,
    GRADE3_CROSSWALK,
    seed,
)

EXPECTED_SKILLS = {
    "MD3.NOS.EQUAL_GROUPS": "MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS",
    "MD3.NOS.EQUAL_SHARING": "MATH.ELEMENTARY.DIVISION.EQUAL_SHARING",
    "MD3.NOS.UNIT_FRACTION": "MATH.ELEMENTARY.FRACTION.UNIT",
    "MD3.GR.RECTANGLE_AREA": "MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA",
}


def test_md_grade3_seed_is_idempotent_provenanced_and_content_ready():
    seed()
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        assert curriculum is not None
        assert curriculum.version == CURRICULUM_VERSION
        assert curriculum.jurisdiction == "Maryland"
        assert curriculum.grade_level == "3"
        assert curriculum.source_uri == GRADE3_CROSSWALK

        skills = list(
            db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id))
        )
        assert {skill.code for skill in skills} == set(EXPECTED_SKILLS)
        skill_ids = {skill.id for skill in skills}
        problems = list(
            db.scalars(
                select(Problem).where(
                    Problem.primary_skill_id.in_(skill_ids),
                    Problem.source_type == "CURATED",
                )
            )
        )
        assert len(problems) == 16
        assert all(problem.solution["provenance"]["origin"] == "AUTHORED" for problem in problems)
        assert all(problem.solution["provenance"]["standards_source"] == GRADE3_CROSSWALK for problem in problems)
        assert all(content_readiness(db, skill_id=skill.id).ready for skill in skills)

        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_(skill_ids)
                )
            )
        )
        assert len(mappings) == len(skills)
        mapped_codes = {
            db.get(CanonicalSkill, mapping.canonical_skill_id).code
            for mapping in mappings
        }
        assert mapped_codes == set(EXPECTED_SKILLS.values())
        assert all(
            any(ref.startswith("3.") for ref in mapping.provenance_json["expectation_refs"])
            for mapping in mappings
        )

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id.in_(skill_ids)
                )
            )
        )
        assert len(edges) == 3
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)


def test_md_grade3_generators_produce_fresh_answer_consistent_variants():
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        skills = list(
            db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id))
        )
        for skill in skills:
            generated = generate_problem(db, skill_id=skill.id, difficulty=2)
            assert generated is not None
            assert generated.source_type == "GENERATED"
            assert generated.solution["problem_family"] == generated.problem_type
            params = generated.solution["parameters"]
            if generated.problem_type in {"EQUAL_GROUPS", "RECTANGLE_AREA"}:
                assert int(generated.canonical_answer) == params["rows"] * params["columns"]
            elif generated.problem_type == "EQUAL_SHARING":
                assert int(generated.canonical_answer) == params["group_size"]
                assert params["total"] == params["groups"] * params["group_size"]
            else:
                assert generated.canonical_answer == f"{params['numerator']}/{params['denominator']}"


def test_canonical_mapping_never_transfers_md_grade3_evidence():
    seed()
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        local_skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MD3.NOS.EQUAL_GROUPS",
            )
        )
        mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == local_skill.id
            )
        )
        other_curriculum = Curriculum(
            code="SYNTH_DC_G3_ISOLATION",
            name="Synthetic DC Grade 3 isolation fixture",
            jurisdiction="District of Columbia",
            grade_level="3",
            version="test-only",
        )
        db.add(other_curriculum)
        db.flush()
        other_skill = Skill(
            curriculum_id=other_curriculum.id,
            code="SYNTH.DC3.EQUAL_GROUPS",
            name="Synthetic equal groups",
            difficulty_level=1,
        )
        db.add(other_skill)
        db.flush()
        db.add(
            CurriculumSkillMapping(
                canonical_skill_id=mapping.canonical_skill_id,
                skill_id=other_skill.id,
                mapping_type="EQUIVALENT",
                provenance_json={"basis": "synthetic isolation test"},
            )
        )
        learner = Student(
            curriculum_id=curriculum.id,
            first_name="Synthetic Grade 3 Learner",
            grade_level="3",
            school_system="TEST",
        )
        db.add(learner)
        db.flush()
        db.add(
            StudentSkill(
                student_id=learner.id,
                skill_id=local_skill.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.900"),
                independent_attempt_count=4,
                independent_correct_count=4,
                status=SkillStatus.MASTERED,
            )
        )
        db.flush()

        assert db.get(StudentSkill, (learner.id, local_skill.id)) is not None
        assert db.get(StudentSkill, (learner.id, other_skill.id)) is None
        assert not hasattr(StudentSkill, "canonical_skill_id")
        db.rollback()


def test_md_grade3_pack_loaded_via_declarative_framework():
    result = seed()
    with SessionLocal() as db:
        curriculum = db.get(Curriculum, result.curriculum_id)
        assert curriculum is not None
        assert curriculum.code == CURRICULUM_CODE
        assert result.skill_count == 4
        assert result.expectation_count == 3
        assert result.problem_count == 16

        skills = list(
            db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id))
        )
        skill_ids = {skill.id for skill in skills}
        problems = list(
            db.scalars(
                select(Problem).where(
                    Problem.primary_skill_id.in_(skill_ids),
                    Problem.source_type == "CURATED",
                )
            )
        )
        assert len(problems) == 16
        assert all("pack_problem_key" in problem.solution for problem in problems)
        assert all(problem.solution["provenance"]["origin"] == "AUTHORED" for problem in problems)
        assert all(
            problem.solution["provenance"]["standards_source"] == GRADE3_CROSSWALK
            for problem in problems
        )
