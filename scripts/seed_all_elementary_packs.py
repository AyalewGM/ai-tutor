from pathlib import Path

from app.core.database import SessionLocal
from app.elementary_pack import load_pack, parse_pack
from app.services.elementary_cross_grade_prerequisites import (
    wire_cross_grade_prerequisites,
)
from app.services.elementary_misconception_loader import (
    load_elementary_misconceptions,
)

_PACK_DIR = Path(__file__).parents[1] / "docs/curriculum/packs"

_PACK_ORDER = [
    "md-grade1-mccrs-2026_27.json",
    "md-grade2-mccrs-2026_27.json",
    "md-grade3-mccrs-2026_27.json",
    "md-grade4-mccrs-2026_27.json",
    "md-grade5-mccrs-2026_27.json",
    "dc-grade1-ccss-2024_25.json",
    "dc-grade2-ccss-2024_25.json",
    "dc-grade3-ccss-2024_25.json",
    "dc-grade4-ccss-2024_25.json",
    "dc-grade5-ccss-2024_25.json",
    "va-grade1-sol-2024_25.json",
    "va-grade2-sol-2024_25.json",
    "va-grade3-sol-2024_25.json",
    "va-grade4-sol-2024_25.json",
    "va-grade5-sol-2024_25.json",
]


def seed() -> list[dict]:
    """Load all DMV elementary curriculum packs idempotently."""
    results = []
    with SessionLocal() as db:
        for filename in _PACK_ORDER:
            path = _PACK_DIR / filename
            pack = parse_pack(path)
            result = load_pack(db, pack)
            results.append(
                {
                    "file": filename,
                    "curriculum_code": pack.curriculum.code,
                    "curriculum_id": result.curriculum_id,
                    "skill_count": result.skill_count,
                    "expectation_count": result.expectation_count,
                    "problem_count": result.problem_count,
                }
            )
        added_edges = wire_cross_grade_prerequisites(db)
        added_misconceptions = load_elementary_misconceptions(db)
        db.commit()
    print(f"Cross-grade prerequisite edges added: {added_edges}")
    print(f"Elementary misconceptions loaded: {added_misconceptions}")
    return results


if __name__ == "__main__":
    results = seed()
    total_skills = sum(r["skill_count"] for r in results)
    total_problems = sum(r["problem_count"] for r in results)
    print(
        f"Loaded {len(results)} packs: {total_skills} skills, {total_problems} problems"
    )
