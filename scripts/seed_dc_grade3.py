from pathlib import Path

from app.core.database import SessionLocal
from app.elementary_pack import LoadResult, load_pack, parse_pack

CURRICULUM_CODE = "DC_MATH_3_2024_25"
CURRICULUM_VERSION = "CCSS-OSSE-2024-25"
OSSE_SOURCE = "https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0"
DC_GRADE3_BLUEPRINT = "https://osse-migrate.dc.gov/sites/default/files/dc/sites/osse/page_content/attachments/mathematics-adjusted-blueprintGrades3_0.pdf"

_PACK_PATH = (
    Path(__file__).parents[1]
    / "docs/curriculum/packs/dc-grade3-ccss-2024-25.json"
)


def seed() -> LoadResult:
    """Load the District of Columbia Grade 3 declarative curriculum pack idempotently."""
    pack = parse_pack(_PACK_PATH)
    with SessionLocal() as db:
        result = load_pack(db, pack)
        db.commit()
        return result


if __name__ == "__main__":
    seed()
