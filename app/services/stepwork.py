"""Stepwise checking for multi-line equation work.

A work line is an equation state (``lhs = rhs``). A step is a legal algebraic
move iff the new equation is mathematically equivalent to the previous one —
i.e. their normalized coefficient vectors are proportional, so the solution
set is preserved. This deliberately permits any legal route (distribute-first
or divide-first), not only the canonical path.

Scope is single-variable polynomials in exact rational arithmetic, which
covers the SOLVE_EQUATION families served today.
"""
import re
from dataclasses import dataclass
from fractions import Fraction

Poly = dict[int, Fraction]

STEP_FAMILIES = {"SOLVE_EQUATION"}

_TOKEN = re.compile(r"\s*(\d+(?:\.\d+)?|[a-zA-Z]|[+\-*/()])")


def _tokenize(text: str) -> list[str] | None:
    text = text.replace("×", "*").replace("·", "*").replace("÷", "/").replace("−", "-")
    tokens: list[str] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if not match:
            return None
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


def _add(p: Poly, q: Poly) -> Poly:
    out = dict(p)
    for power, coef in q.items():
        out[power] = out.get(power, Fraction(0)) + coef
    return {k: v for k, v in out.items() if v != 0}


def _scale(p: Poly, k: Fraction) -> Poly:
    return {power: coef * k for power, coef in p.items()}


def _mul(p: Poly, q: Poly) -> Poly | None:
    if len(p) > 4 or len(q) > 4:
        return None
    out: Poly = {}
    for pk, pv in p.items():
        for qk, qv in q.items():
            power = pk + qk
            out[power] = out.get(power, Fraction(0)) + pv * qv
    return {k: v for k, v in out.items() if v != 0}


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> str | None:
        token = self._peek()
        self.pos += 1
        return token

    def expr(self) -> Poly | None:
        result = self.term()
        if result is None:
            return None
        while self._peek() in {"+", "-"}:
            op = self._next()
            term = self.term()
            if term is None:
                return None
            result = _add(result, _scale(term, Fraction(-1) if op == "-" else Fraction(1)))
        return result

    def term(self) -> Poly | None:
        result = self.factor()
        if result is None:
            return None
        while True:
            peek = self._peek()
            if peek in {"*", "/"}:
                self._next()
                operand = self.factor()
                if operand is None:
                    return None
                if peek == "*":
                    result = _mul(result, operand)
                else:
                    # Division only supported by a constant.
                    if set(operand.keys()) != {0} or operand[0] == 0:
                        return None
                    result = _scale(result, Fraction(1, 1) / operand[0])
                if result is None:
                    return None
            elif peek == "(" or (peek is not None and (peek[0].isdigit() or peek.isalpha())):
                # Implicit multiplication: 3x, 2(x+1), (x+1)x
                operand = self.factor()
                if operand is None:
                    return None
                result = _mul(result, operand)
                if result is None:
                    return None
            else:
                break
        return result

    def factor(self) -> Poly | None:
        token = self._peek()
        if token == "-":
            self._next()
            inner = self.factor()
            return _scale(inner, Fraction(-1)) if inner is not None else None
        if token == "+":
            self._next()
            return self.factor()
        if token == "(":
            self._next()
            inner = self.expr()
            if inner is None or self._next() != ")":
                return None
            return inner
        if token is None:
            return None
        self._next()
        if token[0].isdigit():
            return {0: Fraction(token)}
        if token.isalpha():
            return {1: Fraction(1)} if token == "x" else None
        return None


def parse_expression(text: str) -> Poly | None:
    """Parse a linear/polynomial expression into {power: coefficient}."""
    tokens = _tokenize(text.strip())
    if not tokens:
        return None
    parser = _Parser(tokens)
    result = parser.expr()
    if result is None or parser.pos != len(tokens):
        return None
    return result


def parse_equation(text: str) -> tuple[Poly, Poly] | None:
    """Parse 'lhs = rhs' into two polynomials; None if unparseable."""
    parts = text.strip().split("=")
    if len(parts) != 2:
        return None
    lhs, rhs = parse_expression(parts[0]), parse_expression(parts[1])
    if lhs is None or rhs is None:
        return None
    return lhs, rhs


