"""Pilot family approval gate on parent_profiles.

Existing families are backfilled APPROVED (server default) so nobody
currently using Mihur is locked out.

Revision ID: 0027_family_approval
Revises: 0026_admin_mfa_audit
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0027_family_approval"
down_revision = "0026_admin_mfa_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "approval_status" not in columns:
        op.add_column(
            "parent_profiles",
            sa.Column(
                "approval_status", sa.String(20), server_default="APPROVED", nullable=False
            ),
        )
        op.create_check_constraint(
            "ck_parent_approval_status",
            "parent_profiles",
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
        )
        op.create_index(
            "ix_parent_profiles_approval_status", "parent_profiles", ["approval_status"]
        )
    if "approval_decided_at" not in columns:
        op.add_column(
            "parent_profiles",
            sa.Column("approval_decided_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "approval_decided_by_user_id" not in columns:
        op.add_column(
            "parent_profiles",
            sa.Column(
                "approval_decided_by_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(
                    "users.id", ondelete="SET NULL", name="fk_parent_profiles_approval_decider"
                ),
                nullable=True,
            ),
        )
    if "rejection_reason" not in columns:
        op.add_column(
            "parent_profiles", sa.Column("rejection_reason", sa.String(500), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("parent_profiles", "rejection_reason")
    op.drop_column("parent_profiles", "approval_decided_by_user_id")
    op.drop_column("parent_profiles", "approval_decided_at")
    op.drop_index("ix_parent_profiles_approval_status", table_name="parent_profiles")
    op.drop_constraint("ck_parent_approval_status", "parent_profiles", type_="check")
    op.drop_column("parent_profiles", "approval_status")
