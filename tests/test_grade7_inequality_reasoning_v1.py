"""Fail-closed mathematical and learner-projection draft tests for Grade 7 inequalities.

No database session, app imports, API calls or historical learner writes.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/curriculum/drafts/grade7-inequality-reasoning-v1"
SPEC = json.loads((DIR / "package.json").read_text(encoding="utf-8"))
module_spec = importlib.util.spec_from_file_location("draft_g7_inequalities", DIR / "variants.py")
assert module_spec is not None and module_spec.loader is not None
import sys

MODULE = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = MODULE
module_spec.loader.exec_module(MODULE)


def test_draft_safety_and_eight_learner_phases() -> None:
    assert MODULE.STATUS == "DRAFT_UNVERIFIED"
    assert MODULE.RUNTIME_ACTIVATION is False
    assert SPEC["status"] == "DRAFT_UNVERIFIED"
    assert SPEC["runtime_activation"] is False
    assert SPEC["mastery_writes"] is False
    assert not SPEC["canonical_reuse"]["new_code_created"]
    assert not any(
        SPEC["gates"][key]
        for key in (
            "mve_implemented",
            "student_route_wired",
            "server_scoring_wired",
            "standards_accepted",
            "math_accepted",
            "pedagogy_accepted",
            "muse_qa_accepted",
            "deployed",
        )
    )
    assert [entry["phase"] for entry in SPEC["teaching_flow"]] == [
        "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN",
        "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY",
    ]
    assert len(SPEC["misconception_branches"]) >= 6
    for branch in SPEC["misconception_branches"]:
        assert branch["socratic"] and branch["repair"] and branch["evidence"]


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_seeded_oracle_independently_recomputed_and_replay(mode: str) -> None:
    witnessed = set()
    for seed in range(80):
        variant = MODULE.generate(seed, mode)
        replay = MODULE.generate(seed, mode)
        assert replay == variant
        assert variant.mode == mode
        assert variant.a > 0 and variant.c > 0
        assert variant.b >= 0 and variant.d >= 0
        assert variant.a != variant.c
        assert variant.a * variant.boundary + variant.b == (
            variant.c * variant.boundary + variant.d
        )
        assert variant.boundary in (range(4, 13) if mode == "guided" else range(16, 27))
        assert variant.structure == ("symbolic" if seed % 4 < 2 else "context")
        oracle = variant.teacher_oracle()
        # Independent reconstruction of the inequality coefficient and boundary.
        slope = variant.a - variant.c
        intercept = variant.d - variant.b
        assert slope * variant.boundary == intercept
        expected_sign = variant.relation
        if slope < 0:
            expected_sign = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[expected_sign]
        assert oracle["solution_relation"] == expected_sign
        assert oracle["endpoint"] == (
            "CLOSED" if "=" in expected_sign else "OPEN"
        )
        assert oracle["graph_direction"] == (
            "RIGHT" if expected_sign in (">", ">=") else "LEFT"
        )
        for x in range(35):
            lhs = variant.a * x + variant.b
            rhs = variant.c * x + variant.d
            actual = {"<": lhs < rhs, "<=": lhs <= rhs, ">": lhs > rhs, ">=": lhs >= rhs}[
                variant.relation
            ]
            boundary_model = {
                "<": x < variant.boundary,
                "<=": x <= variant.boundary,
                ">": x > variant.boundary,
                ">=": x >= variant.boundary,
            }[expected_sign]
            assert actual == boundary_model == variant.satisfies(x)
        assert variant.satisfies(oracle["satisfying_test"])
        assert not variant.satisfies(oracle["rejected_test"])
        assert oracle["context_domain"] == "NONNEGATIVE_WHOLE_NUMBERS"
        witnessed.add((variant.structure, slope > 0, variant.relation))
    assert all(struct in {x[0] for x in witnessed} for struct in ("context", "symbolic"))
    assert all(direction in {x[1] for x in witnessed} for direction in (True, False))
    assert {x[2] for x in witnessed} == set(MODULE.RELATIONS)


def test_independent_projection_and_disjoint_mode_prompts() -> None:
    forbidden = {
        "expected", "teacher_oracle", "parameters", "hints",
        "worked_solution", "misconception_tag", "review_status",
        "canonical_skill_id", "mastery", "boundary",
        "solution_relation", "endpoint", "graph_direction",
    }
    for seed in range(160):
        guided = MODULE.generate(seed, "guided")
        independent = MODULE.generate(seed, "independent")
        assert guided.item_id != independent.item_id
        assert guided.boundary != independent.boundary
        assert guided.prompt != independent.prompt
        assert not forbidden.intersection(independent.public_payload())
        assert "written_justification" in independent.public_payload()["response_fields"]
        assert len(independent.public_payload()["response_fields"]) >= 8
        assert "hints" not in independent.public_payload()
    assert SPEC["unseen_transfer_and_independent_assessment"]["answer_oracle"]


def test_guided_specific_response_evidence_and_no_independent_scoring() -> None:
    from copy import deepcopy

    for seed in range(16):
        variant = MODULE.generate(seed, "guided")
        oracle = variant.teacher_oracle()
        complete = {
            key: oracle[key]
            for key in MODULE.RESPONSE_FIELDS
            if key != "written_justification"
        }
        complete["written_justification"] = (
            "I subtracted matching terms on both sides and checked the two costs."
        )
        assert (
            MODULE.diagnose_guided(variant, complete)
            == "GUIDED_STRUCTURED_FIELDS_MATCH_REASONING_UNREVIEWED"
        )
        missing = deepcopy(complete)
        del missing["written_justification"]
        assert MODULE.diagnose_guided(variant, missing) == "INCOMPLETE_GUIDED_EVIDENCE"
        wrong_endpoint = deepcopy(complete)
        wrong_endpoint["endpoint"] = (
            "OPEN" if oracle["endpoint"] == "CLOSED" else "CLOSED"
        )
        assert MODULE.diagnose_guided(variant, wrong_endpoint) == (
            "G7.STRICTNESS_ENDPOINT_CONFUSION"
        )
        wrong_direction = deepcopy(complete)
        wrong_direction["solution_relation"] = {
            "<": ">", "<=": ">=", ">": "<", ">=": "<="
        }[oracle["solution_relation"]]
        assert MODULE.diagnose_guided(variant, wrong_direction) == (
            "G7.NEGATIVE_DIVISION_NO_REVERSAL"
            if variant.a < variant.c
            else "G7.GRAPH_DIRECTION_CONFUSION"
        )
        bad_sample = deepcopy(complete)
        bad_sample["satisfying_test"] = oracle["rejected_test"]
        assert MODULE.diagnose_guided(variant, bad_sample) == (
            "G7.SUBSTITUTION_NOT_A_PROOF"
        )
        wrong_domain = deepcopy(complete)
        wrong_domain["context_domain"] = "ALL_REAL_NUMBERS"
        assert MODULE.diagnose_guided(variant, wrong_domain) == "G7.COUNT_DOMAIN_CONFUSION"
        empty_reason = deepcopy(complete)
        empty_reason["written_justification"] = "  "
        assert MODULE.diagnose_guided(variant, empty_reason) == (
            "G7.EXPLANATION_REQUIRES_EVIDENCE"
        )
    with pytest.raises(ValueError):
        MODULE.diagnose_guided(MODULE.generate(200, "independent"), {})


@pytest.mark.parametrize(
    ("seed", "mode", "error"),
    [
        (-1, "guided", ValueError),
        (True, "guided", TypeError),
        (1.5, "guided", TypeError),
        (1, "assessment", ValueError),
    ],
)
def test_invalid_generator_configuration_fails_closed(seed, mode, error) -> None:
    with pytest.raises(error):
        MODULE.generate(seed, mode)


def test_original_worked_inequalities_are_exact() -> None:
    source = [
        # a,b,relation,c,d,boundary,solution_relation,witness,counterexample
        (5, 4, "<=", 2, 19, 5, "<=", 4, 6),
        (2, 22, ">", 5, 7, 5, "<", 4, 6),
        (4, 8, ">=", 1, 20, 4, ">=", 5, 2),
        (3, 28, "<=", 7, 8, 5, ">=", 5, 4),
        (5, 8, "<=", 2, 23, 5, "<=", 5, 6),
    ]
    for a, b, op, c, d, t, result, yes, no in source:
        assert a * t + b == c * t + d
        sign = op if a > c else {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[op]
        assert sign == result
        def truth(x, a=a, b=b, c=c, d=d, op=op):
            left, right = a * x + b, c * x + d
            return {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
            }[op]
        assert truth(yes)
        assert not truth(no)
    assert len(SPEC["worked_models"]) == len(source)
