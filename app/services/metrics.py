"""Operational metrics for the admin dashboard.

Definitions (kept deliberately honest — no request-level telemetry exists):
- "Active learner" = a student with an Attempt in the window. Attempts are
  the durable learning-engagement signal.
- "Active family" = the owning parent user of an active learner. Parent
  sign-in frequency is not separately measurable (auth sessions carry no
  creation timestamp), so family activity means "a family whose learners
  practiced".
- "Sign-up" = a PARENT user row's created_at.
- Region/curriculum breakdowns use a fixed 30-day window; the family's
  saved country/region and the curriculum the session actually practiced.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.admin_models import AdminAuditEvent
from app.models import Attempt, Curriculum, Student, TutorSession, User
from app.parent_models import ParentProfile
from app.services.plans import FREE_PLAN

WINDOWS = {"1d": 1, "7d": 7, "30d": 30}
BREAKDOWN_DAYS = 30
FUNNEL_WINDOWS = {"30d": 30, "total": None}


def _cutoff(now: datetime, days: int) -> datetime:
    return now - timedelta(days=days)


def overview(db: Session, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    active_learners = {}
    active_families = {}
    attempts = {}
    sessions = {}
    for label, days in WINDOWS.items():
        cutoff = _cutoff(now, days)
        recent = Attempt.created_at >= cutoff
        active_learners[label] = db.scalar(
            select(func.count(distinct(Attempt.student_id))).where(recent)
        )
        active_families[label] = db.scalar(
            select(func.count(distinct(Student.parent_id)))
            .select_from(Attempt)
            .join(Student, Student.id == Attempt.student_id)
            .where(recent, Student.parent_id.is_not(None))
        )
        attempts[label] = db.scalar(select(func.count(Attempt.id)).where(recent))
        sessions[label] = db.scalar(
            select(func.count(TutorSession.id)).where(TutorSession.started_at >= cutoff)
        )
    signups = {
        label: db.scalar(
            select(func.count(User.id)).where(
                User.role == "PARENT", User.created_at >= _cutoff(now, days)
            )
        )
        for label, days in WINDOWS.items()
    }
    signups["total"] = db.scalar(select(func.count(User.id)).where(User.role == "PARENT"))
    daily = db.execute(
        select(
            func.date_trunc("day", User.created_at).label("day"),
            func.count(User.id),
        )
        .where(User.role == "PARENT", User.created_at >= _cutoff(now, 30))
        .group_by("day")
        .order_by("day")
    ).all()
    return {
        "as_of": now,
        "active_learners": active_learners,
        "active_families": active_families,
        "attempts": attempts,
        "tutor_sessions": sessions,
        "signups": signups,
        "signups_daily": [
            {"date": day.date().isoformat(), "count": int(count)} for day, count in daily
        ],
        "learners_total": db.scalar(select(func.count(Student.id))) or 0,
    }


def activity_by_region(db: Session, *, now: datetime | None = None) -> list[dict]:
    """30-day learning activity grouped by the family's saved
    country/state — families without a saved region bucket as UNSET."""
    cutoff = _cutoff(now or datetime.now(UTC), BREAKDOWN_DAYS)
    rows = db.execute(
        select(
            ParentProfile.country_code,
            ParentProfile.region_code,
            func.count(distinct(ParentProfile.id)),
            func.count(distinct(Attempt.student_id)),
            func.count(Attempt.id),
        )
        .select_from(ParentProfile)
        .join(Student, Student.parent_id == ParentProfile.user_id, isouter=True)
        .join(
            Attempt,
            (Attempt.student_id == Student.id) & (Attempt.created_at >= cutoff),
            isouter=True,
        )
        .group_by(ParentProfile.country_code, ParentProfile.region_code)
        .order_by(
            func.count(Attempt.id).desc(),
            ParentProfile.country_code,
            ParentProfile.region_code,
        )
    ).all()
    return [
        {
            "country_code": country or "UNSET",
            "region_code": region or "UNSET",
            "families": int(families),
            "active_learners": int(learners),
            "attempts": int(attempts),
        }
        for country, region, families, learners, attempts in rows
    ]


def activity_by_curriculum(db: Session, *, now: datetime | None = None) -> list[dict]:
    """30-day activity grouped by the curriculum actually practiced
    (attempt -> session -> curriculum)."""
    cutoff = _cutoff(now or datetime.now(UTC), BREAKDOWN_DAYS)
    active = (
        select(
            TutorSession.curriculum_id.label("curriculum_id"),
            func.count(distinct(Attempt.student_id)).label("active_learners"),
            func.count(Attempt.id).label("attempts"),
        )
        .select_from(Attempt)
        .join(TutorSession, TutorSession.id == Attempt.session_id)
        .where(Attempt.created_at >= cutoff, TutorSession.curriculum_id.is_not(None))
        .group_by(TutorSession.curriculum_id)
        .subquery()
    )
    enrolled = (
        select(
            Student.curriculum_id.label("curriculum_id"),
            func.count(Student.id).label("learners_total"),
        )
        .where(Student.curriculum_id.is_not(None))
        .group_by(Student.curriculum_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Curriculum.code,
            Curriculum.name,
            func.coalesce(enrolled.c.learners_total, 0),
            func.coalesce(active.c.active_learners, 0),
            func.coalesce(active.c.attempts, 0),
        )
        .select_from(Curriculum)
        .join(enrolled, enrolled.c.curriculum_id == Curriculum.id, isouter=True)
        .join(active, active.c.curriculum_id == Curriculum.id, isouter=True)
        .where(
            (enrolled.c.learners_total.is_not(None))
            | (active.c.attempts.is_not(None))
        )
        .order_by(func.coalesce(active.c.attempts, 0).desc(), Curriculum.code)
    ).all()
    return [
        {
            "code": code,
            "name": name,
            "learners_total": int(learners),
            "active_learners": int(active_learners),
            "attempts": int(attempts),
        }
        for code, name, learners, active_learners, attempts in rows
    ]


def conversion(db: Session, *, now: datetime | None = None) -> dict:
    """Plan mix and the Stripe trial funnel.

    "Paid family" = a profile whose effective tier isn't the free plan.
    Funnel counts come from the webhook-written audit rows: a "trialing"
    status is a started trial, "active" an activation (also fires on
    renewals — it's an approximation), and a deleted event a cancellation.
    """
    now = now or datetime.now(UTC)
    rows = db.execute(
        select(ParentProfile.subscription_tier, func.count()).group_by(
            ParentProfile.subscription_tier
        )
    ).all()
    breakdown = sorted(
        ({"tier": tier, "families": int(n)} for tier, n in rows),
        key=lambda r: (r["tier"] == FREE_PLAN, -r["families"]),
    )
    total = sum(r["families"] for r in breakdown)
    paid = sum(r["families"] for r in breakdown if r["tier"] != FREE_PLAN)
    trialing = db.scalar(
        select(func.count(ParentProfile.id)).where(
            ParentProfile.subscription_status == "trialing"
        )
    ) or 0

    status = AdminAuditEvent.after_json["status"].as_string()
    base = AdminAuditEvent.actor_label == "stripe-webhook"

    def funnel_count(days: int | None, status_value: str | None, *, deleted: bool = False) -> int:
        stmt = select(func.count(AdminAuditEvent.id)).where(base)
        if deleted:
            stmt = stmt.where(AdminAuditEvent.action == "CUSTOMER_SUBSCRIPTION_DELETED")
        else:
            stmt = stmt.where(status == status_value)
        if days is not None:
            stmt = stmt.where(AdminAuditEvent.created_at >= _cutoff(now, days))
        return db.scalar(stmt) or 0

    funnel: dict[str, dict[str, int]] = {"trials_started": {}, "activations": {}, "cancellations": {}}
    for label, days in FUNNEL_WINDOWS.items():
        funnel["trials_started"][label] = funnel_count(days, "trialing")
        funnel["activations"][label] = funnel_count(days, "active")
        funnel["cancellations"][label] = funnel_count(days, None, deleted=True)

    trials_total = funnel["trials_started"]["total"]
    return {
        "as_of": now,
        "plan_breakdown": breakdown,
        "families_total": total,
        "paid_families": paid,
        "trialing_now": int(trialing),
        "paid_share_pct": round(paid / total * 100, 1) if total else 0.0,
        "funnel": funnel,
        "trial_to_paid_pct": (
            round(funnel["activations"]["total"] / trials_total * 100, 1)
            if trials_total
            else None
        ),
    }
