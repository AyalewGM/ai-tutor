"""Fail-closed checks for Grade 6 comprehensive gap-closure wave."""

from __future__ import annotations
import importlib.util, json, sys
from fractions import Fraction
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade6-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g6_gap_variants",DIR/"variants.py")
assert spec is not None and spec.loader is not None
MODULE=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=MODULE
spec.loader.exec_module(MODULE)

def test_manifest_covers_all_seven_topics_and_remains_fail_closed():
    ids=[p["id"] for p in PACKAGE["packages"]]
    assert len(ids)==7 and len(set(ids))==7
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

def test_fraction_division_exact_oracle_matches_reciprocal():
    for seed in range(50):
        o=MODULE.generate("G6-FRACTION-DIVISION",seed,"independent").teacher_oracle()
        assert Fraction(o["quotient"])==Fraction(o["reciprocal_product"])
        assert o["estimate_relation"] in {"GT1","LT1"}

def test_expression_oracle_distributes_to_both_terms():
    for seed in range(40):
        v=MODULE.generate("G6-EXPRESSIONS",seed,"guided")
        o=v.teacher_oracle()
        assert o["property"]=="DISTRIBUTIVE_PROPERTY"
        assert "x+" in o["expanded"]

def test_equation_solution_verifies_exactly():
    for seed in range(40):
        o=MODULE.generate("G6-EQUATIONS",seed,"independent").teacher_oracle()
        assert "x=" in o["equation"]
        assert o["substitution"] is True
        assert Fraction(o["solution"])>=0

def test_coordinate_rectangle_perimeter_and_area_are_consistent():
    for seed in range(40):
        o=MODULE.generate("G6-POLYGON-COORDINATE",seed,"guided").teacher_oracle()
        assert o["perimeter"]==2*(o["width"]+o["height"])
        assert o["area"]==o["width"]*o["height"]

def test_nets_cover_prism_and_pyramid_and_face_counts():
    shapes={}
    for seed in range(40):
        o=MODULE.generate("G6-NETS-SURFACE",seed,"independent").teacher_oracle()
        shapes[o["shape"]]=o["faces"]
        assert Fraction(str(o["surface_area"]))>0
    assert shapes["RECTANGULAR_PRISM"]==6
    assert shapes["SQUARE_PYRAMID"]==5

def test_statistics_five_number_summary_and_iqr_ordering():
    for seed in range(50):
        o=MODULE.generate("G6-STAT-DISTRIBUTIONS",seed,"guided").teacher_oracle()
        assert o["min"]<=o["q1"]<=o["median"]<=o["q3"]<=o["max"]
        assert o["iqr"]==o["q3"]-o["q1"]>=0

def test_ratio_scaled_pair_and_reciprocal_unit_rates():
    for seed in range(50):
        o=MODULE.generate("G6-RATIO-RATE",seed,"independent").teacher_oracle()
        u=Fraction(o["unit_rate_b_per_a"])
        v=Fraction(o["unit_rate_a_per_b"])
        assert u*v==1
        assert all(x>0 for x in o["scaled"])

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G6-EQUATIONS",-1,"guided",ValueError),("G6-EQUATIONS",True,"guided",TypeError),("G6-EQUATIONS",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
