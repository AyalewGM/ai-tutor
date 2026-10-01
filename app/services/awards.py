"""Evidence-backed learner badges.

Badges are awarded only from authoritative events in the respond path —
never from frontend counters or LLM output. Each badge maps to a real
learning signal: independent correctness, streaks, mastery gates,
prerequisite-gap closure, difficulty promotion, and spaced-review passes.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Attempt, LearnerAward, Problem, Skill


@dataclass(frozen=True)
class BadgeSpec:
    code: str
    name: str
    description: str
    per_skill: bool


BADGE_CATALOG: dict[str, BadgeSpec] = {
    spec.code: spec
    for spec in (
        BadgeSpec(
            "FIRST_CORRECT",
            "First Steps",
            "You solved your first problem — every journey starts here",
            per_skill=False,
        ),
        BadgeSpec(
            "STREAK_3",
            "On a Roll",
            "3 correct answers in a row — you're building momentum",
            per_skill=False,
        ),
        BadgeSpec(
            "STREAK_5",
            "Unstoppable",
            "5 correct answers in a row — serious focus",
            per_skill=False,
        ),
        BadgeSpec(
            "LEVEL_UP",
            "Level Up",
            "You're ready for harder problems — the challenge just increased",
            per_skill=True,
        ),
        BadgeSpec(
            "SKILL_MASTERED",
            "Skill Mastered",
            "You proved this skill on your own — no hints needed",
            per_skill=True,
        ),
        BadgeSpec(
            "GAP_FIXED",
            "Gap Closer",
            "You fixed a missing building block and got back on track",
            per_skill=True,
        ),
        BadgeSpec(
            "FRESH_EYES",
            "Still Sharp",
            "You came back later and still had it — that's real learning",
            per_skill=True,
        ),
    )
}


def _already_awarded(
    db: Session, student_id: uuid.UUID, code: str, skill_id: uuid.UUID | None
) -> bool:
    query = select(func.count(LearnerAward.id)).where(
        LearnerAward.student_id == student_id,
        LearnerAward.badge_code == code,
    )
    if skill_id is None:
        query = query.where(LearnerAward.skill_id.is_(None))
    else:
        query = query.where(LearnerAward.skill_id == skill_id)
    return bool(db.scalar(query))


def _consecutive_correct(db: Session, student_id: uuid.UUID) -> int:
    attempts = db.scalars(
        select(Attempt.is_correct)
        .where(Attempt.student_id == student_id, Attempt.is_correct.isnot(None))
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        .limit(10)
    ).all()
    streak = 0
    for flag in attempts:
        if flag:
            streak += 1
        else:
            break
    return streak


def evaluate_awards(
    db: Session,
    *,
    student_id: uuid.UUID,
    session_id: uuid.UUID,
    active_skill_id: uuid.UUID,
    correct: bool,
    engine_action: str | None,
    mastery_passed: bool,
    review_passed: bool,
    gap_fixed: bool,
) -> list[LearnerAward]:
    """Award badges earned by this response. Call before db.commit()."""
    earned: list[tuple[str, uuid.UUID | None]] = []

    if correct:
        streak = _consecutive_correct(db, student_id)
        if streak == 1:
            earned.append(("FIRST_CORRECT", None))
        if streak >= 3:
            earned.append(("STREAK_3", None))
        if streak >= 5:
            earned.append(("STREAK_5", None))
    if engine_action == "INCREASE_DIFFICULTY":
        earned.append(("LEVEL_UP", active_skill_id))
    if mastery_passed:
        earned.append(("SKILL_MASTERED", active_skill_id))
    if gap_fixed:
        earned.append(("GAP_FIXED", active_skill_id))
    if review_passed:
        earned.append(("FRESH_EYES", active_skill_id))

    awards: list[LearnerAward] = []
    for code, skill_id in earned:
        spec = BADGE_CATALOG[code]
        scoped_skill = skill_id if spec.per_skill else None
        if _already_awarded(db, student_id, code, scoped_skill):
            continue
        award = LearnerAward(
            student_id=student_id,
            badge_code=code,
            skill_id=scoped_skill,
            session_id=session_id,
        )
        db.add(award)
        db.flush()
        awards.append(award)
    return awards


def _current_streak(db: Session, student_id: uuid.UUID) -> int:
    return _consecutive_correct(db, student_id)


STREAK_TARGETS = {"STREAK_3": 3, "STREAK_5": 5}


def badge_collection(
    db: Session, student_id: uuid.UUID
) -> list[dict]:
    """Full badge catalog with earned state and progress hints."""
    earned_rows = db.scalars(
        select(LearnerAward).where(LearnerAward.student_id == student_id)
    ).all()
    earned_global = {
        row.badge_code for row in earned_rows if row.skill_id is None
    }
    earned_skill: dict[str, list[LearnerAward]] = {}
    for row in earned_rows:
        if row.skill_id is not None:
            earned_skill.setdefault(row.badge_code, []).append(row)

    streak = _current_streak(db, student_id)
    collection: list[dict] = []
    for code, spec in BADGE_CATALOG.items():
        if spec.per_skill:
            rows = earned_skill.get(code, [])
            collection.append(
                {
                    "code": code,
                    "name": spec.name,
                    "description": spec.description,
                    "earned": bool(rows),
                    "times_earned": len(rows),
                    "skill_names": [
                        db.get(Skill, row.skill_id).name
                        for row in rows
                        if db.get(Skill, row.skill_id) is not None
                    ],
                    "progress": None,
                }
            )
        else:
            progress = None
            if code in STREAK_TARGETS:
                progress = {
                    "current": min(streak, STREAK_TARGETS[code]),
                    "target": STREAK_TARGETS[code],
                }
            collection.append(
                {
                    "code": code,
                    "name": spec.name,
                    "description": spec.description,
                    "earned": code in earned_global,
                    "times_earned": 1 if code in earned_global else 0,
                    "skill_names": [],
                    "progress": progress,
                }
            )
    return collection


def award_out(db: Session, award: LearnerAward) -> dict:
    spec = BADGE_CATALOG.get(award.badge_code)
    skill_name = None
    if award.skill_id:
        skill = db.get(Skill, award.skill_id)
        skill_name = skill.name if skill else None
    return {
        "code": award.badge_code,
        "name": spec.name if spec else award.badge_code,
        "description": spec.description if spec else "",
        "skill_name": skill_name,
        "awarded_at": award.created_at,
    }


# --- Learner points (XP) -----------------------------------------------------
#
# XP is derived from authoritative attempt + award rows only — never from
# client counters. Independent work pays the most; assisted correctness pays
# partial credit; wrong answers pay nothing. Badges carry a one-time bonus so
# real milestones (mastery, gap closure, retained review) out-earn grinding.

BADGE_XP: dict[str, int] = {
    "FIRST_CORRECT": 10,
    "STREAK_3": 10,
    "STREAK_5": 15,
    "LEVEL_UP": 20,
    "SKILL_MASTERED": 50,
    "GAP_FIXED": 40,
    "FRESH_EYES": 30,
}

LEVEL_TITLES = (
    "Newcomer",
    "Explorer",
    "Solver",
    "Strategist",
    "Scholar",
    "Master",
    "Mentor",
    "Sage",
)


def _xp_for_next_level(level: int) -> int:
    """XP needed to go from `level` to `level + 1` — grows linearly."""
    return 100 + 60 * (level - 1)


def attempt_xp(is_correct: bool, assistance_level: int, difficulty: int) -> int:
    if not is_correct:
        return 0
    if assistance_level <= 0:
        return 8 + 2 * difficulty
    return 4 + difficulty


def level_for_xp(xp: int) -> tuple[int, int]:
    """Return (level, xp_in_level) for a cumulative XP total."""
    level = 1
    remaining = xp
    while remaining >= _xp_for_next_level(level) and level < len(LEVEL_TITLES):
        remaining -= _xp_for_next_level(level)
        level += 1
    return level, remaining


def learner_progress(db: Session, student_id: uuid.UUID) -> dict:
    """Authoritative XP/level snapshot for a learner."""
    rows = db.execute(
        select(Attempt.is_correct, Attempt.assistance_level, Problem.difficulty)
        .join(Problem, Attempt.problem_id == Problem.id)
        .where(Attempt.student_id == student_id, Attempt.is_correct.isnot(None))
    ).all()
    xp = sum(attempt_xp(bool(ok), int(assistance or 0), int(diff or 1))
             for ok, assistance, diff in rows)

    award_codes = db.scalars(
        select(LearnerAward.badge_code).where(LearnerAward.student_id == student_id)
    ).all()
    xp += sum(BADGE_XP.get(code, 0) for code in award_codes)

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_rows = db.execute(
        select(Attempt.is_correct, Attempt.assistance_level, Problem.difficulty)
        .join(Problem, Attempt.problem_id == Problem.id)
        .where(
            Attempt.student_id == student_id,
            Attempt.is_correct.isnot(None),
            Attempt.created_at >= today_start,
        )
    ).all()
    xp_today = sum(
        attempt_xp(bool(ok), int(assistance or 0), int(diff or 1))
        for ok, assistance, diff in today_rows
    )
    today_award_codes = db.scalars(
        select(LearnerAward.badge_code).where(
            LearnerAward.student_id == student_id,
            LearnerAward.created_at >= today_start,
        )
    ).all()
    xp_today += sum(BADGE_XP.get(code, 0) for code in today_award_codes)

    level, xp_in_level = level_for_xp(xp)
    return {
        "xp": xp,
        "level": level,
        "level_title": LEVEL_TITLES[level - 1],
        "xp_in_level": xp_in_level,
        "xp_for_next": _xp_for_next_level(level),
        "xp_today": xp_today,
    }
