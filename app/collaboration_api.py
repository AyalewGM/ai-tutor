"""Durable ordered board operations with cookie-authenticated WebSocket reads.

Writes use HTTP for existing edge controls. Socket readers use database revisions,
so reconnect and multiple workers need neither sticky routing nor in-memory rooms.
"""

import asyncio
import hashlib
import json
import time
import uuid
from contextlib import AsyncExitStack, suppress
from datetime import UTC, datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, _digest, resolve_user_id
from app.board_images import MAX_UPLOAD_BYTES, normalize_photo
from app.board_live import LiveFrame, open_live_channel
from app.collaboration_models import (
    BoardClearReceipt,
    BoardImage,
    BoardOperation,
    CollaborationBoard,
)
from app.core.database import SessionLocal, get_db
from app.models import Student, User
from app.parent_models import FamilyPracticePass, LearnerPassSession

router = APIRouter(prefix="/together", tags=["learn-together"])
Db = Annotated[Session, Depends(get_db)]


def identity(db, cookies):
    # A learner cookie takes precedence, matching the existing workspace policy.
    token = cookies.get("ai_tutor_learner")
    if token:
        row = db.scalar(
            select(LearnerPassSession).where(LearnerPassSession.token_hash == _digest(token))
        )
        if row and row.expires_at > datetime.now(UTC):
            invitation = db.get(FamilyPracticePass, row.practice_pass_id)
            if (
                invitation
                and invitation.student_id == row.student_id
                and not invitation.revoked_at
                and invitation.expires_at > datetime.now(UTC)
            ):
                return "learner", row.student_id
        raise HTTPException(401, "Learner access expired")
    user_id = resolve_user_id(db, cookies.get(SESSION_COOKIE, ""))
    user = db.get(User, user_id) if user_id else None
    if user and user.role.upper() in {"PARENT", "GUARDIAN"}:
        return "parent", user.id
    raise HTTPException(401, "Authentication required")


def authorized(db, cookies, board_id, *, lock=False):
    role, subject = identity(db, cookies)
    query = select(CollaborationBoard).where(CollaborationBoard.id == board_id)
    board = db.scalar(query.with_for_update() if lock else query)
    student = db.get(Student, board.student_id) if board else None
    if not board or not student or not student.active or student.parent_id != board.owner_id:
        raise HTTPException(404, "Board not found")
    if (role == "parent" and subject != board.owner_id) or (
        role == "learner" and subject != board.student_id
    ):
        raise HTTPException(404, "Board not found")
    return board, f"{role}:{subject}"


def metadata(board, author):
    return {
        "id": str(board.id),
        "student_id": str(board.student_id),
        "closed": board.closed,
        "revision": board.revision,
        "author": author,
    }


class CreateBoard(BaseModel):
    student_id: uuid.UUID


@router.post("/boards")
def create_board(payload: CreateBoard, request: Request, db: Db):
    role, subject = identity(db, request.cookies)
    student = db.get(Student, payload.student_id)
    if role != "parent" or not student or not student.active or student.parent_id != subject:
        raise HTTPException(404, "Learner not found")
    board = CollaborationBoard(student_id=student.id, owner_id=subject)
    db.add(board)
    db.commit()
    return metadata(board, f"parent:{subject}")


@router.get("/boards")
def list_boards(request: Request, db: Db):
    role, subject = identity(db, request.cookies)
    query = (
        select(CollaborationBoard)
        .join(Student, Student.id == CollaborationBoard.student_id)
        .where(Student.active.is_(True), Student.parent_id == CollaborationBoard.owner_id)
    )
    query = (
        query.where(CollaborationBoard.owner_id == subject)
        if role == "parent"
        else query.where(CollaborationBoard.student_id == subject)
    )
    return [
        metadata(b, f"{role}:{subject}")
        for b in db.scalars(query.order_by(CollaborationBoard.created_at.desc()).limit(50))
    ]


@router.get("/boards/{board_id}")
def get_board(board_id: uuid.UUID, request: Request, db: Db):
    board, author = authorized(db, request.cookies, board_id)
    return metadata(board, author)


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float = Field(ge=0, le=1600)
    y: float = Field(ge=0, le=1000)


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: uuid.UUID
    kind: Literal["stroke", "text", "undo", "erase", "page"]
    points: list[Point] = Field(default_factory=list, max_length=4000)
    text: str = Field(default="", max_length=1000)
    x: float = Field(default=40, ge=0, le=1600, allow_inf_nan=False)
    y: float = Field(default=60, ge=0, le=1000, allow_inf_nan=False)
    target: uuid.UUID | None = None
    page_id: uuid.UUID | None = None

    def stored_payload(self):
        # Preserve exact historical payloads and idempotent retries from older tabs.
        excluded = {"operation_id"}
        if self.page_id is None:
            excluded.add("page_id")
        return self.model_dump(mode="json", exclude=excluded)


