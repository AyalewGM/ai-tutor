"""Strict deterministic answer contracts for opt-in canonical problem families.

This module does not perform symbolic solving or infer equivalence from an LLM.
Legacy families retain their existing normalization until individually audited.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from fractions import Fraction


class AnswerKind(StrEnum):
    INTEGER = "INTEGER"
    RATIONAL = "RATIONAL"
    DECIMAL = "DECIMAL"
    CATEGORY = "CATEGORY"
    VARIABLE_VALUE = "VARIABLE_VALUE"


AnswerValue = int | Fraction | Decimal | str


@dataclass(frozen=True)
class AnswerContract:
    kind: AnswerKind
    choices: frozenset[str] = frozenset()
    decimal_places: int | None = None
    variable: str | None = None

    def __post_init__(self) -> None:
        if self.kind == AnswerKind.CATEGORY and not self.choices:
            raise ValueError("category contracts require choices")
        if self.kind == AnswerKind.DECIMAL and (
            self.decimal_places is None or not 0 <= self.decimal_places <= 6
        ):
            raise ValueError("decimal contracts require precision from 0 to 6")
        if self.kind == AnswerKind.VARIABLE_VALUE and (
            self.variable is None or re.fullmatch(r"[a-zA-Z]", self.variable) is None
        ):
            raise ValueError("variable-value contracts require one variable letter")

    def parse(self, answer: str) -> AnswerValue | None:
        """Return a typed mathematical value, or None for an invalid response."""
        if not isinstance(answer, str) or len(answer) > 64:
            return None
        raw = answer.strip()
        if not raw:
            return None
        if self.kind == AnswerKind.CATEGORY:
            value = " ".join(raw.split()).casefold()
            return value if value in {choice.casefold() for choice in self.choices} else None
        if self.kind == AnswerKind.INTEGER:
            return int(raw) if re.fullmatch(r"[+-]?\d+", raw) else None
        if self.kind == AnswerKind.RATIONAL:
            if not re.fullmatch(r"[+-]?\d+(?:/\d+)?", raw):
                return None
            try:
                return Fraction(raw)
            except (ValueError, ZeroDivisionError):
                return None
        if self.kind == AnswerKind.DECIMAL:
            if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
                return None
            try:
                value = Decimal(raw)
                places = self.decimal_places
                assert places is not None
                quantized = value.quantize(Decimal(1).scaleb(-places))
                return value if quantized == value else None
            except InvalidOperation:
                return None
        if self.kind == AnswerKind.VARIABLE_VALUE:
            match = re.fullmatch(r"([a-zA-Z])\s*=\s*([+-]?\d+(?:/\d+)?)", raw)
            if match is None or match.group(1).casefold() != self.variable.casefold():
                return None
            try:
                return Fraction(match.group(2))
            except (ValueError, ZeroDivisionError):
                return None
        return None

    def equivalent(self, candidate: str, expected: str) -> bool:
        actual = self.parse(candidate)
        truth = self.parse(expected)
        return actual is not None and truth is not None and actual == truth
