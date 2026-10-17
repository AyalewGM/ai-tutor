"""Regression coverage for fresh and ORM-precreated family pass schemas."""

import importlib.util
import pathlib
import types
import unittest.mock

import pytest


MIGRATION = (
    pathlib.Path(__file__).resolve().parents[1]
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
    inspector = types.SimpleNamespace(
        get_unique_constraints=lambda table: (
            [{"name": name} for name in existing]
            if table == "family_practice_passes"
            else []
        )
    )
    migration_op = types.SimpleNamespace(
        get_bind=lambda: object(),
        drop_constraint=unittest.mock.Mock(),
        create_unique_constraint=unittest.mock.Mock(),
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


@pytest.mark.parametrize("precreated", [False, True])
def test_upgrade_handles_legacy_and_orm_precreated_tables(monkeypatch, precreated):
    spec = importlib.util.spec_from_file_location("migration_0036_upgrade", MIGRATION)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    inspector = types.SimpleNamespace(
        get_unique_constraints=lambda _table: [
            {"name": "uq_family_practice_pass_child" if precreated
             else "uq_family_practice_pass_parent"}
        ],
        get_columns=lambda _table: [{"name": "display_name"}] if precreated else [],
        get_table_names=lambda: (
            ["family_practice_passes", "learner_pass_sessions",
             "parent_invitations", "pilot_entitlements"]
            if precreated else ["family_practice_passes", "learner_pass_sessions"]
        ),
    )
    methods = ("drop_constraint", "create_unique_constraint", "add_column",
               "create_table", "create_index")
    operations = {name: unittest.mock.Mock() for name in methods}
    migration_op = types.SimpleNamespace(get_bind=lambda: object(), **operations)
    monkeypatch.setattr(migration.sa, "inspect", lambda _conn: inspector)
    monkeypatch.setattr(migration, "op", migration_op)

    migration.upgrade()

    assert operations["drop_constraint"].call_count == (0 if precreated else 1)
    assert operations["create_unique_constraint"].call_count == (0 if precreated else 1)
    assert operations["add_column"].call_count == (0 if precreated else 1)
    assert operations["create_table"].call_count == (0 if precreated else 2)
    assert operations["create_index"].call_count == (0 if precreated else 2)
