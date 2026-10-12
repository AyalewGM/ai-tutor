"""Fail-closed checks for Grade 1 comprehensive gap-closure wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade1-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g1_gap_variants",DIR/"variants.py")
assert spec is not None and spec.loader is not None
MODULE=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=MODULE
spec.loader.exec_module(MODULE)

def test_manifest_covers_all_eight_topics_and_hard_gates():
    ids=[p["id"] for p in PACKAGE["packages"]]
    assert len(ids)==8 and len(set(ids))==8
    assert set(ids)==set(MODULE.CONCEPTS)
    assert PACKAGE["status"]=="DRAFT_UNVERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False
    blocked=("production_wired","standards_accepted","math_accepted","pedagogy_accepted","architecture_accepted","mve_implemented","assessment_backend_wired","muse_qa","deployed")
    assert all(PACKAGE["gates"][k] is False for k in blocked)

def test_atomic_boundary_notes_preserved():
    notes=" ".join(PACKAGE["atomic_boundary_notes"])
    assert "Numeral representation is not counting mastery" in notes
    assert "Equality truth is not unknown-solving mastery" in notes
    assert "Reading time and producing time representations require separate evidence" in notes

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

def test_count_representation_boundary_and_ordering():
    for seed in range(60):
        o=MODULE.generate("G1-COUNT-REPRESENT",seed,"guided").teacher_oracle()
        assert 0<=o["numeral"]<=120
        assert o["ordered"]==sorted(o["ordered"])
        assert o["within_boundary"] is True

def test_place_value_reconstructs_two_digit_number():
    for seed in range(30):
        o=MODULE.generate("G1-PLACE-VALUE",seed,"independent").teacher_oracle()
        assert 10*o["tens"]+o["ones"]==o["value"]
        assert o["exchange_preserves_value"] is True

def test_addition_subtraction_within_20_and_inverse_check():
    for seed in range(40):
        add=MODULE.generate("G1-ADDITION",seed,"guided").teacher_oracle()
        sub=MODULE.generate("G1-SUBTRACTION",seed,"independent").teacher_oracle()
        assert 0<=add["answer"]<=20
        assert 0<=sub["answer"]<=20
        assert "=" in sub["addition_check"]

def test_word_problem_roles_cover_required_unknown_positions():
    roles=set()
    for seed in range(20):
        o=MODULE.generate("G1-WORD-PROBLEMS",seed,"guided").teacher_oracle()
        roles.add(o["role"])
        assert o["answer"]>=0
    assert roles=={"RESULT_UNKNOWN","CHANGE_UNKNOWN","START_UNKNOWN","COMPARE_DIFFERENCE"}

def test_equality_truth_and_unknown_solving_are_separate_variant_types():
    seen=set()
    for seed in range(20):
        o=MODULE.generate("G1-EQUALITY-UNKNOWNS",seed,"independent").teacher_oracle()
        if o.get("equality_only"): seen.add("equality")
        if o.get("unknown_solving_only"): seen.add("unknown")
    assert seen=={"equality","unknown"}

def test_time_only_hour_or_half_hour():
    for seed in range(30):
        o=MODULE.generate("G1-TIME",seed,"guided").teacher_oracle()
        assert o["minute"] in {0,30}
        assert 1<=o["hour"]<=12

def test_shape_contract_requires_attributes_and_composition_or_partition():
    for seed in range(30):
        o=MODULE.generate("G1-SHAPES",seed,"independent").teacher_oracle()
        assert o["requires_defining_attributes"] is True
        assert o["composition_or_partition"] is True

@pytest.mark.parametrize(("concept","seed","mode","error"),[
("BAD",1,"guided",ValueError),("G1-TIME",-1,"guided",ValueError),("G1-TIME",True,"guided",TypeError),("G1-TIME",1,"assessment",ValueError)])
def test_invalid_generation_fails_closed(concept,seed,mode,error):
    with pytest.raises(error):
        MODULE.generate(concept,seed,mode)
