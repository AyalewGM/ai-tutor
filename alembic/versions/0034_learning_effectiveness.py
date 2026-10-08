"""learning effectiveness measurement tables

Revision ID: 0034_learning_effectiveness
Revises: 0033_curriculum_schema

Adds tables for the learning-effectiveness measurement system:
- learning_assessments: assessment events at lifecycle points
- assessment_items: individual questions within assessments
- effectiveness_snapshots: computed measurement comparisons
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0034_learning_effectiveness"
down_revision = "0033_curriculum_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())

    if "learning_assessments" not in existing:
        op.create_table(
            "learning_assessments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("student_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("students.id"), nullable=False),
            sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("skills.id"), nullable=False),
            sa.Column("phase", sa.String(30), nullable=False),
            sa.Column("status", sa.String(30), default="SCHEDULED"),
            sa.Column("source_skill_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("skills.id"), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("family_codes_used", postgresql.JSONB, nullable=True),
            sa.Column("items_total", sa.Integer, default=0),
            sa.Column("items_answered", sa.Integer, default=0),
            sa.Column("items_correct", sa.Integer, default=0),
            sa.Column("items_independent_correct", sa.Integer, default=0),
            sa.Column("score", sa.Numeric(4, 3), nullable=True),
            sa.Column("independent_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("difficulty_mean", sa.Numeric(4, 2), nullable=True),
            sa.Column("misconceptions_detected", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_learning_assessments_student_skill",
                        "learning_assessments", ["student_id", "skill_id"])
        op.create_index("ix_learning_assessments_phase",
                        "learning_assessments", ["student_id", "phase"])
        op.create_index("ix_learning_assessments_scheduled",
                        "learning_assessments", ["scheduled_at"])

    if "assessment_items" not in existing:
        op.create_table(
            "assessment_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("assessment_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("learning_assessments.id"), nullable=False),
            sa.Column("sequence_number", sa.Integer, nullable=False),
            sa.Column("family_code", sa.String(100), nullable=False),
            sa.Column("variant_id", sa.String(40), nullable=False),
            sa.Column("generation_seed", sa.String(200), nullable=False),
            sa.Column("difficulty", sa.Integer, nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("canonical_answer", sa.Text, nullable=False),
            sa.Column("student_answer", sa.Text, nullable=True),
            sa.Column("is_correct", sa.Boolean, nullable=True),
            sa.Column("assistance_level", sa.Integer, default=0),
            sa.Column("misconception_code", sa.String(100), nullable=True),
            sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_assessment_items_assessment",
                        "assessment_items", ["assessment_id"])

    if "effectiveness_snapshots" not in existing:
        op.create_table(
            "effectiveness_snapshots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("student_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("students.id"), nullable=False),
            sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("skills.id"), nullable=False),
            sa.Column("measurement_type", sa.String(30), nullable=False),
            sa.Column("baseline_assessment_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("learning_assessments.id"), nullable=True),
            sa.Column("comparison_assessment_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey("learning_assessments.id"), nullable=True),
            sa.Column("baseline_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("baseline_independent_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("comparison_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("comparison_independent_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("observed_improvement", sa.Numeric(5, 3), nullable=True),
            sa.Column("independent_improvement", sa.Numeric(5, 3), nullable=True),
            sa.Column("baseline_difficulty_mean", sa.Numeric(4, 2), nullable=True),
            sa.Column("comparison_difficulty_mean", sa.Numeric(4, 2), nullable=True),
            sa.Column("difficulty_comparable", sa.Boolean, default=True),
            sa.Column("baseline_misconceptions", postgresql.JSONB, nullable=True),
            sa.Column("comparison_misconceptions", postgresql.JSONB, nullable=True),
            sa.Column("misconceptions_resolved", postgresql.JSONB, nullable=True),
            sa.Column("misconceptions_persisting", postgresql.JSONB, nullable=True),
            sa.Column("misconceptions_new", postgresql.JSONB, nullable=True),
            sa.Column("evidence_count", sa.Integer, default=0),
            sa.Column("evidence_sufficient", sa.Boolean, default=False),
            sa.Column("confidence_level", sa.String(20), default="INSUFFICIENT"),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        )
        op.create_index("ix_effectiveness_snapshots_student_skill",
                        "effectiveness_snapshots", ["student_id", "skill_id"])
        op.create_unique_constraint(
            "uq_effectiveness_snapshot_type",
            "effectiveness_snapshots",
            ["student_id", "skill_id", "measurement_type"],
        )


def downgrade() -> None:
    op.drop_table("effectiveness_snapshots")
    op.drop_table("assessment_items")
    op.drop_table("learning_assessments")
