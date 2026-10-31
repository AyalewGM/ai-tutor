"""Real PostgreSQL identity checks in the dedicated, disposable CI service only.

The native host/read-only-grant boundary is explicitly mocked. These tests prove
actual PostgreSQL database, role and cluster identity, not a live host enrollment.
"""
import copy
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.services import content_publishing as publisher
from app.services import development_content_authorization as development
from tests import test_development_content_authorization as runtime_fixtures

ADMIN_URL = "postgresql+psycopg://postgres@localhost:5432/postgres"
ROLE_URL = "postgresql+psycopg://mihur_staging@localhost:5432/mihur_staging"
TARGET_ADMIN_URL = "postgresql+psycopg://postgres@localhost:5432/mihur_staging"
_REAL_DATABASE_IDENTITY = development._database_identity


runtime_owner_key = runtime_fixtures.runtime_owner_key
development_state = runtime_fixtures.development_state


@pytest.fixture(scope="module")
def isolated_postgresql():
    if not (os.environ.get("CI") == "true" and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("MIHUR_DEV_AUTH_PG_ADMIN_URL") == ADMIN_URL):
        pytest.skip("Dedicated isolated GitHub Actions PostgreSQL identity fixture not enabled")
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    role_engine = target_admin = None
    created_database = created_role = False
    database_oid = role_oid = None
    try:
        with admin.connect() as connection:
            identity = connection.execute(text(
                "SELECT pg_catalog.current_database(), current_user"
            )).one()
            assert tuple(identity) == ("postgres", "postgres"), "Unexpected CI admin identity"
            existing_database = connection.scalar(text(
                "SELECT oid FROM pg_catalog.pg_database WHERE datname = 'mihur_staging'"
            ))
            existing_role = connection.scalar(text(
                "SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'mihur_staging'"
            ))
            assert existing_database is None and existing_role is None, (
                "Refusing any DDL: mihur_staging database or role already exists"
            )
            connection.execute(text(
                "CREATE ROLE mihur_staging LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOREPLICATION NOBYPASSRLS"
            ))
            created_role = True
            role_oid = connection.scalar(text(
                "SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'mihur_staging'"
            ))
            connection.execute(text("CREATE DATABASE mihur_staging OWNER mihur_staging"))
            created_database = True
            database_oid = connection.scalar(text(
                "SELECT oid FROM pg_catalog.pg_database WHERE datname = 'mihur_staging'"
            ))
            cluster_id = connection.scalar(text(
                "SELECT system_identifier::text FROM pg_catalog.pg_control_system()"
            ))
        target_admin = create_engine(TARGET_ADMIN_URL)
        with target_admin.begin() as connection:
            # The grant is confined to this newly created disposable database.
            connection.execute(text(
                "GRANT EXECUTE ON FUNCTION pg_catalog.pg_control_system() TO mihur_staging"
            ))
        role_engine = create_engine(ROLE_URL)
        yield {"role": role_engine, "admin": admin, "target_admin": target_admin,
               "cluster_id": cluster_id}
    finally:
        # No sessions/connections remain before removing only objects this fixture
        # created. Never terminate other backends or use wildcard/IF EXISTS cleanup.
        if role_engine is not None:
            role_engine.dispose()
        if target_admin is not None:
            target_admin.dispose()
        try:
            with admin.connect() as connection:
                if created_database:
                    actual = connection.execute(text(
                        "SELECT oid, datdba FROM pg_catalog.pg_database "
                        "WHERE datname = 'mihur_staging'"
                    )).one()
                    assert tuple(actual) == (database_oid, role_oid), (
                        "Refusing cleanup of a replaced or foreign database"
                    )
                    connection.execute(text("DROP DATABASE mihur_staging"))
                if created_role:
                    actual_role = connection.scalar(text(
                        "SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'mihur_staging'"
                    ))
                    assert actual_role == role_oid, "Refusing cleanup of a replaced or foreign role"
                    connection.execute(text("DROP ROLE mihur_staging"))
        finally:
            admin.dispose()


def _bind_actual_cluster(state, cluster_id, monkeypatch):
    # Keep the existing synthetic root-grant/machine fixture explicit, but restore
    # the real PostgreSQL identity function instead of that fixture's identity mock.
    state["context"]["database_cluster_id"] = cluster_id
    state["grant"]["release"] = copy.deepcopy(state["context"])
    state["resign"]()
    monkeypatch.setattr(development, "_database_identity", _REAL_DATABASE_IDENTITY)


def test_actual_postgresql_database_role_and_cluster_identity(isolated_postgresql):
    with Session(isolated_postgresql["role"]) as db:
        actual = _REAL_DATABASE_IDENTITY(db)
    assert actual == {"database": "mihur_staging", "database_role": "mihur_staging",
                      "database_cluster_id": isolated_postgresql["cluster_id"]}


def test_runtime_authorization_accepts_actual_owned_postgresql_target(
    isolated_postgresql, development_state, monkeypatch,
):
    _bind_actual_cluster(development_state, isolated_postgresql["cluster_id"], monkeypatch)
    with Session(isolated_postgresql["role"]) as db:
        assert publisher.authorize_package(development_state["manifest"], db) == (
            development_state["context"]["package_sha256"]
        )


@pytest.mark.parametrize("target", ["admin", "target_admin"])
def test_runtime_rejects_actual_wrong_database_or_role(
    isolated_postgresql, development_state, monkeypatch, target,
):
    _bind_actual_cluster(development_state, isolated_postgresql["cluster_id"], monkeypatch)
    with Session(isolated_postgresql[target]) as db:
        actual = _REAL_DATABASE_IDENTITY(db)
        assert actual["database_role"] == "postgres"
        assert actual["database"] == ("postgres" if target == "admin" else "mihur_staging")
        with pytest.raises(publisher.PublicationBlocked):
            publisher.authorize_package(development_state["manifest"], db)


def test_runtime_rejects_expected_cluster_different_from_actual_server(
    isolated_postgresql, development_state, monkeypatch,
):
    _bind_actual_cluster(development_state, isolated_postgresql["cluster_id"], monkeypatch)
    actual_cluster = isolated_postgresql["cluster_id"]
    mismatched_cluster = "1" if actual_cluster != "1" else "2"
    development_state["context"]["database_cluster_id"] = mismatched_cluster
    development_state["grant"]["release"] = copy.deepcopy(development_state["context"])
    development_state["resign"]()
    with Session(isolated_postgresql["role"]) as db:
        assert _REAL_DATABASE_IDENTITY(db)["database_cluster_id"] == actual_cluster
        with pytest.raises(publisher.PublicationBlocked):
            publisher.authorize_package(development_state["manifest"], db)
