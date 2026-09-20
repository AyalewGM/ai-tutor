from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.telemetry_models import TelemetryEventRecord

KPI_POLICY_VERSION = "pilot-kpi-v1"


@dataclass(frozen=True)
class KpiResult:
    name: str
    policy_version: str
    curriculum_id: uuid.UUID
    numerator: int
    denominator: int

    @property
    def rate(self) -> float | None:
        if self.denominator == 0:
            return None
        return self.numerator / self.denominator


def _events_for_curriculum(db: Session, curriculum_id: uuid.UUID) -> list[TelemetryEventRecord]:
    return list(
        db.scalars(
            select(TelemetryEventRecord).where(
                TelemetryEventRecord.curriculum_id == curriculum_id
            )
        )
    )


def _count(events: list[TelemetryEventRecord], event_type: str) -> int:
    return sum(event.event_type == event_type for event in events)


def _mastery_evidence(events: list[TelemetryEventRecord]) -> list[TelemetryEventRecord]:
    return [event for event in events if event.event_type == "mastery.evidence_recorded"]


def _payload(event: TelemetryEventRecord) -> dict[str, object]:
    payload = event.payload_json
    return payload if isinstance(payload, dict) else {}


def _is_independent(event: TelemetryEventRecord) -> bool:
    return _payload(event).get("assistance_level") == "INDEPENDENT"


def _is_assisted(event: TelemetryEventRecord) -> bool:
    return not _is_independent(event)


def _is_correct(event: TelemetryEventRecord) -> bool:
    return _payload(event).get("correct") is True


def _is_mastery_gate_eligible(event: TelemetryEventRecord) -> bool:
    return _payload(event).get("mastery_gate_eligible") is True


def _is_mastery_check(event: TelemetryEventRecord) -> bool:
    return _payload(event).get("state") == "MASTERY_CHECK"


def pilot_kpis(
    db: Session,
    curriculum_id: uuid.UUID,
    *,
    policy_version: str = KPI_POLICY_VERSION,
) -> list[KpiResult]:
    """Return reproducible, curriculum-scoped pilot KPIs from observability events only.

    These read models report application decisions; they never create mastery evidence or
    influence tutoring, curriculum, prerequisites, assessment, or intervention routing.
    """
    events = _events_for_curriculum(db, curriculum_id)
    mastery_evidence = _mastery_evidence(events)
    mastery_opportunities = [event for event in mastery_evidence if _is_mastery_gate_eligible(event)]
    independent_mastery = [
        event
        for event in mastery_opportunities
        if _is_independent(event) and _is_correct(event)
    ]
    correct_evidence = [event for event in mastery_evidence if _is_correct(event)]
    assisted_correct = [event for event in correct_evidence if _is_assisted(event)]
    fresh_mastery_attempts = [
        event
        for event in mastery_evidence
        if _is_mastery_check(event) and _is_independent(event)
    ]
    fresh_mastery_passes = [
        event
        for event in fresh_mastery_attempts
        if _is_correct(event) and _is_mastery_gate_eligible(event)
    ]

    definitions = (
        KpiResult(
            name="independent_mastery_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=len(independent_mastery),
            denominator=len(mastery_opportunities),
        ),
        KpiResult(
            name="assistance_dependency_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=len(assisted_correct),
            denominator=len(correct_evidence),
        ),
        KpiResult(
            name="remediation_success_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=_count(events, "intervention.fresh_independent_success"),
            denominator=_count(events, "intervention.completed"),
        ),
        KpiResult(
            name="diagnostic_completion_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=_count(events, "diagnostic.completed"),
            denominator=_count(events, "diagnostic.started"),
        ),
        KpiResult(
            name="fresh_mastery_pass_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=len(fresh_mastery_passes),
            denominator=len(fresh_mastery_attempts),
        ),
        KpiResult(
            name="spaced_review_pass_rate",
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=sum(
                _payload(event).get("passed") is True
                for event in events
                if event.event_type == "review.outcome_recorded"
            ),
            denominator=_count(events, "review.outcome_recorded"),
        ),
    )
    return list(definitions)
