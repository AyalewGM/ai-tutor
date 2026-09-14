from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.content_validation import ContentValidationError
from app.core.database import SessionLocal
from app.models import Curriculum, Skill, SkillPrerequisite
from app.prerequisite_ingestion import PrerequisiteEdgeInput, persist_prerequisite_edges


def _curriculum(db, code: str) -> Curriculum:
    curriculum = db.scalar(
        select(Curriculum).where(
            Curriculum.code == code,
            Curriculum.active.is_(True),
        )
    )
    assert curriculum is not None
    return curriculum


def _skills(db, curriculum: Curriculum, limit: int = 2) -> list[Skill]:
    skills = db.scalars(
        select(Skill)
        .where(Skill.curriculum_id == curriculum.id)
        .order_by(Skill.code)
        .limit(limit)
    ).all()
    assert len(skills) >= limit
    return list(skills)


def test_prerequisite_ingestion_is_idempotent_and_curriculum_scoped() -> None:
    with SessionLocal() as db:
        curriculum = _curriculum(db, "MCPS_MATH_8")
        prerequisite, skill = _skills(db, curriculum)
        edge = PrerequisiteEdgeInput(
            skill_code=skill.code,
            prerequisite_skill_code=prerequisite.code,
            importance_weight=Decimal("0.750"),
        )

        first = persist_prerequisite_edges(
            db,
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            edges=(edge,),
        )
        second = persist_prerequisite_edges(
            db,
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            edges=(edge,),
        )

        assert first[0].skill_id == second[0].skill_id
        assert first[0].prerequisite_skill_id == second[0].prerequisite_skill_id
        assert second[0].importance_weight == Decimal("0.750")
        count = db.scalar(
            select(func.count())
            .select_from(SkillPrerequisite)
            .where(
                SkillPrerequisite.skill_id == skill.id,
                SkillPrerequisite.prerequisite_skill_id == prerequisite.id,
            )
        )
        assert count == 1
        db.rollback()


def test_prerequisite_ingestion_rejects_self_reference() -> None:
    with SessionLocal() as db:
        curriculum = _curriculum(db, "MCPS_MATH_8")
        skill = _skills(db, curriculum, limit=1)[0]

        with pytest.raises(ContentValidationError, match="own prerequisite"):
            persist_prerequisite_edges(
                db,
                curriculum_code=curriculum.code,
                curriculum_version=curriculum.version,
                edges=(
                    PrerequisiteEdgeInput(
                        skill_code=skill.code,
                        prerequisite_skill_code=skill.code,
                    ),
                ),
            )
        db.rollback()


def test_prerequisite_ingestion_cannot_resolve_cross_curriculum_skill() -> None:
    with SessionLocal() as db:
        mcps = _curriculum(db, "MCPS_MATH_8")
        ontario = _curriculum(db, "MTH1W")
        mcps_skill = _skills(db, mcps, limit=1)[0]
        ontario_skill = _skills(db, ontario, limit=1)[0]

        with pytest.raises(
            ContentValidationError,
            match="prerequisite skill not found in content-pack curriculum",
        ):
            persist_prerequisite_edges(
                db,
                curriculum_code=mcps.code,
                curriculum_version=mcps.version,
                edges=(
                    PrerequisiteEdgeInput(
                        skill_code=mcps_skill.code,
                        prerequisite_skill_code=ontario_skill.code,
                    ),
                ),
            )
        db.rollback()
