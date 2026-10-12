"""Fail-closed checks for Grade 4 comprehensive gap-closure wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade4-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g4_gap_variants",DIR/"variants.py")
assert spec is not None and spec.loader is not None
MODULE=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=MODULE
spec.loader.exec_module(MODULE)

def test_manifest_covers_all_ten_topics_and_hard_gates():
    ids=[p["id"] for p in PACKAGE["packages"]]
    assert len(ids)==10 and len(set(ids))==10
    assert set(ids)==set(MODULE.CONCEPTS)
    assert PACKAGE["status"]=="DRAFT_UNVERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False
    blocked=("production_wired","standards_accepted","math_accepted","pedagogy_accepted","architecture_accepted","mve_implemented","assessment_backend_wired","muse_qa","deployed")
    assert all(PACKAGE["gates"][k] is False for k in blocked)

@pytest.mark.parametrize("mode",["guided","independent"])
def test_all_concepts_seeded_deterministic_and_answer_isolated(mode):
    for concept in MODULE.CONCEPTS:
        prompts=set()
        for seed in range(24):
            a=MODULE.generate(concept,seed,mode)
            b=MODULE.generate(concept,seed,mode)
            assert a==b
            assert a.teacher_oracle()
            payload=a.public_payload()
            assert "oracle" not in payload and "answer" not in payload
            prompts.add(a.prompt)
        assert len(prompts)>=2

def test_mode_namespaces_are_disjoint():
    for concept in MODULE.CONCEPTS:
        for seed in range(30):
            assert MODULE.generate(concept,seed,"guided").item_id != MODULE.generate(concept,seed,"independent").item_id

def test_multiplicative_comparison_exact():
    for seed in range(30):
        o=MODULE.generate("G4-MULT-COMP",seed,"guided").teacher_oracle()
        assert o["factor"]*o["base"]==o["answer"]

def test_multistep_word_uses_multiply_then_add():
    for seed in range(20):
        o=MODULE.generate("G4-MULTISTEP-WORD",seed,"guided").teacher_oracle()
        assert o["operations"]==["MULTIPLY","ADD"]
        assert o["answer"]>0

def test_factors_are_complete_and_classification_consistent():
    for seed in range(40):
        o=MODULE.generate("G4-FACTORS-PATTERNS",seed,"independent").teacher_oracle()
        factors=o["factors"]
        n=max(factors)
        assert all(n%f==0 for f in factors)
        assert o["classification"]==("PRIME" if len(factors)==2 else "COMPOSITE")
        base=o["multiple_base"]
        assert o["multiples"]==[base*i for i in range(1,6)]
        assert all(value%base==0 for value in o["multiples"])

def test_place_value_uses_elementary_half_up_rounding():
    assert MODULE._round_half_up_positive(14500,1000)==15000
    assert MODULE._round_half_up_positive(15500,1000)==16000
    for seed in range(80):
        o=MODULE.generate("G4-PLACE-VALUE",seed,"guided").teacher_oracle()
        assert o["rounded_thousand"]%1000==0


def test_multiplication_and_division_oracles():
    for seed in range(30):
        m=MODULE.generate("G4-MULTIPLICATION",seed,"guided").teacher_oracle()
        assert m["answer"]>0
        d=MODULE.generate("G4-DIVISION",seed,"independent").teacher_oracle()
        assert d["check"]>0
        assert 0<=d["remainder"]<100

def test_fraction_answer_uses_same_denominator_unit():
    for seed in range(30):
        o=MODULE.generate("G4-FRACTIONS",seed,"guided").teacher_oracle()
        ans=Fraction(o["answer"])
        assert ans.denominator>0
        assert o["common_denominator"]>0

def test_decimal_fraction_format_and_measurement_conversion():
    for seed in range(30):
        dec=MODULE.generate("G4-DECIMAL-FRACTIONS",seed,"guided").teacher_oracle()
        assert "." in dec["decimal"]
        meas=MODULE.generate("G4-MEASUREMENT",seed,"independent").teacher_oracle()
        assert meas["answer"]%meas["factor"]==0

def test_angle_pair_sums_to_right_angle():
    for seed in range(30):
        o=MODULE.generate("G4-ANGLES-LINES-SHAPES",seed,"guided").teacher_oracle()
        assert o["missing_angle"]+ (90-o["missing_angle"])==90
        assert o["sum"]==90

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G4-DIVISION",-1,"guided",ValueError),("G4-DIVISION",True,"guided",TypeError),("G4-DIVISION",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
