"""Per-skill content-depth audit for release curricula.

Beyond the ``content_readiness`` floor (>=2 families OR a generator), this
reports what pilot quality actually needs: difficulty spread, generator
coverage, and word-problem share per skill.

    docker compose exec tutor-api python /app/scripts/ops/content_audit_report.py [CURRICULUM_CODE ...]
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill
from app.services.problem_generation import GENERATORS, content_readiness

MIN_DIFFICULTY_STEPS = 3


def audit_curriculum(db, curriculum: Curriculum) -> dict:
    skills = db.scalars(
        select(Skill).where(Skill.curriculum_id == curriculum.id).order_by(Skill.code)
    ).all()
    report = {"curriculum": curriculum.code, "skills": [], "gaps": []}
    for skill in skills:
        rows = db.scalars(
            select(Problem).where(Problem.primary_skill_id == skill.id)
        ).all()
        types = {p.problem_type for p in rows}
        difficulties = {p.difficulty for p in rows}
        generated_capable = bool(types & GENERATORS.keys())
        word_problems = sum(1 for p in rows if p.problem_type == "WORD_PROBLEM")
        mc_problems = sum(
            1 for p in rows if getattr(p, "answer_kind", None) == "MULTIPLE_CHOICE"
        )
        ready = content_readiness(db, skill_id=skill.id).ready

        gaps = []
        if not ready:
            gaps.append("NOT_READY")
        if len(difficulties) < MIN_DIFFICULTY_STEPS:
            gaps.append(f"thin_difficulty({sorted(difficulties)})")
        if not generated_capable:
            gaps.append("no_generator")
        if word_problems == 0:
            gaps.append("no_word_problems")

        report["skills"].append(
            {
                "code": skill.code,
                "problems": len(rows),
                "difficulties": sorted(difficulties),
                "generator": generated_capable,
                "word_problems": word_problems,
                "multiple_choice": mc_problems,
                "ready": ready,
                "gaps": gaps,
            }
        )
        if gaps:
            report["gaps"].append(skill.code)
    return report


def main() -> None:
    codes = sys.argv[1:]
    with SessionLocal() as db:
        query = select(Curriculum).order_by(Curriculum.code)
        if codes:
            query = query.where(Curriculum.code.in_(codes))
        curricula = db.scalars(query).all()

    total_gaps = 0
    for curriculum in curricula:
        with SessionLocal() as db:
            report = audit_curriculum(db, curriculum)
        print(f"\n=== {report['curriculum']} ===")
        for s in report["skills"]:
            flag = "OK " if not s["gaps"] else "GAP"
            print(
                f"  {flag} {s['code']:<32} problems={s['problems']:<3} "
                f"diff={s['difficulties']} gen={'y' if s['generator'] else 'n'} "
                f"wp={s['word_problems']} mc={s['multiple_choice']} "
                f"{','.join(s['gaps'])}"
            )
        if report["gaps"]:
            print(f"  -> {len(report['gaps'])} skills with depth gaps")
            total_gaps += len(report["gaps"])
    print(f"\n{total_gaps} skill-level depth gaps across {len(curricula)} curricula")


if __name__ == "__main__":
    main()
