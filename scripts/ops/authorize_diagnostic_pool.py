"""Backfill ProblemContentMetadata mode flags on existing banked problems.

Skills whose problems predate the eligibility model are invisible to the
fail-closed selector: no metadata row means no mode may serve them, and the
generator fallback is only authorized for problem types that already carry a
flagged item for that mode. Flagging a small, bounded set per skill and
problem type re-authorizes the mode — generator types then self-sustain via
deterministic generation.

Items are claimed distinctly per mode — an item may never serve two
assessment modes (content_validation enforces no cross-mode reuse; the same
item must not appear in both a diagnostic probe and a mastery check).

    docker compose exec tutor-api python /app/scripts/ops/authorize_diagnostic_pool.py \
        [--dry-run] [--modes diagnostic guided] [CURRICULUM_CODE ...]
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import or_, select

from app.content_models import ProblemContentMetadata
from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill
from app.services.problem_generation import GENERATORS

ALL_MODES = ("diagnostic", "guided", "independent", "mastery")
FLAG_FOR_MODE = {
    "diagnostic": "diagnostic_eligible",
    "guided": "guided_eligible",
    "independent": "independent_eligible",
    "mastery": "mastery_eligible",
}
PER_TYPE_PER_MODE = 2


def _claim_problems(
    problems: list[Problem], claimed: set, count: int
) -> list[Problem]:
    return [p for p in problems if p.id not in claimed][:count]


def _authorize(
    db, problem: Problem, skill: Skill, mode: str, curriculum_id
) -> bool:
    """Set the mode flag on the problem's metadata row. Returns True if a
    change was made."""
    metadata = db.scalar(
        select(ProblemContentMetadata).where(
            ProblemContentMetadata.problem_id == problem.id
        )
    )
    flag = FLAG_FOR_MODE[mode]
    if metadata is not None:
        if any(getattr(metadata, name) for name in FLAG_FOR_MODE.values()):
            return False  # already claimed for a mode — never stack flags
        setattr(metadata, flag, True)
        return True
    db.add(
        ProblemContentMetadata(
            problem_id=problem.id,
            curriculum_id=curriculum_id,
            objective=f"Backfilled {mode} eligibility for banked {skill.code} item.",
            evaluation_type="EXACT",
            extension_eligible=False,
            llm_solution_required=False,
            provenance_json={
                "source_type": "OPS_BACKFILL",
                "script": "authorize_diagnostic_pool",
            },
            **{name: name == flag for name in FLAG_FOR_MODE.values()},
        )
    )
    db.flush()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("curricula", nargs="*", help="Curriculum codes (default: all)")
    parser.add_argument("--modes", nargs="+", default=list(ALL_MODES), choices=ALL_MODES)
    parser.add_argument("--per-type", type=int, default=PER_TYPE_PER_MODE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with SessionLocal() as db:
        query = select(Skill).join(Curriculum, Curriculum.id == Skill.curriculum_id).order_by(
            Curriculum.code, Skill.code
        )
        if args.curricula:
            query = query.where(Curriculum.code.in_(args.curricula))
        skills = db.scalars(query).all()

        touched_skills = flagged = 0
        for skill in skills:
            problems = list(
                db.scalars(
                    select(Problem)
                    .where(
                        Problem.primary_skill_id == skill.id,
                        Problem.canonical_answer.isnot(None),
                        Problem.canonical_answer != "",
                    )
                    .order_by(Problem.problem_type, Problem.difficulty, Problem.id)
                ).all()
            )
            if not problems:
                continue
            by_type: dict[str, list[Problem]] = {}
            for problem in problems:
                by_type.setdefault(problem.problem_type, []).append(problem)
            # Generator types first — one flagged item self-sustains the mode.
            ordered_types = sorted(
                by_type, key=lambda t: (t not in GENERATORS, t)
            )

            claimed: set = {
                row[0]
                for row in db.execute(
                    select(ProblemContentMetadata.problem_id)
                    .join(Problem, ProblemContentMetadata.problem_id == Problem.id)
                    .where(
                        Problem.primary_skill_id == skill.id,
                        or_(
                            ProblemContentMetadata.diagnostic_eligible.is_(True),
                            ProblemContentMetadata.guided_eligible.is_(True),
                            ProblemContentMetadata.independent_eligible.is_(True),
                            ProblemContentMetadata.mastery_eligible.is_(True),
                        ),
                    )
                ).all()
            }
            skill_changed = False
            for mode in args.modes:
                for problem_type in ordered_types:
                    for problem in _claim_problems(
                        by_type[problem_type], claimed, args.per_type
                    ):
                        claimed.add(problem.id)
                        if _authorize(db, problem, skill, mode, skill.curriculum_id):
                            flagged += 1
                            skill_changed = True
            if skill_changed:
                touched_skills += 1

        if args.dry_run:
            db.rollback()
            prefix = "[dry-run] would flag"
        else:
            db.commit()
            prefix = "flagged"
        print(
            f"{prefix} {flagged} problems across {touched_skills}/{len(skills)} skills"
        )


if __name__ == "__main__":
    sys.exit(main())
