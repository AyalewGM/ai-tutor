from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.telemetry_models import TelemetryEventRecord

TELEMETRY_SCHEMA_VERSION = "pilot-v1"
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
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = TELEMETRY_SCHEMA_VERSION


def validate_telemetry_payload(payload: dict[str, Any]) -> None:
    stack: list[tuple[str, Any]] = list(payload.items())
    while stack:
        key, value = stack.pop()
        normalized = key.strip().lower()
        if normalized in PROHIBITED_PAYLOAD_KEYS:
            raise ValueError(f"prohibited telemetry field: {key}")
        if isinstance(value, dict):
            stack.extend(value.items())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    stack.extend(item.items())


def append_telemetry_event(db: Session, envelope: TelemetryEnvelope) -> TelemetryEventRecord:
    """Append one observability event without acquiring pedagogical authority.

    The caller owns transaction boundaries. A duplicate event_id is naturally rejected by the
    primary key, making retry semantics auditable rather than silently double-counted.
    """
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
