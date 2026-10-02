"""Stepwise checking for multi-line equation work.

A work line is an equation state (``lhs = rhs``). A step is a legal algebraic
move iff the new equation is mathematically equivalent to the previous one —
i.e. their normalized coefficient vectors are proportional, so the solution
set is preserved. This deliberately permits any legal route (distribute-first
or divide-first), not only the canonical path.

Scope is single-variable polynomials in exact rational arithmetic, which
covers the SOLVE_EQUATION families served today.
"""
import math
import re
from dataclasses import dataclass
from fractions import Fraction

Poly = dict[int, Fraction]

STEP_FAMILIES = {
    "SOLVE_EQUATION",
    "SIMPLIFY_EXPRESSION",
    "COMBINE_LIKE_TERMS",
    "FRACTION_OPERATIONS",
    "FRACTION_SUBTRACT",
    "WORD_PROBLEM",
}

EXPRESSION_FAMILIES = {
    "SIMPLIFY_EXPRESSION",
    "COMBINE_LIKE_TERMS",
    "FRACTION_OPERATIONS",
}

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
    """Single-variable polynomial parser; the first letter binds the variable."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0
        self.var: str | None = None

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
            if len(token) != 1:
                return None
            if self.var is None:
                self.var = token
            elif token != self.var:
                return None
            return {1: Fraction(1)}
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


def _sympy_to_fraction(coef) -> Fraction | None:
    """Convert a SymPy coefficient to an exact Fraction; None if not rational."""
    import sympy as sp

    if isinstance(coef, sp.Integer):
        return Fraction(int(coef))
    if isinstance(coef, sp.Rational):
        return Fraction(int(coef.p), int(coef.q))
    if isinstance(coef, sp.Float):
        # Learner-typed decimals round-trip exactly through their repr.
        return Fraction(str(float(coef)))
    return None


def _sympy_expression(text: str) -> Poly | None:
    """Bounded SymPy fallback for syntax the native parser can't read.

    The input must reduce to a univariate polynomial — the result is the
    native ``Poly``, so equivalence, solved-form, and classification rules
    downstream stay exact and identical for both parse paths. No heavy SymPy
    machinery (simplify/equals/solve) runs on the request path; the bounds
    are input length, expression size, single symbol, integer exponents.
    """
    cleaned = text.strip()
    if not cleaned or len(cleaned) > 120:
        return None
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
    except ImportError:  # pragma: no cover - dependency is pinned
        return None
    try:
        expr = parse_expr(
            cleaned,
            transformations=standard_transformations
            + (implicit_multiplication_application, convert_xor),
        )
    except (SyntaxError, ValueError, TypeError, AttributeError, NameError, sp.SympifyError):
        return None
    nodes = list(sp.preorder_traversal(expr))
    if len(nodes) > 80:
        return None
    allowed = (sp.Add, sp.Mul, sp.Pow, sp.Symbol, sp.Number)
    if not all(isinstance(node, allowed) for node in nodes):
        return None
    if len(expr.free_symbols) > 1:
        return None
    for pow_node in expr.atoms(sp.Pow):
        if not (isinstance(pow_node.exp, sp.Integer) and pow_node.exp >= 0):
            return None
    var = next(iter(expr.free_symbols), sp.Symbol("x"))
    try:
        poly = sp.Poly(sp.expand(expr), var)
    except (sp.PolynomialError, sp.GeneratorsNeeded, TypeError, ValueError):
        return None
    out: Poly = {}
    for (power,), coef in poly.terms():
        frac = _sympy_to_fraction(coef)
        if frac is None:
            return None
        out[int(power)] = frac
    return out


def parse_expression_lenient(text: str) -> Poly | None:
    """Native parse first; bounded SymPy only for syntax it can't read."""
    result = parse_expression(text)
    return result if result is not None else _sympy_expression(text)


def parse_equation_lenient(text: str) -> tuple[Poly, Poly] | None:
    result = parse_equation(text)
    if result is not None:
        return result
    parts = text.strip().split("=")
    if len(parts) != 2:
        return None
    lhs, rhs = _sympy_expression(parts[0]), _sympy_expression(parts[1])
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


