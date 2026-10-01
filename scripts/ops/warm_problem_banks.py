"""Pre-generate problem inventory for pilot curricula using parametric generators.

Deepens persisted banks across difficulty levels so sessions serve varied items
even before the first learner arrives. Generation is deterministic-correct
(generator-owned canonical answers) and deduplicated by family fingerprint.

    docker compose exec tutor-api python /app/scripts/ops/warm_problem_banks.py [CURRICULUM_CODE ...]
"""

from __future__ import annotations

import random
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Skill
from app.services.problem_generation import generate_problem

TARGET_DIFFICULTIES = (1, 2, 3, 4, 5)
VARIANTS_PER_LEVEL = 2


def main() -> None:
    codes = sys.argv[1:]
    rng = random.Random(20261001)
    with SessionLocal() as db:
        query = (
            select(Skill)
            .join(Curriculum, Curriculum.id == Skill.curriculum_id)
            .order_by(Curriculum.code, Skill.code)
        )
        if codes:
            query = query.where(Curriculum.code.in_(codes))
        skills = db.scalars(query).all()

        created = 0
        for skill in skills:
            for difficulty in TARGET_DIFFICULTIES:
                for _ in range(VARIANTS_PER_LEVEL):
                    if generate_problem(
                        db, skill_id=skill.id, difficulty=difficulty, rng=rng
                    ) is not None:
                        created += 1
        db.commit()
        print(f"warmed {len(skills)} skills — {created} problems generated")


if __name__ == "__main__":
    main()
