"""Synthetic approved-family contract tests; no production registration or learner writes.

The monkeypatch below is process-local, reversible, and never imports #489
draft content or persists eligibility/mode grants.
"""
from types import MappingProxyType

import pytest

from app.answer_contracts import AnswerKind
from app.services import fraction_assessment_registry as registry
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.fraction_scoring_handoff import (
    TrustedRationalItem,
    score_registered_item,
)

_SHA = "f" * 40
_FAMILY = "SYNTHETIC.REVIEW_ONLY.RATIONAL"
_SKILL = "SYNTHETIC.MATH.EQUATIONS"


@pytest.fixture
def approved_synthetic_family(monkeypatch):
    entry = ReviewedFamily(
        family_id=_FAMILY,
        canonical_skill_code=_SKILL,
        content_sha=_SHA,
        modes=frozenset({AssessmentMode.GUIDED, AssessmentMode.INDEPENDENT}),
        answer_kind=AnswerKind.VARIABLE_VALUE,
    )
    monkeypatch.setattr(
        registry, "AUTHORIZED_FAMILIES",
        MappingProxyType({_FAMILY: entry}),
    )
    yield entry


def item(*, family=_FAMILY, skill=_SKILL, sha=_SHA):
    return TrustedRationalItem(
        family_id=family,
        canonical_skill_code=skill,
        content_sha=sha,
        canonical_answer="x=-3/4",
        variable="x",
    )


def test_synthetic_positive_and_negative_exact_answers(approved_synthetic_family):
    good = score_registered_item(
        item(), "x=6/-8", AssessmentMode.INDEPENDENT
    )
    assert good.accepted and good.correct and good.independent_evidence_eligible
    assert score_registered_item(
        item(), "X=-9/12", AssessmentMode.INDEPENDENT
    ) == good
    wrong = score_registered_item(
        item(), "x=-4/3", AssessmentMode.INDEPENDENT
    )
    assert wrong.accepted and not wrong.correct and not wrong.independent_evidence_eligible
    for invalid in ("x=1/0", "x=-(-3/4)", "y=-3/4", "x=-0.75", "x=__import__('os')"):
        result = score_registered_item(item(), invalid, AssessmentMode.INDEPENDENT)
        assert result.accepted and not result.correct and not result.independent_evidence_eligible


def test_assisted_guided_and_unapproved_modes(approved_synthetic_family):
    guided = score_registered_item(item(), "x=-3/4", AssessmentMode.GUIDED)
    assert guided.accepted and guided.correct and not guided.independent_evidence_eligible
    assisted = score_registered_item(
        item(), "x=-3/4", AssessmentMode.INDEPENDENT, assisted=True
    )
    assert assisted.accepted and assisted.correct and not assisted.independent_evidence_eligible
    for mode in (AssessmentMode.DIAGNOSTIC, AssessmentMode.MASTERY):
        result = score_registered_item(item(), "x=-3/4", mode)
        assert not result.accepted and not result.correct and not result.independent_evidence_eligible


def test_wrong_sha_family_and_skill_rejected(approved_synthetic_family):
    for altered in (
        item(sha="a" * 40),
        item(family="DRAFT.489.EQUATIONS"),
        item(skill="MTH1W.C.ALG.EQ2"),
    ):
        result = score_registered_item(altered, "x=-3/4", AssessmentMode.INDEPENDENT)
        assert not result.accepted and not result.independent_evidence_eligible


def test_retries_stable_and_no_oracle_leak(approved_synthetic_family):
    original = item()
    first = score_registered_item(original, "x=6/-8", AssessmentMode.INDEPENDENT)
    assert all(
        score_registered_item(original, "x=6/-8", AssessmentMode.INDEPENDENT) == first
        for _ in range(20)
    )
    assert not hasattr(first, "canonical_answer")
