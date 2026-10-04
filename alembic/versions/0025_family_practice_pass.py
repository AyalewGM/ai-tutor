"""Add one active pilot practice pass per family.

Revision ID: 0025_family_practice_pass
Revises: 0024_tutor_turns_time_index
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0025_family_practice_pass"
down_revision = "0024_tutor_turns_time_index"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Some local/container bootstrap paths may import ORM metadata before
    # Alembic runs. Keep the migration safe and convergent in that case.
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "family_practice_passes" not in tables:
        op.create_table(
        "family_practice_passes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parent_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("parent_profile_id", name="uq_family_practice_pass_parent"),
        sa.UniqueConstraint("token_hash", name="uq_family_practice_pass_token"),
    )
        op.create_index("ix_family_practice_pass_token_hash", "family_practice_passes", ["token_hash"])
    if "learner_pass_sessions" not in tables:
        op.create_table(
        "learner_pass_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("practice_pass_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("family_practice_passes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_learner_pass_session_token"),
    )
        op.create_index("ix_learner_pass_session_token_hash", "learner_pass_sessions", ["token_hash"])

def downgrade() -> None:
    op.drop_table("learner_pass_sessions")
    op.drop_table("family_practice_passes")
