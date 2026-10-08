"""Learning evidence for the private family pilot."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    attempts: int
    correct: int
