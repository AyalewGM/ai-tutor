"""End-to-end proof packs for Maryland and Ontario curriculum ingestion."""

from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    ProposedSkillMapping,
    StandardDraft,
)

MD_SOURCE = "https://www.marylandpublicschools.org/about/Pages/DCAA/Math/index.aspx"
ON_SOURCE = "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w"


def maryland_proof_pack() -> CurriculumIngestionPack:
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code="MD_ALGEBRA_1_2026_27",
        curriculum_version="MCCRS-revised-SY2026-27",
        authority_code="MSDE",
        source_uri=MD_SOURCE,
        standards=(
            StandardDraft(
                code="MIHUR.PROOF.MD.A1.LINEAR.EQ",
                title="Linear equations canonical mapping proof",
                source_uri=MD_SOURCE,
                strand="Algebra I",
            ),
        ),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="MIHUR.PROOF.MD.A1.LINEAR.EQ",
                canonical_skill_code="MATH.ALGEBRA1.LINEAR_EQ",
                mapping_type="ALIGNS_TO",
                rationale="Existing reviewed Maryland Algebra I skill equivalence",
            ),
        ),
    )


def ontario_proof_pack() -> CurriculumIngestionPack:
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code="MTH1W",
        curriculum_version="2021",
        authority_code="ON_MIN_ED",
        source_uri=ON_SOURCE,
        standards=(
            StandardDraft(
                code="MTH1W.C1.5",
                title="Create and Solve Equations",
                source_uri=ON_SOURCE,
                strand="C. Algebra",
            ),
        ),
        proposed_mappings=(
            ProposedSkillMapping(
                standard_code="MTH1W.C1.5",
                canonical_skill_code="MATH.EE.EQUATION.MULTISTEP",
                mapping_type="ALIGNS_TO",
                rationale="Existing reviewed Ontario Grade 9 skill equivalence",
            ),
        ),
    )
