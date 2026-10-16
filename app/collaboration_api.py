"""Durable ordered board operations with cookie-authenticated WebSocket reads.

Writes use HTTP for existing edge controls. Socket readers use database revisions,
so reconnect and multiple workers need neither sticky routing nor in-memory rooms.
"""

import asyncio
import hashlib
import uuid
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
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, _digest, resolve_user_id
from app.board_images import MAX_UPLOAD_BYTES, normalize_photo
from app.collaboration_models import BoardImage, BoardOperation, CollaborationBoard
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
    kind: Literal["stroke", "text", "undo", "erase"]
    points: list[Point] = Field(default_factory=list, max_length=4000)
    text: str = Field(default="", max_length=1000)
    x: float = Field(default=40, ge=0, le=1600, allow_inf_nan=False)
    y: float = Field(default=60, ge=0, le=1000, allow_inf_nan=False)
    target: uuid.UUID | None = None


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
        if old.author != author or old.payload != payload.model_dump(
            mode="json", exclude={"operation_id"}
        ):
            raise HTTPException(409, "Operation ID already used")
        return {"revision": old.revision}
    if board.revision >= 10000:
        raise HTTPException(409, "Board is full; start another board")
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
        if not target or target.author != author or target.payload["kind"] in {"undo", "erase"}:
            raise HTTPException(403, "You can only remove your own marks")
    board.revision += 1
    db.add(
        BoardOperation(
            board_id=board.id,
            operation_id=payload.operation_id,
            revision=board.revision,
            author=author,
            payload=payload.model_dump(mode="json", exclude={"operation_id"}),
        )
    )
    db.commit()
    return {"revision": board.revision}


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
    # Reject cross-site WebSockets before accepting authenticated cookies.
    origin = urlsplit(socket.headers.get("origin", ""))
    if (
        origin.scheme not in {"http", "https"}
        or origin.netloc != socket.headers.get("host")
        or after < 0
    ):
        await socket.close(code=1008)
        return
    try:
        with SessionLocal() as db:
            authorized(db, socket.cookies, board_id)
        await socket.accept()
        while True:
            # Revalidate live credentials and ownership each pass, including revocation.
            def read(cursor=after):
                with SessionLocal() as db:
                    board, _ = authorized(db, socket.cookies, board_id)
                    return operations(db, board_id, cursor), board.closed

            batch, closed = await asyncio.to_thread(read)
            await socket.send_json({"operations": batch, "closed": closed})
            if batch:
                after = batch[-1]["revision"]
            if closed:
                await socket.close(code=1000)
                return
            await asyncio.sleep(0.5)
    except HTTPException:
        await socket.close(code=1008)
    except WebSocketDisconnect:
        pass
