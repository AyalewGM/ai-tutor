"""Cross-grade prerequisite wiring for DMV elementary curricula.

Adds SkillPrerequisite edges between skills in different grade packs that
belong to the same jurisdiction/version. Edges are declared by grade and skill
suffix so the same pedagogical topology can be reused across Maryland, DC, and
Virginia even though local skill codes differ.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Curriculum, Skill, SkillPrerequisite


@dataclass(frozen=True)
class CrossGradeEdge:
    from_grade: int
    from_suffix: str
    to_grade: int
    to_suffix: str


# Pedagogical cross-grade edges common to all three DMV jurisdictions.
# Suffixes match the local skill code suffix after the jurisdiction/grade prefix.
_CROSS_GRADE_EDGES = [
    # Grade 1 -> Grade 2
    CrossGradeEdge(1, "NS.COUNT_COMPARE", 2, "NBT.PLACE_VALUE"),
    CrossGradeEdge(1, "NBT.PLACE_VALUE", 2, "NBT.ADDITION_100"),
    CrossGradeEdge(1, "NBT.PLACE_VALUE", 2, "NBT.SUBTRACTION_100"),
    CrossGradeEdge(1, "OA.ADDITION_20", 2, "NBT.ADDITION_100"),
    CrossGradeEdge(1, "OA.SUBTRACTION_20", 2, "NBT.SUBTRACTION_100"),
    CrossGradeEdge(1, "OA.WORD_PROBLEM_20", 2, "OA.WORD_PROBLEM_100"),
    CrossGradeEdge(1, "MD.TELL_TIME", 2, "MD.TIME"),
    CrossGradeEdge(1, "G.SHAPES", 2, "G.SHAPES_FRACTIONS"),
    # Grade 2 -> Grade 3
    CrossGradeEdge(2, "NBT.PLACE_VALUE", 3, "NBT.PLACE_VALUE"),
    CrossGradeEdge(2, "NBT.ADDITION_100", 3, "OA.MULTIPLICATION"),
    CrossGradeEdge(2, "NBT.SUBTRACTION_100", 3, "OA.DIVISION"),
    CrossGradeEdge(2, "OA.WORD_PROBLEM_100", 3, "OA.MULTIPLICATION"),
    CrossGradeEdge(2, "G.SHAPES_FRACTIONS", 3, "NF.FRACTIONS"),
    CrossGradeEdge(2, "MD.LENGTH", 3, "MD.AREA_PERIMETER"),
    # Grade 3 -> Grade 4
    CrossGradeEdge(3, "OA.MULTIPLICATION", 4, "OA.COMPARISON"),
    CrossGradeEdge(3, "OA.MULTIPLICATION", 4, "NBT.MULTIPLY"),
    CrossGradeEdge(3, "OA.DIVISION", 4, "NBT.DIVIDE"),
    CrossGradeEdge(3, "NF.FRACTIONS", 4, "NF.FRACTIONS"),
    CrossGradeEdge(3, "MD.AREA_PERIMETER", 4, "OA.MULTI_STEP"),
    CrossGradeEdge(3, "G.SHAPES", 4, "MD.ANGLE_LINES"),
    # Grade 4 -> Grade 5
    CrossGradeEdge(4, "NBT.MULTIPLY", 5, "NBT.DECIMALS"),
    CrossGradeEdge(4, "NBT.DIVIDE", 5, "NF.MULTIPLY_DIVIDE"),
    CrossGradeEdge(4, "NF.FRACTIONS", 5, "NF.ADD_SUBTRACT"),
    CrossGradeEdge(4, "NF.FRACTIONS", 5, "NF.MULTIPLY_DIVIDE"),
    CrossGradeEdge(4, "MD.MEASUREMENT", 5, "MD.CONVERSION"),
    CrossGradeEdge(4, "MD.MEASUREMENT", 5, "MD.VOLUME"),
    CrossGradeEdge(4, "MD.ANGLE_LINES", 5, "G.COORDINATES"),
    CrossGradeEdge(4, "MD.ANGLE_LINES", 5, "G.SHAPES"),
]

_JURISDICTIONS = ("MD", "DC", "VA")


def _skill_code(jurisdiction: str, grade: int, suffix: str) -> str:
    return f"{jurisdiction}{grade}.{suffix}"


def _curriculum_code(jurisdiction: str, grade: int) -> str:
    version_tag = "2026_27" if jurisdiction == "MD" else "2024_25"
    return f"{jurisdiction}_MATH_{grade}_{version_tag}"


def _ensure_edge(db: Session, from_skill: Skill, to_skill: Skill) -> bool:
    key = (to_skill.id, from_skill.id)
    if db.get(SkillPrerequisite, key) is None:
        db.add(
            SkillPrerequisite(
                skill_id=to_skill.id,
                prerequisite_skill_id=from_skill.id,
                importance_weight=Decimal("1.0"),
            )
        )
        return True
    return False


def wire_cross_grade_prerequisites(db: Session) -> dict[str, int]:
    """Add cross-grade prerequisite edges for all DMV elementary curricula.

    Returns a dict mapping curriculum code to the number of edges added.
    """
    added: dict[str, int] = {}
    for jurisdiction in _JURISDICTIONS:
        for edge in _CROSS_GRADE_EDGES:
            from_code = _curriculum_code(jurisdiction, edge.from_grade)
            to_code = _curriculum_code(jurisdiction, edge.to_grade)
            from_curriculum = db.scalar(
                select(Curriculum).where(Curriculum.code == from_code)
            )
            to_curriculum = db.scalar(
                select(Curriculum).where(Curriculum.code == to_code)
            )
            if from_curriculum is None or to_curriculum is None:
                continue
            from_skill = db.scalar(
                select(Skill).where(
                    Skill.curriculum_id == from_curriculum.id,
                    Skill.code == _skill_code(
                        jurisdiction, edge.from_grade, edge.from_suffix
                    ),
                )
            )
            to_skill = db.scalar(
                select(Skill).where(
                    Skill.curriculum_id == to_curriculum.id,
                    Skill.code == _skill_code(
                        jurisdiction, edge.to_grade, edge.to_suffix
                    ),
                )
            )
            if from_skill is None or to_skill is None:
                continue
            if _ensure_edge(db, from_skill, to_skill):
                added[to_code] = added.get(to_code, 0) + 1
    return added
