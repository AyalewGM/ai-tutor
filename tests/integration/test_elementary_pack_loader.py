from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.content_models import CurriculumExpectation, ProblemContentMetadata
from app.content_validation import ContentValidationError
from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.elementary_pack import load_pack, parse_pack
from app.models import Curriculum, Problem, Skill, SkillStatus, Student, StudentSkill

EXAMPLE = (
    Path(__file__).parents[2]
    / "docs/curriculum/examples/elementary_pack.schema-v1.example.json"
)


def test_loader_is_idempotent_and_persists_separated_content_layers():
    pack = parse_pack(EXAMPLE)
    with SessionLocal() as db:
        first = load_pack(db, pack)
        second = load_pack(db, pack)
        assert second == first

        curriculum = db.get(Curriculum, first.curriculum_id)
        skills = db.scalars(
            select(Skill).where(Skill.curriculum_id == curriculum.id)
        ).all()
        assert len(skills) == 1
        skill = skills[0]
        mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == skill.id
            )
        )
        canonical = db.get(CanonicalSkill, mapping.canonical_skill_id)
        assert canonical.code == "MATH.SYNTHETIC.CONTEXT"
        assert mapping.provenance_json["expectation_refs"] == ["3.SYNTH.A.1"]

        expectations = db.scalars(
            select(CurriculumExpectation).where(
                CurriculumExpectation.curriculum_id == curriculum.id
            )
        ).all()
        assert len(expectations) == 1
        problems = db.scalars(
            select(Problem).where(Problem.primary_skill_id == skill.id)
        ).all()
        assert len(problems) == 4
        assert {problem.solution["pack_problem_key"] for problem in problems} == {
            "synth3-context-diagnostic-01",
            "synth3-context-guided-01",
            "synth3-context-independent-01",
            "synth3-context-mastery-01",
        }
        metadata = db.scalars(
            select(ProblemContentMetadata).where(
                ProblemContentMetadata.curriculum_id == curriculum.id
            )
        ).all()
        assert len(metadata) == 4
        assert sum(row.diagnostic_eligible for row in metadata) == 1
        assert sum(row.guided_eligible for row in metadata) == 1
        assert sum(row.independent_eligible for row in metadata) == 1
        assert sum(row.mastery_eligible for row in metadata) == 1
        assert all(row.llm_solution_required is False for row in metadata)
        db.rollback()


def test_loader_rolls_back_nested_write_when_canonical_mapping_conflicts():
    pack = parse_pack(EXAMPLE)
    with SessionLocal() as db:
        result = load_pack(db, pack)
        original_count = db.scalar(select(func.count()).select_from(CanonicalSkill))
        conflicting_skill = pack.skills[0].model_copy(
            update={
                "canonical": pack.skills[0].canonical.model_copy(
                    update={"code": "MATH.SYNTHETIC.CONFLICT"}
                )
            }
        )
        conflicting = pack.model_copy(update={"skills": (conflicting_skill,)})

        with pytest.raises(ContentValidationError, match="different canonical concept"):
            load_pack(db, conflicting)

        assert db.scalar(select(func.count()).select_from(CanonicalSkill)) == original_count
        curriculum = db.get(Curriculum, result.curriculum_id)
        skill = db.scalar(
            select(Skill).where(Skill.curriculum_id == curriculum.id)
        )
        mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == skill.id
            )
        )
        canonical = db.get(CanonicalSkill, mapping.canonical_skill_id)
        assert canonical.code == "MATH.SYNTHETIC.CONTEXT"
        assert db.scalar(
            select(CanonicalSkill).where(
                CanonicalSkill.code == "MATH.SYNTHETIC.CONFLICT"
            )
        ) is None
        db.rollback()


def test_shared_canonical_identity_does_not_transfer_cross_version_evidence():
    pack = parse_pack(EXAMPLE)
    second_curriculum = pack.curriculum.model_copy(update={"version": "test-v2"})
    second_pack = pack.model_copy(update={"curriculum": second_curriculum})
    with SessionLocal() as db:
        first = load_pack(db, pack)
        second = load_pack(db, second_pack)
        first_curriculum = db.get(Curriculum, first.curriculum_id)
        second_curriculum_row = db.get(Curriculum, second.curriculum_id)
        first_skill = db.scalar(
            select(Skill).where(Skill.curriculum_id == first_curriculum.id)
        )
        second_skill = db.scalar(
            select(Skill).where(Skill.curriculum_id == second_curriculum_row.id)
        )
        first_mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == first_skill.id
            )
        )
        second_mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == second_skill.id
            )
        )
        assert first_mapping.canonical_skill_id == second_mapping.canonical_skill_id
        assert first_skill.id != second_skill.id

        learner = Student(
            curriculum_id=first_curriculum.id,
            first_name="Synthetic",
            grade_level="3",
            school_system="TEST",
        )
        db.add(learner)
        db.flush()
        db.add(
            StudentSkill(
                student_id=learner.id,
                skill_id=first_skill.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.900"),
                status=SkillStatus.MASTERED,
            )
        )
        db.flush()
        assert db.get(StudentSkill, (learner.id, first_skill.id)) is not None
        assert db.get(StudentSkill, (learner.id, second_skill.id)) is None
        assert not hasattr(StudentSkill, "canonical_skill_id")
        db.rollback()
