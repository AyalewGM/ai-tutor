"""Draft-only checks for the Maryland Grade 7 Unit 6 package."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/curriculum/drafts/maryland-grade7-unit6-algebra-v1"
PACKAGE = json.loads((DIR / "package.json").read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("md_g7_u6_variants", DIR / "variants.py")
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = MODULE
spec.loader.exec_module(MODULE)


def test_draft_gates_and_maryland_scope() -> None:
    assert PACKAGE["jurisdiction"] == "Maryland"
    assert PACKAGE["grade"] == 7
    assert PACKAGE["status"] == "DRAFT_UNVERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False
    targets = {
        row["id"] for row in PACKAGE["source_basis"]["maryland"]["targets"]
    }
    assert targets == {"7.AT.B.5", "7.AT.B.6", "7.AT.C.7", "7.AT.C.8", "7.AT.C.9"}
    assert [row["phase"] for row in PACKAGE["teaching_flow"]] == [
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    ]
    blocked = [
        "math_review",
        "pedagogy_review",
        "standards_mapping_review",
        "architecture_review",
        "mve_implemented",
        "assessment_backend_wired",
        "muse_qa",
        "runtime_activated",
        "deployed",
    ]
    assert all(PACKAGE["gates"][key] is False for key in blocked)


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_all_six_task_kinds_are_seeded_and_exact(mode: str) -> None:
    kinds = set()
    for seed in range(120):
        variant = MODULE.generate(seed, mode)
        kinds.add(variant.kind)
        replay = MODULE.generate(seed, mode)
        assert replay == variant
        assert variant.public_payload()["item_id"] == variant.item_id
        assert "teacher_oracle" not in variant.public_payload()
        assert "answer" not in variant.public_payload()

        oracle = variant.teacher_oracle()

        if variant.kind == "EQUATION_PX_PLUS_Q":
            assert variant.answer is not None
            assert variant.p * variant.answer + variant.q == variant.r
            assert oracle["solution"] == MODULE._fmt(variant.answer)
        elif variant.kind == "EQUATION_P_TIMES_X_PLUS_Q":
            assert variant.answer is not None
            assert variant.p * (variant.answer + variant.q) == variant.r
            assert oracle["solution"] == MODULE._fmt(variant.answer)
        elif variant.kind == "INEQUALITY_PX_PLUS_Q":
            assert variant.answer is not None
            assert variant.p * variant.answer + variant.q == variant.r
            assert _truth_set_matches_boundary(variant)
        elif variant.kind == "INEQUALITY_P_TIMES_X_PLUS_Q":
            assert variant.answer is not None
            assert variant.p * (variant.answer + variant.q) == variant.r
            assert _truth_set_matches_boundary(variant)
        elif variant.kind == "EXPRESSION_EQUIVALENCE":
            expected = f"{MODULE._fmt(variant.p)}x + {MODULE._fmt(variant.p * variant.q)}"
            assert oracle["equivalent_expression"] == expected
        elif variant.kind == "CHOOSE_MODEL":
            if variant.relation:
                assert oracle["model_type"] == "INEQUALITY"
                assert ">=" in variant.model
            else:
                assert oracle["model_type"] == "EQUATION"
                assert "=" in variant.model

    assert kinds == set(MODULE.KINDS)


def _truth_set_matches_boundary(variant) -> bool:
    oracle = variant.teacher_oracle()
    boundary = Fraction(oracle["boundary"])
    relation = oracle["solution_relation"]
    for numerator in range(0, 31):
        x = Fraction(numerator)
        direct = variant.satisfies_inequality(x)
        by_boundary = {
            "<": x < boundary,
            "<=": x <= boundary,
            ">": x > boundary,
            ">=": x >= boundary,
        }[relation]
        if direct != by_boundary:
            return False
    assert variant.satisfies_inequality(Fraction(oracle["witness"]))
    assert not variant.satisfies_inequality(Fraction(oracle["counterexample"]))
    return True


def test_guided_and_independent_namespaces_are_disjoint() -> None:
    for seed in range(180):
        guided = MODULE.generate(seed, "guided")
        independent = MODULE.generate(seed, "independent")
        assert guided.item_id != independent.item_id
        assert guided.prompt != independent.prompt
        if guided.answer is not None and independent.answer is not None:
            assert Fraction(2) <= guided.answer <= Fraction(10)
            assert Fraction(12) <= independent.answer <= Fraction(24)


def test_public_projection_has_no_hidden_math() -> None:
    forbidden = {
        "p",
        "q",
        "r",
        "answer",
        "teacher_oracle",
        "hints",
        "worked_solution",
        "misconception_tag",
        "canonical_skill_id",
        "mastery",
    }
    for seed in range(100):
        payload = MODULE.generate(seed, "independent").public_payload()
        assert not forbidden.intersection(payload)


def _complete_response(variant):
    oracle = variant.teacher_oracle()
    if variant.kind == "CHOOSE_MODEL":
        return {
            "model_type": oracle["model_type"],
            "symbolic_model": oracle["symbolic_model"],
            "context_justification": "The wording describes either one exact total or a range.",
        }
    if variant.kind.startswith("EQUATION"):
        return {
            "symbolic_model": oracle["symbolic_model"],
            "solution": oracle["solution"],
            "inverse_steps": "Undo the outer operation on both sides and simplify.",
            "substitution_check": True,
            "context_interpretation": "The result is the required number of units.",
        }
    if variant.kind.startswith("INEQUALITY"):
        return {
            "symbolic_model": oracle["symbolic_model"],
            "boundary": oracle["boundary"],
            "solution_relation": oracle["solution_relation"],
            "endpoint": oracle["endpoint"],
            "graph_direction": oracle["graph_direction"],
            "witness": oracle["witness"],
            "counterexample": oracle["counterexample"],
            "context_interpretation": "These nonnegative whole-number values meet the condition.",
        }
    return {
        "original_expression": variant.model,
        "equivalent_expression": oracle["equivalent_expression"],
        "property_justification": oracle["property"],
        "context_meaning": "Both expressions count the same repeated groups.",
    }


def test_guided_diagnosis_is_specific_and_never_runs_on_independent() -> None:
    for seed in range(24):
        variant = MODULE.generate(seed, "guided")
        response = _complete_response(variant)
        assert MODULE.diagnose_guided(
            variant, response
        ) == "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"

        partial = dict(response)
        partial.pop(next(iter(partial)))
        assert MODULE.diagnose_guided(variant, partial) == "INCOMPLETE_GUIDED_EVIDENCE"

    with pytest.raises(ValueError):
        MODULE.diagnose_guided(MODULE.generate(240, "independent"), {})


@pytest.mark.parametrize(
    ("seed", "mode", "error"),
    [
        (-1, "guided", ValueError),
        (True, "guided", TypeError),
        (2.5, "guided", TypeError),
        (2, "assessment", ValueError),
    ],
)
def test_invalid_generation_fails_closed(seed, mode, error) -> None:
    with pytest.raises(error):
        MODULE.generate(seed, mode)
