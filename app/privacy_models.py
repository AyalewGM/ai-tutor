import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrivacyNoticeAcknowledgement(Base):
    __tablename__ = "privacy_notice_acknowledgements"
    __table_args__ = (
        UniqueConstraint("user_id", "notice_version", name="uq_privacy_notice_ack_user_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    notice_version: Mapped[str] = mapped_column(String(80))
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
