import uuid
from contextlib import contextmanager

from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.core.database import Base
from app.models import Curriculum, Problem, Skill
from app.services.problem_catalog_authorization import (
    ACTIVE_CATALOG_POLICY_VERSION,
    authorize_active_authored_catalog,
)


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@compiles(UUID, "sqlite")
def _compile_uuid_for_sqlite(_type, _compiler, **_kwargs):
    return "CHAR(36)"


@contextmanager
def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            Curriculum.__table__,
            Skill.__table__,
            Problem.__table__,
            ProblemContentMetadata.__table__,
        ],
    )
    with Session(engine) as db:
        yield db


def _curriculum(db: Session, *, code: str, active: bool = True) -> Curriculum:
    curriculum = Curriculum(code=code, name=code, version="1", active=active)
    db.add(curriculum)
    db.flush()
    return curriculum


def _skill(db: Session, curriculum: Curriculum, *, code: str) -> Skill:
    skill = Skill(
        curriculum_id=curriculum.id,
        code=code,
        name=code,
        difficulty_level=1,
    )
    db.add(skill)
    db.flush()
    return skill


def _problem(
    db: Session,
    skill: Skill,
    *,
    source_type: str = "CURATED",
    provenance: dict | None = None,
) -> Problem:
    problem = Problem(
        primary_skill_id=skill.id,
        problem_type="SOLVE_EQUATION",
        difficulty=1,
        prompt=f"Synthetic {uuid.uuid4()}",
        canonical_answer="x=1",
        source_type=source_type,
        solution={"answer": "x=1", "provenance": provenance} if provenance else {"answer": "x=1"},
    )
    db.add(problem)
    db.flush()
    return problem


def _reviewed_provenance() -> dict:
    return {
        "origin": "AUTHORED",
        "author": "AI Tutor curriculum team",
        "license": "proprietary",
    }


def test_authorization_is_explicit_idempotent_and_fail_closed() -> None:
    with _session() as db:
        active = _curriculum(db, code="ACTIVE")
        other_active = _curriculum(db, code="OTHER")
        inactive = _curriculum(db, code="INACTIVE", active=False)
        active_skill = _skill(db, active, code="ACTIVE.SKILL")
        other_skill = _skill(db, other_active, code="OTHER.SKILL")
        inactive_skill = _skill(db, inactive, code="INACTIVE.SKILL")
        qa_skill = _skill(db, active, code="M8.PROB.MARBLE_QA")

        authorized = _problem(db, active_skill, provenance=_reviewed_provenance())
        wrong_author = _problem(
            db,
            active_skill,
            provenance={**_reviewed_provenance(), "author": "Unreviewed draft author"},
        )
        metadata_free = _problem(db, active_skill)
        generated = _problem(
            db,
            active_skill,
            source_type="GENERATED",
            provenance=_reviewed_provenance(),
        )
        _problem(db, other_skill, provenance=_reviewed_provenance())
        _problem(db, inactive_skill, provenance=_reviewed_provenance())
        _problem(db, qa_skill, provenance=_reviewed_provenance())

        existing = _problem(db, active_skill, provenance=_reviewed_provenance())
        db.add(
            ProblemContentMetadata(
                problem_id=existing.id,
                curriculum_id=active.id,
                objective="Narrow pre-existing authorization.",
                evaluation_type="EXACT",
                guided_eligible=True,
            )
        )
        db.flush()

        assert authorize_active_authored_catalog(db, curriculum_codes={"ACTIVE"}) == 1
        assert authorize_active_authored_catalog(db, curriculum_codes={"ACTIVE"}) == 0

        row = db.scalar(
            select(ProblemContentMetadata).where(ProblemContentMetadata.problem_id == authorized.id)
        )
        assert row is not None
        assert row.diagnostic_eligible is True
        assert row.guided_eligible is True
        assert row.independent_eligible is True
        assert row.mastery_eligible is True
        assert row.extension_eligible is False
        assert row.provenance_json["policy"] == ACTIVE_CATALOG_POLICY_VERSION
        assert row.provenance_json["new_draft_authorization"] is False

        existing_row = db.scalar(
            select(ProblemContentMetadata).where(ProblemContentMetadata.problem_id == existing.id)
        )
        assert existing_row is not None
        assert existing_row.guided_eligible is True
        assert existing_row.diagnostic_eligible is False
        assert existing_row.independent_eligible is False
        assert existing_row.mastery_eligible is False

        unauthorized_ids = {wrong_author.id, metadata_free.id, generated.id}
        assert (
            db.scalar(
                select(func.count())
                .select_from(ProblemContentMetadata)
                .where(ProblemContentMetadata.problem_id.in_(unauthorized_ids))
            )
            == 0
        )
        assert db.scalar(select(func.count()).select_from(ProblemContentMetadata)) == 2
        db.rollback()
