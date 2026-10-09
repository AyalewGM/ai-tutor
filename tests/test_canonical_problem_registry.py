from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.canonical_problem_families import FAMILIES
from app.canonical_problem_registry import register_problem_families
from app.core.database import Base
from app.curriculum_models import CanonicalSkill, ProblemFamily


def test_registry_is_idempotent_and_canonical_only():
    engine = create_engine("sqlite:///:memory:")
    # Create only the two JSONB-free tables the registry touches; the full
    # schema uses PostgreSQL JSONB, which SQLite cannot render.
    Base.metadata.create_all(
        engine, tables=[CanonicalSkill.__table__, ProblemFamily.__table__]
    )
    with Session(engine) as db:
        assert register_problem_families(db) == len(FAMILIES)
        db.commit()
        assert register_problem_families(db) == 0
        assert db.scalar(select(func.count()).select_from(ProblemFamily)) == len(FAMILIES)
        skills = db.scalars(select(CanonicalSkill)).all()
        assert skills
        assert all(skill.code.startswith("MATH.") for skill in skills)
