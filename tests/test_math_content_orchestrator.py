"""Synthetic orchestration routing tests; never call GitHub, DB or agents."""
from __future__ import annotations

import copy

import pytest

from scripts.math_content_orchestrator import reconcile

SHA = "a" * 40


def factory(safe: bool = True) -> dict:
    return {
        "runtime_activation": False,
        "status": "DRAFT_UNVERIFIED",
        "release_authority": "NONE",
        "source_canonical_skill": "MATH.EE.EQUATION.MULTISTEP",
        "quality_gates": {"independent_sympy_oracle_and_replay": safe},
        "automated_math_checks_passed": safe,
    }


def evidence() -> dict:
    return {"content_sha": SHA, "ci": {"sha": SHA, "status": "success"}}


def accepted() -> dict:
    return {
        "status": "ACCEPTED",
        "source_sha": SHA,
        "review_url": "https://github.com/AyalewGM/ai-tutor/pull/484#issuecomment-1",
    }


def test_math_failure_assigns_content_even_if_ci_green() -> None:
    result = reconcile(factory(False), evidence())
    assert result["next_owner"] == "Content Production"
    assert result["production_ready"] is False


def test_first_missing_independent_gate_goes_to_math() -> None:
    result = reconcile(factory(), evidence())
    assert result["next_owner"] == "Independent Math"
    assert result["gates"]["math"] == "PENDING"
    assert result["agent_execution"] == "NOT_EXECUTED"


def test_revision_change_invalidates_all_prior_acceptances() -> None:
    proof = evidence()
    proof["math"] = accepted()
    proof["math"]["source_sha"] = "b" * 40
    assert reconcile(factory(), proof)["next_owner"] == "Independent Math"


def test_reviewer_rejection_returns_to_author_not_user() -> None:
    proof = evidence()
    proof["math"] = accepted()
    proof["pedagogy"] = {**accepted(), "status": "CHANGES_REQUIRED"}
    result = reconcile(factory(), proof)
    assert result["next_owner"] == "Content Production"
    assert "Pedagogy" in result["next_action"]


def test_all_specialists_cannot_authorize_release() -> None:
    proof = evidence()
    for gate in ("math", "pedagogy", "standards", "assessment", "frontend", "muse", "engineering"):
        proof[gate] = accepted()
    proof["staging"] = "success"
    proof["production"] = "success"
    result = reconcile(factory(), proof)
    assert result["next_owner"] == "Engineering Lead / DevOps"
    assert result["release"] == {"staging": "NOT_VERIFIED", "production": "NOT_VERIFIED"}
    assert result["production_ready"] is False
    assert result["runtime_activation"] is False
    assert result["routing_intent_only"] is True


def test_ci_not_independent_math_acceptance() -> None:
    proof = evidence()
    proof["ci"]["sha"] = "b" * 40
    result = reconcile(factory(), proof)
    assert result["next_owner"] == "Engineering / CI"
    assert result["gates"]["math"] == "PENDING"


@pytest.mark.parametrize("bad", [True, "yes", None, {}, []])
def test_invalid_evidence_inputs_fail_closed(bad: object) -> None:
    proof = evidence()
    proof["content_sha"] = bad
    with pytest.raises(ValueError):
        reconcile(factory(), proof)


def test_malformed_review_url_not_acceptance() -> None:
    proof = evidence()
    proof["math"] = {**accepted(), "review_url": "https://example.com/self-approval"}
    assert reconcile(factory(), proof)["gates"]["math"] == "PENDING"


def test_no_runtime_activation_even_on_permitted_inputs() -> None:
    bad = copy.deepcopy(factory())
    bad["runtime_activation"] = True
    with pytest.raises(ValueError):
        reconcile(bad, evidence())
