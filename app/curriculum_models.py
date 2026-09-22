import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"
    __table_args__ = (
        UniqueConstraint("parent_id", "code", name="uq_jurisdictions_parent_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jurisdictions.id"), index=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(255))
    jurisdiction_type: Mapped[str] = mapped_column(String(40))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)


class EducationAuthority(Base):
    __tablename__ = "education_authorities"
    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "code", name="uq_education_authorities_jurisdiction_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jurisdictions.id"), index=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    authority_type: Mapped[str] = mapped_column(String(40))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)


class AuthorityRole(Base):
    __tablename__ = "authority_roles"
    __table_args__ = (
        UniqueConstraint(
            "authority_id",
            "role_type",
            "subject_scope",
            "grade_scope",
            "effective_from",
            name="uq_authority_roles_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authority_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("education_authorities.id"), index=True)
    role_type: Mapped[str] = mapped_column(String(50), index=True)
    subject_scope: Mapped[str | None] = mapped_column(String(120))
    grade_scope: Mapped[str | None] = mapped_column(String(120))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)


class LocalImplementationOverlay(Base):
    __tablename__ = "local_implementation_overlays"
    __table_args__ = (
        UniqueConstraint(
            "local_authority_id",
            "curriculum_id",
            "code",
            "version",
            name="uq_local_overlay_authority_curriculum_code_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    local_authority_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("education_authorities.id"), index=True
    )
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255))
    overlay_type: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(80))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class StudentCurriculumEnrollment(Base):
    __tablename__ = "student_curriculum_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    local_authority_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("education_authorities.id"), index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)


class CanonicalSkill(Base):
    """Curriculum-neutral mathematical identity; never stores learner evidence."""

    __tablename__ = "canonical_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(80), default="MATHEMATICS")


class CurriculumSkillMapping(Base):
    """Maps a curriculum-local skill to reusable mathematical identity.

    Mastery, attempts, prerequisites and interventions remain attached to the
    curriculum-local Skill row, preserving jurisdiction/version isolation.
    """

    __tablename__ = "curriculum_skill_mappings"
    __table_args__ = (
        UniqueConstraint("skill_id", name="uq_curriculum_skill_mapping_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("canonical_skills.id"), index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    mapping_type: Mapped[str] = mapped_column(String(40), default="EQUIVALENT")
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
