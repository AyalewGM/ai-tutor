"""Fail-closed exact-rational assessment adapter; no runtime family activation.

The explicit registry is deliberately empty until independent source, scoring,
mapping, mode and learner-facing approvals are separately recorded and reviewed.
This module does not write Problems, Attempts or MasteryEvents.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType

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

# Bound raw input before stripping, splitting or parsing. This includes variable
# syntax so long whitespace prefixes cannot bypass the rational-answer budget.
_MAX_ANSWER_LENGTH = 64


def _signed_decimal(value: str) -> bool:
    digits = value[1:] if value.startswith(("+", "-")) else value
    # isdecimal matches the Unicode decimal digits previously accepted by \d,
    # without admitting superscripts or other non-decimal digit characters.
    return bool(digits) and digits.isdecimal()


def _fraction(raw: object) -> Fraction | None:
    if not isinstance(raw, str) or len(raw) > _MAX_ANSWER_LENGTH:
        return None
    value = raw.strip()
    numerator, separator, denominator = value.partition("/")
    if not _signed_decimal(numerator):
        return None
    if separator and not _signed_decimal(denominator):
        return None
    try:
        return Fraction(int(numerator), int(denominator)) if separator else Fraction(int(numerator))
    except (ValueError, ZeroDivisionError):
        return None


def _variable_value(raw: str, variable: str) -> str | None:
    value = raw.strip()
    if not value or not value[0].isascii() or not value[0].isalpha():
        return None
    if value[0].casefold() != variable.casefold():
        return None
    remainder = value[1:].lstrip()
    if not remainder.startswith("="):
        return None
    return remainder[1:].lstrip()


def score_fraction(candidate: str, expected: str, *, variable: str | None = None) -> bool:
    """Server-only equality; never evaluate expressions, floats or arbitrary code."""
    if not isinstance(candidate, str) or not isinstance(expected, str):
        return False
    if len(candidate) > _MAX_ANSWER_LENGTH or len(expected) > _MAX_ANSWER_LENGTH:
        return False
    if variable is not None:
        if not isinstance(variable, str) or len(variable) != 1 or not variable.isalpha():
            return False
        candidate = _variable_value(candidate, variable)
        expected = _variable_value(expected, variable)
        if candidate is None or expected is None:
            return False
    # Existing AnswerContract remains authoritative for positive denominators
    # and canonical variable-value parsing. Signed-denominator syntax is
    # narrowly accepted via exact Fraction parsing, never a symbolic evaluator.
    contract = AnswerContract(AnswerKind.RATIONAL)
    actual, truth = _fraction(candidate), _fraction(expected)
    return (
        actual is not None
        and truth is not None
        and actual == truth
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