def _fmt_poly(poly: Poly, var: str = "x") -> str:
    """Render a polynomial as '2x^2 + 3x - 1' text for feedback."""
    parts: list[str] = []
    for power in sorted(poly, reverse=True):
        coef = poly[power]
        if coef == 0:
            continue
        mag = abs(coef)
        if power == 0:
            term = str(mag)
        elif power == 1:
            term = var if mag == 1 else f"{mag}{var}"
        else:
            term = f"{var}^{power}" if mag == 1 else f"{mag}{var}^{power}"
        if not parts:
            parts.append(f"-{term}" if coef < 0 else term)
        else:
            parts.append(f"- {term}" if coef < 0 else f"+ {term}")
    return " ".join(parts) if parts else "0"


def _canonical_next_line(eq: tuple[Poly, Poly], var: str = "x") -> str | None:
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
        return f"{_fmt_poly({1: a}, var)} = {-b}"
    if a != 1:
        value = _solution_value(eq)
        return f"{var} = {value}" if value is not None else None
    return None


_FRACTION_TERM = re.compile(r"^(-?\d+)/(\d+)$")
_EXPR_PREFIX = re.compile(
    r"^(simplify|evaluate|compute|expand|combine( like terms)?( of)?|add|subtract|rewrite|write)"
    r"[:\s]*(the expression|the following)?[:\s]*",
    re.IGNORECASE,
)


def _is_simplified(text: str, poly: Poly) -> bool:
    """Honest 'final form' check for expression families.

    Fully expanded (no parentheses), at most one term per degree, and a
    lone fraction is in lowest terms.
    """
    if "(" in text or ")" in text:
        return False
    pieces = [p for p in re.split(r"[+-]", text.strip()) if p.strip()]
    var_terms = sum(1 for p in pieces if re.search(r"[a-zA-Z]", p))
    const_terms = len(pieces) - var_terms
    if var_terms > 1 or const_terms > 1:
        return False
    if len(pieces) == 1:
        match = _FRACTION_TERM.match(pieces[0].strip())
        if match:
            num, den = int(match.group(1)), int(match.group(2))
            return den != 0 and math.gcd(abs(num), abs(den)) == 1
    return True


_FACTOR_FORM = re.compile(r"(-?\d+)\s*\(\s*([a-zA-Z])\s*([+-])\s*(\d+)\s*\)")


@dataclass
class StepCheck:
    status: str  # "solved" | "valid" | "invalid" | "unparseable" | "duplicate"
    feedback: str | None = None
    misconception_code: str | None = None
    revealed_line: str | None = None
    normalized_line: str | None = None


def _classify_expression_error(prev_text: str, new_poly: Poly) -> str | None:
    """Map a non-equivalent expression step to a catalog misconception."""
    # DIST_001: a(bx + c) -> abx + c (factor applied to only the first term).
    match = _FACTOR_FORM.search(prev_text.replace(" ", ""))
    if match:
        a = int(match.group(1))
        sign = 1 if match.group(3) == "+" else -1
        c = int(match.group(4))
        naive = {1: Fraction(a), 0: Fraction(sign * c)}
        if new_poly == naive:
            return "DIST_001"

    # NUM_003: numerators and denominators added across.
    terms = [t.strip() for t in re.split(r"[+-]", prev_text) if t.strip()]
    fracs = []
    for term in terms:
        match = _FRACTION_TERM.match(term.replace(" ", ""))
        if not match:
            return None
        fracs.append((int(match.group(1)), int(match.group(2))))
    if len(fracs) != 2:
        return None
    (a, b), (c, d) = fracs
    value = new_poly.get(0)
    naive = set()
    for sign in (1, -1):
        for denom in (b + d, b - d):
            if denom:
                naive.add(Fraction(a + sign * c, denom))
    return "NUM_003" if value in naive else None


