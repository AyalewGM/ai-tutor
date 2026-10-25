"""Fail-closed exact-rational assessment adapter; no runtime family activation.

The explicit registry is deliberately empty until independent source, scoring,
mapping, mode and learner-facing approvals are separately recorded and reviewed.
This module does not write Problems, Attempts or MasteryEvents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from app.answer_contracts import AnswerContract, AnswerKind


class AssessmentMode(StrEnum):
    DIAGNOSTIC = "diagnostic"
    GUIDED = "guided"
    INDEPENDENT = "independent"
    MASTERY = "mastery"


@dataclass(frozen=True)
class ReviewedFamily:
    family_id: str
    canonical_skill_code: str
    content_sha: str
    modes: frozenset[AssessmentMode]
    answer_kind: AnswerKind


# Zero authorized families. Addition requires a separate reviewed source
# change, immutable identity evidence and explicit per-mode test coverage.
AUTHORIZED_FAMILIES: Mapping[str, ReviewedFamily] = MappingProxyType({})

_RATIONAL = re.compile(r"[+-]?\d+(?:/[+-]?\d+)?\Z")
_VARIABLE_RATIONAL = re.compile(r"([A-Za-z])\s*=\s*(.+)\Z")


def _fraction(raw: object) -> Fraction | None:
    if not isinstance(raw, str) or len(raw) > 64:
        return None
    value = raw.strip()
    if not _RATIONAL.fullmatch(value):
        return None
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def score_fraction(candidate: str, expected: str, *, variable: str | None = None) -> bool:
    """Server-only equality; never evaluate expressions, floats or arbitrary code."""
    if variable is not None:
        if len(variable) != 1 or not variable.isalpha():
            return False
        if not isinstance(candidate, str) or not isinstance(expected, str):
            return False
        left = _VARIABLE_RATIONAL.fullmatch(candidate.strip())
        right = _VARIABLE_RATIONAL.fullmatch(expected.strip())
        if not left or not right:
            return False
        if left.group(1).casefold() != variable.casefold():
            return False
        if right.group(1).casefold() != variable.casefold():
            return False
        candidate, expected = left.group(2), right.group(2)
    # Existing AnswerContract remains authoritative for positive denominators
    # and canonical variable-value parsing. Signed-denominator syntax is
    # narrowly accepted via exact Fraction parsing, never a symbolic evaluator.
    contract = AnswerContract(AnswerKind.RATIONAL)
    return (
        _fraction(candidate) is not None
        and _fraction(expected) is not None
        and _fraction(candidate) == _fraction(expected)
        and (contract.equivalent(candidate, expected) or "/" in candidate or "/" in expected)
    )


def is_registered_for_mode(
    family_id: str,
    canonical_skill_code: str,
    content_sha: str,
    mode: AssessmentMode,
) -> bool:
    """No source/content/mode is admitted without an explicit reviewed entry."""
    entry = AUTHORIZED_FAMILIES.get(family_id)
    return (
        entry is not None
        and entry.canonical_skill_code == canonical_skill_code
        and entry.content_sha == content_sha
        and mode in entry.modes
        and entry.answer_kind in {AnswerKind.RATIONAL, AnswerKind.VARIABLE_VALUE}
    )
