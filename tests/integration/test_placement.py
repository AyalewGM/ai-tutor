import uuid
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import (
    Curriculum,
    Skill,
    SkillPrerequisite,
    SkillStatus,
    Student,
    StudentSkill,
)
from app.services.placement import (
    PREREQUISITE_GAP,
    READY_TO_START,
    RESUME_IN_PROGRESS,
    recommend_next_skill,
)


def _student() -> tuple[uuid.UUID, uuid.UUID, dict[str, uuid.UUID]]:
    """MCPS_MATH_8 graph: anchors INVERSE(1), DIST(2), TWO_STEP(3), MULTI_STEP(4)
    with fine-grained subskills chained beneath each anchor."""
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        assert curriculum is not None
        skills = {
            skill.code: skill
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == curriculum.id)
            )
        }
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Placement QA Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.commit()
        return (
            student.id,
            curriculum.id,
            {code: skill.id for code, skill in skills.items()},
        )


def _progress(
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    *,
    mastery: str,
    confidence: str = "0.900",
    status: SkillStatus,
    attempts: int = 3,
) -> None:
    with SessionLocal() as db:
        db.add(
            StudentSkill(
                student_id=student_id,
                skill_id=skill_id,
                mastery_score=Decimal(mastery),
                confidence_score=Decimal(confidence),
                attempt_count=attempts,
                status=status,
            )
        )
        db.commit()


def _recommend(student_id: uuid.UUID, curriculum_id: uuid.UUID):
    with SessionLocal() as db:
        return recommend_next_skill(
            db, student_id=student_id, curriculum_id=curriculum_id
        )


def test_fresh_student_starts_at_lowest_skill() -> None:
    student_id, curriculum_id, skills = _student()
    recommendation = _recommend(student_id, curriculum_id)
    assert recommendation is not None
    assert recommendation.skill.id == skills["M8.ALG.INVERSE"]
    assert recommendation.reason == READY_TO_START


def test_in_progress_skill_is_resumed() -> None:
    student_id, curriculum_id, skills = _student()
    _progress(
        student_id,
        skills["M8.ALG.INVERSE"],
        mastery="0.400",
        status=SkillStatus.PRACTICING,
    )
    recommendation = _recommend(student_id, curriculum_id)
    assert recommendation is not None
    assert recommendation.skill.id == skills["M8.ALG.INVERSE"]
    assert recommendation.reason == RESUME_IN_PROGRESS


def test_mastered_skills_advance_placement() -> None:
    student_id, curriculum_id, skills = _student()
    _progress(
        student_id,
        skills["M8.ALG.INVERSE"],
        mastery="0.900",
        status=SkillStatus.MASTERED,
    )
    recommendation = _recommend(student_id, curriculum_id)
    assert recommendation is not None
    # Mastering an anchor unlocks its fine-grained subskills, so placement
    # proceeds into the anchor's chain before moving to the next strand.
    assert recommendation.skill.id == skills["M8.ALG.INVERSE.ADD"]
    assert recommendation.reason == READY_TO_START


def test_recommendation_descends_to_unready_prerequisite() -> None:
    with SessionLocal() as db:
        curriculum = Curriculum(
            code=f"PLACEMENT_{uuid.uuid4().hex[:8]}",
            name="Placement Graph",
            jurisdiction="Test",
            grade_level="8",
            version="1",
        )
        db.add(curriculum)
        db.flush()
        # Higher-numbered difficulty sits *below* the target in the graph so the
        # recommendation must descend to the unready prerequisite, not just the
        # lowest unmastered skill.
        target = Skill(
            curriculum_id=curriculum.id,
            code=f"PLC.TARGET.{uuid.uuid4().hex[:6]}",
            name="Target skill",
            difficulty_level=1,
        )
        blocker = Skill(
            curriculum_id=curriculum.id,
            code=f"PLC.BLOCKER.{uuid.uuid4().hex[:6]}",
            name="Unready prerequisite",
            difficulty_level=5,
        )
        db.add_all([target, blocker])
        db.flush()
        db.add(
            SkillPrerequisite(
                skill_id=target.id,
                prerequisite_skill_id=blocker.id,
                importance_weight=Decimal("1.000"),
            )
        )
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Placement Gap Learner",
            grade_level="8",
            school_system="Test",
        )
        db.add(student)
        db.commit()
        student_id, curriculum_id, blocker_id = student.id, curriculum.id, blocker.id

    recommendation = _recommend(student_id, curriculum_id)
    assert recommendation is not None
    assert recommendation.skill.id == blocker_id
    assert recommendation.reason == PREREQUISITE_GAP


def test_fully_mastered_curriculum_returns_none() -> None:
    student_id, curriculum_id, skills = _student()
    for skill_id in skills.values():
        _progress(
            student_id,
            skill_id,
            mastery="0.950",
            status=SkillStatus.MASTERED,
        )
    assert _recommend(student_id, curriculum_id) is None