def _check_expression_step(
    prev_text: str, new_line: str, invalid_count: int, var: str
) -> StepCheck:
    prev_poly = parse_expression_lenient(prev_text)
    if prev_poly is None:
        return StepCheck(status="unparseable", feedback="The previous line can't be checked.")

    stripped = new_line.strip()
    if not stripped:
        return StepCheck(status="unparseable", feedback="Type a line of work first.")
    if "=" in stripped:
        return StepCheck(
            status="unparseable",
            feedback="This is an expression — write the next form without an equals sign.",
        )
    new_poly = parse_expression_lenient(stripped)
    if new_poly is None:
        return StepCheck(
            status="unparseable",
            feedback="I can't read that — try something like 3x + 12 or 5/6.",
        )
    if stripped == prev_text.strip():
        return StepCheck(status="duplicate", feedback="That's the same line — make a move.")

    if new_poly == prev_poly:
        normalized = _fmt_poly(new_poly, var)
        if _is_simplified(stripped, new_poly):
            return StepCheck(status="solved", normalized_line=normalized)
        return StepCheck(status="valid", normalized_line=normalized)

    code = _classify_expression_error(prev_text, new_poly)
    if invalid_count >= 2:
        revealed = _fmt_poly(prev_poly, var)
        feedback = _ERROR_FEEDBACK.get(code) or "That expression isn't equal to the line above."
        return StepCheck(
            status="invalid",
            feedback=f"{feedback} Fully simplified, the line above is: {revealed}",
            misconception_code=code,
            revealed_line=revealed,
        )
    feedback = _ERROR_FEEDBACK.get(code) or "That expression isn't equal to the line above — check your arithmetic."
    return StepCheck(status="invalid", feedback=feedback, misconception_code=code)


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


def supports_steps(problem_type: str | None) -> bool:
    return problem_type in STEP_FAMILIES


def is_equation_family(problem_type: str | None) -> bool:
    return (
        problem_type not in EXPRESSION_FAMILIES
        and problem_type != "WORD_PROBLEM"
        and supports_steps(problem_type)
    )


def problem_supports_steps(problem) -> bool:
    """A problem offers structured steps only when the checker can parse it."""
    start = starting_point(problem)
    if (
        getattr(problem, "answer_kind", None) not in {"FREE_TEXT", "FRACTION", "INTEGER"}
        or not supports_steps(getattr(problem, "problem_type", None))
    ):
        return False
    if getattr(problem, "problem_type", None) == "WORD_PROBLEM":
        return word_canonical_value(problem) is not None
    if start is None:
        return False
    # The seed line must actually parse, or every check fails closed.
    if "=" in start:
        return parse_equation_lenient(start) is not None
    return parse_expression_lenient(start) is not None


def word_canonical_value(problem) -> Fraction | None:
    """The numeric answer of a word problem, when it is a plain number."""
    if getattr(problem, "problem_type", None) != "WORD_PROBLEM":
        return None
    raw = getattr(problem, "canonical_answer", None) or ""
    try:
        return Fraction(raw.strip())
    except (ValueError, ZeroDivisionError):
        pass
    poly = parse_expression_lenient(raw)
    if poly is not None and set(poly) <= {0}:
        return poly.get(0, Fraction(0))
    return None


def _strip_units(text: str) -> str:
    """Drop a trailing units word so '12 dollars' grades like '12'."""
    return re.sub(r"\s+[a-zA-Z]+$", "", text.strip())


def _word_line_value(line: str) -> Fraction | None:
    """Numeric value of a word-problem work line.

    Accepts a bare expression, ``var = expr``, an equal-sign chain whose
    rightmost side carries the value, and a trailing unit word.
    """
    text = _strip_units(line)
    if "=" in text:
        parts = [p for p in text.split("=") if p.strip()]
        if not parts:
            return None
        # An equals-anchored chain: every side must carry the same value.
        values = []
        for part in parts:
            poly = parse_expression_lenient(part.strip())
            if poly is None or set(poly) - {0, 1}:
                return None
            # A lone variable side (x = ...) is a label, not a value.
            if set(poly) == {1}:
                continue
            values.append(poly.get(0, Fraction(0)))
        if not values or len(set(values)) != 1:
            return None
        return values[0]
    poly = parse_expression_lenient(text)
    if poly is None or set(poly) != {0}:
        return None
    return poly.get(0)


