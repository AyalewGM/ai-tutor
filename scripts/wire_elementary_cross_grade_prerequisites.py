"""Wire cross-grade prerequisite edges within each DMV elementary curriculum.

This is a thin CLI wrapper around the reusable wiring service. It should be
run after all elementary packs are loaded.
"""

from app.core.database import SessionLocal
from app.services.elementary_cross_grade_prerequisites import (
    wire_cross_grade_prerequisites,
)


def main() -> None:
    with SessionLocal() as db:
        counts = wire_cross_grade_prerequisites(db)
        db.commit()
    print(f"Cross-grade prerequisite edges added: {counts}")


if __name__ == "__main__":
    main()