def _normalized(eq: tuple[Poly, Poly]) -> Poly:
    """lhs - rhs as a polynomial."""
    return _add(eq[0], _scale(eq[1], Fraction(-1)))


def _proportional(p: Poly, q: Poly) -> bool:
    """True when p and q describe equations with the same solution set."""
    if not p and not q:
        return True
    keys = set(p) | set(q)
    ratio: Fraction | None = None
    for key in keys:
        pv, qv = p.get(key, Fraction(0)), q.get(key, Fraction(0))
        if pv == 0 and qv == 0:
            continue
        if pv == 0 or qv == 0:
            return False
        current = qv / pv
        if ratio is None:
            ratio = current
        elif ratio != current:
            return False
    return True


def _is_solved_form(eq: tuple[Poly, Poly]) -> bool:
    """The equation is literally 'x = const' (or 'const = x')."""
    lhs, rhs = eq
    unit_x = {1: Fraction(1)}
    return (lhs == unit_x and set(rhs) <= {0}) or (rhs == unit_x and set(lhs) <= {0})


def _solution_value(eq: tuple[Poly, Poly]) -> Fraction | None:
    """x-intercept value when the equation reduces to x = const."""
    norm = _normalized(eq)
    if set(norm.keys()) - {0, 1}:
        return None
    a = norm.get(1, Fraction(0))
    if a == 0:
        return None
    return -norm.get(0, Fraction(0)) / a


def _fmt_poly(poly: Poly) -> str:
    """Render a polynomial (deg<=1) as 'ax + b' text for feedback."""
    a = poly.get(1, Fraction(0))
    b = poly.get(0, Fraction(0))
    parts: list[str] = []
    if a != 0:
        if a == 1:
            parts.append("x")
        elif a == -1:
            parts.append("-x")
        else:
            parts.append(f"{a}x")
    if b != 0 or not parts:
        sign = "+" if b > 0 and parts else ("-" if b < 0 else "")
        parts.append(f"{sign} {abs(b)}".strip())
    return " ".join(parts)


def _canonical_next_line(eq: tuple[Poly, Poly]) -> str | None:
    """One legal next line toward x = const, for the reveal hint.

    Uses the normalized form so it works regardless of the route the learner
    took: move constants off the x-side, then divide off the coefficient.
    """
    norm = _normalized(eq)
    a = norm.get(1, Fraction(0))
    b = norm.get(0, Fraction(0))
    if a == 0:
        return None
    if b != 0:
        # ax + b = 0  ->  ax = -b
        return f"{_fmt_poly({1: a})} = {-b}"
    if a != 1:
        value = _solution_value(eq)
        return f"x = {value}" if value is not None else None
    return None


def _classify_error(
    prev_eq: tuple[Poly, Poly],
    new_eq: tuple[Poly, Poly],
) -> str | None:
    """Map a non-equivalent step to a catalog misconception where honest."""
    prev_lhs, prev_rhs = prev_eq
    new_lhs, new_rhs = new_eq
    # Applied the operation to only one side (e.g. divided just the RHS).
    if new_lhs == prev_lhs and new_rhs != prev_rhs:
        return "EQ_002"
    if new_rhs == prev_rhs and new_lhs != prev_lhs:
        return "EQ_002"
    # Moved a constant term the wrong direction: ax + b = c -> ax = c + b
    # (removed b from the left but added it to the right instead of
    # subtracting). Checked for each side's constant.
    lc, rc = prev_lhs.get(0, Fraction(0)), prev_rhs.get(0, Fraction(0))
    if lc and new_lhs == _add(prev_lhs, {0: -lc}) and new_rhs == _add(prev_rhs, {0: lc}):
        return "EQ_001"
    if rc and new_rhs == _add(prev_rhs, {0: -rc}) and new_lhs == _add(prev_lhs, {0: rc}):
        return "EQ_001"
    return None


