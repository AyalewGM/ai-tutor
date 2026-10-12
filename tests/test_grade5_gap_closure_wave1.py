"""Fail-closed checks for Grade 5 comprehensive gap-closure wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade5-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g5_gap_variants",DIR/"variants.py")
assert spec is not None and spec.loader is not None
MODULE=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=MODULE
spec.loader.exec_module(MODULE)

def test_manifest_covers_all_nine_topics_and_hard_gates():
    ids=[p["id"] for p in PACKAGE["packages"]]
    assert len(ids)==9 and len(set(ids))==9
    assert set(ids)==set(MODULE.CONCEPTS)
    assert PACKAGE["status"]=="DRAFT_UNVERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False
    blocked=("production_wired","standards_accepted","math_accepted","pedagogy_accepted","architecture_accepted","mve_implemented","assessment_backend_wired","muse_qa","deployed")
    assert all(PACKAGE["gates"][k] is False for k in blocked)
    phases=["OBSERVE","PREDICT","MANIPULATE","EXPLAIN","PRACTICE","DIAGNOSE","TRANSFER","VERIFY"]
    for p in PACKAGE["packages"]:
        assert [x["phase"] for x in p["teaching_flow"]]==phases
        assert len(p["core_reasoning"])>=4
        assert len(p["misconception_routes"])>=3
        assert p["independent_transfer"]["unseen_namespace"] is True
        assert p["independent_transfer"]["no_hints"] is True

@pytest.mark.parametrize("mode",["guided","independent"])
def test_all_concepts_have_deterministic_varied_answer_isolated_variants(mode):
    for concept in MODULE.CONCEPTS:
        prompts=set()
        for seed in range(24):
            a=MODULE.generate(concept,seed,mode)
            b=MODULE.generate(concept,seed,mode)
            assert a==b
            assert a.teacher_oracle()
            payload=a.public_payload()
            assert payload["item_id"]==a.item_id
            assert "oracle" not in payload and "teacher_oracle" not in payload and "answer" not in payload
            prompts.add(a.prompt)
        assert len(prompts)>=2

def test_guided_and_independent_namespaces_are_disjoint():
    for concept in MODULE.CONCEPTS:
        for seed in range(50):
            g=MODULE.generate(concept,seed,"guided")
            i=MODULE.generate(concept,seed,"independent")
            assert g.item_id!=i.item_id
            assert g.prompt!=i.prompt

def test_expression_grouping_and_value_contract():
    for seed in range(30):
        o=MODULE.generate("G5-EXPRESSIONS",seed,"guided").teacher_oracle()
        assert o["grouping_required"] is True
        assert isinstance(o["value"],int)

def test_patterns_have_five_paired_terms_and_differences():
    for seed in range(30):
        o=MODULE.generate("G5-PATTERNS",seed,"independent").teacher_oracle()
        assert len(o["pairs"])==5
        assert len(o["differences"])==5

def test_nbt_variants_cover_four_operation_depth_cases():
    seen=set()
    for seed in range(40):
        v=MODULE.generate("G5-NBT-OPERATIONS",seed,"guided")
        o=v.teacher_oracle()
        if "place_value" in o: seen.add("place")
        if "remainder" in o: seen.add("division")
        if "estimate_reasonable" in o and isinstance(o.get("answer"),int): seen.add("whole_mult")
        if "estimate_reasonable" in o and isinstance(o.get("answer"),str): seen.add("decimal_add")
    assert seen=={"place","division","whole_mult","decimal_add"}

def test_fraction_add_sub_oracles_are_exact():
    for seed in range(40):
        o=MODULE.generate("G5-FRAC-ADD-SUB",seed,"guided").teacher_oracle()
        assert Fraction(o["answer"])>=0
        assert o["operation"] in {"+","-"}

def test_fraction_mul_div_oracles_are_exact_and_structured():
    for seed in range(40):
        o=MODULE.generate("G5-FRAC-MUL-DIV",seed,"independent").teacher_oracle()
        assert Fraction(o["answer"])>=0
        assert ("scaling_relation" in o) ^ ("measurement_division" in o)

def test_measurement_conversion_is_multiplicative():
    for seed in range(30):
        o=MODULE.generate("G5-MEAS-CONVERSION",seed,"guided").teacher_oracle()
        assert o["answer"]%o["factor"]==0
        assert o["direction"]=="LARGER_TO_SMALLER"

def test_volume_oracle_positive_and_additive_case_present():
    seen_add=False
    for seed in range(30):
        o=MODULE.generate("G5-VOLUME",seed,"independent").teacher_oracle()
        assert o["volume"]>0
        seen_add = seen_add or o.get("additive_volume") is True
    assert seen_add

def test_coordinate_points_first_quadrant_and_origin_contract():
    for seed in range(30):
        o=MODULE.generate("G5-COORDINATES",seed,"guided").teacher_oracle()
        x,y=o["point"]
        assert 0<=x<=9 and 0<=y<=9
        assert o["x_first"] is True and o["origin"]==[0,0]

def test_shape_hierarchy_inclusive_relations():
    relations={}
    for seed in range(20):
        o=MODULE.generate("G5-SHAPE-HIERARCHY",seed,"guided").teacher_oracle()
        relations[seed%4]=o["relation"]
        assert o["use_defining_attributes"] is True
    assert relations[0]=="ALWAYS"
    assert relations[1]=="ALWAYS"
    assert relations[2]=="ALWAYS"
    assert relations[3]=="SOMETIMES"

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G5-VOLUME",-1,"guided",ValueError),("G5-VOLUME",True,"guided",TypeError),("G5-VOLUME",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
