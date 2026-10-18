"""Independent exact checks for Issue #451 Grade 3 data depth."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/curriculum/drafts/grade3-gap-closure-wave1"
PACKAGE=json.loads((DIR/"package.json").read_text(encoding="utf-8"))
spec=importlib.util.spec_from_file_location("g3_data_depth_variants",DIR/"variants.py")
assert spec is not None and spec.loader is not None
MODULE=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=MODULE
spec.loader.exec_module(MODULE)


def _dict_from_prompt(prompt:str)->dict[str,int]:
    match=re.search(r"counts (\{[^}]+\})",prompt)
    assert match
    return ast.literal_eval(match.group(1))


def _list_from_prompt(prompt:str)->list[int]:
    match=re.search(r"data (\[[^]]+\])",prompt)
    assert match
    return ast.literal_eval(match.group(1))


def independent_answer(family:str,prompt:str)->str:
    if family=="MATH.DATA.BAR.READ":
        data=_dict_from_prompt(prompt)
        category=re.search(r"count for (\w+)\?",prompt).group(1)
        return str(data[category])
    if family=="MATH.DATA.BAR.COMPARE":
        data=_dict_from_prompt(prompt)
        first,second=re.search(r"between (\w+) and (\w+)\?",prompt).groups()
        return str(abs(data[first]-data[second]))
    if family=="MATH.DATA.BAR.TOTAL":
        data=_dict_from_prompt(prompt)
        first,second=re.search(r"for (\w+) and (\w+)\?",prompt).groups()
        return str(data[first]+data[second])
    if family=="MATH.DATA.PICTURE.SCALE":
        scale,symbols=map(int,re.search(r"represents (\d+) students.*has (\d+) symbols",prompt).groups())
        return str(scale*symbols)
    if family=="MATH.DATA.TALLY.READ":
        groups,extras=map(int,re.search(r"shows (\d+) complete groups.*and (\d+) extra",prompt).groups())
        return str(groups*5+extras)
    if family=="MATH.DATA.FREQ.MODE":
        data=_dict_from_prompt(prompt)
        return max(data,key=data.get)
    if family=="MATH.DATA.LINEPLOT.FREQUENCY":
        values=_list_from_prompt(prompt)
        target=int(re.search(r"above (\d+)\?",prompt).group(1))
        return str(values.count(target))
    if family=="MATH.DATA.LINEPLOT.DIFFERENCE":
        values=_list_from_prompt(prompt)
        first,second=map(int,re.search(r"frequencies of (\d+) and (\d+)\?",prompt).groups())
        return str(abs(values.count(first)-values.count(second)))
    raise AssertionError(f"untested family: {family}")


def test_machine_readable_provenance_is_honest_and_runtime_off():
    provenance=PACKAGE["content_provenance"]
    assert provenance["package_id"]=="G3-DATA-DEPTH-R2"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_history_writes"] is False
    assert provenance["standards_mapping_status"]=="UNKNOWN_NOT_REASSESSED"
    assert provenance["learner_visible_availability"]=="NOT_VERIFIED"
    assert provenance["independent_reviews"]=={
        "mathematical":"PENDING",
        "pedagogical":"PENDING",
        "muse_qa":"PENDING",
    }


@pytest.mark.parametrize("mode",MODULE.DATA_MODES)
def test_each_mode_covers_eight_distinct_mathematical_families(mode):
    variants=[MODULE.generate("G3-DATA",seed,mode) for seed in range(8)]
    assert {variant.family_code for variant in variants}==set(MODULE.DATA_FAMILIES)
    assert len({variant.prompt for variant in variants})==8


@pytest.mark.parametrize("mode",MODULE.DATA_MODES)
def test_exact_oracles_are_independently_recomputed(mode):
    for seed in range(64):
        variant=MODULE.generate("G3-DATA",seed,mode)
        oracle=variant.teacher_oracle()
        assert oracle["canonical_answer"]==independent_answer(variant.family_code,variant.prompt)
        assert oracle["family_code"]==variant.family_code
        assert oracle["misconception_answers"]
        assert all(str(wrong)!=str(oracle["canonical_answer"]) for wrong in oracle["misconception_answers"].values())


def test_same_seed_is_full_math_distinct_across_modes():
    for seed in range(128):
        variants=[MODULE.generate("G3-DATA",seed,mode) for mode in MODULE.DATA_MODES]
        fingerprints={(v.family_code,v.prompt,v.teacher_oracle()["canonical_answer"]) for v in variants}
        assert len(fingerprints)==len(MODULE.DATA_MODES)


def test_guided_support_is_isolated_from_diagnostic_independent_and_mastery():
    for mode in MODULE.DATA_MODES:
        variant=MODULE.generate("G3-DATA",19,mode)
        payload=variant.public_payload()
        assert "oracle" not in payload and "answer" not in payload and "seed" not in payload and "item_id" not in payload
        assert payload["mastery_credit"] is False
        if mode=="guided":
            assert len(payload["guided_support"])==2
        else:
            assert payload["guided_support"]==[]


@pytest.mark.parametrize(("source_mode","target_mode"),[("diagnostic","independent"),("guided","mastery")])
def test_unseen_transfer_is_deterministic_and_changes_structure(source_mode,target_mode):
    for seed in range(32):
        source=MODULE.generate("G3-DATA",seed,source_mode)
        first=MODULE.generate_data_transfer(seed,source_mode,target_mode)
        second=MODULE.generate_data_transfer(seed,source_mode,target_mode)
        assert first==second
        assert first.mode==target_mode
        assert first.family_code!=source.family_code
        assert first.prompt!=source.prompt
        assert first.teacher_oracle()["canonical_answer"]==independent_answer(first.family_code,first.prompt)


def test_generation_is_idempotent_in_two_passes():
    first=[MODULE.generate("G3-DATA",seed,mode) for mode in MODULE.DATA_MODES for seed in range(128)]
    second=[MODULE.generate("G3-DATA",seed,mode) for mode in MODULE.DATA_MODES for seed in range(128)]
    assert first==second
    assert len({variant.item_id for variant in first})==len(first)


def test_draft_is_not_imported_by_runtime_application():
    draft_name="grade3-gap-closure-wave1"
    assert all(draft_name not in path.read_text(encoding="utf-8",errors="ignore") for path in (ROOT/"app").rglob("*.py"))


def test_pure_generator_has_no_learner_history_write_surface():
    source=(DIR/"variants.py").read_text(encoding="utf-8")
    forbidden=("Attempt", "DiagnosticAttempt", "MasteryEvent", "LearnerVariant", "Session(", ".commit(", ".flush(")
    assert all(token not in source for token in forbidden)
    assert PACKAGE["mastery_writes"] is False
    assert PACKAGE["content_provenance"]["learner_history_writes"] is False
