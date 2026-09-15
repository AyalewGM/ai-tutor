import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.telemetry import (
    RetentionPolicy,
    TelemetryEnvelope,
    append_telemetry_event,
    publish_telemetry_fail_open,
    validate_telemetry_payload,
)


class FakeSession:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.added: list[Any] = []
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def add(self, value: Any) -> None:
        self.added.append(value)

    def commit(self) -> None:
        if self.fail_commit:
            raise RuntimeError("telemetry unavailable")
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


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
def test_raw_child_content_and_secrets_are_rejected(payload: dict[str, Any]) -> None:
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

    record = append_telemetry_event(fake_db, envelope)  # type: ignore[arg-type]

    assert fake_db.added == [record]
    assert record.id == event_id
    assert record.curriculum_id == curriculum_id
    assert record.retention_class == "DISPOSABLE_90D"
    assert record.payload_json == {"outcome_code": "RETURNED_TO_TARGET"}
    assert not hasattr(record, "mastery_score")


def test_fail_open_publisher_commits_isolated_telemetry_transaction() -> None:
    fake_db = FakeSession()
    envelope = TelemetryEnvelope(
        event_type="session.started",
        learner_pseudonymous_id="learner-hash-1",
        curriculum_id=uuid.uuid4(),
    )

    published = publish_telemetry_fail_open(lambda: fake_db, envelope)  # type: ignore[arg-type]

    assert published is True
    assert fake_db.committed is True
    assert fake_db.rolled_back is False
    assert fake_db.closed is True


def test_fail_open_publisher_swallows_observability_failure() -> None:
    fake_db = FakeSession(fail_commit=True)
    envelope = TelemetryEnvelope(
        event_type="session.started",
        learner_pseudonymous_id="learner-hash-1",
        curriculum_id=uuid.uuid4(),
    )

    published = publish_telemetry_fail_open(lambda: fake_db, envelope)  # type: ignore[arg-type]

    assert published is False
    assert fake_db.rolled_back is True
    assert fake_db.closed is True


def test_retention_policy_is_versioned_and_uses_configurable_days() -> None:
    now = datetime(2026, 9, 15, tzinfo=UTC)
    policy = RetentionPolicy(days=30, policy_version="pilot-retention-test")

    assert policy.policy_version == "pilot-retention-test"
    assert policy.cutoff(now) == datetime(2026, 8, 16, tzinfo=UTC)
