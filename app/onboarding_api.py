import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.curriculum_models import StudentCurriculumEnrollment
from app.identity import (
    CurrentLearningAccess,
    CurrentParent,
    require_learning_owns_student,
    require_parent_owns_student,
)
from app.models import (
    Curriculum,
    LearnerAward,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
)
from app.parent_models import (
    ParentProfile,
    ParentStudentRelationship,
    ParentStudentRelationshipEvent,
)
from app.plan_models import Plan
from app.services.placement import recommend_next_skill
from app.services.plans import currency_for, effective_seats, localized_price, upgrade_target
from app.services.problem_generation import content_readiness
from app.services.regions import COUNTRIES
from app.services.review_schedule import reviews_due
from app.workspace_api import LearnContentOut, build_learn_content

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
DbSession = Annotated[Session, Depends(get_db)]


class CurriculumChoice(BaseModel):
    id: uuid.UUID
    code: str
    version: str
    jurisdiction: str | None
    grade_level: str | None
    country_code: str | None = None
    region_code: str | None = None


class RegionOption(BaseModel):
    code: str
    name: str
    has_curriculum: bool


class CountryOption(BaseModel):
    code: str
    name: str
    regions: list[RegionOption]


class FamilyRegionOut(BaseModel):
    country_code: str
    region_code: str


class RegionsOut(BaseModel):
    countries: list[CountryOption]
    family: FamilyRegionOut | None


class PlanPriceOut(BaseModel):
    currency: str
    amount: str


class PlanOption(BaseModel):
    code: str
    name: str
    max_students: int
    price: PlanPriceOut


class PlansOut(BaseModel):
    currency: str
    plans: list[PlanOption]


AVATAR_IDS = [f"avatar-{i}" for i in range(1, 9)]


class LearnerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    curriculum_id: uuid.UUID
    avatar_id: str = Field(default="avatar-1", max_length=80)


class LearnerAvatarUpdate(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=80)


class LearnerCreated(BaseModel):
    id: uuid.UUID
    first_name: str
    curriculum_id: uuid.UUID
    curriculum_code: str
    curriculum_version: str
    jurisdiction: str | None
    avatar_id: str = "avatar-1"


class LearnerChoice(BaseModel):
    id: uuid.UUID
    first_name: str
    curriculum_id: uuid.UUID
    curriculum_code: str
    curriculum_version: str
    jurisdiction: str | None
    avatar_id: str = "avatar-1"


