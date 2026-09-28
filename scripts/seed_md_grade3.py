from pathlib import Path

from app.core.database import SessionLocal
from app.elementary_pack import LoadResult, load_pack, parse_pack

CURRICULUM_CODE = "MD_MATH_3_2026_27"
CURRICULUM_VERSION = "MCCRS-revised-SY2026-27"
MSDE_SOURCE = "https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx"
GRADE3_CROSSWALK = "https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Crosswalk-A.pdf"
GRADE3_COMPANION = "https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Standard-Companion-Guide-A.pdf"

_PACK_PATH = (
    Path(__file__).parents[1]
    / "docs/curriculum/packs/md-grade3-mccrs-2026-27.json"
)


def seed() -> LoadResult:
    """Load the Maryland Grade 3 declarative curriculum pack idempotently."""
    pack = parse_pack(_PACK_PATH)
    with SessionLocal() as db:
        result = load_pack(db, pack)
        db.commit()
        return result


if __name__ == "__main__":
    seed()
