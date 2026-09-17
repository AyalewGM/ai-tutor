"""Scope misconception codes by skill.

Revision ID: 0012
Revises: 0011
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("misconceptions_code_key", "misconceptions", type_="unique")
    op.create_unique_constraint(
        "uq_misconceptions_skill_code",
        "misconceptions",
        ["skill_id", "code"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_misconceptions_skill_code", "misconceptions", type_="unique")
    op.create_unique_constraint("misconceptions_code_key", "misconceptions", ["code"])
