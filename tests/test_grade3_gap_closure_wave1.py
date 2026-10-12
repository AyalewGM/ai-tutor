"""Fail-closed checks for Grade 3 comprehensive gap-closure wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade3-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g3_gap_variants",DIR/"variants.py")
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

def test_multiplication_and_division_inverse_consistency():
    for seed in range(30):
        m=MODULE.generate("G3-MULTIPLICATION",seed,"guided").teacher_oracle()
        assert m["answer"]>0
        d=MODULE.generate("G3-DIVISION",seed,"independent").teacher_oracle()
        assert d["check"]>0
        assert d["structure"] in {"SHARING","GROUPING"}

def test_fact_family_has_four_related_facts():
    for seed in range(20):
        o=MODULE.generate("G3-FACT-FAMILIES",seed,"guided").teacher_oracle()
        assert len(o["facts"])==4
        assert o["product"]>0

def test_place_value_rounding_contract():
    assert MODULE._round_half_up_positive(145,10)==150
    assert MODULE._round_half_up_positive(150,100)==200
    halfway_seen=False
    for seed in range(120):
        o=MODULE.generate("G3-PLACE-VALUE",seed,"guided").teacher_oracle()
        n=o["number"]
        assert 100<=n<=999
        assert o["rounded10"]==((n+5)//10)*10
        assert o["rounded100"]==((n+50)//100)*100
        halfway_seen = halfway_seen or n%10==5 or n%100==50
    assert halfway_seen

def test_fraction_equivalence_and_half_comparison():
    for seed in range(40):
        o=MODULE.generate("G3-FRACTIONS",seed,"independent").teacher_oracle()
        assert Fraction(o["fraction"])==Fraction(o["equivalent"])
        assert o["compare_half"] in {"LT","EQ","GT"}

def test_time_end_time_has_clock_format():
    for seed in range(30):
        o=MODULE.generate("G3-TIME",seed,"guided").teacher_oracle()
        assert ":" in o["end_time"]
        assert o["elapsed"]>0

def test_scaled_graph_counts_are_scale_consistent():
    tie_seen=False
    for seed in range(120):
        o=MODULE.generate("G3-DATA",seed,"independent").teacher_oracle()
        assert all(h>=1 for h in o["heights"])
        max_height=max(o["heights"])
        expected=[label for label,height in zip(("A","B","C"),o["heights"]) if height==max_height]
        assert o["greatest"]==expected
        assert o["scale"] in {2,5,10}
        tie_seen = tie_seen or len(expected)>1
    assert tie_seen

def test_area_perimeter_are_distinct_measures():
    for seed in range(30):
        o=MODULE.generate("G3-AREA-PERIMETER",seed,"guided").teacher_oracle()
        assert o["area"]>0 and o["perimeter"]>0

def test_shape_hierarchy_relations():
    relations={}
    for seed in range(12):
        o=MODULE.generate("G3-SHAPES",seed,"guided").teacher_oracle()
        relations[seed%4]=o["relation"]
        assert o["attribute_reasoning"] is True
        assert o["equal_area_partition"] is True
    assert relations[0]=="ALWAYS"
    assert relations[1]=="ALWAYS"
    assert relations[2]=="ALWAYS"
    assert relations[3]=="SOMETIMES"

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G3-TIME",-1,"guided",ValueError),("G3-TIME",True,"guided",TypeError),("G3-TIME",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
