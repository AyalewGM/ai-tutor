import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

APPROVAL_PENDING = "PENDING"
APPROVAL_APPROVED = "APPROVED"
APPROVAL_REJECTED = "REJECTED"

class ParentProfile(Base):
    __tablename__ = "parent_profiles"
    __table_args__ = (
        CheckConstraint("subscription_tier IN ('free', 'pro')", name="ck_parent_subscription_tier"),
        CheckConstraint("max_students >= 1", name="ck_parent_max_students_positive"),
        CheckConstraint(
            "(subscription_tier = 'free' AND max_students = 1) OR "
            "(subscription_tier = 'pro' AND max_students = 5)",
            name="ck_parent_subscription_seat_policy",
        ),
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_parent_approval_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default="free", server_default="free", nullable=False
    )
    max_students: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    parent_pin_hash: Mapped[str | None] = mapped_column(String(255))
    coppa_consent_given: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Pilot approval gate. Self-registered families start PENDING when
    # REQUIRE_FAMILY_APPROVAL is on; operator-provisioned rows default APPROVED.
    approval_status: Mapped[str] = mapped_column(
        String(20),
        default=APPROVAL_APPROVED,
        server_default=APPROVAL_APPROVED,
        nullable=False,
        index=True,
    )
    approval_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500))
    # Family's chosen jurisdiction ("US"/"CA" + state/province code). Drives
    # the curriculum cascade and feeds state-level usage analytics.
    country_code: Mapped[str | None] = mapped_column(String(2))
    region_code: Mapped[str | None] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class ParentStudentRelationship(Base):
    __tablename__ = "parent_student_relationships"
    __table_args__ = (
        UniqueConstraint(
            "parent_profile_id",
            "student_id",
            name="uq_parent_student_relationship",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_profiles.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(30), default="GUARDIAN", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ParentStudentRelationshipEvent(Base):
    __tablename__ = "parent_student_relationship_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    relationship_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_student_relationships.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class FamilyPracticePass(Base):
    __tablename__ = "family_practice_passes"
    __table_args__ = (
        UniqueConstraint("parent_profile_id", name="uq_family_practice_pass_parent"),
        UniqueConstraint("token_hash", name="uq_family_practice_pass_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parent_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class LearnerPassSession(Base):
    __tablename__ = "learner_pass_sessions"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_learner_pass_session_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_pass_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family_practice_passes.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ChildLinkClaim(Base):
    __tablename__ = "child_link_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
