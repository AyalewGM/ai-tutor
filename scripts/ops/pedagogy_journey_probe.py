"""Offline pedagogical *evidence* validator, not a learner state machine.

A release reviewer may run this against a synthetic journey trace. It never
scores a student's answer, generates content, authorizes a package, or writes
Attempt/MasteryEvent. Rejects incomplete journeys rather than inferring mastery.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class JourneyEvent:
    stage: str
    family: str
    fingerprint: str
    correct: bool
    misconception: str | None = None
    assisted: bool = False


class JourneyNotVerified(ValueError):
    pass


def verify_journey(events: Sequence[JourneyEvent]) -> None:
    """Require two wrong probes, targeted repair, corrected practice, unseen transfer.

    The same misconception must occur in two separate task fingerprints.
    Transfer must use a different mathematical family with no assistance,
    must be unseen across the entire preceding trace and must be correct.
    This is a trace-quality check ONLY, not a rule for awarding mastery.
    """
    required = ("probe", "probe", "repair", "guided_retest", "transfer", "verify")
    if not isinstance(events, (tuple, list)) or len(events) != len(required):
        raise JourneyNotVerified("Missing or extra pedagogical stages")
    if not all(isinstance(e, JourneyEvent) for e in events):
        raise JourneyNotVerified("Malformed journey event")
    if tuple(e.stage for e in events) != required:
        raise JourneyNotVerified("Incorrect stage order")
    p1, p2, repair, guided, transfer, verification = events
    if not p1.misconception or p1.misconception != p2.misconception:
        raise JourneyNotVerified("Misconception not corroborated")
    if p1.correct or p2.correct or not p1.fingerprint or not p2.fingerprint:
        raise JourneyNotVerified("Two distinct failed probes required")
    if p1.fingerprint == p2.fingerprint or p1.family != p2.family:
        raise JourneyNotVerified("Probes must be distinct tasks in one family")
    if repair.family != p1.family or repair.misconception != p1.misconception or not repair.assisted:
        raise JourneyNotVerified("Targeted assisted remediation missing")
    if guided.family != p1.family or not guided.correct or not guided.assisted:
        raise JourneyNotVerified("Correct assisted guided retest required")
    if not transfer.correct or transfer.assisted or transfer.family == guided.family:
        raise JourneyNotVerified("Unassisted different-family transfer missing")
    if not transfer.fingerprint or transfer.fingerprint in {e.fingerprint for e in events[:4]}:
        raise JourneyNotVerified("Transfer task must be unseen")
    if (verification.family != transfer.family or verification.fingerprint != transfer.fingerprint
            or not verification.correct or verification.assisted):
        raise JourneyNotVerified("Independent transfer verification missing")
