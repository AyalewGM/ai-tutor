"""Staff access: TOTP second factor, per-session MFA state, admin audit log.

Revision ID: 0026_admin_mfa_audit
Revises: 0025_family_practice_pass
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0026_admin_mfa_audit"
down_revision = "0025_family_practice_pass"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    session_columns = {c["name"] for c in inspector.get_columns("auth_sessions")}
    if "mfa_verified_at" not in session_columns:
        op.add_column(
            "auth_sessions",
            sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "admin_mfa" not in tables:
        op.create_table(
            "admin_mfa",
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("secret_encrypted", sa.Text(), nullable=False),
            sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_step", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "admin_audit_events" not in tables:
        op.create_table(
            "admin_audit_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "actor_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("actor_label", sa.String(255), nullable=False),
            sa.Column("action", sa.String(80), nullable=False),
            sa.Column("target_type", sa.String(50), nullable=True),
            sa.Column("target_id", sa.String(64), nullable=True),
            sa.Column("before_json", postgresql.JSONB(), nullable=True),
            sa.Column("after_json", postgresql.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_admin_audit_events_actor_user_id", "admin_audit_events", ["actor_user_id"]
        )
        op.create_index("ix_admin_audit_events_action", "admin_audit_events", ["action"])
        op.create_index("ix_admin_audit_events_created_at", "admin_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("admin_audit_events")
    op.drop_table("admin_mfa")
    op.drop_column("auth_sessions", "mfa_verified_at")
