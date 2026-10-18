from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.core.database import Base
from app.models import Curriculum, Problem, Skill
from app.services import problem_catalog_authorization as catalog_authorization


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
    prompt: str,
    source_type: str = "CURATED",
    provenance: dict | None = None,
) -> Problem:
    problem = Problem(
        primary_skill_id=skill.id,
        problem_type="SOLVE_EQUATION",
        difficulty=1,
        prompt=prompt,
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


def _snapshot(db: Session, curriculum: Curriculum):
    records = list(
        db.execute(
            select(Problem, Skill, Curriculum, ProblemContentMetadata)
            .join(Skill, Skill.id == Problem.primary_skill_id)
            .join(Curriculum, Curriculum.id == Skill.curriculum_id)
            .outerjoin(
                ProblemContentMetadata,
                ProblemContentMetadata.problem_id == Problem.id,
            )
            .where(
                Curriculum.id == curriculum.id,
                Problem.source_type == "CURATED",
                Skill.code != "M8.PROB.MARBLE_QA",
            )
        )
    )
    return catalog_authorization._catalog_snapshot(records)


def _approve_current_snapshot(monkeypatch: pytest.MonkeyPatch, db, curriculum) -> None:
    monkeypatch.setitem(
        catalog_authorization._REVIEWED_CATALOG_SNAPSHOTS,
        (curriculum.code, curriculum.version),
        frozenset({_snapshot(db, curriculum)}),
    )


def test_exact_snapshot_authorizes_only_missing_rows_and_preserves_narrow_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _session() as db:
        curriculum = _curriculum(db, code="REVIEWED")
        skill = _skill(db, curriculum, code="REVIEWED.SKILL")
        authorized = _problem(
            db,
            skill,
            prompt="Reviewed exact task",
            provenance=_reviewed_provenance(),
        )
        existing = _problem(
            db,
            skill,
            prompt="Reviewed guided-only task",
            provenance=_reviewed_provenance(),
        )
        db.add(
            ProblemContentMetadata(
                problem_id=existing.id,
                curriculum_id=curriculum.id,
                objective="Narrow pre-existing authorization.",
                evaluation_type="EXACT",
                guided_eligible=True,
            )
        )
        db.flush()
        _approve_current_snapshot(monkeypatch, db, curriculum)

        assert catalog_authorization.authorize_active_authored_catalog(db) == 1
        assert catalog_authorization.authorize_active_authored_catalog(db) == 0

        row = db.scalar(
            select(ProblemContentMetadata).where(ProblemContentMetadata.problem_id == authorized.id)
        )
        assert row is not None
        assert row.diagnostic_eligible is True
        assert row.guided_eligible is True
        assert row.independent_eligible is True
        assert row.mastery_eligible is True
        assert row.extension_eligible is False
        assert row.provenance_json["policy"] == (
            catalog_authorization.ACTIVE_CATALOG_POLICY_VERSION
        )
        assert row.provenance_json["catalog_digest"] == _snapshot(db, curriculum).digest

        existing_row = db.scalar(
            select(ProblemContentMetadata).where(ProblemContentMetadata.problem_id == existing.id)
        )
        assert existing_row is not None
        assert existing_row.guided_eligible is True
        assert existing_row.diagnostic_eligible is False
        assert existing_row.independent_eligible is False
        assert existing_row.mastery_eligible is False


def test_future_lookalike_with_same_provenance_changes_snapshot_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _session() as db:
        curriculum = _curriculum(db, code="REVIEWED")
        skill = _skill(db, curriculum, code="REVIEWED.SKILL")
        reviewed = _problem(
            db,
            skill,
            prompt="Only reviewed exact task",
            provenance=_reviewed_provenance(),
        )
        _approve_current_snapshot(monkeypatch, db, curriculum)
        assert catalog_authorization.authorize_active_authored_catalog(db) == 1

        lookalike = _problem(
            db,
            skill,
            prompt="Future unreviewed task with copied provenance",
            provenance=_reviewed_provenance(),
        )
        assert catalog_authorization.authorize_active_authored_catalog(db) == 0
        assert (
            db.scalar(
                select(ProblemContentMetadata).where(
                    ProblemContentMetadata.problem_id == lookalike.id
                )
            )
            is None
        )
        assert (
            db.scalar(
                select(ProblemContentMetadata).where(
                    ProblemContentMetadata.problem_id == reviewed.id
                )
            )
            is not None
        )


@pytest.mark.parametrize(
    "change",
    ["prompt", "answer", "problem_type", "difficulty", "solution"],
)
def test_any_mathematical_content_change_invalidates_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    with _session() as db:
        curriculum = _curriculum(db, code="REVIEWED")
        skill = _skill(db, curriculum, code="REVIEWED.SKILL")
        problem = _problem(
            db,
            skill,
            prompt="Reviewed exact task",
            provenance=_reviewed_provenance(),
        )
        _approve_current_snapshot(monkeypatch, db, curriculum)
        if change == "prompt":
            problem.prompt = "Edited task"
        elif change == "answer":
            problem.canonical_answer = "x=2"
        elif change == "problem_type":
            problem.problem_type = "WORD_PROBLEM"
        elif change == "difficulty":
            problem.difficulty = 2
        else:
            problem.solution = {**problem.solution, "worked_step": "unreviewed"}
        db.flush()

        assert catalog_authorization.authorize_active_authored_catalog(db) == 0
        assert (
            db.scalar(
                select(ProblemContentMetadata).where(
                    ProblemContentMetadata.problem_id == problem.id
                )
            )
            is None
        )


def test_unknown_partial_generated_inactive_and_qa_catalogs_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _session() as db:
        active = _curriculum(db, code="REVIEWED")
        inactive = _curriculum(db, code="INACTIVE", active=False)
        active_skill = _skill(db, active, code="REVIEWED.SKILL")
        inactive_skill = _skill(db, inactive, code="INACTIVE.SKILL")
        qa_skill = _skill(db, active, code="M8.PROB.MARBLE_QA")
        approved = _problem(
            db,
            active_skill,
            prompt="Reviewed exact task",
            provenance=_reviewed_provenance(),
        )
        _approve_current_snapshot(monkeypatch, db, active)
        _problem(
            db,
            active_skill,
            prompt="Generated task",
            source_type="GENERATED",
            provenance=_reviewed_provenance(),
        )
        _problem(
            db,
            inactive_skill,
            prompt="Inactive task",
            provenance=_reviewed_provenance(),
        )
        _problem(
            db,
            qa_skill,
            prompt="QA-only task",
            provenance=_reviewed_provenance(),
        )

        assert catalog_authorization.authorize_active_authored_catalog(db) == 1
        rows = list(db.scalars(select(ProblemContentMetadata)))
        assert len(rows) == 1
        assert rows[0].problem_id == approved.id
