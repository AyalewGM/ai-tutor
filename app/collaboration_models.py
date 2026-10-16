"""Standalone family boards: never linked to assessment or mastery evidence."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CollaborationBoard(Base):
    __tablename__ = "collaboration_boards"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    closed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class BoardOperation(Base):
    __tablename__ = "board_operations"
    __table_args__ = (
        UniqueConstraint("board_id", "revision"),
        UniqueConstraint("board_id", "operation_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collaboration_boards.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[uuid.UUID] = mapped_column()
    revision: Mapped[int] = mapped_column(Integer)
    author: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSON)
