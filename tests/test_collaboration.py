"""Isolated API tests use real cookies and durable SQL rows, without seeded curricula.

SQLite is used for these sequential contracts; PostgreSQL lock concurrency remains
an additional integration gate, rather than being inferred from these tests.
"""

import os
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, create_engine, event, select
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect

from app import collaboration_api as api
from app.auth import SESSION_COOKIE, _digest, create_session
from app.auth_models import AuthSession
from app.collaboration_models import (
    BoardClearReceipt,
    BoardImage,
    BoardOperation,
    CollaborationBoard,
)
from app.core.database import get_db
from app.middleware.board_upload_limit import BoardUploadLimitMiddleware
from app.middleware.pii_sanitizer import PIISanitizerMiddleware
from app.models import Student, User
from app.parent_models import FamilyPracticePass, LearnerPassSession, ParentProfile
from tests.board_live_helpers import TestLiveRelay


@pytest.fixture
def family(monkeypatch, tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'boards.db'}", connect_args={"check_same_thread": False}
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
        BoardImage,
        BoardClearReceipt,
    ):
        model.__table__.create(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    @event.listens_for(factory, "loaded_as_persistent")
    def sqlite_utc(_session, obj):
        # SQLite strips timezone information; PostgreSQL preserves it.
        for column in obj.__table__.columns:
            if not isinstance(column.type, DateTime):
                continue
            value = getattr(obj, column.name)
            if isinstance(value, datetime) and value.tzinfo is None:
                setattr(obj, column.name, value.replace(tzinfo=UTC))

    app = FastAPI()
    app.add_middleware(PIISanitizerMiddleware)
    app.add_middleware(BoardUploadLimitMiddleware)
    app.include_router(api.router, prefix="/api/v1")

    def db_dependency():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = db_dependency
    monkeypatch.setattr(api, "SessionLocal", factory)
    if not os.environ.get("MIHUR_TEST_REAL_REDIS"):
        monkeypatch.setattr(api, "open_live_channel", TestLiveRelay().open)
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


def photo_bytes(size=(300, 200), exif=True):
    from io import BytesIO

    from PIL import Image

    photo = Image.new("RGB", size, "white")
    metadata = Image.Exif()
    if exif:
        metadata[270] = "private student name"
        metadata[274] = 6
    output = BytesIO()
    photo.save(output, "JPEG", exif=metadata)
    return output.getvalue()


def upload(client, path, photo=None, operation_id=None):
    return client.post(
        path + "/photos",
        data={"operation_id": operation_id or str(uuid.uuid4())},
        files={
            "photo": (
                "private-student-name.jpg",
                photo if photo is not None else photo_bytes(),
                "image/jpeg",
            )
        },
    )


def test_photo_privacy_replay_and_eraser_ownership(family):
    from io import BytesIO

    from PIL import Image

    client, factory, child, _, other_token, _ = family
    path = create_board(client, child)
    operation_id = str(uuid.uuid4())
    assert upload(client, path, operation_id=operation_id).json() == {"revision": 1}
    assert upload(client, path, operation_id=operation_id).json() == {"revision": 1}
    assert upload(client, path, photo_bytes((200, 200)), operation_id).status_code == 409
    operation = client.get(path + "/operations").json()[0]
    photo_url = path + "/photos/" + operation["image_id"]
    response = client.get(photo_url)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "image/jpeg"
    with Image.open(BytesIO(response.content)) as image:
        assert image.size == (200, 300)  # EXIF orientation applied before metadata removal.
        assert not image.getexif()
        assert "private student name" not in str(image.info)
    client.cookies.set(SESSION_COOKIE, other_token)
    assert client.get(photo_url).status_code == 404
    client.cookies.set("ai_tutor_learner", "child-cookie")
    assert client.get(photo_url).status_code == 200
    assert (
        client.post(
            path + "/operations", json=mark(kind="erase", points=[], target=operation_id)
        ).status_code
        == 403
    )
    child_mark = mark(kind="text", points=[], text="x = 4")
    assert client.post(path + "/operations", json=child_mark).status_code == 200
    assert (
        client.post(
            path + "/operations",
            json=mark(kind="erase", points=[], target=child_mark["operation_id"]),
        ).status_code
        == 200
    )
    with factory() as db:
        assert len(db.scalars(select(BoardImage)).all()) == 1


def test_photo_validation_and_closed_board(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    assert upload(client, path, b"<svg onload='alert(1)'/>").status_code == 422
    assert upload(client, path, b"x" * (5 * 1024 * 1024 + 1)).status_code == 413
    assert upload(client, path, b"x" * (6 * 1024 * 1024 + 1)).status_code == 413
    assert upload(client, path, photo_bytes((5000, 4000))).status_code == 413
    client.post(path + "/close")
    assert upload(client, path).status_code == 409


def test_photo_limit_is_enforced_under_board_transaction(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    for _ in range(10):
        assert upload(client, path).status_code == 200
    assert upload(client, path).status_code == 409
    assert len(client.get(path + "/operations").json()) == 10


def test_photo_migration_metadata_bootstrap_and_cascade():
    import importlib.util

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    modules = []
    for filename in ("0036_collaboration.py", "0037_board_images.py"):
        spec = importlib.util.spec_from_file_location(filename[:-3], "alembic/versions/" + filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.exec_driver_sql("CREATE TABLE users (id CHAR(32) PRIMARY KEY)")
        connection.exec_driver_sql("CREATE TABLE students (id CHAR(32) PRIMARY KEY)")
        # Reproduce the existing 0001 live-metadata bootstrap, before 0036/0037.
        for model in (CollaborationBoard, BoardOperation, BoardImage):
            model.__table__.create(connection)
        with Operations.context(MigrationContext.configure(connection)):
            for module in modules:
                module.upgrade()
            user_id, child_id, board_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
            connection.exec_driver_sql("INSERT INTO users VALUES (?)", (user_id.hex,))
            connection.exec_driver_sql("INSERT INTO students VALUES (?)", (child_id.hex,))
            connection.execute(
                sa.insert(CollaborationBoard),
                {"id": board_id, "student_id": child_id, "owner_id": user_id},
            )
            connection.execute(
                sa.insert(BoardImage),
                {
                    "board_id": board_id,
                    "operation_id": uuid.uuid4(),
                    "digest": "x" * 64,
                    "pixels": photo_bytes(),
                },
            )
            connection.exec_driver_sql("DELETE FROM students WHERE id=?", (child_id.hex,))
            assert connection.scalar(sa.select(sa.func.count()).select_from(BoardImage)) == 0
            for module in reversed(modules):
                module.downgrade()
            for module in modules:
                module.upgrade()
    engine.dispose()


def test_photo_chunked_body_is_bounded_before_spooling(family):
    client, _, child, *_ = family
    path = create_board(client, child)

    def body():
        yield b'--boundary\r\nContent-Disposition: form-data; name="photo"; filename="photo.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
        for _ in range(7):
            yield b"x" * (1024 * 1024)
        yield b"\r\n--boundary--\r\n"

    response = client.post(
        path + "/photos",
        content=body(),
        headers={"Content-Type": "multipart/form-data; boundary=boundary"},
    )
    assert response.status_code == 413


def test_worksheet_pages_are_scoped_and_navigation_cannot_be_erased(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    page_id = str(uuid.uuid4())
    assert upload(client, path, operation_id=page_id).status_code == 200
    annotation = mark(kind="text", points=[], text="page one", page_id=page_id)
    assert client.post(path + "/operations", json=annotation).status_code == 200
    assert client.post(path + "/operations", json=annotation).json()["revision"] == 2
    navigation = mark(kind="page", points=[], target=page_id)
    assert client.post(path + "/operations", json=navigation).status_code == 200
    assert (
        client.post(
            path + "/operations",
            json=mark(kind="erase", points=[], target=navigation["operation_id"]),
        ).status_code
        == 403
    )
    assert (
        client.post(
            path + "/operations",
            json=mark(kind="erase", points=[], target=annotation["operation_id"]),
        ).status_code
        == 409
    )
    assert (
        client.post(
            path + "/operations",
            json=mark(kind="erase", points=[], target=annotation["operation_id"], page_id=page_id),
        ).status_code
        == 200
    )
    assert (
        client.post(
            path + "/operations", json=mark(kind="page", points=[], target=None)
        ).status_code
        == 200
    )
    other_path = create_board(client, child)
    assert client.post(other_path + "/operations", json=mark(page_id=page_id)).status_code == 404
    assert (
        client.post(
            other_path + "/operations", json=mark(kind="page", points=[], target=page_id)
        ).status_code
        == 404
    )
    assert (
        client.post(
            path + "/operations",
            json=mark(kind="page", points=[], target=annotation["operation_id"]),
        ).status_code
        == 404
    )


def test_historical_blank_page_payload_remains_retry_compatible(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    payload = mark()
    assert client.post(path + "/operations", json=payload).status_code == 200
    assert "page_id" not in client.get(path + "/operations").json()[0]
    assert client.post(path + "/operations", json={**payload, "page_id": None}).json() == {
        "revision": 1
    }


def test_closed_board_replays_every_batch_before_disconnect(family):
    client, factory, child, *_ = family
    path = create_board(client, child)
    board_id = uuid.UUID(path.rsplit("/", 1)[-1])
    with factory() as db:
        board = db.get(CollaborationBoard, board_id)
        board.closed = True
        board.revision = 201
        db.add_all(
            [
                BoardOperation(
                    board_id=board_id,
                    operation_id=uuid.uuid4(),
                    revision=index,
                    author=f"parent:{board.owner_id}",
                    payload={"kind": "text", "text": str(index)},
                )
                for index in range(1, 202)
            ]
        )
        db.commit()
    with client.websocket_connect(
        path + "/live", headers={"origin": "http://testserver"}
    ) as socket:
        first, second = socket.receive_json(), socket.receive_json()
        assert len(first["operations"]) == 200
        assert second["operations"][0]["revision"] == 201
        assert second["closed"] is True
        with pytest.raises(WebSocketDisconnect):
            socket.receive_json()


def live_message(socket, predicate):
    for _ in range(20):
        message = socket.receive_json()
        if predicate(message):
            return message
    raise AssertionError("Expected live message not received")


def test_live_pointer_and_unfinished_ink_never_create_saved_operations(family):
    client, factory, child, *_ = family
    path = create_board(client, child)
    with client.websocket_connect(
        path + "/live", headers={"origin": "http://testserver"}
    ) as parent:
        assert parent.receive_json()["live_available"] is True
        client.cookies.set("ai_tutor_learner", "child-cookie")
        with client.websocket_connect(
            path + "/live", headers={"origin": "http://testserver"}
        ) as learner:
            assert learner.receive_json()["live_available"] is True
            learner.send_json({"kind": "pointer", "point": {"x": 50, "y": 75}})
            event = live_message(parent, lambda m: "ephemeral" in m)["ephemeral"]
            assert event["author"] == f"learner:{child}"
            assert uuid.UUID(event["source"])
            assert event["point"] == {"x": 50, "y": 75}
            operation_id = str(uuid.uuid4())
            learner.send_json(
                {
                    "kind": "stroke",
                    "operation_id": operation_id,
                    "points": [{"x": 10, "y": 10}, {"x": 60, "y": 80}],
                }
            )
            assert (
                live_message(parent, lambda m: m.get("ephemeral", {}).get("kind") == "stroke")[
                    "ephemeral"
                ]["operation_id"]
                == operation_id
            )
            with factory() as db:
                assert db.scalars(select(BoardOperation)).all() == []
            learner.send_json({"kind": "clear"})
            assert live_message(parent, lambda m: m.get("ephemeral", {}).get("kind") == "clear")
            # Let server disconnect cleanup finish before TestClient cancels its scope.
            learner.close()
            assert live_message(parent, lambda m: m.get("ephemeral", {}).get("kind") == "clear")
            # Close in-band and yield so the server finishes its disconnect path
            # before TestClient cancels the session scope on __exit__.
            parent.close()
            time.sleep(0.1)


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "pointer", "point": {"x": -1, "y": 0}},
        {"kind": "pointer", "point": {"x": 1, "y": 0}, "author": "parent:forged"},
        {"kind": "stroke", "operation_id": str(uuid.uuid4()), "points": [{"x": 1, "y": 1}] * 129},
        {"kind": "pointer", "point": {"x": 1, "y": 1}, "page_id": str(uuid.uuid4())},
        {"kind": "stroke", "points": []},
    ],
)
def test_live_rejects_invalid_or_spoofed_frames(family, payload):
    client, _, child, *_ = family
    path = create_board(client, child)
    with client.websocket_connect(
        path + "/live", headers={"origin": "http://testserver"}
    ) as socket:
        socket.receive_json()
        socket.send_json(payload)
        with pytest.raises(WebSocketDisconnect) as exc:
            while True:
                socket.receive_json()
        assert exc.value.code == 1008


def test_live_rejects_binary_and_oversized_frames(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    for raw in (b"binary", "x" * 16385):
        with client.websocket_connect(
            path + "/live", headers={"origin": "http://testserver"}
        ) as socket:
            socket.receive_json()
            socket.send_bytes(raw) if isinstance(raw, bytes) else socket.send_text(raw)
            with pytest.raises(WebSocketDisconnect) as exc:
                while True:
                    socket.receive_json()
            assert exc.value.code == 1008


def test_live_broker_outage_preserves_durable_saving(family, monkeypatch):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def unavailable(_board):
        raise ConnectionError("synthetic outage")
        yield  # pragma: no cover

    monkeypatch.setattr(api, "open_live_channel", unavailable)
    client, _, child, *_ = family
    path = create_board(client, child)
    with client.websocket_connect(
        path + "/live", headers={"origin": "http://testserver"}
    ) as socket:
        assert socket.receive_json()["live_available"] is False
        result = client.post(path + "/operations", json=mark())
        assert result.status_code == 200
        saved = live_message(socket, lambda m: bool(m.get("operations")))
        assert saved["operations"][0]["revision"] == 1
        # Close in-band and yield so the server finishes its disconnect path
        # before TestClient cancels the session scope on __exit__.
        socket.close()
        time.sleep(0.1)
    client, _, child, *_ = family
    first, second = create_board(client, child), create_board(client, child)
    with (
        client.websocket_connect(
            first + "/live", headers={"origin": "http://testserver"}
        ) as sender,
        client.websocket_connect(
            second + "/live", headers={"origin": "http://testserver"}
        ) as other_board,
    ):
        sender.receive_json()
        other_board.receive_json()
        sender.send_json({"kind": "pointer", "point": {"x": 10, "y": 10}})
        for _ in range(2):
            assert "ephemeral" not in other_board.receive_json()
        # Close in-band and yield so the server finishes its disconnect path
        # before TestClient cancels the session scope on __exit__.
        sender.close()
        other_board.close()
        time.sleep(0.1)


def test_clear_my_writing_is_atomic_scoped_and_idempotent(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    parent_mark = mark()
    assert client.post(path + "/operations", json=parent_mark).status_code == 200
    client.cookies.set("ai_tutor_learner", "child-cookie")
    learner_mark = mark()
    assert client.post(path + "/operations", json=learner_mark).status_code == 200
    request = {
        "operation_id": str(uuid.uuid4()),
        "page_id": None,
        "expected_revision": 2,
    }
    result = client.post(path + "/clear-my-writing", json=request)
    assert result.status_code == 200, result.text
    assert result.json()["cleared_operation_ids"] == [learner_mark["operation_id"]]
    assert result.json()["result_revision"] == 3
    replay = client.post(path + "/clear-my-writing", json=request)
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["result_revision"] == 3
    assert client.post(path + "/clear-my-writing", json={
        **request, "expected_revision": 3
    }).status_code == 409
    events = client.get(path + "/operations?after=0").json()
    assert [e["kind"] for e in events] == ["stroke", "stroke", "erase"]
    assert events[-1]["target"] == learner_mark["operation_id"]


def test_clear_my_writing_rejects_stale_and_unauthorized(family):
    client, _, child, _, other_token, _ = family
    path = create_board(client, child)
    assert client.post(path + "/operations", json=mark()).status_code == 200
    request = {
        "operation_id": str(uuid.uuid4()),
        "page_id": None,
        "expected_revision": 0,
    }
    assert client.post(path + "/clear-my-writing", json=request).status_code == 409
    assert client.post(path + "/clear-my-writing", json={
        "operation_id": str(uuid.uuid4()), "expected_revision": 1
    }).status_code == 422
    client.cookies.set(SESSION_COOKIE, other_token)
    assert client.post(path + "/clear-my-writing", json={
        **request, "expected_revision": 1
    }).status_code == 404
    client.cookies.clear()
    assert client.post(path + "/clear-my-writing", json=request).status_code == 401


def test_clear_my_writing_does_not_reerase_prior_erased_marks(family):
    client, _, child, *_ = family
    path = create_board(client, child)
    first = mark()
    assert client.post(path + "/operations", json=first).status_code == 200
    erase = mark(kind="erase", points=[], target=first["operation_id"])
    assert client.post(path + "/operations", json=erase).status_code == 200
    request = {
        "operation_id": str(uuid.uuid4()),
        "page_id": None,
        "expected_revision": 2,
    }
    reply = client.post(path + "/clear-my-writing", json=request)
    assert reply.status_code == 200
    assert reply.json()["cleared_count"] == 0
    assert reply.json()["result_revision"] == 2
    replay = client.post(path + "/clear-my-writing", json=request)
    assert replay.json()["idempotent_replay"] is True
