import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CurriculumExpectation(Base):
    """Authoritative curriculum expectation metadata, not tutor pedagogy."""

    __tablename__ = "curriculum_expectations"
    __table_args__ = (
        UniqueConstraint(
            "curriculum_id",
            "curriculum_version",
            "source_identifier",
            name="uq_expectation_curriculum_version_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    curriculum_version: Mapped[str] = mapped_column(String(80))
    source_identifier: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    strand: Mapped[str | None] = mapped_column(String(160), index=True)
    parent_source_identifier: Mapped[str | None] = mapped_column(String(120))
    source_uri: Mapped[str] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ExpectationSkillMapping(Base):
    """Explicit application-owned mapping from source expectations to tutor skills."""

    __tablename__ = "expectation_skill_mappings"
    __table_args__ = (
        UniqueConstraint("expectation_id", "skill_id", name="uq_expectation_skill_mapping"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    expectation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("curriculum_expectations.id"), index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    mapping_type: Mapped[str] = mapped_column(String(40), default="ALIGNS_TO")
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
