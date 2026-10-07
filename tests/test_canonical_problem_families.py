import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate


def test_same_seed_produces_same_variant_and_truth():
    first = generate("MATH.EQ.TWO.WORD.FIXED_RATE", seed="learner-safe-1", difficulty=3)
    second = generate("MATH.EQ.TWO.WORD.FIXED_RATE", seed="learner-safe-1", difficulty=3)
    assert first == second
    assert first.is_correct(first.canonical_answer)


def test_different_seeds_create_diverse_original_variants():
    prompts = {
        generate("MATH.EQ.TWO.WORD.FIXED_RATE", seed=seed, difficulty=3).prompt
        for seed in range(20)
    }
    assert len(prompts) >= 12


@pytest.mark.parametrize(
    "family_code",
    [
        "MATH.EQ.TWO.WORD.FIXED_RATE",
        "MATH.EQ.TWO.WORD.UNKNOWN_START",
        "MATH.EQ.TWO.WORD.COMPARISON",
    ],
)
def test_word_problem_families_probe_distinct_structures(family_code):
    spec = FAMILIES[family_code]
    problem = generate(family_code, seed=17, difficulty=3, mode=LearningMode.DIAGNOSTIC)
    assert spec.problem_type == "WORD_PROBLEM"
    assert "modeling" in spec.evidence_dimensions
    assert problem.hints
    assert problem.misconception_answers
    assert problem.provenance["origin"] == "MIHUR_AUTHORED"


def test_misconception_answer_is_classified_deterministically():
    problem = generate("MATH.EQ.ONE.ADD_DIRECT", seed=9, difficulty=2)
    code, wrong = next(iter(problem.misconception_answers.items()))
    assert not problem.is_correct(wrong)
    assert problem.misconception_for(wrong) == code


def test_family_is_curriculum_neutral():
    for spec in FAMILIES.values():
        assert spec.canonical_skill_code.startswith("MATH.")
        assert all(token not in spec.code for token in ("CA.", "MD.", "VA.", "NY.", "NJ."))


def test_out_of_range_difficulty_fails_closed():
    with pytest.raises(ValueError, match="difficulty outside family range"):
        generate("MATH.EQ.ONE.ADD_DIRECT", seed=1, difficulty=9)
