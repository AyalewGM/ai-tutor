import uuid
from types import SimpleNamespace
from typing import Any

from app.telemetry_kpis import KPI_POLICY_VERSION, pilot_kpis


class FakeScalars:
    def __init__(self, events: list[Any]) -> None:
        self.events = events

    def __iter__(self):
        return iter(self.events)


class FakeKpiSession:
    def __init__(self, events: list[Any]) -> None:
        self.events = events

    def scalars(self, _statement: Any) -> FakeScalars:
        return FakeScalars(self.events)


def event(event_type: str, **payload: object) -> Any:
    return SimpleNamespace(event_type=event_type, payload_json=payload)


def test_kpis_expose_counts_denominators_policy_and_derived_rates() -> None:
    curriculum_id = uuid.uuid4()
    db = FakeKpiSession(
        [
            event(
                "mastery.evidence_recorded",
                correct=True,
                assistance_level="INDEPENDENT",
                mastery_gate_eligible=True,
            ),
            event(
                "mastery.evidence_recorded",
                correct=False,
                assistance_level="INDEPENDENT",
                mastery_gate_eligible=True,
            ),
            event("diagnostic.started"),
            event("diagnostic.completed"),
        ]
    )

    results = {result.name: result for result in pilot_kpis(db, curriculum_id)}  # type: ignore[arg-type]

    mastery = results["independent_mastery_rate"]
    assert mastery.policy_version == KPI_POLICY_VERSION
    assert mastery.curriculum_id == curriculum_id
    assert mastery.numerator == 1
    assert mastery.denominator == 2
    assert mastery.rate == 0.5

    diagnostic = results["diagnostic_completion_rate"]
    assert diagnostic.numerator == 1
    assert diagnostic.denominator == 1
    assert diagnostic.rate == 1.0


def test_assisted_success_never_counts_as_independent_mastery() -> None:
    curriculum_id = uuid.uuid4()
    db = FakeKpiSession(
        [
            event(
                "mastery.evidence_recorded",
                correct=True,
                assistance_level="ASSISTED",
                mastery_gate_eligible=True,
            ),
            event(
                "mastery.evidence_recorded",
                correct=True,
                assistance_level="INDEPENDENT",
                mastery_gate_eligible=True,
            ),
        ]
    )

    results = {result.name: result for result in pilot_kpis(db, curriculum_id)}  # type: ignore[arg-type]
    mastery = results["independent_mastery_rate"]

    assert mastery.numerator == 1
    assert mastery.denominator == 2
    assert mastery.rate == 0.5


def test_ineligible_evidence_is_not_a_mastery_opportunity() -> None:
    curriculum_id = uuid.uuid4()
    db = FakeKpiSession(
        [
            event(
                "mastery.evidence_recorded",
                correct=True,
                assistance_level="INDEPENDENT",
                mastery_gate_eligible=False,
            )
        ]
    )

    results = {result.name: result for result in pilot_kpis(db, curriculum_id)}  # type: ignore[arg-type]
    mastery = results["independent_mastery_rate"]

    assert mastery.numerator == 0
    assert mastery.denominator == 0
    assert mastery.rate is None


def test_zero_denominator_rate_is_null_not_zero() -> None:
    curriculum_id = uuid.uuid4()
    db = FakeKpiSession([])

    results = pilot_kpis(db, curriculum_id)  # type: ignore[arg-type]

    assert results
    assert all(result.numerator == 0 for result in results)
    assert all(result.denominator == 0 for result in results)
    assert all(result.rate is None for result in results)
