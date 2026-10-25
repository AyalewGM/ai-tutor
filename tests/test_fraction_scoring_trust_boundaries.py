"""Synthetic backend trust-boundary regression tests.

These checks do not register any production family, authorize a learner route,
or grant actual independent review. They exercise the existing pure handoff
with an isolated, process-local synthetic family.
"""
from types import MappingProxyType

import pytest

from app.answer_contracts import AnswerKind
from app.services import fraction_assessment_registry as registry
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.fraction_scoring_handoff import (
    DENIED,
    TrustedRationalItem,
    score_registered_item,
)

_FAMILY = "SYNTHETIC.TRUST_BOUNDARY"
_SKILL = "SYNTHETIC.EXACT.RATIONAL"
_SHA = "a" * 40


@pytest.fixture
def synthetic_authorized(monkeypatch):
    synthetic = ReviewedFamily(
        family_id=_FAMILY,
        canonical_skill_code=_SKILL,
        content_sha=_SHA,
        modes=frozenset({AssessmentMode.GUIDED, AssessmentMode.INDEPENDENT}),
        answer_kind=AnswerKind.VARIABLE_VALUE,
    )
    monkeypatch.setattr(
        registry,
        "AUTHORIZED_FAMILIES",
        MappingProxyType({_FAMILY: synthetic}),
    )


def trusted(*, family=_FAMILY, skill=_SKILL, sha=_SHA, answer="x=-5/6"):
    return TrustedRationalItem(
        family_id=family,
        canonical_skill_code=skill,
        content_sha=sha,
        canonical_answer=answer,
        variable="x",
    )


@pytest.mark.parametrize(
    "forged",
    [
        trusted(family="MATH.EE.EQUATION.TWO"),
        trusted(skill="MTH1W.C.ALG.EQ2"),
        trusted(sha="b" * 40),
    ],
)
def test_candidate_cannot_bypass_family_skill_or_content_revision(
    synthetic_authorized, forged
):
    assert score_registered_item(
        forged, "x=-5/6", AssessmentMode.INDEPENDENT
    ) == DENIED


@pytest.mark.parametrize(
    "response",
    ["x=5/-6", "X=-10/12", "x=-15/18"],
)
def test_exact_equivalent_rational_answers(synthetic_authorized, response):
    decision = score_registered_item(
        trusted(), response, AssessmentMode.INDEPENDENT
    )
    assert decision.accepted and decision.correct
    assert decision.independent_evidence_eligible


@pytest.mark.parametrize(
    "response",
    ["x=5/6", "x=-6/5", "x=0/0", "x=1/0", "y=-5/6", "x=-0.833333"],
)
def test_near_misses_never_grant_independent_evidence(synthetic_authorized, response):
    decision = score_registered_item(
        trusted(), response, AssessmentMode.INDEPENDENT
    )
    assert decision.accepted and not decision.correct
    assert not decision.independent_evidence_eligible


@pytest.mark.parametrize("mode", [AssessmentMode.GUIDED, AssessmentMode.DIAGNOSTIC, AssessmentMode.MASTERY])
def test_modes_cannot_escalate_to_independent_credit(synthetic_authorized, mode):
    result = score_registered_item(trusted(), "x=-5/6", mode)
    assert not result.independent_evidence_eligible
    if mode is AssessmentMode.GUIDED:
        assert result.accepted and result.correct
    else:
        assert result == DENIED


@pytest.mark.parametrize("assisted", [True, 1, "false", None])
def test_assistance_cannot_be_downgraded_into_credit(synthetic_authorized, assisted):
    result = score_registered_item(
        trusted(), "x=-5/6", AssessmentMode.INDEPENDENT, assisted=assisted
    )
    assert not result.independent_evidence_eligible
    if type(assisted) is not bool:
        assert result == DENIED
    else:
        assert result.accepted and result.correct


def test_server_decision_exposes_no_answer_key(synthetic_authorized):
    result = score_registered_item(
        trusted(), "x=-5/6", AssessmentMode.INDEPENDENT
    )
    assert set(vars(result)) == {
        "accepted", "correct", "independent_evidence_eligible"
    }
