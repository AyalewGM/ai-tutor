"""deepen_skill_breadth: companion types must stay grade-appropriate and
stranded to the skill's actual content domain."""

from types import SimpleNamespace

from app.services.problem_generation import GENERATORS
from scripts.ops.deepen_skill_breadth import (
    COMPANION_TYPES,
    _companions_for,
    _grade_number,
    _word_problem_companions,
)


def _skill(code: str, name: str = "") -> SimpleNamespace:
    return SimpleNamespace(code=code, name=name)


def test_companion_map_only_references_real_generators() -> None:
    for existing, companions in COMPANION_TYPES.items():
        for companion in companions:
            assert companion.problem_type in GENERATORS, (
                f"{existing} -> {companion.problem_type} has no generator"
            )
            assert 1 <= companion.min_grade <= 12


def test_grade_guards_block_too_mature_companions() -> None:
    skill = _skill("DC1.NBT.PLACE_VALUE", "Place value")
    # Grade 1: rounding (min_grade 3) is withheld; compare numbers is fine.
    companions = _companions_for({"PLACE_VALUE_BASE_TEN"}, skill, grade=1)
    assert "COMPARE_NUMBERS" in companions
    assert "ROUNDING" not in companions
    # Grade 3: rounding unlocks.
    assert "ROUNDING" in _companions_for({"PLACE_VALUE_BASE_TEN"}, skill, grade=3)


def test_arithmetic_and_word_problem_types_are_companions() -> None:
    skill = _skill("VA1.OA.ADDITION_20", "Add within 20")
    assert _companions_for({"ADDITION_WITHIN_20"}, skill, grade=1) == [
        "SUBTRACTION_WITHIN_20",
        "WORD_PROBLEM_ADD_SUB_20",
    ]


def test_equation_word_problem_skills_get_equation_types() -> None:
    skill = _skill("VAA1.LINEAR.EQ", "Linear equations")
    companions = _word_problem_companions(skill, grade=9)
    assert "SOLVE_EQUATION" in companions
    assert "ALGEBRA_WORD_PROBLEM" in companions


def test_strands_without_generators_stay_untouched() -> None:
    # Probability/data skills get nothing rather than off-target items.
    assert _word_problem_companions(_skill("DC7.SP.PROBABILITY", "Probability"), 7) == []
    assert _word_problem_companions(_skill("IA1.DS.A.1", "Data displays"), 9) == []


def test_existing_types_are_never_reattached() -> None:
    skill = _skill("M8.ALG.INVERSE", "One-step equations")
    out = _companions_for({"SOLVE_EQUATION", "ALGEBRA_WORD_PROBLEM"}, skill, grade=8)
    assert out == []


def test_grade_level_strings_parse() -> None:
    assert _grade_number("3") == 3
    assert _grade_number("Algebra I") == 9
    assert _grade_number(None) == 1
