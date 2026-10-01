"""Backfill ``answer_kind`` on freshly seeded problems (idempotent).

Seed scripts create problems with the ``FREE_TEXT`` default. This pass upgrades
problems whose canonical answer is a bare fraction to ``FRACTION`` (grader then
accepts equivalent forms like 2/4 = 1/2) or a bare integer to ``INTEGER``.
Multiple-choice problems must be authored explicitly with ``choices``; this
script never infers them.

Run after any curriculum seed on a fresh database:

    docker compose -f docker-compose.pilot.yml exec tutor-api \
        python /app/scripts/ops/backfill_answer_kinds.py
"""

from __future__ import annotations

import re

from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.models import Problem

_FRACTION = re.compile(r"^\s*-?\d+\s*/\s*-?\d+\s*$")
_INTEGER = re.compile(r"^\s*-?\d+\s*$")


def main() -> None:
    with SessionLocal() as db:
        problems = db.scalars(
            select(Problem).where(Problem.answer_kind == "FREE_TEXT")
        ).all()
        upgraded = {"FRACTION": 0, "INTEGER": 0}
        for problem in problems:
            canonical = problem.canonical_answer or ""
            if _FRACTION.match(canonical):
                kind = "FRACTION"
            elif _INTEGER.match(canonical):
                kind = "INTEGER"
            else:
                continue
            db.execute(
                update(Problem)
                .where(Problem.id == problem.id)
                .values(answer_kind=kind)
            )
            upgraded[kind] += 1
        db.commit()
    print(f"backfill complete: {upgraded['FRACTION']} FRACTION, {upgraded['INTEGER']} INTEGER")


if __name__ == "__main__":
    main()
