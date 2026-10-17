"""Regression coverage for fresh and ORM-precreated family pass schemas."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0036_multi_child_practice_links.py"
)


@pytest.mark.parametrize(
    ("existing", "drop_old", "create_child"),
    [
        ({"uq_family_practice_pass_parent"}, True, True),
        ({"uq_family_practice_pass_child"}, False, False),
        (set(), False, True),
    ],
)
def test_upgrade_uses_actual_unique_constraint_state(
    monkeypatch, existing, drop_old, create_child
):
    spec = importlib.util.spec_from_file_location("migration_0036_passes", MIGRATION)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    inspector = SimpleNamespace(
        get_unique_constraints=lambda table: (
            [{"name": name} for name in existing]
            if table == "family_practice_passes"
            else []
        )
    )
    migration_op = SimpleNamespace(
        get_bind=lambda: object(),
        drop_constraint=Mock(),
        create_unique_constraint=Mock(),
    )
    monkeypatch.setattr(migration.sa, "inspect", lambda _conn: inspector)
    monkeypatch.setattr(migration, "op", migration_op)

    migration._upgrade_practice_pass_uniqueness()

    assert migration_op.drop_constraint.called is drop_old
    assert migration_op.create_unique_constraint.called is create_child
    if create_child:
        migration_op.create_unique_constraint.assert_called_once_with(
            "uq_family_practice_pass_child",
            "family_practice_passes",
            ["parent_profile_id", "student_id"],
        )
