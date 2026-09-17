"""Scope misconception codes by skill.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def _unique_constraints() -> list[dict[str, object]]:
    return sa.inspect(op.get_bind()).get_unique_constraints("misconceptions")


def upgrade() -> None:
    constraints = _unique_constraints()
    for constraint in constraints:
        if constraint.get("column_names") == ["code"] and constraint.get("name"):
            op.drop_constraint(str(constraint["name"]), "misconceptions", type_="unique")

    constraints = _unique_constraints()
    has_scoped_constraint = any(
        constraint.get("column_names") == ["skill_id", "code"]
        for constraint in constraints
    )
    if not has_scoped_constraint:
        op.create_unique_constraint(
            "uq_misconceptions_skill_code",
            "misconceptions",
            ["skill_id", "code"],
        )


def downgrade() -> None:
    constraints = _unique_constraints()
    for constraint in constraints:
        if (
            constraint.get("column_names") == ["skill_id", "code"]
            and constraint.get("name")
        ):
            op.drop_constraint(str(constraint["name"]), "misconceptions", type_="unique")

    constraints = _unique_constraints()
    has_global_constraint = any(
        constraint.get("column_names") == ["code"]
        for constraint in constraints
    )
    if not has_global_constraint:
        op.create_unique_constraint("misconceptions_code_key", "misconceptions", ["code"])
