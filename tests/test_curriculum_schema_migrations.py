from pathlib import Path

REQUIRED_TABLES = {
    "curriculum_versions",
    "curriculum_standards",
    "standard_skill_mappings",
    "canonical_concepts",
    "canonical_skill_concepts",
    "canonical_skill_prerequisites",
    "canonical_misconceptions",
    "problem_families",
}


def test_scalability_schema_migration_covers_required_tables():
    source = Path("alembic/versions/0033_curriculum_scalability_schema.py").read_text()
    for table in REQUIRED_TABLES:
        assert f'"{table}"' in source


def test_lifecycle_migration_allows_pre_scalability_upgrade_path():
    source = Path("alembic/versions/0032_curriculum_lifecycle.py").read_text()
    assert '"curriculum_versions" not in set(inspector.get_table_names())' in source
    assert "return" in source
