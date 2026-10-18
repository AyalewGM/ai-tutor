from __future__ import annotations

import ast
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "docs/curriculum/drafts/grade6-gap-closure-wave1/fraction_division_depth_r2.py"
PACKAGE_PATH = MODULE_PATH.with_suffix(".package.json")
SPEC = importlib.util.spec_from_file_location("fraction_division_depth_r2", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _fraction(text: str) -> Fraction:
    return Fraction(text)


def test_provenance_pins_measured_audit_and_stays_fail_closed() -> None:
    package = json.loads(PACKAGE_PATH.read_text())
    assert package["package_id"] == "grade6-gap-closure-wave1"
    assert package["component_revision"] == "fraction-division-depth-r2"
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["learner_visible"] is False
    assert package["learner_data_writes"] is False
    assert package["mastery_writes"] is False
    audit = package["reuse_first_audit"]
    assert audit["main_sha"] == "ecb8ad8d6e0acf5388e03bbc6dea14a9f5bb2913"
    assert audit["audit_head_sha"] == "195806169943268a5d2d7878a34834c39d92f7a7"
    assert audit["artifact_id"] == 12126245961
    assert (
        audit["artifact_sha256"]
        == "33bede1875efe5f70649c97c6158ddc233795d70c584926d8a79a5a138a86978"
    )
    assert {row["local_skill"] for row in audit["measured_rows"]} == {
        "M6.NS.FRACTION",
        "DC6.NS.FRACTION",
        "VA6.CE.FRACTION",
    }
    assert all(row["stored_distinct_tasks"] == 2 for row in audit["measured_rows"])
    assert all(
        row["learner_visible_integrated_status"] == "NOT_VERIFIED" for row in audit["measured_rows"]
    )
    assert package["build_once_map_many"]["new_canonical_identity"] is False
    assert package["build_once_map_many"]["local_mapping_changes"] == []
    assert package["standards_provenance"]["mapping_approval"] == "NOT_ASSESSED"
    assert package["independent_gates"]["mathematics"] == "PENDING"


@pytest.mark.parametrize("mode", module.MODES)
def test_all_eight_mathematical_families_are_reachable(mode: str) -> None:
    seen = {module.generate(seed, mode).family for seed in range(64)}
    assert seen == set(module.FAMILIES)


def test_two_pass_seed_replay_is_byte_for_byte_stable() -> None:
    def snapshot() -> str:
        rows = []
        for mode in module.MODES:
            for seed in range(96):
                item = module.generate(seed, mode)
                rows.append(
                    {
                        "public": item.public_payload(),
                        "teacher": item.teacher_oracle(),
                    }
                )
        return json.dumps(rows, sort_keys=True, separators=(",", ":"))

    assert snapshot() == snapshot()


@pytest.mark.parametrize("mode", module.MODES)
@pytest.mark.parametrize("family", module.FAMILIES)
@pytest.mark.parametrize("seed", range(40))
def test_exact_oracle_reconstructs_division_and_multiplication(
    mode: str, family: str, seed: int
) -> None:
    item = module.generate(seed, mode, family)
    oracle = item.teacher_oracle()
    dividend = _fraction(oracle["dividend"])
    divisor = _fraction(oracle["divisor"])
    quotient = _fraction(oracle["exact_quotient"])
    assert divisor != 0
    assert quotient == dividend / divisor
    assert _fraction(oracle["reciprocal_product"]["left_factor"]) == dividend
    assert _fraction(oracle["reciprocal_product"]["right_factor"]) == Fraction(
        divisor.denominator, divisor.numerator
    )
    assert _fraction(oracle["reciprocal_product"]["result"]) == quotient
    assert (
        _fraction(oracle["multiplication_check"]["quotient"])
        * _fraction(oracle["multiplication_check"]["divisor"])
        == dividend
    )
    assert _fraction(oracle["multiplication_check"]["reconstructed_dividend"]) == dividend
    relation = oracle["size_relation"]
    if divisor < 1:
        assert relation == "QUOTIENT_GREATER_THAN_DIVIDEND"
    elif divisor > 1:
        assert relation == "QUOTIENT_LESS_THAN_DIVIDEND"


@pytest.mark.parametrize("mode", module.MODES)
@pytest.mark.parametrize("family", module.FAMILIES)
@pytest.mark.parametrize("seed", range(80))
def test_misconception_answers_never_collide_with_oracle(mode: str, family: str, seed: int) -> None:
    item = module.generate(seed, mode, family)
    oracle = item.teacher_oracle()
    answer = _fraction(oracle["exact_quotient"])
    wrong = {_fraction(value) for value in oracle["misconception_answers"].values()}
    assert wrong
    assert answer not in wrong


@pytest.mark.parametrize("seed", range(64))
def test_modes_are_namespaced_and_transfer_changes_structure(seed: int) -> None:
    items = [module.generate(seed, mode) for mode in module.MODES]
    assert len({item.variant_id for item in items}) == len(module.MODES)
    assert len({item.family for item in items}) == len(module.MODES)
    transfer = module.fresh_transfer(seed)
    guided = module.generate(seed, "guided")
    assert transfer.mode == "independent"
    assert transfer.family != guided.family
    assert transfer.prompt != guided.prompt


@pytest.mark.parametrize("mode", ("independent", "mastery"))
@pytest.mark.parametrize("seed", range(64))
def test_independent_public_payload_has_no_answer_hint_or_oracle(mode: str, seed: int) -> None:
    item = module.generate(seed, mode)
    public = item.public_payload()
    serialized = json.dumps(public, sort_keys=True).lower()
    assert "teacher_oracle" not in serialized
    assert "misconception_answers" not in serialized
    assert "socratic_support" not in public
    assert set(public) == {
        "variant_id",
        "mode",
        "family",
        "prompt",
        "representation_prompt",
        "response_fields",
        "interaction_contract",
    }


def test_guided_support_is_question_based_and_accessibility_is_equivalent() -> None:
    public = module.generate(17, "guided").public_payload()
    assert len(public["socratic_support"]) == 3
    assert all(question.endswith("?") for question in public["socratic_support"])
    contract = public["interaction_contract"]
    assert set(contract) == {
        "keyboard",
        "screen_reader",
        "reduced_motion",
        "focus_recovery",
        "color_independence",
    }
    assert "without drag" in contract["keyboard"]
    assert "partition" in contract["screen_reader"]


@pytest.mark.parametrize(
    ("seed", "mode", "family", "error"),
    [
        (True, "guided", None, TypeError),
        (1.5, "guided", None, TypeError),
        (-1, "guided", None, ValueError),
        (1, "practice", None, ValueError),
        (1, "guided", "UNKNOWN", ValueError),
    ],
)
def test_invalid_inputs_fail_closed(
    seed: object, mode: str, family: str | None, error: type[Exception]
) -> None:
    with pytest.raises(error):
        module.generate(seed, mode, family)


def test_draft_module_cannot_touch_learner_history_or_runtime() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {"__future__", "random", "dataclasses", "fractions", "math"}
    source = MODULE_PATH.read_text()
    for forbidden in (
        "sqlalchemy",
        "app.models",
        "Attempt(",
        "DiagnosticAttempt(",
        "MasteryEvent(",
        "ProblemVariant(",
        "session.add",
        "session.commit",
    ):
        assert forbidden not in source
    assert module.RUNTIME_ACTIVATION is False
    assert module.STATUS == "DRAFT_UNVERIFIED"
