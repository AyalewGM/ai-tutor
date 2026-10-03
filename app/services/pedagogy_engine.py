"""Session-level pedagogical state: CPA level and reverse-Socratic trigger.

CPA (Concrete-Pictorial-Abstract) scaffolding sits above the step ladder.
The ladder decides *what to say* about a wrong line; the CPA level decides
*how to present* the problem space — ABSTRACT (symbols only), PICTORIAL
(structured visual of the learner's current line), CONCRETE (visual plus a
Socratic cue naming the manipulation, for learners still stuck).

Everything here is deterministic and derived from persisted WORK_STEP turn
metadata — no LLM involvement, no trusting client state.

Reverse-Socratic ("teach the tutor"): after a run of correct steps the tutor
plants a deliberately flawed next line and asks the learner to catch it.
``craft_flawed_step`` builds that line by applying a real catalogued
misconception transform, so the planted error is one the deterministic
classifier already knows — a learner who copies it verbatim is flagged with
the authentic code, not a synthetic one.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from app.services import stepwork

CPA_ABSTRACT = "ABSTRACT"
CPA_PICTORIAL = "PICTORIAL"
CPA_CONCRETE = "CONCRETE"

_CPA_ORDER = (CPA_ABSTRACT, CPA_PICTORIAL, CPA_CONCRETE)

# Consecutive-failure count that steps the presentation level down, and the
# recovery streak that steps it back up. Kept deliberately small at the top
# of the ladder: two wrong lines is enough evidence that symbolic-only
# presentation isn't landing, but a single valid step isn't enough evidence
# the learner no longer needs the picture.
_DOWNGRADE_AFTER = 2
_UPGRADE_AFTER = 2
REVERSE_SOCRATIC_AFTER = 3

_VALID = {"valid", "solved"}


@dataclass(frozen=True)
class PedagogyState:
    """Target pedagogical state after the latest step."""

    cpa_level: str
    cpa_changed: bool
    consecutive_invalid: int
    consecutive_valid: int
    misconception_tag: str | None
    trigger_reverse_socratic: bool


def evaluate_pedagogical_state(
    steps: Sequence[Mapping],
    *,
    prior_cpa: str = CPA_ABSTRACT,
    challenge_pending: bool = False,
) -> PedagogyState:
    """Derive CPA level and reverse-Socratic trigger from step history.

    ``steps`` is the ordered WORK_STEP metadata sequence for the current
    problem (oldest first), each with ``step_status`` and optionally
    ``misconception_code``. ``prior_cpa`` is the session's current level;
    the returned ``cpa_level`` moves at most one rung per evaluation so a
    learner never jumps straight from symbols to manipulatives.
    """
    statuses = [str(step.get("step_status") or "") for step in steps]
    consecutive_invalid = consecutive_valid = 0
    for status in reversed(statuses):
        if status == "invalid":
            if consecutive_valid:
                break
            consecutive_invalid += 1
        elif status in _VALID:
            if consecutive_invalid:
                break
            consecutive_valid += 1
        else:  # duplicate / unparseable — neutral, ends either streak
            break

    misconception_tag = None
    if consecutive_invalid:
        for step in reversed(steps):
            if str(step.get("step_status") or "") != "invalid":
                break
            code = step.get("misconception_code")
            if code:
                misconception_tag = str(code)
                break

    index = _CPA_ORDER.index(prior_cpa) if prior_cpa in _CPA_ORDER else 0
    if consecutive_invalid >= _DOWNGRADE_AFTER:
        index = min(index + 1, len(_CPA_ORDER) - 1)
    elif statuses and (statuses[-1] == "solved" or consecutive_valid >= _UPGRADE_AFTER):
        index = max(index - 1, 0)
    cpa_level = _CPA_ORDER[index]

    trigger = (
        not challenge_pending
        and consecutive_valid >= REVERSE_SOCRATIC_AFTER
        and bool(statuses)
        and statuses[-1] == "valid"  # a solved problem has no next step to flaw
    )
    return PedagogyState(
        cpa_level=cpa_level,
        cpa_changed=cpa_level != prior_cpa,
        consecutive_invalid=consecutive_invalid,
        consecutive_valid=consecutive_valid,
        misconception_tag=misconception_tag,
        trigger_reverse_socratic=trigger,
    )


def _fmt_number(value: Fraction | int) -> str:
    frac = Fraction(value)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _fmt_linear(a: Fraction, b: Fraction) -> str:
    """Render 'a*x + b' in learner-facing notation."""
    if a == 1:
        head = "x"
    elif a == -1:
        head = "-x"
    else:
        head = f"{_fmt_number(a)}x"
    if b == 0:
        return head
    sign = "+" if b > 0 else "-"
    return f"{head} {sign} {_fmt_number(abs(b))}"


def _same_equation(a: str | None, b: str | None) -> bool:
    """True when two line texts parse to identical equations."""
    if not a or not b:
        return False
    pa, pb = stepwork.parse_equation(a), stepwork.parse_equation(b)
    return pa is not None and pb is not None and pa == pb


def line_matches(a: str | None, b: str | None) -> bool:
    """Public wrapper used by the endpoint for challenge comparison."""
    return _same_equation(a, b)


def craft_flawed_step(line: str) -> tuple[str, str] | None:
    """Build a deliberately wrong successor to ``line``.

    Returns ``(flawed_line, planted_code)`` where the code is the real
    classifier code the flawed line would trigger, or None when the line
    isn't a shape we can corrupt honestly. Covers the two most instructive
    equation errors:

    - ``ax + b = c`` (b != 0): move ``b`` across without inverting it,
      yielding ``ax = c + b`` — the sign-flip family (EQ_001).
    - ``ax = c`` with |a| > 1: undo the coefficient by multiplying,
      yielding ``x = c*a`` — EQ_003.

    Anything else (constants already isolated, nonlinear, variables on the
    right) returns None and the caller simply doesn't issue a challenge.
    """
    parsed = stepwork.parse_equation(line)
    if parsed is None:
        return None
    lhs, rhs = parsed
    rhs_powers = {p for p, c in rhs.items() if c != 0}
    lhs_powers = {p for p, c in lhs.items() if c != 0}
    if rhs_powers - {0} or lhs_powers - {0, 1} or 1 not in lhs_powers:
        return None
    a = lhs.get(1, Fraction(0))
    b = lhs.get(0, Fraction(0))
    c = rhs.get(0, Fraction(0))
    if b != 0:
        # Moving b across '=' without flipping its sign: ax + b = c -> ax = c + b.
        return f"{_fmt_linear(a, Fraction(0))} = {_fmt_number(c + b)}", "EQ_001"
    if abs(a) != 1:
        # Undoing the coefficient by multiplying instead of dividing.
        return f"x = {_fmt_number(c * a)}", "EQ_003"
    return None