class SkillChoice(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    content_ready: bool = True
    learn: LearnContentOut | None = None


class LaunchpadSkill(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    reason: str
    mastery_score: float
    session_id: uuid.UUID | None = None


class LaunchpadReview(BaseModel):
    skill_id: uuid.UUID
    skill_name: str


class LearnerLaunchpad(BaseModel):
    recommended: LaunchpadSkill | None
    reviews_due: list[LaunchpadReview]
    mastered_count: int
    learning_count: int
    ready_skill_count: int
    award_count: int


@router.get("/regions", response_model=RegionsOut)
def list_regions(access: CurrentLearningAccess, db: DbSession) -> RegionsOut:
    """Country → state/province cascade data + the family's saved region."""
    covered = set(
        db.scalars(
            select(Curriculum.region_code).where(
                Curriculum.active.is_(True), Curriculum.region_code.is_not(None)
            )
        ).all()
    )
    parent = access.parent
    return RegionsOut(
        countries=[
            CountryOption(
                code=country_code,
                name=country["name"],
                regions=[
                    RegionOption(
                        code=region_code,
                        name=region_name,
                        has_curriculum=region_code in covered,
                    )
                    for region_code, region_name in sorted(
                        country["regions"].items(), key=lambda item: item[1]
                    )
                ],
            )
            for country_code, country in COUNTRIES.items()
        ],
        family=(
            FamilyRegionOut(country_code=parent.country_code, region_code=parent.region_code)
            if parent.country_code and parent.region_code
            else None
        ),
    )


@router.get("/curricula", response_model=list[CurriculumChoice])
def list_active_curricula(access: CurrentLearningAccess, db: DbSession) -> list[CurriculumChoice]:
    query = select(Curriculum).where(Curriculum.active.is_(True))
    if access.learner_id is not None:
        student = require_learning_owns_student(access, db.get(Student, access.learner_id))
        query = query.where(Curriculum.id == student.curriculum_id)
    else:
        # Family cascade: a region with coverage sees only its own curricula.
        # A region without coverage (or country only) falls back to the whole
        # country so the family can pick the closest grade-level fit.
        parent = access.parent
        if parent.region_code:
            covered = db.scalar(
                select(func.count(Curriculum.id)).where(
                    Curriculum.active.is_(True),
                    Curriculum.region_code == parent.region_code,
                )
            )
            if covered:
                query = query.where(Curriculum.region_code == parent.region_code)
            elif parent.country_code:
                query = query.where(Curriculum.country_code == parent.country_code)
        elif parent.country_code:
            query = query.where(Curriculum.country_code == parent.country_code)
    curricula = db.scalars(
        query.order_by(
            Curriculum.jurisdiction, Curriculum.grade_level, Curriculum.code, Curriculum.version
        )
    ).all()
    return [
        CurriculumChoice(
            id=curriculum.id,
            code=curriculum.code,
            version=curriculum.version,
            jurisdiction=curriculum.jurisdiction,
            grade_level=curriculum.grade_level,
            country_code=curriculum.country_code,
            region_code=curriculum.region_code,
        )
        for curriculum in curricula
    ]


@router.get("/plans", response_model=PlansOut)
def list_plans(access: CurrentLearningAccess, db: DbSession) -> PlansOut:
    """Active plans priced in the family's currency (CAD for Canada, USD
    otherwise). CAD amounts are the stored 3-year-average conversion, not a
    live quote."""
    country = access.parent.country_code if access.parent else None
    return PlansOut(
        currency=currency_for(country),
        plans=[
            PlanOption(
                code=plan.code,
                name=plan.name,
                max_students=plan.max_students,
                price=PlanPriceOut(**localized_price(plan, country)),
            )
            for plan in db.scalars(
                select(Plan).where(Plan.active.is_(True)).order_by(Plan.monthly_price_usd)
            ).all()
        ],
    )


@router.get("/learners", response_model=list[LearnerChoice])
def list_learners(access: CurrentLearningAccess, db: DbSession) -> list[LearnerChoice]:
    rows = db.execute(
        select(Student, Curriculum)
        .join(Curriculum, Curriculum.id == Student.curriculum_id)
        .where(
            Student.parent_id == access.parent.user_id,
            Student.active.is_(True),
            *([Student.id == access.learner_id] if access.learner_id is not None else []),
        )
        .order_by(Student.first_name, Student.id)
    ).all()
    return [
        LearnerChoice(
            id=student.id,
            first_name=student.first_name,
            curriculum_id=curriculum.id,
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            jurisdiction=curriculum.jurisdiction,
            avatar_id=student.avatar_id,
        )
        for student, curriculum in rows
    ]


@router.patch("/learners/{student_id}", response_model=LearnerChoice)
def update_learner_avatar(
    student_id: uuid.UUID,
    payload: LearnerAvatarUpdate,
    parent: CurrentParent,
    db: DbSession,
) -> LearnerChoice:
    student = require_parent_owns_student(parent, db.get(Student, student_id))
    if payload.avatar_id not in AVATAR_IDS:
        raise HTTPException(status_code=422, detail="Unknown avatar")
    student.avatar_id = payload.avatar_id
    db.commit()
    curriculum = db.get(Curriculum, student.curriculum_id) if student.curriculum_id else None
    if curriculum is None:
        raise HTTPException(status_code=409, detail="Learner curriculum is unavailable")
    return LearnerChoice(
        id=student.id,
        first_name=student.first_name,
        curriculum_id=curriculum.id,
        curriculum_code=curriculum.code,
        curriculum_version=curriculum.version,
        jurisdiction=curriculum.jurisdiction,
        avatar_id=student.avatar_id,
    )


@router.get("/learners/{student_id}/skills", response_model=list[SkillChoice])
def list_learner_skills(
    student_id: uuid.UUID, access: CurrentLearningAccess, db: DbSession
) -> list[SkillChoice]:
    student = require_learning_owns_student(access, db.get(Student, student_id))
    if student.curriculum_id is None:
        raise HTTPException(status_code=409, detail="Learner curriculum is unavailable")
    skills = db.scalars(
        select(Skill)
        .where(Skill.curriculum_id == student.curriculum_id)
        .order_by(Skill.difficulty_level, Skill.code)
    ).all()
    return [
        SkillChoice(
            id=skill.id,
            code=skill.code,
            name=skill.name,
            content_ready=content_readiness(db, skill_id=skill.id).ready,
            learn=build_learn_content(skill.learn_content),
        )
        for skill in skills
    ]


@router.get("/learners/{student_id}/launchpad", response_model=LearnerLaunchpad)
def get_learner_launchpad(
    student_id: uuid.UUID, access: CurrentLearningAccess, db: DbSession
) -> LearnerLaunchpad:
    student = require_learning_owns_student(access, db.get(Student, student_id))
    if student.curriculum_id is None:
        raise HTTPException(status_code=409, detail="Learner curriculum is unavailable")

    skills = db.scalars(select(Skill).where(Skill.curriculum_id == student.curriculum_id)).all()
    skill_ids = [skill.id for skill in skills]
    progress_rows = (
        db.scalars(
            select(StudentSkill).where(
                StudentSkill.student_id == student.id,
                StudentSkill.skill_id.in_(skill_ids),
            )
        ).all()
        if skill_ids
        else []
    )
    progress_by_skill = {row.skill_id: row for row in progress_rows}

    active_session = db.scalar(
        select(TutorSession)
        .where(
            TutorSession.student_id == student.id,
            TutorSession.curriculum_id == student.curriculum_id,
            TutorSession.status == "ACTIVE",
        )
        .order_by(TutorSession.started_at.desc(), TutorSession.id.desc())
    )
    recommended = None
    if active_session is not None:
        active_skill = db.get(
            Skill, active_session.active_skill_id or active_session.primary_skill_id
        )
        if active_skill is not None and active_skill.curriculum_id == student.curriculum_id:
            progress = progress_by_skill.get(active_skill.id)
            recommended = LaunchpadSkill(
                id=active_skill.id,
                code=active_skill.code,
                name=active_skill.name,
                reason="CONTINUE_SESSION",
                mastery_score=float(progress.mastery_score) if progress else 0.0,
                session_id=active_session.id,
            )
    if recommended is None:
        placement = recommend_next_skill(
            db, student_id=student.id, curriculum_id=student.curriculum_id
        )
        if placement is not None and content_readiness(db, skill_id=placement.skill.id).ready:
            progress = progress_by_skill.get(placement.skill.id)
            recommended = LaunchpadSkill(
                id=placement.skill.id,
                code=placement.skill.code,
                name=placement.skill.name,
                reason=placement.reason,
                mastery_score=float(progress.mastery_score) if progress else 0.0,
            )

    review_items = reviews_due(db, student_id=student.id, curriculum_id=student.curriculum_id)
    mastered_count = sum(row.status == SkillStatus.MASTERED for row in progress_rows)
    learning_count = sum(
        row.status not in {SkillStatus.NOT_STARTED, SkillStatus.MASTERED} for row in progress_rows
    )
    ready_skill_count = sum(content_readiness(db, skill_id=skill.id).ready for skill in skills)
    award_count = (
        db.scalar(select(func.count(LearnerAward.id)).where(LearnerAward.student_id == student.id))
        or 0
    )
    return LearnerLaunchpad(
        recommended=recommended,
        reviews_due=[
            LaunchpadReview(skill_id=item.skill.id, skill_name=item.skill.name)
            for item in review_items
        ],
        mastered_count=mastered_count,
        learning_count=learning_count,
        ready_skill_count=ready_skill_count,
        award_count=award_count,
    )


@router.post("/learners", response_model=LearnerCreated, status_code=status.HTTP_201_CREATED)
def create_learner(payload: LearnerCreate, parent: CurrentParent, db: DbSession) -> LearnerCreated:
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
    seat_limit = effective_seats(db, locked_parent)
    if current_count >= seat_limit:
        upgrade = upgrade_target(db, locked_parent)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "STUDENT_SEAT_LIMIT_REACHED",
                "subscription_tier": locked_parent.subscription_tier,
                "current_students": current_count,
                "max_students": seat_limit,
                "upgrade": (
                    {"recommended_tier": upgrade.code, "max_students": upgrade.max_students}
                    if upgrade is not None
                    else None
                ),
            },
        )

    curriculum = db.get(Curriculum, payload.curriculum_id)
    if curriculum is None or not curriculum.active:
        raise HTTPException(status_code=404, detail="Active curriculum not found")

    first_name = payload.first_name.strip()
    if not first_name:
        raise HTTPException(status_code=422, detail="Learner first name is required")

    if payload.avatar_id not in AVATAR_IDS:
        raise HTTPException(status_code=422, detail="Unknown avatar")
    student = Student(
        parent_id=parent.user_id,
        curriculum_id=curriculum.id,
        first_name=first_name,
        grade_level=curriculum.grade_level or "UNSPECIFIED",
        school_system=None,
        avatar_id=payload.avatar_id,
    )
    db.add(student)
    db.flush()
    db.add(
        StudentCurriculumEnrollment(
            student_id=student.id,
            curriculum_id=curriculum.id,
            provenance_json={"source": "parent_onboarding"},
        )
    )
    relationship = ParentStudentRelationship(
        parent_profile_id=parent.id,
        student_id=student.id,
        relationship_type="GUARDIAN",
        active=True,
    )
    db.add(relationship)
    db.flush()
    db.add(ParentStudentRelationshipEvent(relationship_id=relationship.id, action="LINKED"))
    db.commit()

    return LearnerCreated(
        id=student.id,
        first_name=student.first_name,
        curriculum_id=curriculum.id,
        curriculum_code=curriculum.code,
        curriculum_version=curriculum.version,
        jurisdiction=curriculum.jurisdiction,
        avatar_id=student.avatar_id,
    )
