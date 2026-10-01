"""Add freemium family privacy controls.

Revision ID: 0019_freemium_family_privacy
Revises: 0018_canonical_skills
"""

import sqlalchemy as sa

from alembic import op

revision = "0019_freemium_family_privacy"
down_revision = "0018_canonical_skills"
branch_labels = None
depends_on = None


def _column_names(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "parent_profiles" in tables:
        columns = _column_names("parent_profiles")
        if "subscription_tier" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("subscription_tier", sa.String(length=20), nullable=False, server_default="free"),
            )
        if "max_students" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("max_students", sa.Integer(), nullable=False, server_default="1"),
            )
        if "parent_pin_hash" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("parent_pin_hash", sa.String(length=255), nullable=True),
            )
        if "coppa_consent_given" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("coppa_consent_given", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if "consent_timestamp" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True),
            )
        if "terms_accepted_at" not in columns:
            op.add_column(
                "parent_profiles",
                sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
            )

        if op.get_bind().dialect.name != "sqlite":
            constraints = {
                constraint["name"]
                for constraint in sa.inspect(op.get_bind()).get_check_constraints("parent_profiles")
            }
            if "ck_parent_subscription_tier" not in constraints:
                op.create_check_constraint(
                    "ck_parent_subscription_tier",
                    "parent_profiles",
                    "subscription_tier IN ('free', 'pro')",
                )
            if "ck_parent_max_students_positive" not in constraints:
                op.create_check_constraint(
                    "ck_parent_max_students_positive",
                    "parent_profiles",
                    "max_students >= 1",
                )

    if "students" in tables:
        columns = _column_names("students")
        if "avatar_id" not in columns:
            op.add_column(
                "students",
                sa.Column("avatar_id", sa.String(length=80), nullable=False, server_default="avatar-1"),
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "students" in tables and "avatar_id" in _column_names("students"):
        op.drop_column("students", "avatar_id")

    if "parent_profiles" in tables:
        if op.get_bind().dialect.name != "sqlite":
            constraints = {
                constraint["name"]
                for constraint in sa.inspect(op.get_bind()).get_check_constraints("parent_profiles")
            }
            if "ck_parent_max_students_positive" in constraints:
                op.drop_constraint(
                    "ck_parent_max_students_positive", "parent_profiles", type_="check"
                )
            if "ck_parent_subscription_tier" in constraints:
                op.drop_constraint(
                    "ck_parent_subscription_tier", "parent_profiles", type_="check"
                )

        columns = _column_names("parent_profiles")
        for column in (
            "terms_accepted_at",
            "consent_timestamp",
            "coppa_consent_given",
            "parent_pin_hash",
            "max_students",
            "subscription_tier",
        ):
            if column in columns:
                op.drop_column("parent_profiles", column)
