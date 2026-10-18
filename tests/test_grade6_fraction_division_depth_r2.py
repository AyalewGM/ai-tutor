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
    assert package["independent_gates"]["mathematics"].startswith("ACCEPTED_AT_")
    assert package["independent_gates"]["pedagogy"].endswith("PENDING_REREVIEW")


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
    assert "socratic_support_contract" not in public
    assert set(public) == {
        "variant_id",
        "mode",
        "family",
        "prompt",
        "representation_prompt",
        "response_fields",
        "interaction_contract",
    }


def test_guided_support_contract_is_response_triggered_and_accessibility_is_equivalent() -> None:
    public = module.generate(17, "guided").public_payload()
    support = public["socratic_support_contract"]
    assert support == {
        "trigger": "AFTER_EXACT_QUOTIENT_SUBMISSION",
        "selection": "MATCH_OBSERVED_ANSWER_TO_MISCONCEPTION_PATHWAY",
        "ambiguous_match": "RETURN_EACH_SUPPORTED_HYPOTHESIS_WITHOUT_CHOOSING_FOR_THE_LEARNER",
        "fallback": "UNCLASSIFIED_WRONG_ANSWER",
        "answer_reveal": False,
    }
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


def test_every_misconception_has_distinct_socratic_support() -> None:
    expected_codes = {
        code
        for family in module.FAMILIES
        for code, _answer in module.generate(19, "guided", family).misconceptions
    }
    assert expected_codes == set(module.MISCONCEPTION_SUPPORT)
    questions = [item["socratic_question"] for item in module.MISCONCEPTION_SUPPORT.values()]
    moves = [item["representation_move"] for item in module.MISCONCEPTION_SUPPORT.values()]
    assert len(questions) == len(set(questions)) == 13
    assert len(moves) == len(set(moves)) == 13
    assert all(question.endswith("?") for question in questions)


@pytest.mark.parametrize("family", module.FAMILIES)
@pytest.mark.parametrize("seed", range(80))
def test_observed_misconception_answer_selects_only_supported_guided_pathways(
    family: str, seed: int
) -> None:
    item = module.generate(seed, "guided", family)
    by_answer: dict[Fraction, set[str]] = {}
    for code, wrong_answer in item.misconceptions:
        by_answer.setdefault(wrong_answer, set()).add(code)
    for wrong_answer, expected_codes in by_answer.items():
        support = item.guided_support_for_answer(wrong_answer)
        assert support is not None
        assert support["answer_reveal"] is False
        assert support["status"] in {"MATCHED_MISCONCEPTION", "AMBIGUOUS_MATCH"}
        pathways = support["pathways"]
        assert {path["misconception_code"] for path in pathways} == expected_codes
        assert all(path["socratic_question"].endswith("?") for path in pathways)
        assert all(_fraction(str(wrong_answer)) != item.quotient for _path in pathways)


def test_guided_support_handles_correct_unclassified_and_malformed_answers_without_leakage() -> (
    None
):
    item = module.generate(23, "guided", "RECIPE_BATCHES")
    correct = item.guided_support_for_answer(str(item.quotient))
    assert correct == {
        "status": "CORRECT_NO_REMEDIATION",
        "observed_answer": str(item.quotient),
        "pathways": [],
        "answer_reveal": False,
    }
    unclassified = item.guided_support_for_answer(item.quotient + 101)
    assert unclassified is not None
    assert unclassified["status"] == "UNCLASSIFIED_WRONG_ANSWER"
    assert [path["misconception_code"] for path in unclassified["pathways"]] == [
        "UNCLASSIFIED_WRONG_ANSWER"
    ]
    assert str(item.quotient) not in json.dumps(unclassified)
    for malformed, error in (
        (True, TypeError),
        (1.5, TypeError),
        ("", ValueError),
        ("3/0", ValueError),
    ):
        with pytest.raises(error):
            item.guided_support_for_answer(malformed)


@pytest.mark.parametrize("mode", ("diagnostic", "independent", "mastery"))
@pytest.mark.parametrize("family", module.FAMILIES)
def test_misconception_support_is_unavailable_outside_guided_mode(mode: str, family: str) -> None:
    item = module.generate(29, mode, family)
    wrong = item.misconceptions[0][1]
    assert item.guided_support_for_answer(wrong) is None


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
