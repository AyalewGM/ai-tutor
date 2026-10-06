"""Alberta Grade 9 mathematics lifecycle/no-fork onboarding proof."""

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

AB_SOURCE = "https://www.alberta.ca/curriculum-mathematics"
AUTHORITY_CODE = "AB_EDU"
CURRICULUM_CODE = "AB_MATH_9_DRAFT_2026"


def register_alberta_grade9_draft(db: Session) -> Curriculum:
    canada = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id.is_(None), Jurisdiction.code == "CA"
        )
    )
    if canada is None:
        canada = Jurisdiction(code="CA", name="Canada", jurisdiction_type="COUNTRY")
        db.add(canada)
        db.flush()

    alberta = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == canada.id, Jurisdiction.code == "AB"
        )
    )
    if alberta is None:
        alberta = Jurisdiction(
            parent_id=canada.id,
            code="AB",
            name="Alberta",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=AB_SOURCE,
        )
        db.add(alberta)
        db.flush()

    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == alberta.id,
            EducationAuthority.code == AUTHORITY_CODE,
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=alberta.id,
            code=AUTHORITY_CODE,
            name="Alberta Education and Childcare",
            authority_type="MINISTRY",
            source_uri=AB_SOURCE,
            provenance_json={"role": "Alberta provincial curriculum authority"},
        )
        db.add(authority)
        db.flush()

    curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
    if curriculum is None:
        curriculum = Curriculum(
            code=CURRICULUM_CODE,
            name="Alberta Grade 9 Mathematics — 2026 Draft",
            jurisdiction="Alberta, Canada",
            grade_level="9",
            version="2026-draft",
            authority_id=authority.id,
            source_uri=AB_SOURCE,
            active=False,
        )
        db.add(curriculum)
        db.flush()
    return curriculum


def alberta_grade9_pilot_pack() -> CurriculumIngestionPack:
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code=CURRICULUM_CODE,
        curriculum_version="2026-draft",
        authority_code=AUTHORITY_CODE,
        source_uri=AB_SOURCE,
        lifecycle_status="PILOT",
        standards=(
            StandardDraft(
                code="AB9.DRAFT.LINEAR_INEQUALITIES",
                title="Solve linear inequalities",
                source_uri=AB_SOURCE,
                strand="Algebra",
            ),
        ),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="AB9.DRAFT.LINEAR_INEQUALITIES",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                mapping_type="PARTIAL",
                coverage="PARTIAL",
                rationale=(
                    "The Alberta 2026 draft Grade 9 snapshot includes solving linear "
                    "inequalities. This proof reuses only the overlapping existing "
                    "equation/inequality skill and does not claim full equivalence."
                ),
            ),
        ),
    )
