"""PostgreSQL-only ordering gate, run against the repository's migrated test DB."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import SESSION_COOKIE, create_session
from app.collaboration_api import router
from app.collaboration_models import BoardOperation, CollaborationBoard
from app.core.database import SessionLocal, engine
from app.models import Student, User

pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql", reason="Requires PostgreSQL row locks"
)


@pytest.mark.parametrize("duplicate", [False, True])
def test_concurrent_writers_serialize_and_retry_idempotently(duplicate):
    with SessionLocal() as db:
        user = User(email=f"board-{uuid.uuid4()}@example.test", role="PARENT")
        db.add(user)
        db.flush()
        student = Student(parent_id=user.id, first_name="Synthetic", grade_level="9")
        db.add(student)
        db.flush()
        board = CollaborationBoard(owner_id=user.id, student_id=student.id)
        db.add(board)
        token, _ = create_session(db, user.id)
        db.commit()
        board_id = board.id
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    barrier = Barrier(2)
    operation_id = str(uuid.uuid4())

    def write(index):
        with TestClient(app) as client:
            client.cookies.set(SESSION_COOKIE, token)
            barrier.wait(timeout=10)
            response = client.post(
                f"/api/v1/together/boards/{board_id}/operations",
                json={
                    "operation_id": operation_id if duplicate else str(uuid.uuid4()),
                    "kind": "text",
                    "text": "same" if duplicate else str(index),
                },
            )
            assert response.status_code == 200, response.text
            return response.json()["revision"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        revisions = list(pool.map(write, [0, 1]))
    assert sorted(revisions) == ([1, 1] if duplicate else [1, 2])
    with SessionLocal() as db:
        operations = list(
            db.scalars(select(BoardOperation).where(BoardOperation.board_id == board_id))
        )
        assert len(operations) == (1 if duplicate else 2)
        assert db.get(CollaborationBoard, board_id).revision == len(operations)
