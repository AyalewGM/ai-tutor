"""Curated problems must carry provenance metadata (Issue #45 acceptance)."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill

SEEDED_CURRICULA = (
    "MCPS_MATH_8",
    "MCPS_MATH_7",
    "MCPS_ALGEBRA_1_2026_27",
    "MTH1W",
)


def test_all_curated_problems_carry_provenance() -> None:
    """Every CURATED problem served in a shipped curriculum has provenance."""
    with SessionLocal() as db:
        problems = db.scalars(
            select(Problem)
            .join(Skill, Skill.id == Problem.primary_skill_id)
            .join(Curriculum, Curriculum.id == Skill.curriculum_id)
            .where(
                Problem.source_type == "CURATED",
                Curriculum.code.in_(SEEDED_CURRICULA),
            )
        ).all()
        assert problems, "Expected seeded curated problems"
        for problem in problems:
            provenance = (problem.solution or {}).get("provenance")
            assert provenance is not None, (
                f"Curated problem {problem.id} ({problem.prompt[:40]}) "
                "lacks provenance metadata"
            )
            assert provenance["origin"] == "AUTHORED"
            assert provenance["author"]
            assert provenance["license"]
            assert provenance["source_uri"].startswith("http")


def test_generated_problems_carry_family_identity() -> None:
    """GENERATED rows keep problem_family/parameters; provenance stays curated-only."""
    with SessionLocal() as db:
        generated = db.scalars(
            select(Problem).where(Problem.source_type == "GENERATED").limit(20)
        ).all()
        for problem in generated:
            assert (problem.solution or {}).get("problem_family")
