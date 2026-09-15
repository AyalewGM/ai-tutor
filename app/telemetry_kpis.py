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
    definitions = (
        ("independent_mastery_rate", "mastery.independent", "mastery.opportunity"),
        ("assistance_dependency_rate", "problem.solved_assisted", "problem.solved"),
        ("remediation_success_rate", "intervention.fresh_independent_success", "intervention.completed"),
        ("diagnostic_completion_rate", "diagnostic.completed", "diagnostic.started"),
        ("fresh_mastery_pass_rate", "mastery.fresh_passed", "mastery.fresh_attempted"),
    )
    return [
        KpiResult(
            name=name,
            policy_version=policy_version,
            curriculum_id=curriculum_id,
            numerator=_count(events, numerator_event),
            denominator=_count(events, denominator_event),
        )
        for name, numerator_event, denominator_event in definitions
    ]
