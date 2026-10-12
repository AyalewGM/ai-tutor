"""Independent exact checks for draft Grades 2–5 additive unseen candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.draft_foundations_additive_unseen import STRUCTURES, generate

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts/draft-word-problem-structures-v0"


def _oracle(structure: str, operands: dict[str, int]) -> int:
    if structure == "result-unknown":
        return operands["start"] + operands["increase"]
    if structure == "change-unknown":
        return operands["final"] - operands["start"]
    if structure == "start-unknown":
        return operands["final"] - operands["increase"]
    if structure == "comparison-difference":
        return operands["larger"] - operands["smaller"]
    if structure == "comparison-smaller-unknown":
        return operands["larger"] - operands["difference"]
    if structure == "comparison-larger-unknown":
        return operands["smaller"] + operands["difference"]
    if structure == "two-change-unknown":
        return operands["start"] + operands["increase"] - operands["decrease"]
    if structure == "part-part-whole":
        return operands["whole"] - operands["known_part_a"] - operands["known_part_b"]
    raise AssertionError(f"unknown structure: {structure}")


def test_generator_reproducibility_diversity_and_scope() -> None:
    assert generate(91, 4) == generate(91, 4)
    assert generate(91, 4) != generate(92, 4)
    document = generate(91, 6)
    assert document["status"] == "DRAFT_UNVERIFIED"
    assert document["runtime_activation"] is False
    assert document["mastery_activation"] is False
    assert document["canonical_skill_ids"] == []
    assert document["curriculum_mappings"] == []
    assert document["server_trusted_scoring"] == (
        "PENDING_ASSESSMENT_BACKEND_IMPLEMENTATION"
    )
    assert len(document["items"]) == 48
    assert Counter(item["problem_structure"] for item in document["items"]) == {
        structure: 6 for structure in STRUCTURES
    }


@pytest.mark.parametrize("seed", [0, 7, 20261011, 99991])
def test_exact_answers_and_substitution_evidence(seed: int) -> None:
    for item in generate(seed, 8)["items"]:
        oracle = item["teacher_oracle_server_only"]
        expected = _oracle(item["problem_structure"], oracle["operands"])
        assert int(oracle["exact_answer"]) == expected
        evidence = oracle["verification_evidence"]
        assert evidence["substituted_left"] == evidence["substituted_right"]
        if item["problem_structure"] == "result-unknown":
            operands = oracle["operands"]
            assert evidence["substituted_left"] == operands["start"] + operands["increase"]
            assert evidence["substituted_right"] == expected
        assert expected >= 0


def test_result_unknown_tampered_claim_fails_independent_substitution_check() -> None:
    item = next(
        candidate
        for candidate in generate(20261011, 3)["items"]
        if candidate["problem_structure"] == "result-unknown"
    )
    oracle = item["teacher_oracle_server_only"]
    operands = oracle["operands"]
    reconstructed_left = operands["start"] + operands["increase"]
    correct_claim = int(oracle["exact_answer"])
    tampered_claim = correct_claim + 1

    assert reconstructed_left == correct_claim
    assert reconstructed_left != tampered_claim


def test_candidates_are_fresh_from_fixed_practice_and_fixed_exits() -> None:
    practice = json.loads((DRAFT / "content.draft.json").read_text())["practice_items"][:8]
    pathways = json.loads((DRAFT / "adaptive_pathways.draft.json").read_text())["pathways"][:8]
    original_by_structure = {item["problem_structure"]: item for item in practice}
    exit_by_source = {
        path["linked_item_id"]: path["mastery_exit"] for path in pathways
    }
    prompts: set[str] = set()
    for item in generate(20261011, 10)["items"]:
        structure = item["problem_structure"]
        original = original_by_structure[structure]
        fixed_exit = exit_by_source[item["linked_practice_item_id"]]
        prompt = item["learner_payload"]["question"]
        operands = list(item["teacher_oracle_server_only"]["operands"].values())
        assert prompt != original["question"]
        assert prompt != fixed_exit["prompt"]
        assert operands != original["operands"]
        assert operands != fixed_exit["variant_operands_server_only"]
        assert prompt not in prompts
        prompts.add(prompt)


def test_learner_payload_omits_oracle_and_teaching_leakage() -> None:
    forbidden = {
        "exact_answer",
        "operands",
        "operation",
        "relation",
        "verification_evidence",
        "diagnostic_routes_server_only",
        "hints",
        "worked_solution",
    }
    for item in generate(44, 5)["items"]:
        payload = item["learner_payload"]
        contract = item["learner_payload_contract"]
        assert set(payload) == set(contract["fields"])
        assert forbidden <= set(contract["omit"])
        serialized = json.dumps(payload).lower()
        assert "exact_answer" not in serialized
        assert "teacher_oracle" not in serialized
        assert "correct setup" not in serialized
        assert "worked_solution" not in serialized
        assert len(item["diagnostic_routes_server_only"]) == 3
        for route in item["diagnostic_routes_server_only"]:
            assert route["classification"]
            assert route["evidence"]
            assert len(route["socratic_questions"]) == 3


def test_machine_readable_provenance_is_complete_and_conservative() -> None:
    provenance = json.loads((DRAFT / "provenance.v1.json").read_text())
    assert provenance["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert provenance["package_id"] == "draft-word-problem-structures-v0"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    standards = provenance["standards"]
    assert standards["official_source_url"].startswith("UNKNOWN_")
    assert standards["exact_expectation_ids"] == []
    assert standards["mapping_approval"] == "NONE"
    assert provenance["canonical"]["identity_change"] is False
    assert provenance["canonical"]["approval_status"].startswith("UNKNOWN_")
    phases = provenance["learning_design"]["mihur_phases"]
    assert set(phases) == {
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    }
    representations = provenance["learning_design"]["representation_progression"]
    assert set(representations) == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    reviews = provenance["independent_reviews"]
    assert reviews["current_generator_mathematics"] == "PENDING"
    assert reviews["current_generator_pedagogy"] == "PENDING"
    assert reviews["muse_accessibility_and_e2e"] == "PENDING"
    assert reviews["release"] == "NOT_APPROVED"


@pytest.mark.parametrize("bad", [-1, 0, 21])
def test_bad_variant_counts_fail_closed(bad: int) -> None:
    with pytest.raises(ValueError):
        generate(5, bad)


@pytest.mark.parametrize("bad", [True, "5", 1.2, None])
def test_bad_seed_types_fail_closed(bad: object) -> None:
    with pytest.raises(TypeError):
        generate(bad)  # type: ignore[arg-type]
