import uuid
from typing import Any

import pytest

from app.telemetry import TelemetryEnvelope, append_telemetry_event, validate_telemetry_payload


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []

    def add(self, value: Any) -> None:
        self.added.append(value)


def test_safe_metadata_payload_is_allowed() -> None:
    validate_telemetry_payload(
        {
            "assistance_class": "INDEPENDENT",
            "latency_ms": 125,
            "model_usage": {"provider": "openai", "input_tokens": 42},
        }
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"prompt": "raw learner text"},
        {"nested": {"raw_answer": "7"}},
        {"events": [{"transcript": "private conversation"}]},
        {"auth_token": "secret"},
    ],
)
def test_raw_child_content_and_secrets_are_rejected(payload: dict) -> None:
    with pytest.raises(ValueError, match="prohibited telemetry field"):
        validate_telemetry_payload(payload)


def test_append_event_is_observational_and_preserves_envelope_identity() -> None:
    fake_db = FakeSession()
    curriculum_id = uuid.uuid4()
    event_id = uuid.uuid4()
    envelope = TelemetryEnvelope(
        event_id=event_id,
        event_type="intervention.completed",
        learner_pseudonymous_id="learner-hash-1",
        curriculum_id=curriculum_id,
        policy_version="pilot-v1",
        payload={"outcome_code": "RETURNED_TO_TARGET"},
    )

    record = append_telemetry_event(fake_db, envelope)

    assert fake_db.added == [record]
    assert record.id == event_id
    assert record.curriculum_id == curriculum_id
    assert record.retention_class == "DISPOSABLE_90D"
    assert record.payload_json == {"outcome_code": "RETURNED_TO_TARGET"}
    assert not hasattr(record, "mastery_score")
