"""Fail-closed checks for Grade 2 comprehensive gap-closure wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade2-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g2_gap_variants",DIR/"variants.py")
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

def test_place_value_decomposition_reconstructs_number():
    for seed in range(30):
        o=MODULE.generate("G2-PLACE-VALUE",seed,"guided").teacher_oracle()
        assert 100*o["hundreds"]+10*o["tens"]+o["ones"]==o["value"]

def test_skip_patterns_have_constant_step():
    for seed in range(30):
        o=MODULE.generate("G2-SKIP-PATTERNS",seed,"independent").teacher_oracle()
        seq=o["sequence"]; step=o["step"]
        assert all(seq[i+1]-seq[i]==step for i in range(len(seq)-1))

def test_addition_subtraction_oracles_within_grade_bounds():
    for seed in range(40):
        a=MODULE.generate("G2-ADDITION",seed,"guided").teacher_oracle()
        s=MODULE.generate("G2-SUBTRACTION",seed,"independent").teacher_oracle()
        assert 0<=a["answer"]<100
        assert 0<=s["answer"]<100

def test_word_problem_roles_cover_key_unknown_positions():
    roles=set()
    for seed in range(20):
        o=MODULE.generate("G2-WORD-PROBLEMS",seed,"guided").teacher_oracle()
        roles.add(o["role"])
        assert o["answer"]>=0
    assert roles=={"RESULT_UNKNOWN","CHANGE_UNKNOWN","START_UNKNOWN","COMPARE_DIFFERENCE"}

def test_money_notation_matches_cents():
    for seed in range(30):
        o=MODULE.generate("G2-MONEY",seed,"independent").teacher_oracle()
        assert o["notation"]==f"${o['cents']/100:.2f}"

def test_length_comparison_and_start_zero():
    for seed in range(30):
        o=MODULE.generate("G2-LENGTH",seed,"guided").teacher_oracle()
        assert o["length"]-o["difference"]==o["other_length"]
        assert o["start_at_zero"] is True

def test_time_five_minute_groups_consistent():
    for seed in range(40):
        o=MODULE.generate("G2-TIME",seed,"independent").teacher_oracle()
        minute=int(o["time"].split(":")[1])
        assert minute%5==0
        assert o["five_minute_groups"]==minute//5

def test_shape_shares_use_supported_equal_part_names():
    seen=set()
    for seed in range(30):
        o=MODULE.generate("G2-SHAPES-SHARES",seed,"guided").teacher_oracle()
        seen.add(o["parts"])
        assert o["equal_area_required"] is True
        assert o["share_name"] in {"halves","thirds","fourths"}
    assert seen=={2,3,4}

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G2-TIME",-1,"guided",ValueError),("G2-TIME",True,"guided",TypeError),("G2-TIME",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
