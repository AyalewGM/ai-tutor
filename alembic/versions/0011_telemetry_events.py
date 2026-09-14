"""Add append-only pilot telemetry events.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telemetry_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("learner_pseudonymous_id", sa.String(length=100), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("policy_version", sa.String(length=80), nullable=True),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.Column("retention_class", sa.String(length=40), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("deletion_audit_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_telemetry_events_event_type", ["event_type"]),
        ("ix_telemetry_events_occurred_at", ["occurred_at"]),
        ("ix_telemetry_events_learner_pseudonymous_id", ["learner_pseudonymous_id"]),
        ("ix_telemetry_events_session_id", ["session_id"]),
        ("ix_telemetry_events_curriculum_id", ["curriculum_id"]),
        ("ix_telemetry_events_skill_id", ["skill_id"]),
        ("ix_telemetry_events_retention_class", ["retention_class"]),
    ):
        op.create_index(name, "telemetry_events", columns)


def downgrade() -> None:
    op.drop_table("telemetry_events")
