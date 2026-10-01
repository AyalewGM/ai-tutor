import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentParent, CurrentUser, require_parent_role
from app.models import Attempt, MasteryEvent, Student, TutorSession
from app.parent_models import ParentProfile, ParentStudentRelationship, ParentStudentRelationshipEvent
from app.parent_schemas import (
    ChildDashboardOut,
    ChildSummaryOut,
    LinkChildIn,
    LinkChildOut,
    ParentProfileOut,
    ParentProfileUpdateIn,
)
from app.services.parent_dashboard import (
    dashboard,
    link_child_with_claim,
    list_children,
    unlink_child,
)
from app.schemas import (
    PINVerifyOut,
    PINVerifySchema,
    ProgressStudentSummary,
    ProgressSummaryOut,
    StudentCreateSchema,
    StudentProfileOut,
)
from app.services.parent_gate import (
    clear_pin_attempts,
    issue_parent_unlock,
    register_pin_attempt,
    require_parent_unlock,
)

router = APIRouter(prefix="/parents", tags=["parents"])
DbSession = Annotated[Session, Depends(get_db)]
_pin_hasher = PasswordHasher()


def _profile_out(user: CurrentUser, parent: ParentProfile) -> ParentProfileOut:
    return ParentProfileOut(
        id=parent.id,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
    )


@router.post("/profile", response_model=ParentProfileOut)
def create_or_load_profile(user: CurrentUser, db: DbSession) -> ParentProfileOut:
    require_parent_role(user)
    parent = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
    if parent is None:
        parent = ParentProfile(user_id=user.id)
        db.add(parent)
        db.commit()
        db.refresh(parent)
    return _profile_out(user, parent)


@router.get("/profile", response_model=ParentProfileOut)
def get_profile(request: Request, user: CurrentUser, parent: CurrentParent) -> ParentProfileOut:
    require_parent_unlock(request, parent.user_id)
    return _profile_out(user, parent)


@router.patch("/profile", response_model=ParentProfileOut)
def update_profile(
    payload: ParentProfileUpdateIn,
    request: Request,
    user: CurrentUser,
    parent: CurrentParent,
    db: DbSession,
) -> ParentProfileOut:
    require_parent_unlock(request, parent.user_id)
    user.display_name = payload.display_name.strip()
    db.commit()
    db.refresh(user)
    return _profile_out(user, parent)


@router.get("/children", response_model=list[ChildSummaryOut])
def get_children(parent: CurrentParent, db: DbSession) -> list[ChildSummaryOut]:
    return list_children(db, parent=parent)


@router.post("/children/link", response_model=LinkChildOut)
def link_child(payload: LinkChildIn, parent: CurrentParent, db: DbSession) -> LinkChildOut:
    locked_parent = db.scalar(
        select(ParentProfile).where(ParentProfile.id == parent.id).with_for_update()
    )
    if locked_parent is None:
        raise HTTPException(status_code=404, detail="Parent profile not found")
    active_relationships = int(
        db.scalar(
            select(func.count(ParentStudentRelationship.id)).where(
                ParentStudentRelationship.parent_profile_id == parent.id,
                ParentStudentRelationship.active.is_(True),
            )
        )
        or 0
    )
    seat_limit = locked_parent.max_students or 1
    if active_relationships >= seat_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "STUDENT_SEAT_LIMIT_REACHED",
                "subscription_tier": locked_parent.subscription_tier,
                "current_students": active_relationships,
                "max_students": seat_limit,
                "upgrade": {"recommended_tier": "pro", "max_students": 5},
            },
        )
    result = link_child_with_claim(db, parent=parent, claim_token=payload.claim_token)
    db.commit()
    return result


