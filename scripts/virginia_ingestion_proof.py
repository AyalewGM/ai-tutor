"""Virginia 2023 Algebra 1 no-fork curriculum onboarding proof."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    ProposedSkillMapping,
    StandardDraft,
)
from app.curriculum_models import EducationAuthority, Jurisdiction
from app.models import Curriculum

VA_SOURCE = (
    "https://www.doe.virginia.gov/teaching-learning-assessment/instruction/"
    "mathematics/standards-of-learning-for-mathematics"
)
CURRICULUM_CODE = "VA_ALGEBRA_1_2023"
AUTHORITY_CODE = "VDOE"


def register_virginia_algebra1(db: Session) -> Curriculum:
    us = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"
        )
    )
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us)
        db.flush()

    virginia = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == us.id, Jurisdiction.code == "VA"
        )
    )
    if virginia is None:
        virginia = Jurisdiction(
            parent_id=us.id,
            code="VA",
            name="Virginia",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=VA_SOURCE,
        )
        db.add(virginia)
        db.flush()

    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == virginia.id,
            EducationAuthority.code == AUTHORITY_CODE,
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=virginia.id,
            code=AUTHORITY_CODE,
            name="Virginia Department of Education",
            authority_type="STATE_AGENCY",
            source_uri=VA_SOURCE,
            provenance_json={"role": "Virginia mathematics standards authority"},
        )
        db.add(authority)
        db.flush()

    curriculum = db.scalar(
        select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
    )
    if curriculum is None:
        curriculum = Curriculum(
            code=CURRICULUM_CODE,
            name="Virginia Algebra 1 — 2023 Standards of Learning",
            jurisdiction="Virginia",
            grade_level="Algebra 1",
            version="2023",
            authority_id=authority.id,
            source_uri=VA_SOURCE,
            active=True,
        )
        db.add(curriculum)
        db.flush()
    return curriculum


def virginia_algebra1_proof_pack() -> CurriculumIngestionPack:
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code=CURRICULUM_CODE,
        curriculum_version="2023",
        authority_code=AUTHORITY_CODE,
        source_uri=VA_SOURCE,
        standards=(
            StandardDraft(
                code="A.EI.1",
                title=(
                    "Represent, solve, explain, and interpret multistep linear "
                    "equations and inequalities in one variable"
                ),
                source_uri=VA_SOURCE,
                strand="Equations and Inequalities",
            ),
        ),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="A.EI.1",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                mapping_type="ALIGNS_TO",
                coverage="PARTIAL",
                rationale=(
                    "A.EI.1 explicitly includes solving multistep linear equations "
                    "in one variable; the canonical skill is reused without "
                    "transferring learner evidence."
                ),
            ),
        ),
    )
