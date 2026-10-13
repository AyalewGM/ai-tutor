"""Draft-only exact-mathematics regression checks for the bounded G7 wave."""

import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ALG = _load("bounded_g7_algebra", "docs/curriculum/drafts/maryland-grade7-unit6-algebra-v1/variants.py")
SCALE = _load("bounded_g7_scale", "docs/curriculum/drafts/middle-grades-rational-scale-v1/seeded_variants.py")


@pytest.mark.parametrize(("submitted", "expected"), [
    ("3 + 2x = 13", "2x + 3 = 13"),
    ("4x + 6 = 26", "2x + 3 = 13"),
    ("6 + 2x >= 16", "2x + 6 >= 16"),
    ("3 + 2x", "2x + 3"),
    ("3 + 2*x", "2x + 3"),
    ("2*(x+3)", "2x + 6"),
    ("6 + 2x", "2(x + 3)"),
    ("1/2*x + 3/2", "(x + 3)/2"),
])
def test_equivalent_algebra_accepted(submitted, expected):
    assert ALG._mathematically_equivalent(submitted, expected)


@pytest.mark.parametrize(("submitted", "expected"), [
    ("2x + 4 = 13", "2x + 3 = 13"),
    ("2x + 3 >= 13", "2x + 3 > 13"),
    ("-2x - 3 >= -13", "2x + 3 >= 13"),
    ("2x + 5", "2x + 6"),
    ("x*x + 1", "x + 1"),
    ("__import__('os').system('true')", "x"),
    ("x / x", "1"),
    ("2x + 3 = 13 OR x = 1", "2x + 3 = 13"),
])
def test_near_misses_fail_closed(submitted, expected):
    assert not ALG._mathematically_equivalent(submitted, expected)


def test_guided_model_accepts_commuted_terms_and_rejects_constant_miss():
    v = ALG.generate(0, "guided")
    o = v.teacher_oracle()
    response = {
        "model_type": o["model_type"],
        "symbolic_model": f"{v.q} + {v.p}x >= {v.r}",
        "context_justification": "at least means inclusive inequality",
    }
    assert ALG.diagnose_guided(v, response) == "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"
    response["symbolic_model"] = f"{v.q + 1} + {v.p}x >= {v.r}"
    assert ALG.diagnose_guided(v, response) == "MD7.MODEL_TRANSLATION"


@pytest.mark.parametrize("mode", ["guided", "independent"])
@pytest.mark.parametrize(("seed", "scale"), [(4, Fraction(1)), (5, Fraction(-1))])
def test_unit_scale_same_magnitude_exact_oracle(seed, scale, mode):
    v = SCALE.generate(seed, mode, unit_scale=int(scale))
    assert v.input_value != 0
    assert v.magnitude_relation == "SAME"
    assert v.direction == "POSITIVE"
    assert v.answer == (scale if v.hidden_quantity == "scale" else v.input_value * scale)
    assert v.teacher_oracle()["magnitude_relation"] == "SAME"
    assert SCALE.generate(seed, mode, unit_scale=int(scale)) == v
    assert SCALE.generate(seed, mode).variant_id != v.variant_id
    assert not any(key in v.public_payload() for key in ("answer", "direction", "magnitude_relation"))


def test_zero_direction_explicitly_unsupported():
    with pytest.raises(ValueError):
        SCALE._direction(Fraction(0))
    for mode in ("guided", "independent"):
        for seed in range(60):
            v = SCALE.generate(seed, mode)
            assert v.input_value != 0
            assert v.given_value != 0


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_all_discrete_inequalities_have_genuine_domain_witnesses(mode):
    for seed in range(3, 120, 6):
        for which in (seed, seed + 1):
            v = ALG.generate(which, mode)
            if not v.kind.startswith("INEQUALITY"):
                continue
            oracle = v.teacher_oracle()
            witness = Fraction(oracle["witness"])
            counterexample = Fraction(oracle["counterexample"])
            assert oracle["graph_representation"] == "DISCRETE_NONNEGATIVE_INTEGER_POINTS"
            assert all(x >= 0 and x.denominator == 1 for x in (witness, counterexample))
            assert v.satisfies_inequality(witness)
            assert not v.satisfies_inequality(counterexample)
            assert not v.satisfies_inequality(Fraction(-1))
            assert not v.satisfies_inequality(Fraction(1, 2))
            assert v.public_payload()["response_fields"].count("graph_representation") == 1


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_fractional_physical_group_count_is_never_generated(mode):
    for seed in range(300):
        v = ALG.generate(seed, mode)
        if v.kind in ("EQUATION_P_TIMES_X_PLUS_Q", "INEQUALITY_P_TIMES_X_PLUS_Q"):
            assert v.p > 0 and v.p.denominator == 1
            assert v.q.denominator == 1
            assert v.r == v.p * (v.answer + v.q)


def test_discrete_graph_diagnosis_rejects_continuous_ray():
    v = ALG.generate(3, "guided")
    oracle = v.teacher_oracle()
    response = {
        "symbolic_model": oracle["symbolic_model"],
        "boundary": oracle["boundary"],
        "solution_relation": oracle["solution_relation"],
        "endpoint": oracle["endpoint"],
        "graph_direction": oracle["graph_direction"],
        "graph_representation": "CONTINUOUS_REAL_RAY",
        "witness": oracle["witness"],
        "counterexample": oracle["counterexample"],
        "context_interpretation": "whole number visit counts",
    }
    assert ALG.diagnose_guided(v, response) == "MD7.CONTINUOUS_VS_DISCRETE_DOMAIN"
    response["graph_representation"] = oracle["graph_representation"]
    assert ALG.diagnose_guided(v, response) == "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"
    response["witness"] = "-1"
    assert ALG.diagnose_guided(v, response) == "MD7.WITNESS_COUNTEREXAMPLE_INVALID"
