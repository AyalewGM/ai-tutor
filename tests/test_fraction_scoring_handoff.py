"""No runtime authority is installed; all synthetic modes fail closed."""
from dataclasses import FrozenInstanceError

import pytest

from app.services.fraction_assessment_registry import AssessmentMode
from app.services.fraction_scoring_handoff import (
    DENIED,
    TrustedRationalItem,
    score_registered_item,
)


def _item() -> TrustedRationalItem:
    return TrustedRationalItem(
        family_id="MATH.EE.EQUATION.TWO",
        canonical_skill_code="MATH.EE.EQUATION.TWO",
        content_sha="a" * 40,
        canonical_answer="x=3/4",
        variable="x",
    )


@pytest.mark.parametrize("mode", list(AssessmentMode))
def test_every_mode_denied_while_approval_registry_is_empty(mode):
    assert score_registered_item(_item(), "x=6/8", mode) == DENIED
    assert score_registered_item(_item(), "x=6/8", mode, assisted=True) == DENIED


def test_malformed_mode_and_assistance_rejected():
    assert score_registered_item(_item(), "x=3/4", "mastery") == DENIED
    assert score_registered_item(_item(), "x=3/4", AssessmentMode.GUIDED, assisted=1) == DENIED
    assert score_registered_item(_item(), "x=3/4", AssessmentMode.GUIDED, assisted=False) == DENIED


def test_retry_is_deterministic_and_has_no_side_effect():
    item = _item()
    first = score_registered_item(item, "x=6/8", AssessmentMode.MASTERY)
    for _ in range(12):
        assert score_registered_item(item, "x=6/8", AssessmentMode.MASTERY) == first
    assert first == DENIED
    with pytest.raises(FrozenInstanceError):
        item.canonical_answer = "x=2"


def test_draft_oracle_is_never_exposed_by_decision():
    decision = score_registered_item(_item(), "x=3/4", AssessmentMode.GUIDED)
    assert not decision.accepted
    assert not decision.independent_evidence_eligible
    assert not hasattr(decision, "canonical_answer")