def check_word_step(
    canonical_text: str,
    canonical: Fraction,
    accepted_lines: list[str],
    new_line: str,
    invalid_count: int,
) -> StepCheck:
    """Grade a word-problem work line against the model-compute structure.

    The first accepted line is the learner's *model* (the calculation that
    produces the answer); its value must equal the canonical answer. Later
    lines must preserve that value, ending at the bare answer. A bare correct
    answer at any point counts as solved — the structure is scaffolding, not
    a gate. There is no honest way to reveal a semantic model, so the
    escalation ceiling is targeted feedback, never an answer leak.
    """
    stripped = new_line.strip()
    if not stripped:
        return StepCheck(status="unparseable", feedback="Type a line of work first.")
    if stripped in {line.strip() for line in accepted_lines}:
        return StepCheck(status="duplicate", feedback="That's the same line — make a move.")

    value = _word_line_value(stripped)
    if value is None:
        return StepCheck(
            status="unparseable",
            feedback=(
                "Write a calculation, like 0.2 * 60, or your final answer "
                "with its unit, like 12 dollars."
            ),
        )
    if value == canonical:
        # Solved when the line ends at the bare answer; otherwise it is an
        # accepted model/computation line and work continues.
        last_side = _strip_units(stripped.split("=")[-1])
        last_poly = parse_expression_lenient(last_side)
        last_is_bare = (
            last_poly is not None
            and set(last_poly) == {0}
            and not _looks_like_model(last_side)
        )
        return StepCheck(
            status="solved" if last_is_bare else "valid",
            # On solve, hand respond() the authored canonical answer — the
            # learner's raw line ("0.2 * 60 = 12", "12 dollars") may not
            # match the final-answer normalizer.
            normalized_line=canonical_text if last_is_bare else stripped,
        )

    if not accepted_lines:
        feedback = (
            "That calculation doesn't produce the answer the problem asks for — "
            "check which numbers and operation the problem describes."
        )
    else:
        feedback = (
            "That line doesn't match the value of your calculation above — "
            "check your arithmetic."
        )
    return StepCheck(
        status="invalid",
        feedback=feedback,
        misconception_code=None if not accepted_lines else "NUM_003",
    )


def _looks_like_model(line: str) -> bool:
    """A line containing an operator is a computation, not a bare answer."""
    return bool(re.search(r"[+\-*/^]", line))


def starting_equation(prompt: str) -> str | None:
    """Extract the equation text from a problem prompt."""
    text = re.sub(r"^(solve( for \w)?|find \w|evaluate)[:\s]*", "", prompt.strip(), flags=re.IGNORECASE)
    text = text.strip().rstrip(".;?")
    return text if "=" in text else None


def starting_expression(prompt: str) -> str | None:
    """Extract the expression text from a problem prompt."""
    text = prompt.strip().rstrip(".;?")
    if parse_expression_lenient(text) is not None:
        return text
    stripped = _EXPR_PREFIX.sub("", text).strip().rstrip(".;?")
    return stripped if parse_expression_lenient(stripped) is not None else None


def starting_point(problem) -> str | None:
    """The checkable seed line for a problem — equation or expression."""
    prompt = getattr(problem, "prompt", "") or ""
    if is_equation_family(getattr(problem, "problem_type", None)):
        return starting_equation(prompt)
    if supports_steps(getattr(problem, "problem_type", None)):
        return starting_expression(prompt)
    return None


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
    var_match = re.search(r"[a-zA-Z]", start_text)
    var = var_match.group(0) if var_match else "x"
    prior_text = accepted_lines[-1] if accepted_lines else start_text

    if "=" not in start_text:
        return _check_expression_step(prior_text, new_line, invalid_count, var)

    prev_eq = parse_equation_lenient(prior_text)
    if prev_eq is None:
        return StepCheck(status="unparseable", feedback="The previous line can't be checked.")

    stripped = new_line.strip()
    if not stripped:
        return StepCheck(status="unparseable", feedback="Type a line of work first.")

    # A bare number is a proposed solution state; a bare expression isn't
    # gradeable as a step.
    if "=" not in stripped:
        candidate = parse_expression_lenient(stripped)
        if candidate is None or set(candidate) != {0}:
            return StepCheck(
                status="unparseable",
                feedback="Write each step as an equation, like 3x + 12 = 30.",
            )
        stripped = f"{var} = {stripped}"

    new_eq = parse_equation_lenient(stripped)
    if new_eq is None:
        return StepCheck(
            status="unparseable",
            feedback="I can't read that line — try something like 3x + 12 = 30.",
        )

    if stripped == prior_text.strip():
        return StepCheck(status="duplicate", feedback="That's the same line — make a move.")

    if _proportional(_normalized(prev_eq), _normalized(new_eq)):
        normalized = f"{_fmt_poly(new_eq[0], var)} = {_fmt_poly(new_eq[1], var)}"
        if _is_solved_form(new_eq):
            return StepCheck(status="solved", normalized_line=normalized)
        return StepCheck(status="valid", normalized_line=normalized)

    code = _classify_error(prev_eq, new_eq)
    if invalid_count >= 2:
        revealed = _canonical_next_line(prev_eq, var)
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
