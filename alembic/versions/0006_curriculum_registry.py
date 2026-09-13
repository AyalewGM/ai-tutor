"""Add versioned curriculum registry and jurisdiction isolation foundations.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13

The repository's legacy 0001 migration calls ``Base.metadata.create_all()``. On a
fresh database that can pre-create tables/columns added by later model imports.
This migration is therefore intentionally idempotent at the schema-object level
so it works both for fresh CI databases and real upgrades from revision 0005.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return table in set(_inspector().get_table_names())


def _column_names(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def _index_names(table: str) -> set[str]:
    return {index["name"] for index in _inspector().get_indexes(table) if index.get("name")}


def _unique_names(table: str) -> set[str]:
    return {
        constraint["name"]
        for constraint in _inspector().get_unique_constraints(table)
        if constraint.get("name")
    }


def _foreign_key_names(table: str) -> set[str]:
    return {
        key["name"] for key in _inspector().get_foreign_keys(table) if key.get("name")
    }


def _drop_single_column_unique(table: str, column: str) -> None:
    for constraint in _inspector().get_unique_constraints(table):
        if constraint.get("column_names") == [column] and constraint.get("name"):
            op.drop_constraint(constraint["name"], table, type_="unique")

    for index in _inspector().get_indexes(table):
        if (
            index.get("unique")
            and index.get("column_names") == [column]
            and index.get("name")
        ):
            op.drop_index(index["name"], table_name=table)


def _ensure_jurisdictions() -> None:
    if not _table_exists("jurisdictions"):
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
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["parent_id"], ["jurisdictions.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("parent_id", "code", name="uq_jurisdictions_parent_code"),
        )
    indexes = _index_names("jurisdictions")
    if "ix_jurisdictions_parent_id" not in indexes:
        op.create_index("ix_jurisdictions_parent_id", "jurisdictions", ["parent_id"])
    if "ix_jurisdictions_code" not in indexes:
        op.create_index("ix_jurisdictions_code", "jurisdictions", ["code"])
    if "uq_jurisdictions_root_code" not in indexes:
        op.create_index(
            "uq_jurisdictions_root_code",
            "jurisdictions",
            ["code"],
            unique=True,
            postgresql_where=sa.text("parent_id IS NULL"),
        )


def _ensure_authorities() -> None:
    if not _table_exists("education_authorities"):
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
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "jurisdiction_id",
                "code",
                name="uq_education_authorities_jurisdiction_code",
            ),
        )
    indexes = _index_names("education_authorities")
    if "ix_education_authorities_jurisdiction_id" not in indexes:
        op.create_index(
            "ix_education_authorities_jurisdiction_id",
            "education_authorities",
            ["jurisdiction_id"],
        )
    if "ix_education_authorities_code" not in indexes:
        op.create_index("ix_education_authorities_code", "education_authorities", ["code"])

    if not _table_exists("authority_roles"):
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
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
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
    indexes = _index_names("authority_roles")
    if "ix_authority_roles_authority_id" not in indexes:
        op.create_index("ix_authority_roles_authority_id", "authority_roles", ["authority_id"])
    if "ix_authority_roles_role_type" not in indexes:
        op.create_index("ix_authority_roles_role_type", "authority_roles", ["role_type"])


def _ensure_curriculum_columns() -> None:
    columns = _column_names("curricula")
    additions = {
        "authority_id": sa.Column("authority_id", sa.UUID(), nullable=True),
        "version": sa.Column("version", sa.String(length=80), nullable=True),
        "effective_from": sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        "effective_to": sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        "source_uri": sa.Column("source_uri", sa.Text(), nullable=True),
        "provenance_json": sa.Column(
            "provenance_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    }
    for name, column in additions.items():
        if name not in columns:
            op.add_column("curricula", column)

    _drop_single_column_unique("curricula", "code")
    if "fk_curricula_authority_id" not in _foreign_key_names("curricula"):
        has_authority_fk = any(
            key.get("constrained_columns") == ["authority_id"]
            for key in _inspector().get_foreign_keys("curricula")
        )
        if not has_authority_fk:
            op.create_foreign_key(
                "fk_curricula_authority_id",
                "curricula",
                "education_authorities",
                ["authority_id"],
                ["id"],
            )

    indexes = _index_names("curricula")
    if "ix_curricula_authority_id" not in indexes:
        op.create_index("ix_curricula_authority_id", "curricula", ["authority_id"])
    if "ix_curricula_code" not in indexes:
        op.create_index("ix_curricula_code", "curricula", ["code"], unique=False)

    bind = op.get_bind()
    bind.execute(sa.text("UPDATE curricula SET version = '1' WHERE version IS NULL"))
    version = next(column for column in _inspector().get_columns("curricula") if column["name"] == "version")
    if version.get("nullable", True):
        op.alter_column("curricula", "version", nullable=False)
    if "uq_curricula_authority_code_version" not in _unique_names("curricula"):
        op.create_unique_constraint(
            "uq_curricula_authority_code_version",
            "curricula",
            ["authority_id", "code", "version"],
        )


def _ensure_overlay_and_enrollment_tables() -> None:
    if not _table_exists("local_implementation_overlays"):
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
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
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
    indexes = _index_names("local_implementation_overlays")
    if "ix_local_implementation_overlays_local_authority_id" not in indexes:
        op.create_index(
            "ix_local_implementation_overlays_local_authority_id",
            "local_implementation_overlays",
            ["local_authority_id"],
        )
    if "ix_local_implementation_overlays_curriculum_id" not in indexes:
        op.create_index(
            "ix_local_implementation_overlays_curriculum_id",
            "local_implementation_overlays",
            ["curriculum_id"],
        )

    if not _table_exists("student_curriculum_enrollments"):
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
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.ForeignKeyConstraint(["local_authority_id"], ["education_authorities.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = _index_names("student_curriculum_enrollments")
    index_specs = {
        "ix_student_curriculum_enrollments_student_id": ["student_id"],
        "ix_student_curriculum_enrollments_curriculum_id": ["curriculum_id"],
        "ix_student_curriculum_enrollments_local_authority_id": ["local_authority_id"],
    }
    for name, columns in index_specs.items():
        if name not in indexes:
            op.create_index(name, "student_curriculum_enrollments", columns)
    if "uq_student_curriculum_enrollments_one_active" not in indexes:
        op.create_index(
            "uq_student_curriculum_enrollments_one_active",
            "student_curriculum_enrollments",
            ["student_id"],
            unique=True,
            postgresql_where=sa.text("active = TRUE"),
        )


def _ensure_session_columns() -> None:
    columns = _column_names("tutor_sessions")
    if "curriculum_id" not in columns:
        op.add_column("tutor_sessions", sa.Column("curriculum_id", sa.UUID(), nullable=True))
    if "curriculum_enrollment_id" not in columns:
        op.add_column(
            "tutor_sessions",
            sa.Column("curriculum_enrollment_id", sa.UUID(), nullable=True),
        )

    foreign_keys = _inspector().get_foreign_keys("tutor_sessions")
    constrained = {tuple(key.get("constrained_columns") or []) for key in foreign_keys}
    if ("curriculum_id",) not in constrained:
        op.create_foreign_key(
            "fk_tutor_sessions_curriculum_id",
            "tutor_sessions",
            "curricula",
            ["curriculum_id"],
            ["id"],
        )
    if ("curriculum_enrollment_id",) not in constrained:
        op.create_foreign_key(
            "fk_tutor_sessions_curriculum_enrollment_id",
            "tutor_sessions",
            "student_curriculum_enrollments",
            ["curriculum_enrollment_id"],
            ["id"],
        )

    indexes = _index_names("tutor_sessions")
    if "ix_tutor_sessions_curriculum_id" not in indexes:
        op.create_index("ix_tutor_sessions_curriculum_id", "tutor_sessions", ["curriculum_id"])
    if "ix_tutor_sessions_curriculum_enrollment_id" not in indexes:
        op.create_index(
            "ix_tutor_sessions_curriculum_enrollment_id",
            "tutor_sessions",
            ["curriculum_enrollment_id"],
        )


def _ensure_skill_scope_constraint() -> None:
    _drop_single_column_unique("skills", "code")
    indexes = _index_names("skills")
    if "ix_skills_code" not in indexes:
        op.create_index("ix_skills_code", "skills", ["code"], unique=False)
    if "uq_skills_curriculum_code" not in _unique_names("skills"):
        op.create_unique_constraint(
            "uq_skills_curriculum_code",
            "skills",
            ["curriculum_id", "code"],
        )


def _backfill_registry() -> None:
    bind = op.get_bind()
    statements = [
        """
        INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
        SELECT gen_random_uuid(), NULL, 'US', 'United States', 'COUNTRY'
        WHERE NOT EXISTS (
            SELECT 1 FROM jurisdictions WHERE parent_id IS NULL AND code = 'US'
        )
        """,
        """
        INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
        SELECT gen_random_uuid(), c.id, 'MD', 'Maryland', 'STATE_PROVINCE_TERRITORY'
        FROM jurisdictions c
        WHERE c.parent_id IS NULL AND c.code = 'US'
          AND NOT EXISTS (
              SELECT 1 FROM jurisdictions j WHERE j.parent_id = c.id AND j.code = 'MD'
          )
        """,
        """
        INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
        SELECT gen_random_uuid(), md.id, 'MONTGOMERY_COUNTY', 'Montgomery County',
               'LOCAL_EDUCATION_AREA'
        FROM jurisdictions md
        WHERE md.code = 'MD'
          AND NOT EXISTS (
              SELECT 1 FROM jurisdictions j
              WHERE j.parent_id = md.id AND j.code = 'MONTGOMERY_COUNTY'
          )
        """,
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
        """,
        """
        INSERT INTO education_authorities
            (id, jurisdiction_id, code, name, authority_type, source_uri)
        SELECT gen_random_uuid(), local.id, 'MCPS',
               'Montgomery County Board of Education / MCPS', 'COUNTY_BOARD',
               'https://www.montgomeryschoolsmd.org/'
        FROM jurisdictions local
        WHERE local.code = 'MONTGOMERY_COUNTY'
          AND NOT EXISTS (
              SELECT 1 FROM education_authorities ea
              WHERE ea.jurisdiction_id = local.id AND ea.code = 'MCPS'
          )
        """,
        """
        UPDATE curricula c
        SET authority_id = ea.id,
            version = COALESCE(c.version, '1'),
            source_uri = COALESCE(
                c.source_uri,
                'https://www.montgomeryschoolsmd.org/curriculum/middleschool/grade8/'
            )
        FROM education_authorities ea
        WHERE c.code = 'MCPS_MATH_8' AND ea.code = 'MCPS' AND c.authority_id IS NULL
        """,
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
        """,
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
        """,
        """
        INSERT INTO student_curriculum_enrollments
            (id, student_id, curriculum_id, local_authority_id, active, effective_from, source_uri)
        SELECT gen_random_uuid(), s.id, s.curriculum_id, ea.id, TRUE,
               CURRENT_TIMESTAMP, 'legacy-backfill'
        FROM students s
        LEFT JOIN education_authorities ea ON ea.code = 'MCPS'
        WHERE s.curriculum_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM student_curriculum_enrollments e
              WHERE e.student_id = s.id AND e.active = TRUE
          )
        """,
        """
        UPDATE tutor_sessions ts
        SET curriculum_id = sk.curriculum_id,
            curriculum_enrollment_id = (
                SELECT e.id
                FROM student_curriculum_enrollments e
                WHERE e.student_id = ts.student_id AND e.active = TRUE
                ORDER BY e.effective_from DESC
                LIMIT 1
            )
        FROM skills sk
        WHERE sk.id = ts.primary_skill_id AND ts.curriculum_id IS NULL
        """,
        """
        INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
        SELECT gen_random_uuid(), NULL, 'CA', 'Canada', 'COUNTRY'
        WHERE NOT EXISTS (
            SELECT 1 FROM jurisdictions WHERE parent_id IS NULL AND code = 'CA'
        )
        """,
        """
        INSERT INTO jurisdictions (id, parent_id, code, name, jurisdiction_type)
        SELECT gen_random_uuid(), c.id, 'ON', 'Ontario', 'STATE_PROVINCE_TERRITORY'
        FROM jurisdictions c
        WHERE c.parent_id IS NULL AND c.code = 'CA'
          AND NOT EXISTS (
              SELECT 1 FROM jurisdictions j WHERE j.parent_id = c.id AND j.code = 'ON'
          )
        """,
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
        """,
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
        """,
        """
        INSERT INTO curricula
            (id, code, name, jurisdiction, grade_level, authority_id, version, source_uri, active)
        SELECT gen_random_uuid(), 'MTH1W', 'Grade 9 Mathematics (MTH1W)',
               'Ontario, Canada', '9', ea.id, '2021',
               'https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w',
               TRUE
        FROM education_authorities ea
        WHERE ea.code = 'ON_MIN_ED'
          AND NOT EXISTS (
              SELECT 1 FROM curricula c
              WHERE c.authority_id = ea.id AND c.code = 'MTH1W' AND c.version = '2021'
          )
        """,
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
        """,
        """
        INSERT INTO local_implementation_overlays
            (id, local_authority_id, curriculum_id, code, name, overlay_type,
             version, source_uri, active)
        SELECT gen_random_uuid(), ocdsb.id, c.id, 'OCDSB_MTH1W_CONTEXT',
               'OCDSB implementation context for MTH1W', 'IMPLEMENTATION_CONTEXT',
               '1', 'https://www.ocdsb.ca/', TRUE
        FROM education_authorities ocdsb
        JOIN curricula c ON c.code = 'MTH1W'
        WHERE ocdsb.code = 'OCDSB'
          AND NOT EXISTS (
              SELECT 1 FROM local_implementation_overlays lio
              WHERE lio.local_authority_id = ocdsb.id
                AND lio.curriculum_id = c.id
                AND lio.code = 'OCDSB_MTH1W_CONTEXT'
                AND lio.version = '1'
          )
        """,
    ]
    for statement in statements:
        bind.execute(sa.text(statement))


def upgrade() -> None:
    _ensure_jurisdictions()
    _ensure_authorities()
    _ensure_curriculum_columns()
    _ensure_overlay_and_enrollment_tables()
    _ensure_session_columns()
    _ensure_skill_scope_constraint()
    _backfill_registry()


def downgrade() -> None:
    # F-006 is additive by design. Downgrade removes only objects introduced by
    # this revision when they exist; legacy curriculum/student data is retained.
    if _table_exists("student_curriculum_enrollments"):
        op.drop_table("student_curriculum_enrollments")
    if _table_exists("local_implementation_overlays"):
        op.drop_table("local_implementation_overlays")
    if _table_exists("authority_roles"):
        op.drop_table("authority_roles")
    if _table_exists("education_authorities"):
        op.drop_table("education_authorities")
    if _table_exists("jurisdictions"):
        op.drop_table("jurisdictions")
