"""Mathematical oracle and evidence-isolation tests for financial depth."""

import re

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

CODES = (
    "MATH.FIN.DISCOUNT.FINAL_PRICE",
    "MATH.FIN.TAX.FINAL_PRICE",
    "MATH.FIN.UNIT_PRICE.COMPARE",
)


@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("difficulty", range(1, 5))
@pytest.mark.parametrize("seed", range(30))
def test_financial_depth_math_oracle(code, difficulty, seed):
    problem = generate(code, seed=seed, difficulty=difficulty)
    assert problem == generate(code, seed=seed, difficulty=difficulty)
    assert problem.answer_contract is not None
    assert problem.is_correct(problem.canonical_answer)
    assert not problem.is_correct("1+1")
    assert problem.misconception_answers
    for misconception, wrong in problem.misconception_answers.items():
        assert not problem.is_correct(wrong)
        assert problem.misconception_for(wrong) == misconception

    if code == CODES[0]:
        price, rate = map(
            int, re.search(r"costs \$(\d+).*?(\d+)% discount", problem.prompt).groups()
        )
        assert int(problem.canonical_answer) == price * (100 - rate) // 100
    elif code == CODES[1]:
        price, rate = map(
            int, re.search(r"costs \$(\d+).*?tax is (\d+)%", problem.prompt).groups()
        )
        assert int(problem.canonical_answer) == price * (100 + rate) // 100
    else:
        count_a, cost_a, count_b, cost_b = map(
            int,
            re.search(
                r"Offer A: (\d+) identical notebooks for \$(\d+).*?"
                r"Offer B: (\d+) identical notebooks for \$(\d+)",
                problem.prompt,
            ).groups(),
        )
        assert cost_a * count_b != cost_b * count_a
        assert problem.canonical_answer == (
            "A" if cost_a * count_b < cost_b * count_a else "B"
        )


@pytest.mark.parametrize("code", CODES)
def test_financial_depth_assessment_isolation(code):
    assert code in FAMILIES
    problems = [generate(code, seed=17, difficulty=3, mode=mode) for mode in LearningMode]
    assert len({p.variant_id for p in problems}) == len(LearningMode)
    assert all(p.mode == mode for p, mode in zip(problems, LearningMode, strict=True))
