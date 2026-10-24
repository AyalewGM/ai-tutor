"""Independent source-coefficient SymPy oracle and author-side safety regression."""
from __future__ import annotations

import json
import re
from fractions import Fraction

import pytest
from sympy import Eq, Rational, S, Symbol, solveset

from scripts.author_ontario_linear_depth import (
    FAMILIES,
    MODES,
    SKILLS,
    create_candidate,
    create_pack,
    learner_projection,
)


def _coefficients_from_prompt(data: dict) -> dict[str, str]:
    """Independently parse actual student text to catch prompt/oracle divergence."""
    family, prompt = data["candidate_family"], data["prompt"]
    if family == "TWO_STEP_SIGNED_RATIONAL":
        m = re.fullmatch(r"Solve (-?\d+)x ([+-]\d+) = (-?\d+)\.", prompt)
        assert m is not None
        a, b, d = map(int, m.groups())
        result = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
    elif family == "TWO_STEP_FRACTIONAL_COEFFICIENT":
        m = re.fullmatch(r"Solve \((-?\d+)/(\d+)\)x ([+-]\d+) = (-?\d+)\.", prompt)
        assert m is not None
        a, den, b, d = map(int, m.groups())
        result = (Fraction(a, den), Fraction(b), Fraction(0), Fraction(d))
    elif family == "MULTISTEP_NEGATIVE_DISTRIBUTION":
        m = re.fullmatch(r"Solve -(\d+)\(x - \((-?\d+)\)\) \+ \((-?\d+)\) = (-?\d+)\.", prompt)
        assert m is not None
        k, b, c, d = map(int, m.groups())
        result = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(d))
    else:
        assert family == "MULTISTEP_VARIABLES_BOTH_SIDES"
        m = re.fullmatch(r"Solve (-?\d+)x ([+-]\d+) = (-?\d+)x ([+-]\d+)\.", prompt)
        assert m is not None
        a, b, c, d = map(int, m.groups())
        result = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
    return dict(zip(("lhs_x", "lhs_constant", "rhs_x", "rhs_constant"),
                    (str(value) for value in result)))


def _independent_solution(data: dict) -> Fraction:
    x = Symbol("x")
    p = data["equation_coefficients"]
    lhs = Rational(p["lhs_x"]) * x + Rational(p["lhs_constant"])
    rhs = Rational(p["rhs_x"]) * x + Rational(p["rhs_constant"])
    solved = solveset(Eq(lhs, rhs), x, domain=S.Reals)
    assert solved.is_FiniteSet and len(solved) == 1
    root = next(iter(solved))
    return Fraction(int(root.p), int(root.q))


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", MODES)
def test_exact_noninteger_oracle_for_60_seeds(family, mode):
    for seed in range(60):
        q = create_candidate(family, seed=seed, mode=mode)
        correct = Fraction(q["canonical_answer"].split("=", 1)[1])
        wrong = Fraction(q["misconception_answer"].split("=", 1)[1])
        assert correct.denominator > 1
        assert _coefficients_from_prompt(q) == q["equation_coefficients"]
        assert _independent_solution(q) == correct
        assert wrong != correct
        assert q["canonical_skill_hint"] == SKILLS[family]
        assert "answer" not in learner_projection(q)
        assert "hint" not in json.dumps(learner_projection(q)).casefold()
        assert "misconception" not in json.dumps(learner_projection(q)).casefold()
        assert q == create_candidate(family, seed=seed, mode=mode)


def test_mode_pools_and_pack_are_distinct_and_fail_closed():
    pack = create_pack(count_per_family_mode=25)
    assert len(pack["candidates"]) == 25 * len(FAMILIES) * len(MODES)
    assert pack["runtime_registered"] is False
    assert pack["runtime_activation"] is False
    assert pack["math_review"] == "PENDING_INDEPENDENT"
    assert len({q["variant_id"] for q in pack["candidates"]}) == len(pack["candidates"])
    for family in FAMILIES:
        group = [q for q in pack["candidates"] if q["candidate_family"] == family]
        assert len({q["task_fingerprint"] for q in group}) == len(group)
        assert {q["mode"] for q in group} == set(MODES)
    assert pack == create_pack(count_per_family_mode=25)


def test_invalid_requests_cannot_bypass_scope():
    with pytest.raises(ValueError):
        create_candidate("UNKNOWN", seed=1, mode="GUIDED")
    with pytest.raises(ValueError):
        create_candidate(FAMILIES[0], seed=1, mode="EXTENSION")
    with pytest.raises(ValueError):
        create_pack(count_per_family_mode=0)
    with pytest.raises(ValueError):
        create_pack(count_per_family_mode=101)
