"""Draft-only Maryland Grade 7 Unit 6 algebra variants.

Targets source-linked Maryland 2025 expectations 7.AT.B.5, 7.AT.B.6,
7.AT.C.7, 7.AT.C.8, and 7.AT.C.9 plus MCPS Math 7 Unit 6 sequencing.

Never imported by runtime code. No database, routing, scoring, or mastery writes.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
NAMESPACE = "maryland-grade7-unit6-algebra-v1"
MODES = frozenset({"guided", "independent"})
KINDS = (
    "CHOOSE_MODEL",
    "EQUATION_PX_PLUS_Q",
    "EQUATION_P_TIMES_X_PLUS_Q",
    "INEQUALITY_PX_PLUS_Q",
    "INEQUALITY_P_TIMES_X_PLUS_Q",
    "EXPRESSION_EQUIVALENCE",
)


def _fmt(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _holds(left: Fraction, relation: str, right: Fraction) -> bool:
    return {
        "<": left < right,
        "<=": left <= right,
        ">": left > right,
        ">=": left >= right,
    }[relation]


def _flip(relation: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[relation]



def _linear_coefficients(source: object) -> tuple[Fraction, Fraction] | None:
    """Parse only exact linear rational arithmetic; no calls, powers or names but x."""
    if not isinstance(source, str) or len(source) > 180:
        return None
    text = source.replace("−", "-").replace("×", "*").strip()
    text = re.sub(r"(?<=\d)\s*(?=x\b|\()", "*", text)
    text = re.sub(r"(?<=\))\s*(?=x\b|\()", "*", text)
    text = re.sub(r"(?<=x)\s*(?=\()", "*", text)
    try:
        expression = ast.parse(text, mode="eval").body

        def visit(node: ast.AST) -> tuple[Fraction, Fraction]:
            if isinstance(node, ast.Name) and node.id == "x":
                return Fraction(1), Fraction(0)
            if isinstance(node, ast.Constant) and type(node.value) is int:
                return Fraction(0), Fraction(node.value)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                a, b = visit(node.operand)
                sign = -1 if isinstance(node.op, ast.USub) else 1
                return sign * a, sign * b
            if isinstance(node, ast.BinOp):
                a, b = visit(node.left)
                c, d = visit(node.right)
                if isinstance(node.op, ast.Add):
                    return a + c, b + d
                if isinstance(node.op, ast.Sub):
                    return a - c, b - d
                if isinstance(node.op, ast.Mult) and not (a and c):
                    return a * d + b * c, b * d
                if isinstance(node.op, ast.Div) and not c and d:
                    return a / d, b / d
            raise ValueError("Not a supported exact linear expression")

        return visit(expression)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, RecursionError):
        return None


def _mathematically_equivalent(actual: object, expected: str) -> bool:
    """Compare exact linear expressions or zero-set/half-plane representations.

    Equation differences may have a nonzero common multiplier. Inequalities
    require a positive multiplier with identical relational orientation.
    """

    def parse(value: object) -> tuple[str | None, tuple[Fraction, Fraction]] | None:
        if not isinstance(value, str) or len(value) > 180:
            return None
        pieces = re.split(r"(<=|>=|=|<|>)", value, maxsplit=1)
        if len(pieces) == 1:
            coefficients = _linear_coefficients(pieces[0])
            return (None, coefficients) if coefficients is not None else None
        if len(pieces) != 3:
            return None
        lhs, rel, rhs = pieces
        left = _linear_coefficients(lhs)
        right = _linear_coefficients(rhs)
        if left is None or right is None:
            return None
        return rel, (left[0] - right[0], left[1] - right[1])

    found, target = parse(actual), parse(expected)
    if found is None or target is None:
        return False
    actual_rel, (a, b) = found
    expected_rel, (c, d) = target
    if actual_rel != expected_rel:
        return False
    if actual_rel is None:
        return (a, b) == (c, d)
    if not (c or d):
        # Avoid accepting arbitrary tautologies or degenerate equalities.
        return (a, b) == (c, d)
    factor = a / c if c else b / d
    return factor != 0 and (actual_rel == "=" or factor > 0) and (a, b) == (factor * c, factor * d)


def _exact_number_matches(actual: object, expected: object) -> bool:
    if isinstance(actual, (bool, float)) or not isinstance(actual, (int, str, Fraction)):
        return False
    try:
        return Fraction(str(actual)) == Fraction(str(expected))
    except (ValueError, ZeroDivisionError, TypeError):
        return False


@dataclass(frozen=True)
class Variant:
    item_id: str
    mode: str
    kind: str
    prompt: str
    p: Fraction
    q: Fraction
    r: Fraction
    relation: str | None
    context_domain: str
    model: str
    answer: Fraction | None

    def public_payload(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "mode": self.mode,
            "kind": self.kind,
            "prompt": self.prompt,
            "response_fields": self.response_fields(),
        }

    def response_fields(self) -> list[str]:
        if self.kind == "CHOOSE_MODEL":
            return ["model_type", "symbolic_model", "context_justification"]
        if self.kind.startswith("EQUATION"):
            return [
                "symbolic_model",
                "solution",
                "inverse_steps",
                "substitution_check",
                "context_interpretation",
            ]
        if self.kind.startswith("INEQUALITY"):
            return [
                "symbolic_model",
                "boundary",
                "solution_relation",
                "endpoint",
                "graph_direction",
                "witness",
                "counterexample",
                "context_interpretation",
            ]
        return [
            "original_expression",
            "equivalent_expression",
            "property_justification",
            "context_meaning",
        ]

    def teacher_oracle(self) -> dict[str, object]:
        if self.kind == "CHOOSE_MODEL":
            return {
                "model_type": "INEQUALITY" if self.relation else "EQUATION",
                "symbolic_model": self.model,
            }
        if self.kind.startswith("EQUATION"):
            assert self.answer is not None
            return {
                "symbolic_model": self.model,
                "solution": _fmt(self.answer),
                "substitution_check": True,
            }
        if self.kind.startswith("INEQUALITY"):
            assert self.answer is not None and self.relation is not None
            solution_relation = self.relation if self.p > 0 else _flip(self.relation)
            endpoint = "CLOSED" if "=" in solution_relation else "OPEN"
            direction = "RIGHT" if solution_relation in (">", ">=") else "LEFT"
            witness = self.answer + (1 if direction == "RIGHT" else -1)
            counterexample = self.answer - (1 if direction == "RIGHT" else -1)
            if self.context_domain == "NONNEGATIVE_WHOLE_NUMBERS":
                witness = max(Fraction(0), witness)
                counterexample = max(Fraction(0), counterexample)
            return {
                "symbolic_model": self.model,
                "boundary": _fmt(self.answer),
                "solution_relation": solution_relation,
                "endpoint": endpoint,
                "graph_direction": direction,
                "witness": _fmt(witness),
                "counterexample": _fmt(counterexample),
            }
        # Expression equivalence uses p(x+q) = px + pq.
        return {
            "symbolic_model": self.model,
            "equivalent_expression": f"{_fmt(self.p)}x + {_fmt(self.p * self.q)}",
            "property": "DISTRIBUTIVE_PROPERTY",
        }

    def satisfies_inequality(self, x: Fraction) -> bool:
        if not self.kind.startswith("INEQUALITY") or self.relation is None:
            raise ValueError("Not an inequality variant")
        if self.kind == "INEQUALITY_PX_PLUS_Q":
            lhs = self.p * x + self.q
        else:
            lhs = self.p * (x + self.q)
        return _holds(lhs, self.relation, self.r)


def generate(seed: int, mode: str) -> Variant:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("mode must be guided or independent")

    rng = Random(f"{NAMESPACE}:{mode}:{seed}")
    kind = KINDS[seed % len(KINDS)]

    # Guided and independent namespaces intentionally use disjoint solution bands.
    solution = Fraction(rng.randint(2, 10) if mode == "guided" else rng.randint(12, 24), 1)
    p = Fraction(rng.choice((2, 3, 4, 5, 6)), rng.choice((1, 1, 1, 2)))
    q = Fraction(rng.randint(1, 9), rng.choice((1, 1, 2)))
    relation = rng.choice(("<", "<=", ">", ">="))
    domain = "NONNEGATIVE_WHOLE_NUMBERS"

    if kind == "EQUATION_PX_PLUS_Q":
        r = p * solution + q
        model = f"{_fmt(p)}x + {_fmt(q)} = {_fmt(r)}"
        prompt = (
            f"A service charges a fixed {_fmt(q)} dollars plus {_fmt(p)} dollars "
            f"per unit. The total is {_fmt(r)} dollars. Write an equation of the "
            "form px+q=r, solve it using inverse operations, and verify by substitution."
        )
        rel = None
        ans = solution
    elif kind == "EQUATION_P_TIMES_X_PLUS_Q":
        r = p * (solution + q)
        model = f"{_fmt(p)}(x + {_fmt(q)}) = {_fmt(r)}"
        prompt = (
            f"Each of {_fmt(p)} identical groups contains x items plus an extra "
            f"{_fmt(q)} items. Altogether there are {_fmt(r)} items. Write and solve "
            "p(x+q)=r, then connect each algebraic step to the context."
        )
        rel = None
        ans = solution
    elif kind == "INEQUALITY_PX_PLUS_Q":
        r = p * solution + q
        model = f"{_fmt(p)}x + {_fmt(q)} {relation} {_fmt(r)}"
        wording = {"<":"less than","<=":"no more than",">":"more than",">=":"at least"}[relation]
        prompt = (
            f"A club cost is {_fmt(q)} dollars plus {_fmt(p)} dollars per visit. "
            f"For which nonnegative whole-number visit counts is the cost {wording} "
            f"{_fmt(r)} dollars? Write the inequality, solve it, graph the solution set, "
            "and interpret which counts are reasonable."
        )
        rel = relation
        ans = solution
    elif kind == "INEQUALITY_P_TIMES_X_PLUS_Q":
        r = p * (solution + q)
        model = f"{_fmt(p)}(x + {_fmt(q)}) {relation} {_fmt(r)}"
        wording = {"<":"below","<=":"at most",">":"above",">=":"at least"}[relation]
        prompt = (
            f"A package has {_fmt(p)} equal sections, each containing x regular units "
            f"and {_fmt(q)} reserved units. The total must be {wording} {_fmt(r)} units. "
            "Model with p(x+q), solve, graph, and explain the feasible whole-number values."
        )
        rel = relation
        ans = solution
    elif kind == "EXPRESSION_EQUIVALENCE":
        r = Fraction(0)
        model = f"{_fmt(p)}(x + {_fmt(q)})"
        prompt = (
            f"Rewrite {_fmt(p)}(x + {_fmt(q)}) in an equivalent expanded form. "
            "Name the property used and explain what both forms mean in a context "
            "with equal groups."
        )
        rel = None
        ans = None
    else:
        # C.7: distinguish equality (exact total) from inequality (constraint).
        is_ineq = (seed // len(KINDS)) % 2 == 0
        r = p * solution + q
        if is_ineq:
            model = f"{_fmt(p)}x + {_fmt(q)} >= {_fmt(r)}"
            prompt = (
                f"A fundraiser earns {_fmt(p)} dollars per item after a fixed "
                f"{_fmt(q)}-dollar starting amount and needs at least {_fmt(r)} dollars. "
                "Should this be modeled by an equation or inequality? Write the model "
                "and justify your choice from the phrase 'at least'."
            )
            rel = ">="
        else:
            model = f"{_fmt(p)}x + {_fmt(q)} = {_fmt(r)}"
            prompt = (
                f"A fundraiser earns {_fmt(p)} dollars per item after a fixed "
                f"{_fmt(q)}-dollar starting amount and finished with exactly {_fmt(r)} dollars. "
                "Should this be modeled by an equation or inequality? Write the model "
                "and justify your choice from the phrase 'exactly'."
            )
            rel = None
        ans = None

    return Variant(
        item_id=f"{NAMESPACE}:{mode}:{seed}:{kind.lower()}",
        mode=mode,
        kind=kind,
        prompt=prompt,
        p=p,
        q=q,
        r=r,
        relation=rel,
        context_domain=domain,
        model=model,
        answer=ans,
    )


def diagnose_guided(variant: Variant, response: Mapping[str, object]) -> str:
    if variant.mode != "guided":
        raise ValueError("Diagnosis is guided-only")
    required = variant.response_fields()
    if not all(key in response for key in required):
        return "INCOMPLETE_GUIDED_EVIDENCE"

    oracle = variant.teacher_oracle()

    if variant.kind == "CHOOSE_MODEL":
        if response["model_type"] != oracle["model_type"]:
            return "MD7.EQ_VS_INEQ_CONTEXT_SIGNAL"
        if not _mathematically_equivalent(
            response["symbolic_model"], str(oracle["symbolic_model"])
        ):
            return "MD7.MODEL_TRANSLATION"
        if not str(response["context_justification"]).strip():
            return "MD7.CONTEXT_JUSTIFICATION_MISSING"
        return "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"

    if variant.kind.startswith("EQUATION"):
        if response["symbolic_model"] != oracle["symbolic_model"]:
            return "MD7.MODEL_TRANSLATION"
        if not _exact_number_matches(response["solution"], oracle["solution"]):
            return "MD7.INVERSE_OPERATION_OR_ARITHMETIC"
        if response["substitution_check"] is not True:
            return "MD7.SUBSTITUTION_CHECK_MISSING"
        if not str(response["inverse_steps"]).strip():
            return "MD7.INVERSE_STEPS_UNEXPLAINED"
        if not str(response["context_interpretation"]).strip():
            return "MD7.CONTEXT_INTERPRETATION_MISSING"
        return "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"

    if variant.kind.startswith("INEQUALITY"):
        if response["symbolic_model"] != oracle["symbolic_model"]:
            return "MD7.MODEL_TRANSLATION"
        if not _exact_number_matches(response["boundary"], oracle["boundary"]):
            return "MD7.INEQUALITY_BOUNDARY_ERROR"
        if response["solution_relation"] != oracle["solution_relation"]:
            return "MD7.INEQUALITY_DIRECTION_ERROR"
        if response["endpoint"] != oracle["endpoint"]:
            return "MD7.STRICT_VS_INCLUSIVE_ENDPOINT"
        if response["graph_direction"] != oracle["graph_direction"]:
            return "MD7.GRAPH_DIRECTION_ERROR"
        try:
            witness = Fraction(str(response["witness"]))
            counterexample = Fraction(str(response["counterexample"]))
        except (ValueError, ZeroDivisionError):
            return "MD7.WITNESS_COUNTEREXAMPLE_INVALID"
        if not variant.satisfies_inequality(witness) or variant.satisfies_inequality(counterexample):
            return "MD7.WITNESS_COUNTEREXAMPLE_INVALID"
        if not str(response["context_interpretation"]).strip():
            return "MD7.CONTEXT_INTERPRETATION_MISSING"
        return "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"

    if not _mathematically_equivalent(
        response["equivalent_expression"], str(oracle["equivalent_expression"])
    ):
        return "MD7.DISTRIBUTIVE_STRUCTURE_ERROR"
    if response["property_justification"] != oracle["property"]:
        return "MD7.PROPERTY_JUSTIFICATION"
    if not str(response["context_meaning"]).strip():
        return "MD7.CONTEXT_INTERPRETATION_MISSING"
    return "GUIDED_STRUCTURED_MATCH_REASONING_UNREVIEWED"
