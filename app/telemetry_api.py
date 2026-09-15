from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.telemetry_models import TelemetryEventRecord

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
DbSession = Annotated[Session, Depends(get_db)]
KPI_POLICY_VERSION = "pilot-kpi-v1"


class KpiMetric(BaseModel):
    name: str
    policy_version: str
    curriculum_id: uuid.UUID
    numerator: int
    denominator: int
    rate: float | None


class PilotKpisOut(BaseModel):
    curriculum_id: uuid.UUID
    policy_version: str
    metrics: list[KpiMetric]


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _metric(name: str, curriculum_id: uuid.UUID, numerator: int, denominator: int) -> KpiMetric:
    return KpiMetric(
        name=name,
        policy_version=KPI_POLICY_VERSION,
        curriculum_id=curriculum_id,
        numerator=numerator,
        denominator=denominator,
        rate=_rate(numerator, denominator),
    )


def build_pilot_kpis(db: Session, curriculum_id: uuid.UUID) -> PilotKpisOut:
    """Derive observational pilot KPIs without making pedagogical decisions."""
    events = list(
        db.scalars(
            select(TelemetryEventRecord).where(
                TelemetryEventRecord.curriculum_id == curriculum_id
            )
        )
    )

    mastery = [event for event in events if event.event_type == "mastery.evidence_recorded"]
    independent = [
        event
        for event in mastery
        if event.payload_json.get("assistance_level") == "independent"
    ]
    independent_correct = [event for event in independent if event.payload_json.get("correct") is True]
    assisted = [
        event
        for event in mastery
        if event.payload_json.get("assistance_level") != "independent"
    ]
    assisted_correct = [event for event in assisted if event.payload_json.get("correct") is True]

    diagnostic_started = sum(event.event_type == "diagnostic.started" for event in events)
    diagnostic_completed = sum(event.event_type == "diagnostic.completed" for event in events)

    return PilotKpisOut(
        curriculum_id=curriculum_id,
        policy_version=KPI_POLICY_VERSION,
        metrics=[
            _metric(
                "independent_mastery_rate",
                curriculum_id,
                len(independent_correct),
                len(independent),
            ),
            _metric(
                "assistance_dependency_rate",
                curriculum_id,
                len(assisted_correct),
                len(mastery),
            ),
            _metric(
                "diagnostic_completion_rate",
                curriculum_id,
                diagnostic_completed,
                diagnostic_started,
            ),
        ],
    )


@router.get("/kpis/{curriculum_id}", response_model=PilotKpisOut)
def get_pilot_kpis(curriculum_id: uuid.UUID, db: DbSession) -> PilotKpisOut:
    return build_pilot_kpis(db, curriculum_id)
