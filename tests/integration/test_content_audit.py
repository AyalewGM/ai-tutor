import uuid

import pytest

from app.content_audit import (
    audit_curriculum_problem_inventory,
    audit_curriculum_skill_traceability,
)
from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.content_models import ProblemContentMetadata
from app.content_validation import ContentValidationError
from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill


def _isolated_curriculum(db) -> tuple[Curriculum, Skill]:
    suffix = uuid.uuid4().hex[:10]
    curriculum = Curriculum(
        code=f"F007_AUDIT_{suffix}",
        name="F-007 traceability audit fixture",
        jurisdiction="TEST",
        grade_level="TEST",
        version="2026-test",
        source_uri="https://example.edu/f007/audit",
        active=True,
    )
    db.add(curriculum)
    db.flush()
    skill = Skill(
        curriculum_id=curriculum.id,
        code="AUDIT.SKILL.1",
        name="Audit skill",
        difficulty_level=1,
    )
    db.add(skill)
    db.flush()
    return curriculum, skill


def _add_problem(db, *, curriculum: Curriculum, skill: Skill, mode: str) -> Problem:
    problem = Problem(
        primary_skill_id=skill.id,
        problem_type="NUMERIC",
        difficulty=1,
        prompt=f"Original {mode} audit problem",
        canonical_answer="1",
        source_type="CURATED",
    )
    db.add(problem)
    db.flush()
    metadata = ProblemContentMetadata(
        problem_id=problem.id,
        curriculum_id=curriculum.id,
        objective="Verify persisted mode-specific inventory",
        evaluation_type="EXACT",
        diagnostic_eligible=mode == "diagnostic",
        guided_eligible=mode == "guided",
        independent_eligible=mode == "independent",
        mastery_eligible=mode == "mastery",
        llm_solution_required=False,
        provenance_json={"source_type": "AI_TUTOR_ORIGINAL"},
    )
    db.add(metadata)
    db.flush()
    return problem


def test_traceability_audit_rejects_unmapped_skill() -> None:
    with SessionLocal() as db:
        curriculum, _ = _isolated_curriculum(db)

        with pytest.raises(ContentValidationError, match="must map to at least one"):
            audit_curriculum_skill_traceability(db, curriculum_id=curriculum.id)
        db.rollback()


def test_traceability_audit_accepts_explicit_curriculum_scoped_mapping() -> None:
    with SessionLocal() as db:
        curriculum, skill = _isolated_curriculum(db)
        pack = ContentPackInput(
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            expectations=(
                ExpectationInput(
                    source_identifier="TEST.EXPECTATION.1",
                    title="Test expectation",
                    strand="Test",
                    source_uri="https://example.edu/f007/audit/expectation-1",
                ),
            ),
            mappings=(
                ExpectationSkillMappingInput(
                    source_identifier="TEST.EXPECTATION.1",
                    skill_code=skill.code,
                ),
            ),
        )
        persist_expectation_pack(db, pack)

        audit_curriculum_skill_traceability(db, curriculum_id=curriculum.id)
        db.rollback()


def test_problem_inventory_audit_rejects_missing_learning_modes() -> None:
    with SessionLocal() as db:
        curriculum, skill = _isolated_curriculum(db)
        _add_problem(db, curriculum=curriculum, skill=skill, mode="diagnostic")

        with pytest.raises(ContentValidationError, match="guided, independent, mastery"):
            audit_curriculum_problem_inventory(db, curriculum_id=curriculum.id)
        db.rollback()


def test_problem_inventory_audit_accepts_fresh_mode_specific_pools() -> None:
    with SessionLocal() as db:
        curriculum, skill = _isolated_curriculum(db)
        for mode in ("diagnostic", "guided", "independent", "mastery"):
            _add_problem(db, curriculum=curriculum, skill=skill, mode=mode)

        audit_curriculum_problem_inventory(db, curriculum_id=curriculum.id)
        db.rollback()


def test_problem_inventory_audit_rejects_problem_reused_across_modes() -> None:
    with SessionLocal() as db:
        curriculum, skill = _isolated_curriculum(db)
        diagnostic = _add_problem(db, curriculum=curriculum, skill=skill, mode="diagnostic")
        _add_problem(db, curriculum=curriculum, skill=skill, mode="guided")
        _add_problem(db, curriculum=curriculum, skill=skill, mode="independent")
        _add_problem(db, curriculum=curriculum, skill=skill, mode="mastery")

        metadata = db.query(ProblemContentMetadata).filter_by(problem_id=diagnostic.id).one()
        metadata.mastery_eligible = True
        db.flush()

        with pytest.raises(ContentValidationError, match="reuses problem IDs"):
            audit_curriculum_problem_inventory(db, curriculum_id=curriculum.id)
        db.rollback()
