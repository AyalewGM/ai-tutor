"""Add versioned curriculum registry and jurisdiction isolation foundations.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_single_column_unique(table: str, column: str) -> None:
    inspector = sa.inspect(op.get_bind())
    for constraint in inspector.get_unique_constraints(table):
        if constraint.get("column_names") == [column] and constraint.get("name"):
            op.drop_constraint(constraint["name"], table, type_="unique")

    inspector = sa.inspect(op.get_bind())
    for index in inspector.get_indexes(table):
        if (
            index.get("unique")
            and index.get("column_names") == [column]
            and index.get("name")
        ):
            op.drop_index(index["name"], table_name=table)


def upgrade() -> None:
    op.create_table(
        "jurisdictions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction_type", sa.String(length=40), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["jurisdictions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_id", "code", name="uq_jurisdictions_parent_code"),
    )
    op.create_index("ix_jurisdictions_parent_id", "jurisdictions", ["parent_id"])
    op.create_index("ix_jurisdictions_code", "jurisdictions", ["code"])

    op.create_table(
        "education_authorities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("jurisdiction_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("authority_type", sa.String(length=40), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "jurisdiction_id", "code", name="uq_education_authorities_jurisdiction_code"
        ),
    )
    op.create_index(
        "ix_education_authorities_jurisdiction_id",
        "education_authorities",
        ["jurisdiction_id"],
    )
    op.create_index("ix_education_authorities_code", "education_authorities", ["code"])

    op.create_table(
        "authority_roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("authority_id", sa.UUID(), nullable=False),
        sa.Column("role_type", sa.String(length=50), nullable=False),
        sa.Column("subject_scope", sa.String(length=120), nullable=True),
        sa.Column("grade_scope", sa.String(length=120), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["authority_id"], ["education_authorities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "authority_id",
            "role_type",
            "subject_scope",
            "grade_scope",
            "effective_from",
            name="uq_authority_roles_scope",
        ),
    )
    op.create_index("ix_authority_roles_authority_id", "authority_roles", ["authority_id"])
    op.create_index("ix_authority_roles_role_type", "authority_roles", ["role_type"])

    _drop_single_column_unique("curricula", "code")
    op.add_column("curricula", sa.Column("authority_id", sa.UUID(), nullable=True))
    op.add_column("curricula", sa.Column("version", sa.String(length=80), nullable=True))
    op.add_column("curricula", sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True))
    op.add_column("curricula", sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True))
    op.add_column("curricula", sa.Column("source_uri", sa.Text(), nullable=True))
    op.add_column(
        "curricula",
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_curricula_authority_id",
        "curricula",
        "education_authorities",
        ["authority_id"],
        ["id"],
    )
    op.create_index("ix_curricula_authority_id", "curricula", ["authority_id"])
    op.create_index("ix_curricula_code", "curricula", ["code"], unique=False)

    bind = op.get_bind()
    bind.execute(sa.text("UPDATE curricula SET version = '1' WHERE version IS NULL"))
    op.alter_column("curricula", "version", nullable=False)
    op.create_unique_constraint(
        "uq_curricula_authority_code_version",
        "curricula",
        ["authority_id", "code", "version"],
    )

    op.create_table(
        "local_implementation_overlays",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("local_authority_id", sa.UUID(), nullable=False),
        sa.Column("curriculum_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("overlay_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["local_authority_id"], ["education_authorities.id"]),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "local_authority_id",
            "curriculum_id",
            "code",
            "version",
            name="uq_local_overlay_authority_curriculum_code_version",
        ),
    )
    op.create_index(
        "ix_local_implementation_overlays_local_authority_id",
        "local_implementation_overlays",
        ["local_authority_id"],
    )
    op.create_index(
        "ix_local_implementation_overlays_curriculum_id",
        "local_implementation_overlays",
        ["curriculum_id"],
    )

    op.create_table(
        "student_curriculum_enrollments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("curriculum_id", sa.UUID(), nullable=False),
        sa.Column("local_authority_id", sa.UUID(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
        sa.ForeignKeyConstraint(["local_authority_id"], ["education_authorities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_curriculum_enrollments_student_id",
        "student_curriculum_enrollments",
        ["student_id"],
    )
    op.create_index(
        "ix_student_curriculum_enrollments_curriculum_id",
        "student_curriculum_enrollments",
        ["curriculum_id"],
    )
    op.create_index(
        "ix_student_curriculum_enrollments_local_authority_id",
        "student_curriculum_enrollments",
        ["local_authority_id"],
    )
    op.create_index(
        "uq_student_curriculum_enrollments_one_active",
        "student_curriculum_enrollments",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("active = TRUE"),
    )

    op.add_column("tutor_sessions", sa.Column("curriculum_id", sa.UUID(), nullable=True))
    op.add_column(
        "tutor_sessions", sa.Column("curriculum_enrollment_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_tutor_sessions_curriculum_id",
        "tutor_sessions",
        "curricula",
        ["curriculum_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_tutor_sessions_curriculum_enrollment_id",
        "tutor_sessions",
        "student_curriculum_enrollments",
        ["curriculum_enrollment_id"],
        ["id"],
    )
    op.create_index("ix_tutor_sessions_curriculum_id", "tutor_sessions", ["curriculum_id"])
    op.create_index(
        "ix_tutor_sessions_curriculum_enrollment_id",
        "tutor_sessions",
        ["curriculum_enrollment_id"],
    )

    _drop_single_column_unique("skills", "code")
    op.create_index("ix_skills_code", "skills", ["code"], unique=False)
    op.create_unique_constraint(
        "uq_skills_curriculum_code", "skills", ["curriculum_id", "code"]
    )

    # Backfill a verified authority path for the legacy MCPS seed without deleting
    # legacy fields. gen_random_uuid() is already required by migration 0005.
    bind.execute(
        sa.text(
            """
            INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
            SELECT gen_random_uuid(), NULL, 'US', 'United States', 'COUNTRY'
            WHERE NOT EXISTS (SELECT 1 FROM jurisdictions WHERE parent_id IS NULL AND code = 'US')
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
            SELECT gen_random_uuid(), c.id, 'MD', 'Maryland', 'STATE_PROVINCE_TERRITORY'
            FROM jurisdictions c
            WHERE c.parent_id IS NULL AND c.code = 'US'
              AND NOT EXISTS (
                  SELECT 1 FROM jurisdictions j WHERE j.parent_id = c.id AND j.code = 'MD'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
            SELECT gen_random_uuid(), md.id, 'MONTGOMERY_COUNTY', 'Montgomery County', 'LOCAL_EDUCATION_AREA'
            FROM jurisdictions md
            WHERE md.code = 'MD'
              AND NOT EXISTS (
                  SELECT 1 FROM jurisdictions j
                  WHERE j.parent_id = md.id AND j.code = 'MONTGOMERY_COUNTY'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO education_authorities
                (id, jurisdiction_id, code, name, authority_type, source_uri)
            SELECT gen_random_uuid(), md.id, 'MSDE', 'Maryland State Department of Education',
                   'STATE_AGENCY', 'https://marylandpublicschools.org/'
            FROM jurisdictions md
            WHERE md.code = 'MD'
              AND NOT EXISTS (
                  SELECT 1 FROM education_authorities ea
                  WHERE ea.jurisdiction_id = md.id AND ea.code = 'MSDE'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO education_authorities
                (id, jurisdiction_id, code, name, authority_type, source_uri)
            SELECT gen_random_uuid(), local.id, 'MCPS', 'Montgomery County Public Schools',
                   'COUNTY_BOARD', 'https://www.montgomeryschoolsmd.org/'
            FROM jurisdictions local
            WHERE local.code = 'MONTGOMERY_COUNTY'
              AND NOT EXISTS (
                  SELECT 1 FROM education_authorities ea
                  WHERE ea.jurisdiction_id = local.id AND ea.code = 'MCPS'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE curricula c
            SET authority_id = ea.id,
                version = COALESCE(c.version, '1'),
                source_uri = COALESCE(c.source_uri, 'https://www.montgomeryschoolsmd.org/curriculum/middleschool/grade8/')
            FROM education_authorities ea
            WHERE c.code = 'MCPS_MATH_8' AND ea.code = 'MCPS' AND c.authority_id IS NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO authority_roles
                (id, authority_id, role_type, subject_scope, grade_scope, source_uri)
            SELECT gen_random_uuid(), ea.id, 'CURRICULUM', 'MATHEMATICS', '8',
                   'https://mgaleg.maryland.gov/mgawebsite/laws/StatuteText?article=ged&section=4-111'
            FROM education_authorities ea
            WHERE ea.code = 'MCPS'
              AND NOT EXISTS (
                  SELECT 1 FROM authority_roles ar
                  WHERE ar.authority_id = ea.id AND ar.role_type = 'CURRICULUM'
                    AND ar.subject_scope = 'MATHEMATICS' AND ar.grade_scope = '8'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO authority_roles
                (id, authority_id, role_type, subject_scope, grade_scope, source_uri)
            SELECT gen_random_uuid(), ea.id, 'STANDARDS', 'MATHEMATICS', NULL,
                   'https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article=ged&section=7-202.1'
            FROM education_authorities ea
            WHERE ea.code = 'MSDE'
              AND NOT EXISTS (
                  SELECT 1 FROM authority_roles ar
                  WHERE ar.authority_id = ea.id AND ar.role_type = 'STANDARDS'
                    AND ar.subject_scope = 'MATHEMATICS'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO student_curriculum_enrollments
                (id, student_id, curriculum_id, local_authority_id, active, effective_from, source_uri)
            SELECT gen_random_uuid(), s.id, s.curriculum_id, ea.id, TRUE, CURRENT_TIMESTAMP, 'legacy-backfill'
            FROM students s
            LEFT JOIN curricula c ON c.id = s.curriculum_id
            LEFT JOIN education_authorities ea ON ea.code = 'MCPS'
            WHERE s.curriculum_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM student_curriculum_enrollments e
                  WHERE e.student_id = s.id AND e.active = TRUE
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE tutor_sessions ts
            SET curriculum_id = sk.curriculum_id,
                curriculum_enrollment_id = e.id
            FROM skills sk
            LEFT JOIN student_curriculum_enrollments e
              ON e.student_id = ts.student_id AND e.active = TRUE
            WHERE sk.id = ts.primary_skill_id AND ts.curriculum_id IS NULL
            """
        )
    )

    # Seed Ontario authority identity and MTH1W registry record without assigning
    # any student. OCDSB is local context and does not own/fork MTH1W.
    bind.execute(
        sa.text(
            """
            INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
            SELECT gen_random_uuid(), NULL, 'CA', 'Canada', 'COUNTRY'
            WHERE NOT EXISTS (SELECT 1 FROM jurisdictions WHERE parent_id IS NULL AND code = 'CA')
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
            SELECT gen_random_uuid(), c.id, 'ON', 'Ontario', 'STATE_PROVINCE_TERRITORY'
            FROM jurisdictions c
            WHERE c.parent_id IS NULL AND c.code = 'CA'
              AND NOT EXISTS (
                  SELECT 1 FROM jurisdictions j WHERE j.parent_id = c.id AND j.code = 'ON'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO education_authorities
                (id, jurisdiction_id, code, name, authority_type, source_uri)
            SELECT gen_random_uuid(), j.id, 'ON_MIN_ED', 'Ontario Ministry of Education',
                   'MINISTRY', 'https://www.ontario.ca/page/ministry-education'
            FROM jurisdictions j
            WHERE j.code = 'ON'
              AND NOT EXISTS (
                  SELECT 1 FROM education_authorities ea
                  WHERE ea.jurisdiction_id = j.id AND ea.code = 'ON_MIN_ED'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO education_authorities
                (id, jurisdiction_id, code, name, authority_type, source_uri)
            SELECT gen_random_uuid(), j.id, 'OCDSB', 'Ottawa-Carleton District School Board',
                   'SCHOOL_BOARD', 'https://www.ocdsb.ca/'
            FROM jurisdictions j
            WHERE j.code = 'ON'
              AND NOT EXISTS (
                  SELECT 1 FROM education_authorities ea
                  WHERE ea.jurisdiction_id = j.id AND ea.code = 'OCDSB'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO curricula
                (id, code, name, jurisdiction, grade_level, authority_id, version, source_uri, active)
            SELECT gen_random_uuid(), 'MTH1W', 'Grade 9 Mathematics (MTH1W)', 'Ontario, Canada',
                   '9', ea.id, '2021',
                   'https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w', TRUE
            FROM education_authorities ea
            WHERE ea.code = 'ON_MIN_ED'
              AND NOT EXISTS (
                  SELECT 1 FROM curricula c
                  WHERE c.authority_id = ea.id AND c.code = 'MTH1W' AND c.version = '2021'
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO authority_roles
                (id, authority_id, role_type, subject_scope, grade_scope, source_uri)
            SELECT gen_random_uuid(), ea.id, 'CURRICULUM', 'MATHEMATICS', '9',
                   'https://www.ontario.ca/page/responsibility-publicly-funded-elementary-and-secondary-education'
            FROM education_authorities ea
            WHERE ea.code = 'ON_MIN_ED'
              AND NOT EXISTS (
                  SELECT 1 FROM authority_roles ar
                  WHERE ar.authority_id = ea.id AND ar.role_type = 'CURRICULUM'
                    AND ar.subject_scope = 'MATHEMATICS' AND ar.grade_scope = '9'
              )
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("uq_skills_curriculum_code", "skills", type_="unique")
    op.drop_index("ix_skills_code", table_name="skills")
    op.create_index("ix_skills_code", "skills", ["code"], unique=True)

    op.drop_index("ix_tutor_sessions_curriculum_enrollment_id", table_name="tutor_sessions")
    op.drop_index("ix_tutor_sessions_curriculum_id", table_name="tutor_sessions")
    op.drop_constraint(
        "fk_tutor_sessions_curriculum_enrollment_id", "tutor_sessions", type_="foreignkey"
    )
    op.drop_constraint("fk_tutor_sessions_curriculum_id", "tutor_sessions", type_="foreignkey")
    op.drop_column("tutor_sessions", "curriculum_enrollment_id")
    op.drop_column("tutor_sessions", "curriculum_id")

    op.drop_table("student_curriculum_enrollments")
    op.drop_table("local_implementation_overlays")

    op.drop_constraint("uq_curricula_authority_code_version", "curricula", type_="unique")
    op.drop_index("ix_curricula_code", table_name="curricula")
    op.drop_index("ix_curricula_authority_id", table_name="curricula")
    op.drop_constraint("fk_curricula_authority_id", "curricula", type_="foreignkey")
    op.drop_column("curricula", "provenance_json")
    op.drop_column("curricula", "source_uri")
    op.drop_column("curricula", "effective_to")
    op.drop_column("curricula", "effective_from")
    op.drop_column("curricula", "version")
    op.drop_column("curricula", "authority_id")
    op.create_index("ix_curricula_code", "curricula", ["code"], unique=True)

    op.drop_table("authority_roles")
    op.drop_table("education_authorities")
    op.drop_table("jurisdictions")