@router.delete("/children/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_child(student_id: uuid.UUID, parent: CurrentParent, db: DbSession) -> Response:
    unlink_child(db, parent=parent, student_id=student_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/children/{student_id}/dashboard", response_model=ChildDashboardOut)
def child_dashboard(
    student_id: uuid.UUID,
    request: Request,
    parent: CurrentParent,
    db: DbSession,
) -> ChildDashboardOut:
    require_parent_unlock(request, parent.user_id)
    return dashboard(db, parent=parent, student_id=student_id)



@router.post(
    "/{parent_id}/add-student",
    response_model=StudentProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def add_student(
    parent_id: uuid.UUID,
    payload: StudentCreateSchema,
    parent: CurrentParent,
    db: DbSession,
) -> StudentProfileOut:
    if parent_id != parent.user_id:
        raise HTTPException(status_code=404, detail="Parent account not found")

    locked_parent = db.scalar(
        select(ParentProfile).where(ParentProfile.id == parent.id).with_for_update()
    )
    if locked_parent is None:
        raise HTTPException(status_code=404, detail="Parent profile not found")

    current_count = int(
        db.scalar(
            select(func.count(ParentStudentRelationship.id)).where(
                ParentStudentRelationship.parent_profile_id == parent.id,
                ParentStudentRelationship.active.is_(True),
            )
        )
        or 0
    )
    seat_limit = locked_parent.max_students or 1
    if current_count >= seat_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "STUDENT_SEAT_LIMIT_REACHED",
                "message": "Your current plan has no available student seats.",
                "subscription_tier": locked_parent.subscription_tier,
                "current_students": current_count,
                "max_students": seat_limit,
                "upgrade": {
                    "recommended_tier": "pro",
                    "max_students": 5,
                    "action": "OPEN_BILLING",
                },
            },
        )

    student = Student(
        parent_id=parent.user_id,
        curriculum_id=None,
        first_name=payload.display_name,
        grade_level=payload.grade_level or "UNSPECIFIED",
        school_system=None,
        avatar_id=payload.avatar_id,
        active=True,
    )
    db.add(student)
    db.flush()
    relationship = ParentStudentRelationship(
        parent_profile_id=parent.id,
        student_id=student.id,
        relationship_type="GUARDIAN",
        active=True,
    )
    db.add(relationship)
    db.flush()
    db.add(
        ParentStudentRelationshipEvent(
            relationship_id=relationship.id,
            action="LINKED",
        )
    )
    db.commit()
    db.refresh(student)
    return StudentProfileOut(
        id=student.id,
        display_name=student.first_name,
        grade_level=None if student.grade_level == "UNSPECIFIED" else student.grade_level,
        avatar_id=student.avatar_id,
    )


@router.post("/verify-pin", response_model=PINVerifyOut)
def verify_parent_pin(
    payload: PINVerifySchema,
    parent: CurrentParent,
) -> PINVerifyOut:
    register_pin_attempt(parent.user_id)
    if not parent.parent_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parent PIN is not configured; use password re-authentication",
        )
    try:
        valid = _pin_hasher.verify(parent.parent_pin_hash, payload.parent_pin)
    except VerificationError:
        valid = False
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid parent PIN",
        )
    clear_pin_attempts(parent.user_id)
    unlock_token = issue_parent_unlock(parent.user_id)
    return PINVerifyOut(
        verified=True,
        unlock_token=unlock_token,
        expires_in_seconds=600,
    )


@router.get("/progress-summary", response_model=ProgressSummaryOut)
def progress_summary(
    request: Request,
    parent: CurrentParent,
    db: DbSession,
) -> ProgressSummaryOut:
    require_parent_unlock(request, parent.user_id)
    since = datetime.now(UTC) - timedelta(days=7)
    students = db.scalars(
        select(Student)
        .join(
            ParentStudentRelationship,
            ParentStudentRelationship.student_id == Student.id,
        )
        .where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.active.is_(True),
            Student.active.is_(True),
        )
        .order_by(Student.first_name, Student.id)
    ).all()

    summaries: list[ProgressStudentSummary] = []
    for student in students:
        sessions_started = int(
            db.scalar(
                select(func.count(TutorSession.id)).where(
                    TutorSession.student_id == student.id,
                    TutorSession.started_at >= since,
                )
            )
            or 0
        )
        sessions_completed = int(
            db.scalar(
                select(func.count(TutorSession.id)).where(
                    TutorSession.student_id == student.id,
                    TutorSession.ended_at.is_not(None),
                    TutorSession.ended_at >= since,
                )
            )
            or 0
        )
        attempts = int(
            db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.student_id == student.id,
                    Attempt.created_at >= since,
                )
            )
            or 0
        )
        correct_attempts = int(
            db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.student_id == student.id,
                    Attempt.created_at >= since,
                    Attempt.is_correct.is_(True),
                )
            )
            or 0
        )
        average_mastery = db.scalar(
            select(func.avg(MasteryEvent.new_score)).where(
                MasteryEvent.student_id == student.id,
                MasteryEvent.created_at >= since,
            )
        )
        summaries.append(
            ProgressStudentSummary(
                student_id=student.id,
                display_name=student.first_name,
                sessions_started=sessions_started,
                sessions_completed=sessions_completed,
                attempts=attempts,
                correct_attempts=correct_attempts,
                average_mastery=float(average_mastery or 0.0),
            )
        )

    return ProgressSummaryOut(window_days=7, students=summaries)
