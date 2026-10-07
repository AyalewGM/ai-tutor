import re
from fractions import Fraction

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

ALG_CODES = [c for c in FAMILIES if c.startswith("MATH.ALG.") or c.startswith("MATH.FUNC.")]


@pytest.mark.parametrize("code", ALG_CODES)
def test_new_families_are_deterministic(code):
    spec=FAMILIES[code]
    a=generate(code,seed=41,difficulty=spec.min_difficulty)
    b=generate(code,seed=41,difficulty=spec.min_difficulty)
    assert a == b
    assert a.provenance["origin"] == "MIHUR_AUTHORED"


@pytest.mark.parametrize("code", ALG_CODES)
def test_all_learning_modes_supported(code):
    spec=FAMILIES[code]
    for mode in LearningMode:
        p=generate(code,seed=9,difficulty=spec.min_difficulty,mode=mode)
        assert p.mode == mode


@pytest.mark.parametrize("code", ALG_CODES)
def test_misconceptions_never_collide_with_answer(code):
    spec=FAMILIES[code]
    for seed in range(25):
        p=generate(code,seed=seed,difficulty=spec.min_difficulty)
        assert all(v.replace(" ","").lower() != p.canonical_answer.replace(" ","").lower() for v in p.misconception_answers.values())


@pytest.mark.parametrize("seed", range(30))
def test_oracle_expression_evaluation(seed):
    p=generate("MATH.ALG.EXPR.EVALUATE",seed=seed,difficulty=3)
    m=re.search(r"Evaluate (-?\d+)x \+ (\d+) when x = (-?\d+)",p.prompt)
    assert m
    a,b,x=map(int,m.groups())
    assert int(p.canonical_answer) == a*x+b


@pytest.mark.parametrize("seed", range(30))
def test_oracle_one_step_multiplicative_equation(seed):
    p=generate("MATH.ALG.EQ.ONE.MULT",seed=seed,difficulty=2)
    m=re.search(r"Solve (\d+)x = (\d+)",p.prompt)
    assert m
    a,total=map(int,m.groups())
    answer=int(p.canonical_answer.split("=")[1])
    assert a*answer == total


@pytest.mark.parametrize("seed", range(30))
def test_oracle_distributive_equation(seed):
    p=generate("MATH.ALG.EQ.MULTISTEP.DISTRIBUTE",seed=seed,difficulty=3)
    m=re.search(r"Solve (\d+)\(x \+ (\d+)\) \+ (\d+) = (\d+)",p.prompt)
    assert m
    a,b,c,total=map(int,m.groups())
    x=int(p.canonical_answer.split("=")[1])
    assert a*(x+b)+c == total


@pytest.mark.parametrize("seed", range(30))
def test_oracle_both_sides_equation(seed):
    p=generate("MATH.ALG.EQ.MULTISTEP.BOTH_SIDES",seed=seed,difficulty=3)
    m=re.search(r"Solve (\d+)x \+ (\d+) = (\d+)x \+ (\d+)",p.prompt)
    assert m
    la,b,ra,d=map(int,m.groups())
    x=int(p.canonical_answer.split("=")[1])
    assert la*x+b == ra*x+d


@pytest.mark.parametrize("seed", range(30))
def test_oracle_linear_function_evaluation(seed):
    p=generate("MATH.FUNC.LINEAR.EVALUATE",seed=seed,difficulty=3)
    m=re.search(r"f\(x\) = (\d+)x \+ (-?\d+), find f\((-?\d+)\)",p.prompt)
    assert m
    slope,intercept,x=map(int,m.groups())
    assert int(p.canonical_answer) == slope*x+intercept


@pytest.mark.parametrize("seed", range(30))
def test_oracle_slope_from_points(seed):
    p=generate("MATH.FUNC.LINEAR.SLOPE.TABLE",seed=seed,difficulty=3)
    nums=list(map(int,re.findall(r"-?\d+",p.prompt)))
    x0,y0,x1,y1=nums[-4:]
    expected=Fraction(y1-y0,x1-x0)
    assert expected.denominator == 1
    assert int(p.canonical_answer) == expected.numerator


def test_reasoning_assessments_are_structured():
    for code in ["MATH.ALG.EXPR.ERROR.DISTRIBUTE","MATH.ALG.LIKE.CLASSIFY","MATH.FUNC.LINEAR.ERROR.INTERCEPT"]:
        p=generate(code,seed=3,difficulty=2)
        assert p.canonical_answer in {"A","B","C","D"}
        assert "(A)" in p.prompt


def test_word_modeling_and_representation_depth_present():
    types={FAMILIES[c].problem_type for c in ALG_CODES}
    dims=set().union(*(FAMILIES[c].evidence_dimensions for c in ALG_CODES))
    assert {"WORD_PROBLEM","MODEL_EQUATION","ERROR_ANALYSIS","SOLVE_EQUATION"} <= types
    assert {"modeling","transfer","representation","reasoning","error_analysis","misconception_probe"} <= dims


def test_curriculum_neutrality():
    forbidden={"california","maryland","virginia","ontario","alberta","texas"}
    for code in ALG_CODES:
        p=generate(code,seed=5,difficulty=FAMILIES[code].min_difficulty)
        text=(code+" "+p.prompt+" "+str(p.provenance)).lower()
        assert not any(word in text for word in forbidden)