def operations(db, board_id, after):
    return [
        {
            "operation_id": str(o.operation_id),
            "revision": o.revision,
            "author": o.author,
            **o.payload,
        }
        for o in db.scalars(
            select(BoardOperation)
            .where(BoardOperation.board_id == board_id, BoardOperation.revision > after)
            .order_by(BoardOperation.revision)
            .limit(200)
        )
    ]


@router.get("/boards/{board_id}/operations")
def read_operations(board_id: uuid.UUID, request: Request, db: Db, after: int = Query(0, ge=0)):
    authorized(db, request.cookies, board_id)
    return operations(db, board_id, after)


@router.post("/boards/{board_id}/operations")
def write_operation(board_id: uuid.UUID, payload: Operation, request: Request, db: Db):
    board, author = authorized(db, request.cookies, board_id, lock=True)
    if board.closed:
        raise HTTPException(409, "Board is closed")
    old = db.scalar(
        select(BoardOperation).where(
            BoardOperation.board_id == board_id, BoardOperation.operation_id == payload.operation_id
        )
    )
    if old:
        if old.author != author or old.payload != payload.stored_payload():
            raise HTTPException(409, "Operation ID already used")
        return {"revision": old.revision}
    if board.revision >= 10000:
        raise HTTPException(409, "Board is full; start another board")
    page_id = payload.target if payload.kind == "page" else payload.page_id
    if page_id is not None:
        image_page = db.scalar(
            select(BoardImage.id).where(
                BoardImage.board_id == board_id, BoardImage.operation_id == page_id
            )
        )
        if image_page is None:
            raise HTTPException(404, "Worksheet page not found")
    if payload.kind == "page" and payload.page_id is not None:
        raise HTTPException(422, "Page navigation cannot carry annotation scope")
    if payload.kind == "stroke" and len(payload.points) < 1:
        raise HTTPException(422, "Stroke needs points")
    if payload.kind == "text" and not payload.text.strip():
        raise HTTPException(422, "Text cannot be empty")
    if payload.kind in {"undo", "erase"}:
        target = db.scalar(
            select(BoardOperation).where(
                BoardOperation.board_id == board_id, BoardOperation.operation_id == payload.target
            )
        )
        if (
            not target
            or target.author != author
            or target.payload["kind"] in {"undo", "erase", "page"}
        ):
            raise HTTPException(403, "You can only remove your own marks")
        target_page = (
            str(target.operation_id)
            if target.payload["kind"] == "image"
            else target.payload.get("page_id")
        )
        if (str(payload.page_id) if payload.page_id else None) != target_page:
            raise HTTPException(409, "The mark belongs to a different worksheet page")
    board.revision += 1
    db.add(
        BoardOperation(
            board_id=board.id,
            operation_id=payload.operation_id,
            revision=board.revision,
            author=author,
            payload=payload.stored_payload(),
        )
    )
    db.commit()
    return {"revision": board.revision}



class ClearMyWriting(BaseModel):
    """Client-provided revision freezes the confirmed clear scope."""

    model_config = ConfigDict(extra="forbid")
    operation_id: uuid.UUID
    page_id: uuid.UUID | None
    expected_revision: int = Field(ge=0)


