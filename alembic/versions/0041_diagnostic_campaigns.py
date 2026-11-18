"""Curriculum-wide diagnostic campaigns and campaign linkage on probe sessions."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0041_diagnostic_campaigns"
down_revision = "0040_board_management"
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "diagnostic_campaigns" not in tables:
        op.create_table(
            "diagnostic_campaigns",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("curriculum_id", UUID(as_uuid=True), sa.ForeignKey("curricula.id"), nullable=True),
            sa.Column(
                "curriculum_enrollment_id",
                UUID(as_uuid=True),
                sa.ForeignKey("student_curriculum_enrollments.id"),
                nullable=True,
            ),
            sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
            sa.Column("target_skill_ids", JSONB, nullable=False, server_default="[]"),
            sa.Column("probed_target_ids", JSONB, nullable=False, server_default="[]"),
            sa.Column("recommended_skill_id", UUID(as_uuid=True), sa.ForeignKey("skills.id"), nullable=True),
            sa.Column("question_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("max_questions", sa.Integer, nullable=False, server_default="24"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_diagnostic_campaigns_student_id", "diagnostic_campaigns", ["student_id"])
        op.create_index("ix_diagnostic_campaigns_curriculum_id", "diagnostic_campaigns", ["curriculum_id"])
        op.create_index(
            "ix_diagnostic_campaigns_curriculum_enrollment_id",
            "diagnostic_campaigns",
            ["curriculum_enrollment_id"],
        )

    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("diagnostic_sessions")}
    if "campaign_id" not in columns:
        op.add_column(
            "diagnostic_sessions",
            sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("diagnostic_campaigns.id"), nullable=True),
        )
        op.create_index("ix_diagnostic_sessions_campaign_id", "diagnostic_sessions", ["campaign_id"])


def downgrade():
    op.drop_index("ix_diagnostic_sessions_campaign_id", table_name="diagnostic_sessions")
    op.drop_column("diagnostic_sessions", "campaign_id")
    op.drop_table("diagnostic_campaigns")
