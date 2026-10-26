"""Synthetic author tests for the offline trace contract, not independent review."""
from dataclasses import replace

import pytest

from scripts.ops.pedagogy_journey_probe import JourneyEvent, JourneyNotVerified, verify_journey


def trace():
    return (
        JourneyEvent("probe", "two_step", "p1", False, "SIGN"),
        JourneyEvent("probe", "two_step", "p2", False, "SIGN"),
        JourneyEvent("repair", "two_step", "repair", False, "SIGN", True),
        JourneyEvent("guided_retest", "two_step", "guided", True, assisted=True),
        JourneyEvent("transfer", "multistep", "fresh", True),
        JourneyEvent("verify", "multistep", "fresh", True),
    )


def test_complete_trace_is_structurally_verifiable():
    verify_journey(trace())


@pytest.mark.parametrize("index,changes", [
    (1, {"fingerprint": "p1"}),
    (1, {"misconception": "DISTRIBUTION"}),
    (2, {"assisted": False}),
    (3, {"correct": False}),
    (4, {"family": "two_step"}),
    (4, {"assisted": True}),
    (4, {"fingerprint": "p1"}),
    (5, {"correct": False}),
    (5, {"fingerprint": "not-the-transfer"}),
])
def test_missing_or_invalid_learning_evidence_fails_closed(index, changes):
    events = list(trace())
    events[index] = replace(events[index], **changes)
    with pytest.raises(JourneyNotVerified):
        verify_journey(events)


def test_missing_stage_rejected():
    with pytest.raises(JourneyNotVerified):
        verify_journey(trace()[:-1])
