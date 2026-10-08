"""Deterministic checks for financial content and strict opt-in grading."""
import re

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

CODES = ("MATH.FIN.INTEREST.SIMPLE", "MATH.FIN.BUDGET.CAPACITY")

@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("seed", range(40))
def test_financial_families(code, seed):
    p = generate(code, seed=seed, difficulty=3)
    assert p == generate(code, seed=seed, difficulty=3)
    assert p.answer_contract is not None
    assert p.is_correct(p.canonical_answer)
    assert p.is_correct("+" + p.canonical_answer)
    assert not p.is_correct(p.canonical_answer + " dollars")
    assert not p.is_correct("1+1")
    assert p.misconception_answers
    assert all(not p.is_correct(v) and p.misconception_for(v) == k for k, v in p.misconception_answers.items())
    if code.endswith("SIMPLE"):
        a, rate, years = map(int, re.search(r"deposit of (\d+) dollars earns (\d+)%.*for (\d+) years", p.prompt).groups())
        assert int(p.canonical_answer) == a * rate * years // 100
    else:
        fee, cost, budget = map(int, re.search(r"charges (\d+) dollars to join and (\d+) dollars per visit.*With (\d+) dollars", p.prompt).groups())
        assert int(p.canonical_answer) == (budget - fee) // cost

@pytest.mark.parametrize("code", CODES)
def test_mode_separation(code):
    assert len({generate(code, seed=7, difficulty=3, mode=m).variant_id for m in LearningMode}) == len(LearningMode)
    assert code in FAMILIES
