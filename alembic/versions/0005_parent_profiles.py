"""Add parent profiles, parent-child relationships, and child link claims.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "parent_profiles" not in tables:
        op.create_table(
            "parent_profiles",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_parent_profiles_user_id"),
        )
        op.create_index("ix_parent_profiles_user_id", "parent_profiles", ["user_id"])

    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "parent_student_relationships" not in tables:
        op.create_table(
            "parent_student_relationships",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("parent_profile_id", sa.UUID(), nullable=False),
            sa.Column("student_id", sa.UUID(), nullable=False),
            sa.Column("relationship_type", sa.String(length=30), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["parent_profile_id"], ["parent_profiles.id"]),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "parent_profile_id",
                "student_id",
                name="uq_parent_student_relationship",
            ),
        )
        op.create_index(
            "ix_parent_student_relationships_parent_profile_id",
            "parent_student_relationships",
            ["parent_profile_id"],
        )
        op.create_index(
            "ix_parent_student_relationships_student_id",
            "parent_student_relationships",
            ["student_id"],
        )

    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "child_link_claims" not in tables:
        op.create_table(
            "child_link_claims",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("student_id", sa.UUID(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_child_link_claims_token_hash"),
        )
        op.create_index("ix_child_link_claims_student_id", "child_link_claims", ["student_id"])
        op.create_index("ix_child_link_claims_token_hash", "child_link_claims", ["token_hash"])

    # Non-destructive compatibility migration from the legacy students.parent_id field.
    # One ParentProfile is created for each distinct legacy parent user, then active
    # relationship rows are inserted for students that do not already have one.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO parent_profiles (id, user_id, created_at)
            SELECT gen_random_uuid(), legacy.parent_id, CURRENT_TIMESTAMP
            FROM (
                SELECT DISTINCT parent_id
                FROM students
                WHERE parent_id IS NOT NULL
            ) AS legacy
            WHERE NOT EXISTS (
                SELECT 1 FROM parent_profiles pp WHERE pp.user_id = legacy.parent_id
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO parent_student_relationships
                (id, parent_profile_id, student_id, relationship_type, active, created_at, unlinked_at)
            SELECT gen_random_uuid(), pp.id, s.id, 'GUARDIAN', TRUE, CURRENT_TIMESTAMP, NULL
            FROM students s
            JOIN parent_profiles pp ON pp.user_id = s.parent_id
            WHERE s.parent_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM parent_student_relationships psr
                  WHERE psr.parent_profile_id = pp.id AND psr.student_id = s.id
              )
            """
        )
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "child_link_claims" in tables:
        op.drop_table("child_link_claims")
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "parent_student_relationships" in tables:
        op.drop_table("parent_student_relationships")
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "parent_profiles" in tables:
        op.drop_table("parent_profiles")
