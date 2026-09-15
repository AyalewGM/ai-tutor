from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.telemetry_kpis import KPI_POLICY_VERSION, pilot_kpis

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
DbSession = Annotated[Session, Depends(get_db)]


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


@router.get("/kpis/{curriculum_id}", response_model=PilotKpisOut)
def get_pilot_kpis(curriculum_id: uuid.UUID, db: DbSession) -> PilotKpisOut:
    """Expose deterministic curriculum-scoped observational KPIs."""
    results = pilot_kpis(db, curriculum_id)
    return PilotKpisOut(
        curriculum_id=curriculum_id,
        policy_version=KPI_POLICY_VERSION,
        metrics=[
            KpiMetric(
                name=result.name,
                policy_version=result.policy_version,
                curriculum_id=result.curriculum_id,
                numerator=result.numerator,
                denominator=result.denominator,
                rate=result.rate,
            )
            for result in results
        ],
    )