@dataclass
class StepCheck:
    status: str  # "solved" | "valid" | "invalid" | "unparseable" | "duplicate"
    feedback: str | None = None
    misconception_code: str | None = None
    revealed_line: str | None = None
    normalized_line: str | None = None


def supports_steps(problem_type: str | None) -> bool:
    return problem_type in STEP_FAMILIES


def problem_supports_steps(problem) -> bool:
    """A problem offers structured steps only when the checker can parse it."""
    return (
        getattr(problem, "answer_kind", None) == "FREE_TEXT"
        and supports_steps(getattr(problem, "problem_type", None))
        and starting_equation(getattr(problem, "prompt", "") or "") is not None
    )


def starting_equation(prompt: str) -> str | None:
    """Extract the equation text from a problem prompt."""
    text = re.sub(r"^(solve( for \w)?|find \w|evaluate)[:\s]*", "", prompt.strip(), flags=re.IGNORECASE)
    text = text.strip().rstrip(".;")
    return text if "=" in text else None


def check_step(
    start_text: str,
    accepted_lines: list[str],
    new_line: str,
    invalid_count: int,
) -> StepCheck:
    """Grade one work line against the last accepted state.

    ``accepted_lines`` are the previously validated lines; ``invalid_count`` is
    the number of invalid submissions since the last valid line (server-derived
    so the escalation policy can't be gamed).
    """
    prior_text = accepted_lines[-1] if accepted_lines else start_text
    prev_eq = parse_equation(prior_text)
    if prev_eq is None:
        return StepCheck(status="unparseable", feedback="The previous line can't be checked.")

    stripped = new_line.strip()
    if not stripped:
        return StepCheck(status="unparseable", feedback="Type a line of work first.")

    # A bare number is a proposed solution state; a bare expression isn't
    # gradeable as a step.
    if "=" not in stripped:
        candidate = parse_expression(stripped)
        if candidate is None or set(candidate) != {0}:
            return StepCheck(
                status="unparseable",
                feedback="Write each step as an equation, like 3x + 12 = 30.",
            )
        stripped = f"x = {stripped}"

    new_eq = parse_equation(stripped)
    if new_eq is None:
        return StepCheck(
            status="unparseable",
            feedback="I can't read that line — try something like 3x + 12 = 30.",
        )

    if stripped == prior_text.strip():
        return StepCheck(status="duplicate", feedback="That's the same line — make a move.")

    if _proportional(_normalized(prev_eq), _normalized(new_eq)):
        normalized = f"{_fmt_poly(new_eq[0])} = {_fmt_poly(new_eq[1])}"
        if _is_solved_form(new_eq):
            return StepCheck(status="solved", normalized_line=normalized)
        return StepCheck(status="valid", normalized_line=normalized)

    code = _classify_error(prev_eq, new_eq)
    if invalid_count >= 2:
        revealed = _canonical_next_line(prev_eq)
        feedback = _ERROR_FEEDBACK.get(code) or "Check that every operation applies to both sides."
        return StepCheck(
            status="invalid",
            feedback=f"{feedback} One legal next line: {revealed}" if revealed else feedback,
            misconception_code=code,
            revealed_line=revealed,
        )
    if invalid_count == 1:
        feedback = _ERROR_FEEDBACK.get(code) or "That step doesn't follow — check the operation."
        return StepCheck(status="invalid", feedback=feedback, misconception_code=code)
    return StepCheck(
        status="invalid",
        feedback="That step doesn't follow from the line above — try again.",
        misconception_code=code,
    )


_ERROR_FEEDBACK = {
    "EQ_001": "Careful — use the inverse operation. To remove +b, subtract it (don't add).",
    "EQ_002": "Apply the same operation to every term on both sides of the equation.",
    "EQ_003": "Undo multiplication by dividing — not by multiplying.",
    "DIST_001": "Multiply the factor by every term inside the parentheses.",
    "ALG_001": "Only combine like terms — variable terms and constants stay separate.",
}