@router.post("/boards/{board_id}/clear-my-writing")
def clear_my_writing(board_id: uuid.UUID, payload: ClearMyWriting, request: Request, db: Db):
    # Reject an omitted page field rather than silently clearing the base page.
    if "page_id" not in payload.model_fields_set:
        raise HTTPException(422, "Explicit page_id is required")
    board, author = authorized(db, request.cookies, board_id, lock=True)
    receipt = db.scalar(
        select(BoardClearReceipt).where(
            BoardClearReceipt.board_id == board_id,
            BoardClearReceipt.operation_id == payload.operation_id,
        )
    )
    if receipt is not None:
        if (
            receipt.author != author
            or receipt.page_id != payload.page_id
            or receipt.expected_revision != payload.expected_revision
        ):
            raise HTTPException(409, "IDEMPOTENCY_CONFLICT")
        return {
            "operation_id": str(receipt.operation_id),
            "board_id": str(board_id),
            "page_id": str(receipt.page_id) if receipt.page_id else None,
            "expected_revision": receipt.expected_revision,
            "result_revision": receipt.result_revision,
            "cleared_count": len(receipt.target_ids),
            "cleared_operation_ids": receipt.target_ids,
            "idempotent_replay": True,
        }
    if board.closed:
        raise HTTPException(409, "BOARD_CLOSED")
    if payload.page_id is not None:
        exists = db.scalar(
            select(BoardImage.id).where(
                BoardImage.board_id == board_id,
                BoardImage.operation_id == payload.page_id,
            )
        )
        if exists is None:
            raise HTTPException(404, "Worksheet page not found")
    if board.revision != payload.expected_revision:
        raise HTTPException(409, "STALE_BOARD_REVISION")
    rows = list(db.scalars(
        select(BoardOperation).where(BoardOperation.board_id == board_id)
        .order_by(BoardOperation.revision)
    ))
    # Only text/stroke records on the selected page may be cleared.
    hidden = {
        str(row.payload.get("target"))
        for row in rows
        if row.payload.get("kind") in {"undo", "erase"}
    }
    targets = [
        row for row in rows
        if row.author == author
        and row.payload.get("kind") in {"stroke", "text"}
        and row.payload.get("page_id") == (
            str(payload.page_id) if payload.page_id else None
        )
        and str(row.operation_id) not in hidden
    ]
    if board.revision + len(targets) > 10000:
        raise HTTPException(409, "BOARD_FULL")
    for index, target in enumerate(targets, start=1):
        # Namespaced UUIDv5 is deterministic across retries, unique per target.
        operation_id = uuid.uuid5(payload.operation_id, str(target.operation_id))
        db.add(BoardOperation(
            board_id=board_id,
            operation_id=operation_id,
            revision=board.revision + index,
            author=author,
            payload={
                "kind": "erase",
                "points": [],
                "text": "",
                "x": 40,
                "y": 60,
                "target": str(target.operation_id),
                **({"page_id": str(payload.page_id)} if payload.page_id else {}),
            },
        ))
    board.revision += len(targets)
    ids = [str(row.operation_id) for row in targets]
    db.add(BoardClearReceipt(
        board_id=board_id,
        operation_id=payload.operation_id,
        author=author,
        page_id=payload.page_id,
        expected_revision=payload.expected_revision,
        result_revision=board.revision,
        target_ids=ids,
    ))
    db.commit()
    return {
        "operation_id": str(payload.operation_id),
        "board_id": str(board_id),
        "page_id": str(payload.page_id) if payload.page_id else None,
        "expected_revision": payload.expected_revision,
        "result_revision": board.revision,
        "cleared_count": len(ids),
        "cleared_operation_ids": ids,
        "idempotent_replay": False,
    }


@router.post("/boards/{board_id}/photos")
def upload_photo(
    board_id: uuid.UUID,
    request: Request,
    db: Db,
    operation_id: Annotated[uuid.UUID, Form()],
    photo: Annotated[UploadFile, File()],
):
    # Authenticate before decoding or retaining any image bytes.
    authorized(db, request.cookies, board_id)
    raw = photo.file.read(MAX_UPLOAD_BYTES + 1)
    digest = hashlib.sha256(raw).hexdigest()
    pixels = normalize_photo(raw)
    # Recheck access and serialize with all other board mutations after decoding.
    board, author = authorized(db, request.cookies, board_id, lock=True)
    if board.closed:
        raise HTTPException(409, "Board is closed")
    old = db.scalar(
        select(BoardOperation).where(
            BoardOperation.board_id == board_id, BoardOperation.operation_id == operation_id
        )
    )
    if old:
        image = db.scalar(
            select(BoardImage).where(
                BoardImage.board_id == board_id, BoardImage.operation_id == operation_id
            )
        )
        if old.author != author or not image or image.digest != digest:
            raise HTTPException(409, "Operation ID already used")
        return {"revision": old.revision}
    if board.revision >= 10000:
        raise HTTPException(409, "Board is full; start another board")
    count = db.scalar(
        select(func.count()).select_from(BoardImage).where(BoardImage.board_id == board_id)
    )
    if count >= 10:
        raise HTTPException(409, "This board has ten photos; start another board")
    image_id = uuid.uuid4()
    board.revision += 1
    db.add(
        BoardImage(
            id=image_id, board_id=board_id, operation_id=operation_id, digest=digest, pixels=pixels
        )
    )
    db.add(
        BoardOperation(
            board_id=board_id,
            operation_id=operation_id,
            revision=board.revision,
            author=author,
            payload={"kind": "image", "image_id": str(image_id)},
        )
    )
    db.commit()
    return {"revision": board.revision}


