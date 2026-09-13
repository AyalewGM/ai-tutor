from app.content_models import CurriculumExpectation, ExpectationSkillMapping
from app.core.database import Base


def test_content_tables_registered_with_metadata():
    assert CurriculumExpectation.__tablename__ in Base.metadata.tables
    assert ExpectationSkillMapping.__tablename__ in Base.metadata.tables


def test_expectation_identity_is_curriculum_version_scoped():
    table = Base.metadata.tables["curriculum_expectations"]
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("curriculum_id", "curriculum_version", "source_identifier") in unique_column_sets


def test_mapping_carries_explicit_curriculum_boundary():
    table = Base.metadata.tables["expectation_skill_mappings"]
    assert "curriculum_id" in table.columns
    assert "expectation_id" in table.columns
    assert "skill_id" in table.columns
