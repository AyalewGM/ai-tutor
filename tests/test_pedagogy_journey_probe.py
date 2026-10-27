"""Original author-side math evidence; never authenticates student mastery."""
from dataclasses import replace

import pytest

from scripts.author_ontario_linear_depth import (
    create_candidate,
    simulate_authored_learning_journey,
)
from scripts.ops.pedagogy_journey_probe import (
    AuthorJourneyInputs,
    JourneyEvent,
    JourneyNotVerified,
    verify_authored_journey,
    verify_journey,
)


def complete_inputs(seed=17):
    source = create_candidate("TWO_STEP_SIGNED_RATIONAL", seed=seed, mode="GUIDED")
    signal = source["diagnostic_contract_for_author_review"]["signals"][0]
    response = signal["candidate_response"]
    reason = signal["confirmation_evidence_choice_for_author_review"]
    repair = simulate_authored_learning_journey(
        source, practice_response=response, follow_up_reasoning_response=reason,
    )
    assert repair["stage"] == "GUIDED_RETEST"
    guided_answer = repair["private_guided_retest_for_author_review"]["canonical_answer"]
    exit_task = simulate_authored_learning_journey(
        source, practice_response=response, follow_up_reasoning_response=reason,
        guided_retest_response=guided_answer, readiness_confirmed=True,
    )
    assert exit_task["stage"] == "INDEPENDENT_EXIT"
    independent_answer = exit_task["private_transfer_for_author_review"][
        "private_exact_oracle_for_review"
    ]
    return AuthorJourneyInputs(
        family="TWO_STEP_SIGNED_RATIONAL",
        seed=seed,
        practice_response=response,
        reasoning_choice=reason,
        guided_retest_response=guided_answer,
        independent_response=independent_answer,
    )


def test_metadata_only_labels_never_certify_learning():
    fake = (
        JourneyEvent("probe", "two_step", "p1", False, "SIGN"),
        JourneyEvent("probe", "two_step", "p2", False, "SIGN"),
        JourneyEvent("repair", "two_step", "repair", False, "SIGN", True),
        JourneyEvent("guided_retest", "two_step", "guided", True, assisted=True),
        JourneyEvent("transfer", "multistep", "fresh", True),
        JourneyEvent("verify", "multistep", "fresh", True),
    )
    with pytest.raises(JourneyNotVerified, match="Metadata labels"):
        verify_journey(fake)


@pytest.mark.parametrize("seed", [0, 1, 2, 17, 23])
def test_original_author_math_repair_and_unseen_transfer(seed):
    report = verify_authored_journey(complete_inputs(seed))
    assert report.verified_math
    assert report.changed_reasoning_family
    assert not report.runtime_credit_authorized
    assert len({
        report.source_fingerprint,
        report.guided_retest_fingerprint,
        report.transfer_fingerprint,
    }) == 3
    assert not hasattr(report, "correct_answer")


@pytest.mark.parametrize("field,wrong", [
    ("practice_response", "x=123456"),
    ("reasoning_choice", "CONFIRM_WITHOUT_REASONING"),
    ("guided_retest_response", "x=123456"),
    ("independent_response", "x=123456"),
    ("family", "NOT_A_GENERATOR"),
])
def test_wrong_response_or_uncorroborated_reasoning_fails_closed(field, wrong):
    with pytest.raises(JourneyNotVerified):
        verify_authored_journey(replace(complete_inputs(), **{field: wrong}))


def test_absent_response_never_certifies_learning():
    with pytest.raises(JourneyNotVerified):
        verify_authored_journey(replace(complete_inputs(), independent_response=""))


def test_author_side_evidence_is_not_student_release_authority():
    result = verify_authored_journey(complete_inputs())
    assert result.runtime_credit_authorized is False
