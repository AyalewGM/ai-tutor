from pathlib import Path

from app.curriculum_models import CurriculumStandard, CurriculumVersion, StandardSkillMapping
from app.models import StudentSkill


def test_curriculum_scalability_models_keep_learner_evidence_local():
    version_columns = set(CurriculumVersion.__table__.columns.keys())
    standard_columns = set(CurriculumStandard.__table__.columns.keys())
    mapping_columns = set(StandardSkillMapping.__table__.columns.keys())

    forbidden = {"student_id", "mastery_score", "attempt_count", "last_attempt_at"}
    assert forbidden.isdisjoint(version_columns)
    assert forbidden.isdisjoint(standard_columns)
    assert forbidden.isdisjoint(mapping_columns)

    # Learner evidence remains explicitly keyed to a curriculum-local Skill.
    assert "skill_id" in StudentSkill.__table__.columns
    assert "canonical_skill_id" not in StudentSkill.__table__.columns


def test_onboarding_runbook_declares_no_fork_gate():
    text = Path("docs/curriculum/onboarding_runbook.md").read_text()
    assert "Virginia + Alberta" in text
    assert "validator" in text
    assert "Math Visual Engine" in text
    assert "mastery" in text
    assert "StudentSkill" in text
