"""Load elementary misconception/remediation catalogs into the database.

The JSON catalogs are keyed by canonical concept code. For every curriculum-local
skill that maps to a canonical concept with catalog entries, this service creates
a `Misconception` row scoped to that skill. This lets the tutoring engine select
remediation paths deterministically while keeping learner evidence isolated per
curriculum.
"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Misconception, Skill

_CATALOG_DIR = Path(__file__).parents[2] / "docs/curriculum/misconceptions"


def _catalog_entries() -> dict[str, list[dict]]:
    entries: dict[str, list[dict]] = {}
    for filename in ("grades_1_2.json", "grades_3_5.json"):
        path = _CATALOG_DIR / filename
        if not path.exists():
            continue
        catalog = json.loads(path.read_text())
        for canonical_code, item in catalog["catalog"].items():
            entries.setdefault(canonical_code, []).extend(item.get("misconceptions", []))
    return entries


def load_elementary_misconceptions(db: Session) -> dict[str, int]:
    """Create or update Misconception rows for all elementary skills.

    Returns a mapping of jurisdiction name to count of misconceptions added/updated.
    """
    catalog_entries = _catalog_entries()
    if not catalog_entries:
        return {}

    canonical_codes = list(catalog_entries.keys())
    canonical_by_code = {
        row.code: row
        for row in db.scalars(
            select(CanonicalSkill).where(CanonicalSkill.code.in_(canonical_codes))
        )
    }

    added: dict[str, int] = {}
    for canonical_code, misconceptions in catalog_entries.items():
        canonical = canonical_by_code.get(canonical_code)
        if canonical is None:
            continue
        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.canonical_skill_id == canonical.id
                )
            )
        )
        for mapping in mappings:
            skill = db.get(Skill, mapping.skill_id)
            if skill is None:
                continue
            existing = {
                m.code: m
                for m in db.scalars(
                    select(Misconception).where(Misconception.skill_id == skill.id)
                )
            }
            for entry in misconceptions:
                misconception = existing.get(entry["code"])
                if misconception is None:
                    misconception = Misconception(
                        skill_id=skill.id,
                        code=entry["code"],
                    )
                    db.add(misconception)
                misconception.name = entry["name"]
                misconception.description = entry.get("description") or entry["name"]
                misconception.remediation_strategy = entry["remediation"]
                jurisdiction = (
                    db.get(Curriculum, skill.curriculum_id).jurisdiction
                    if skill.curriculum_id
                    else "unknown"
                )
                added[jurisdiction] = added.get(jurisdiction, 0) + 1

    return added


def load() -> dict[str, int]:
    """CLI entry point."""
    from app.core.database import SessionLocal

    with SessionLocal() as db:
        counts = load_elementary_misconceptions(db)
        db.commit()
        return counts


if __name__ == "__main__":
    counts = load()
    print(f"Elementary misconceptions loaded by jurisdiction: {counts}")