@router.get("/boards/{board_id}/photos/{image_id}")
def read_photo(board_id: uuid.UUID, image_id: uuid.UUID, request: Request, db: Db):
    authorized(db, request.cookies, board_id)
    image = db.scalar(
        select(BoardImage).where(BoardImage.board_id == board_id, BoardImage.id == image_id)
    )
    if image is None:
        raise HTTPException(404, "Photo not found")
    return Response(
        content=image.pixels,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": 'inline; filename="homework.jpg"',
        },
    )


@router.post("/boards/{board_id}/close")
def close_board(board_id: uuid.UUID, request: Request, db: Db):
    board, author = authorized(db, request.cookies, board_id, lock=True)
    if not author.startswith("parent:"):
        raise HTTPException(403, "Only the parent can close the board")
    board.closed = True
    db.commit()
    return metadata(board, author)


@router.websocket("/boards/{board_id}/live")
async def live_board(socket: WebSocket, board_id: uuid.UUID, after: int = 0):
    origin = urlsplit(socket.headers.get("origin", ""))
    if (
        origin.scheme not in {"http", "https"}
        or origin.netloc != socket.headers.get("host")
        or after < 0
    ):
        await socket.close(code=1008)
        return
    source = str(uuid.uuid4())
    scope = {"closed": False, "author": "", "pages": set()}
    tasks = []
    send_lock = asyncio.Lock()

    def read(cursor):
        with SessionLocal() as db:
            board, author = authorized(db, socket.cookies, board_id)
            pages = {
                str(value)
                for value in db.scalars(
                    select(BoardImage.operation_id).where(BoardImage.board_id == board_id)
                )
            }
            return operations(db, board_id, cursor), board.closed, author, pages

    async def send(message):
        async with send_lock:
            await asyncio.wait_for(socket.send_json(message), timeout=2)

    try:
        _, closed, author, pages = await asyncio.to_thread(read, after)
        scope.update(closed=closed, author=author, pages=pages)
        await socket.accept()
        async with AsyncExitStack() as stack:
            channel = None
            try:
                channel = await stack.enter_async_context(open_live_channel(board_id))
            except (RedisError, OSError, ConnectionError):
                pass  # Durable replay remains available; the client shows live mode unavailable.

            async def replay():
                nonlocal after
                while True:
                    batch, closed, author, pages = await asyncio.to_thread(read, after)
                    scope.update(closed=closed, author=author, pages=pages)
                    await send(
                        {
                            "operations": batch,
                            "closed": closed,
                            "live_available": channel is not None,
                        }
                    )
                    if batch:
                        after = batch[-1]["revision"]
                    if closed and len(batch) < 200:
                        return
                    await asyncio.sleep(0.5)

            async def receive():
                tokens, last = 40.0, time.monotonic()
                while True:
                    message = await socket.receive()
                    if message["type"] == "websocket.disconnect":
                        raise WebSocketDisconnect(message.get("code", 1000))
                    raw = message.get("text")
                    if not isinstance(raw, str):
                        raise TypeError("Live updates require text frames")
                    now = time.monotonic()
                    tokens = min(40, tokens + (now - last) * 30) - 1
                    last = now
                    if len(raw.encode("utf-8")) > 16384 or tokens < 0:
                        raise ValueError("Live update limit exceeded")
                    frame = LiveFrame.model_validate_json(raw)
                    if scope["closed"] or (
                        frame.page_id is not None and frame.page_id not in scope["pages"]
                    ):
                        raise ValueError("Live worksheet scope unavailable")
                    if channel:
                        # Source/author are always supplied by the authenticated server.
                        await channel.publish(
                            {
                                **frame.model_dump(mode="json"),
                                "source": source,
                                "author": scope["author"],
                            }
                        )

            async def relay():
                while True:
                    event = await channel.receive()
                    if event and event.get("source") != source:
                        await send({"ephemeral": event})

            tasks = [asyncio.create_task(replay()), asyncio.create_task(receive())]
            if channel:
                tasks.append(asyncio.create_task(relay()))
            try:
                completed, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in completed:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                if channel:
                    with suppress(RedisError, OSError, ConnectionError):
                        await channel.publish(
                            {
                                "kind": "clear",
                                "source": source,
                                "author": scope["author"],
                                "page_id": None,
                            }
                        )
        await socket.close(code=1000)
    except (HTTPException, ValidationError, TypeError, ValueError, json.JSONDecodeError):
        await socket.close(code=1008)
    except (RedisError, OSError, ConnectionError, TimeoutError):
        with suppress(RuntimeError, WebSocketDisconnect):
            await socket.close(code=1013)
    except WebSocketDisconnect:
        pass
