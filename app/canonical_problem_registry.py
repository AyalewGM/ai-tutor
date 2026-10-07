"""Registry helpers for canonical Mihur problem families."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.canonical_problem_families import FAMILIES
from app.curriculum_models import CanonicalSkill, ProblemFamily


def register_problem_families(db: Session) -> int:
    """Idempotently register implemented generators against canonical skills."""
    created = 0
    for spec in FAMILIES.values():
        skill = db.scalar(
            select(CanonicalSkill).where(CanonicalSkill.code == spec.canonical_skill_code)
        )
        if skill is None:
            skill = CanonicalSkill(
                code=spec.canonical_skill_code,
                name=spec.canonical_skill_code.rsplit(".", 1)[-1].replace("_", " ").title(),
                description="Canonical Mihur mathematics skill.",
                subject="MATHEMATICS",
            )
            db.add(skill)
            db.flush()

        family = db.scalar(select(ProblemFamily).where(ProblemFamily.code == spec.code))
        if family is None:
            db.add(
                ProblemFamily(
                    code=spec.code,
                    name=spec.name,
                    canonical_skill_id=skill.id,
                    generator_key=spec.code,
                    description=(
                        "Mihur-authored deterministic family; "
                        f"evidence dimensions: {', '.join(sorted(spec.evidence_dimensions))}"
                    ),
                    active=True,
                )
            )
            db.flush()
            created += 1
        elif family.canonical_skill_id != skill.id:
            raise ValueError(f"Problem family {spec.code} is bound to a different canonical skill")
    return created
