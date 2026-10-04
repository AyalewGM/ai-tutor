"""Country/region codes for the profile → curriculum cascade.

Adds country_code + region_code to parent_profiles (the family's chosen
jurisdiction, kept for analytics) and to curricula (normalized from the
authority → jurisdiction tree, with a free-text fallback for legacy rows
whose jurisdiction was only ever a display string).

Revision ID: 0028_region_codes
Revises: 0027_family_approval
"""

import sqlalchemy as sa

from alembic import op

revision = "0028_region_codes"
down_revision = "0027_family_approval"
branch_labels = None
depends_on = None

# Fallback for curricula whose jurisdiction is only a display string.
_TEXT_REGION_MAP = [
    ("ontario", ("CA", "ON")),
    ("maryland", ("US", "MD")),
    ("columbia", ("US", "DC")),
    ("virginia", ("US", "VA")),
]


def _region_from_text(jurisdiction: str | None) -> tuple[str | None, str | None]:
    if not jurisdiction:
        return None, None
    text = jurisdiction.lower()
    for needle, (country, region) in _TEXT_REGION_MAP:
        if needle in text:
            return country, region
    return None, None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    parent_cols = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "country_code" not in parent_cols:
        op.add_column("parent_profiles", sa.Column("country_code", sa.String(2)))
    if "region_code" not in parent_cols:
        op.add_column("parent_profiles", sa.Column("region_code", sa.String(3)))

    curr_cols = {c["name"] for c in inspector.get_columns("curricula")}
    if "country_code" not in curr_cols:
        op.add_column("curricula", sa.Column("country_code", sa.String(2)))
    if "region_code" not in curr_cols:
        op.add_column("curricula", sa.Column("region_code", sa.String(20)))

    index_names = {ix["name"] for ix in inspector.get_indexes("curricula")}
    if "ix_curricula_region_code" not in index_names:
        op.create_index("ix_curricula_region_code", "curricula", ["region_code"])

    # Backfill: Curriculum → EducationAuthority → Jurisdiction, walking
    # parents until the STATE_PROVINCE_TERRITORY and COUNTRY rows are found.
    jurisdictions = {
        row.id: row
        for row in bind.execute(
            sa.text(
                "SELECT id, code, jurisdiction_type, parent_id FROM jurisdictions"
            )
        )
    }
    authority_jurisdiction = {
        row.id: row.jurisdiction_id
        for row in bind.execute(
            sa.text("SELECT id, jurisdiction_id FROM education_authorities")
        )
    }
    for row in bind.execute(
        sa.text("SELECT id, jurisdiction, authority_id FROM curricula")
    ):
        country = region = None
        jurisdiction_id = authority_jurisdiction.get(row.authority_id)
        while jurisdiction_id is not None:
            node = jurisdictions.get(jurisdiction_id)
            if node is None:
                break
            if node.jurisdiction_type == "STATE_PROVINCE_TERRITORY" and region is None:
                region = node.code
            if node.jurisdiction_type == "COUNTRY":
                country = node.code
            jurisdiction_id = node.parent_id
        if region is None:
            country, region = _region_from_text(row.jurisdiction)
        if country is not None or region is not None:
            bind.execute(
                sa.text(
                    "UPDATE curricula SET country_code = :country, "
                    "region_code = :region WHERE id = :id"
                ),
                {"country": country, "region": region, "id": row.id},
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    index_names = {ix["name"] for ix in inspector.get_indexes("curricula")}
    if "ix_curricula_region_code" in index_names:
        op.drop_index("ix_curricula_region_code", table_name="curricula")
    curr_cols = {c["name"] for c in inspector.get_columns("curricula")}
    if "region_code" in curr_cols:
        op.drop_column("curricula", "region_code")
    if "country_code" in curr_cols:
        op.drop_column("curricula", "country_code")
    parent_cols = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "region_code" in parent_cols:
        op.drop_column("parent_profiles", "region_code")
    if "country_code" in parent_cols:
        op.drop_column("parent_profiles", "country_code")
