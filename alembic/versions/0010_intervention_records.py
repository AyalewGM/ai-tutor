"""Add auditable intervention decision records.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return table in set(_inspector().get_table_names())


def _index_names(table: str) -> set[str]:
    return {
        index["name"]
        for index in _inspector().get_indexes(table)
        if index.get("name")
    }


def upgrade() -> None:
    if not _table_exists("intervention_records"):
        op.create_table(
            "intervention_records",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("target_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("prerequisite_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("policy_version", sa.String(length=80), nullable=False),
            sa.Column("state", sa.String(length=50), nullable=False),
            sa.Column("reason_code", sa.String(length=120), nullable=False),
            sa.Column("evidence_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("return_condition", sa.String(length=160), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="RECOMMENDED"),
            sa.Column("outcome_code", sa.String(length=80), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.ForeignKeyConstraint(["target_skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["prerequisite_skill_id"], ["skills.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = _index_names("intervention_records")
    for name, columns in (
        ("ix_intervention_records_student_id", ["student_id"]),
        ("ix_intervention_records_curriculum_id", ["curriculum_id"]),
        ("ix_intervention_records_target_skill_id", ["target_skill_id"]),
        ("ix_intervention_records_prerequisite_skill_id", ["prerequisite_skill_id"]),
        ("ix_intervention_records_policy_version", ["policy_version"]),
        ("ix_intervention_records_state", ["state"]),
        ("ix_intervention_records_status", ["status"]),
    ):
        if name not in indexes:
            op.create_index(name, "intervention_records", columns)


def downgrade() -> None:
    if not _table_exists("intervention_records"):
        return
    indexes = _index_names("intervention_records")
    for name in (
        "ix_intervention_records_status",
        "ix_intervention_records_state",
        "ix_intervention_records_policy_version",
        "ix_intervention_records_prerequisite_skill_id",
        "ix_intervention_records_target_skill_id",
        "ix_intervention_records_curriculum_id",
        "ix_intervention_records_student_id",
    ):
        if name in indexes:
            op.drop_index(name, table_name="intervention_records")
    op.drop_table("intervention_records")
