"""Isolated API tests use real cookies and durable SQL rows, without seeded curricula.

SQLite is used for these sequential contracts; PostgreSQL lock concurrency remains
an additional integration gate, rather than being inferred from these tests.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketDisconnect

from app import collaboration_api as api
from app.auth import SESSION_COOKIE, _digest, create_session
from app.auth_models import AuthSession
from app.collaboration_models import BoardOperation, CollaborationBoard
from app.core.database import get_db
from app.middleware.pii_sanitizer import PIISanitizerMiddleware
from app.models import Student, User
from app.parent_models import FamilyPracticePass, LearnerPassSession, ParentProfile


@pytest.fixture
def family(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    for model in (
        User,
        Student,
        ParentProfile,
        AuthSession,
        FamilyPracticePass,
        LearnerPassSession,
        CollaborationBoard,
        BoardOperation,
    ):
        model.__table__.create(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    @event.listens_for(factory, "loaded_as_persistent")
    def sqlite_utc(_session, obj):
        # SQLite strips timezone information; PostgreSQL preserves it.
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime) and value.tzinfo is None:
                setattr(obj, column.name, value.replace(tzinfo=UTC))

    app = FastAPI()
    app.add_middleware(PIISanitizerMiddleware)
    app.include_router(api.router, prefix="/api/v1")

    def db_dependency():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = db_dependency
    monkeypatch.setattr(api, "SessionLocal", factory)
    with factory() as db:
        user = User(email="parent@example.test", role="PARENT")
        other = User(email="other@example.test", role="PARENT")
        db.add_all([user, other])
        db.flush()
        child = Student(parent_id=user.id, first_name="Child", grade_level="9")
        sibling = Student(parent_id=user.id, first_name="Sibling", grade_level="7")
        profile = ParentProfile(user_id=user.id)
        db.add_all([child, sibling, profile])
        db.flush()
        invite = FamilyPracticePass(
            parent_profile_id=profile.id,
            student_id=child.id,
            token_hash=_digest("invite"),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        db.add(invite)
        db.flush()
        db.add(
            LearnerPassSession(
                practice_pass_id=invite.id,
                student_id=child.id,
                token_hash=_digest("child-cookie"),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        parent_token, _ = create_session(db, user.id)
        other_token, _ = create_session(db, other.id)
        db.commit()
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, parent_token)
    yield client, factory, child.id, sibling.id, other_token, invite.id
    engine.dispose()


def create_board(client, child_id):
    result = client.post("/api/v1/together/boards", json={"student_id": str(child_id)})
    assert result.status_code == 200, result.text
    return f"/api/v1/together/boards/{result.json()['id']}"


def mark(**updates):
    return {
        "operation_id": str(uuid.uuid4()),
        "kind": "stroke",
        "points": [{"x": 12, "y": 30}],
        **updates,
    }


def test_cookie_access_family_isolation_and_learner_scope(family):
    client, _, child, sibling, other_token, _ = family
    path = create_board(client, child)
    sibling_path = create_board(client, sibling)
    client.cookies.set(SESSION_COOKIE, other_token)
    assert client.get(path).status_code == 404
    assert client.post(path + "/operations", json=mark()).status_code == 404
    assert client.get("/api/v1/together/boards").json() == []
    client.cookies.set("ai_tutor_learner", "child-cookie")
    assert client.get(path).status_code == 200
    assert client.get(sibling_path).status_code == 404
    assert (
        client.post("/api/v1/together/boards", json={"student_id": str(child)}).status_code == 404
    )
    assert len(client.get("/api/v1/together/boards").json()) == 1
    assert client.post(path + "/close").status_code == 403
    client.cookies.clear()
    assert client.get(path).status_code == 401


def test_replay_idempotency_and_author_scoped_undo(family):
    client, factory, child, *_ = family
    path = create_board(client, child)
    first = mark()
    assert client.post(path + "/operations", json=first).json() == {"revision": 1}
    assert client.post(path + "/operations", json=first).json() == {"revision": 1}
    assert (
        client.post(
            path + "/operations", json={**first, "points": [{"x": 99, "y": 99}]}
        ).status_code
        == 409
    )
    client.cookies.set("ai_tutor_learner", "child-cookie")
    undo = mark(kind="undo", points=[], target=first["operation_id"])
    assert client.post(path + "/operations", json=undo).status_code == 403
    second = mark(kind="text", points=[], text="2x + 3 = 11")
    assert client.post(path + "/operations", json=second).json() == {"revision": 2}
    undo["target"] = second["operation_id"]
    assert client.post(path + "/operations", json=undo).json() == {"revision": 3}
    replay = client.get(path + "/operations?after=1").json()
    assert [item["revision"] for item in replay] == [2, 3]
    assert client.get(path + "/operations?after=3").json() == []
    with factory() as db:
        assert len(db.scalars(select(BoardOperation)).all()) == 3
    # No tutor/attempt/mastery tables even exist in this isolated database.


def test_revocation_closure_and_validation(family):
    client, factory, child, _, _, invite_id = family
    path = create_board(client, child)
    assert (
        client.post(path + "/operations", json=mark(points=[{"x": -1, "y": 1}])).status_code == 422
    )
    assert client.post(path + "/operations", json=mark(points=[])).status_code == 422
    assert (
        client.post(path + "/operations", json=mark(kind="text", points=[], text=" ")).status_code
        == 422
    )
    assert client.get(path + "/operations?after=-1").status_code == 422
    with factory() as db:
        db.get(FamilyPracticePass, invite_id).revoked_at = datetime.now(UTC)
        db.commit()
    client.cookies.set("ai_tutor_learner", "child-cookie")
    assert client.get(path).status_code == 401
    client.cookies.delete("ai_tutor_learner")
    assert client.post(path + "/close").status_code == 200
    assert client.post(path + "/operations", json=mark()).status_code == 409
    assert client.get(path + "/operations").status_code == 200


def test_socket_replay_origin_and_revocation(family):
    client, factory, child, *_ = family
    path = create_board(client, child)
    client.post(path + "/operations", json=mark())
    client.post(path + "/operations", json=mark())
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(path + "/live", headers={"origin": "https://attacker.example"}),
    ):
        pass
    with client.websocket_connect(
        path + "/live?after=1", headers={"origin": "http://testserver"}
    ) as ws:
        assert [item["revision"] for item in ws.receive_json()["operations"]] == [2]
        with factory() as db:
            for row in db.scalars(select(AuthSession)):
                db.delete(row)
            db.commit()
        with pytest.raises(WebSocketDisconnect):
            while True:
                ws.receive_json()


def test_typed_text_uses_existing_pii_filter(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    payload = mark(kind="text", points=[], text="email me at child@example.com")
    assert client.post(path + "/operations", json=payload).status_code == 200
    assert client.post(path + "/operations", json=payload).json()["revision"] == 1
    assert client.get(path + "/operations").json()[0]["text"] == "email me at [REDACTED_EMAIL]"


def test_migration_round_trip_and_learner_erasure_cascade():
    import importlib.util

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    spec = importlib.util.spec_from_file_location(
        "collab_migration", "alembic/versions/0036_collaboration.py"
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.exec_driver_sql("CREATE TABLE users (id CHAR(32) PRIMARY KEY)")
        connection.exec_driver_sql("CREATE TABLE students (id CHAR(32) PRIMARY KEY)")
        user_id, child_id, board_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        connection.exec_driver_sql("INSERT INTO users VALUES (?)", (user_id.hex,))
        connection.exec_driver_sql("INSERT INTO students VALUES (?)", (child_id.hex,))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            connection.execute(
                sa.insert(CollaborationBoard),
                {"id": board_id, "student_id": child_id, "owner_id": user_id},
            )
            connection.execute(
                sa.insert(BoardOperation),
                {
                    "board_id": board_id,
                    "operation_id": uuid.uuid4(),
                    "revision": 1,
                    "author": "parent",
                    "payload": {"kind": "text", "text": "work"},
                },
            )
            connection.exec_driver_sql("DELETE FROM students WHERE id=?", (child_id.hex,))
            assert (
                connection.scalar(sa.select(sa.func.count()).select_from(CollaborationBoard)) == 0
            )
            assert connection.scalar(sa.select(sa.func.count()).select_from(BoardOperation)) == 0
            migration.downgrade()
            assert "collaboration_boards" not in sa.inspect(connection).get_table_names()
            migration.upgrade()
    engine.dispose()
