from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.telemetry_models import TelemetryEventRecord

logger = logging.getLogger(__name__)

TELEMETRY_SCHEMA_VERSION = "pilot-v1"
RETENTION_POLICY_VERSION = "pilot-retention-v1"
DEFAULT_RETENTION_DAYS = 90
PROHIBITED_PAYLOAD_KEYS = {
    "answer",
    "auth_token",
    "chat",
    "email",
    "first_name",
    "last_name",
    "message",
    "name",
    "precise_location",
    "prompt",
    "raw_answer",
    "session_replay",
    "token",
    "transcript",
}


@dataclass(frozen=True)
class TelemetryEnvelope:
    event_type: str
    learner_pseudonymous_id: str
    curriculum_id: uuid.UUID
    session_id: uuid.UUID | None = None
    skill_id: uuid.UUID | None = None
    policy_version: str | None = None
    purpose: str = "pilot_observability"
    retention_class: str = "DISPOSABLE_90D"
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = TELEMETRY_SCHEMA_VERSION


@dataclass(frozen=True)
class RetentionPolicy:
    days: int = DEFAULT_RETENTION_DAYS
    policy_version: str = RETENTION_POLICY_VERSION
    retention_class: str = "DISPOSABLE_90D"

    def __post_init__(self) -> None:
        if self.days <= 0:
            raise ValueError("retention days must be positive")
        if not self.policy_version.strip():
            raise ValueError("retention policy_version is required")
        if not self.retention_class.startswith("DISPOSABLE_"):
            raise ValueError("retention policy may target disposable telemetry only")

    def cutoff(self, now: datetime | None = None) -> datetime:
        anchor = now or datetime.now(UTC)
        return anchor - timedelta(days=self.days)


def _normalized_payload_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _payload_key_is_prohibited(key: str) -> bool:
    normalized = _normalized_payload_key(key)
    if normalized in PROHIBITED_PAYLOAD_KEYS:
        return True
    parts = {part for part in normalized.split("_") if part}
    sensitive_parts = {"answer", "chat", "email", "message", "name", "prompt", "token", "transcript"}
    return bool(parts & sensitive_parts)


def validate_telemetry_payload(payload: dict[str, Any]) -> None:
    stack: list[tuple[str, Any]] = list(payload.items())
    while stack:
        key, value = stack.pop()
        if _payload_key_is_prohibited(key):
            raise ValueError(f"prohibited telemetry field: {key}")
        if isinstance(value, dict):
            stack.extend(value.items())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    stack.extend(item.items())


def append_telemetry_event(db: Session, envelope: TelemetryEnvelope) -> TelemetryEventRecord:
    """Append one observability event without acquiring pedagogical authority."""
    validate_telemetry_payload(envelope.payload)
    record = TelemetryEventRecord(
        id=envelope.event_id,
        event_type=envelope.event_type,
        occurred_at=envelope.occurred_at,
        schema_version=envelope.schema_version,
        learner_pseudonymous_id=envelope.learner_pseudonymous_id,
        session_id=envelope.session_id,
        curriculum_id=envelope.curriculum_id,
        skill_id=envelope.skill_id,
        policy_version=envelope.policy_version,
        purpose=envelope.purpose,
        retention_class=envelope.retention_class,
        payload_json=envelope.payload,
    )
    db.add(record)
    return record


def publish_telemetry_fail_open(
    session_factory: Callable[[], Session], envelope: TelemetryEnvelope
) -> bool:
    """Publish in an isolated transaction; observability failure never affects tutoring state."""
    db: Session | None = None
    try:
        db = session_factory()
        append_telemetry_event(db, envelope)
        db.commit()
        return True
    except Exception:
        if db is not None:
            db.rollback()
        logger.warning("telemetry publication failed open", exc_info=True)
        return False
    finally:
        if db is not None:
            db.close()


def expire_disposable_telemetry(
    db: Session, policy: RetentionPolicy, now: datetime | None = None
) -> int:
    """Delete only disposable telemetry selected by retention class and age."""
    expired_ids = list(
        db.scalars(
            select(TelemetryEventRecord.id).where(
                TelemetryEventRecord.retention_class == policy.retention_class,
                TelemetryEventRecord.occurred_at < policy.cutoff(now),
            )
        )
    )
    if not expired_ids:
        return 0
    result = db.execute(delete(TelemetryEventRecord).where(TelemetryEventRecord.id.in_(expired_ids)))
    return int(result.rowcount or 0)
