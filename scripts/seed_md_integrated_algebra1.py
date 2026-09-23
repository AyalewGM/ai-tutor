from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority, Jurisdiction
from app.models import Curriculum

CURRICULUM_CODE = "MD_INTEGRATED_ALGEBRA_1_2027_28"
CURRICULUM_VERSION = "MCCRS-2025-INTEGRATED-ALGEBRA-1-SY2027-28"
MSDE_SOURCE = (
    "https://www.marylandpublicschools.org/about/Documents/DCAA/Math/revised/"
    "Integrated-Algebra-1-Crosswalk-A.pdf"
)


def _authority(db):
    us = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id.is_(None),
            Jurisdiction.code == "US",
        )
    )
    if us is None:
        us = Jurisdiction(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY",
        )
        db.add(us)
        db.flush()

    md = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == us.id,
            Jurisdiction.code == "MD",
        )
    )
    if md is None:
        md = Jurisdiction(
            parent_id=us.id,
            code="MD",
            name="Maryland",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=MSDE_SOURCE,
        )
        db.add(md)
        db.flush()

    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == md.id,
            EducationAuthority.code == "MSDE",
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=md.id,
            code="MSDE",
            name="Maryland State Department of Education",
            authority_type="STATE_AGENCY",
            source_uri=MSDE_SOURCE,
            provenance_json={"role": "Maryland mathematics standards authority"},
        )
        db.add(authority)
        db.flush()
    return authority


def seed() -> None:
    """Register the future Integrated Algebra I course without mutating legacy Algebra I.

    Standards-to-skill mappings and original instructional content are deliberately
    added in reviewed follow-up slices. The MSDE crosswalk blends algebra, geometry,
    and statistics, so F-012 must not infer equivalence from the traditional Algebra I
    pack merely because both courses contain Algebra I in their names.
    """
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="Maryland Integrated Algebra I — 2025 revised MCCRS",
                jurisdiction="Maryland",
                grade_level="Integrated Algebra I",
                authority_id=authority.id,
                version=CURRICULUM_VERSION,
                source_uri=MSDE_SOURCE,
            )
            db.add(curriculum)
        else:
            curriculum.name = "Maryland Integrated Algebra I — 2025 revised MCCRS"
            curriculum.jurisdiction = "Maryland"
            curriculum.grade_level = "Integrated Algebra I"
            curriculum.authority_id = authority.id
            curriculum.version = CURRICULUM_VERSION
            curriculum.source_uri = MSDE_SOURCE

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
