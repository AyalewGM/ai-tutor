"""Deterministic DRAFT variants for the Grade 9 gap-closure wave.

This module is test evidence only. It is not imported into runtime, exposes no
assessment endpoint, writes no learner data, and awards no mastery.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
NAMESPACE = "grade9-gap-closure-wave1"
MODES = frozenset({"guided", "independent"})
CONCEPTS = (
    "G9-ABS-EQUATIONS",
    "G9-TWO-VAR-INEQUALITIES",
    "G9-SYSTEMS-INEQUALITIES",
    "G9-LINEAR-OPTIMIZATION",
    "G9-LINEAR-EXP-INTERSECTION",
    "G9-DOMAIN-RANGE-NOTATION",
    "G9-INVERSE-LINEAR",
    "G9-PIECEWISE-ABS-FUNCTIONS",
    "G9-AVERAGE-RATE-CHANGE",
    "G9-SEQUENCES",
    "G9-FUNCTION-TRANSFORMATIONS",
    "G9-SLOPE-GEOMETRY",
    "G9-TRIANGLE-CONGRUENCE",
    "G9-RANDOM-SAMPLING",
    "G9-STAT-INVESTIGATION",
    "G9-BIVARIATE-MODELING",
    "G9-CORRELATION-CAUSATION",
    "G9-QUANTITY-PRECISION",
    "G9-FORMULA-REARRANGE",
    "G9-TWO-VAR-EQUATIONS",
)


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class Variant:
    concept_id: str
    mode: str
    seed: int
    item_id: str
    prompt: str
    public_fields: tuple[str, ...]
    oracle: dict[str, object]

    def public_payload(self) -> dict[str, object]:
        return {
            "concept_id": self.concept_id,
            "mode": self.mode,
            "item_id": self.item_id,
            "prompt": self.prompt,
            "response_fields": list(self.public_fields),
        }

    def teacher_oracle(self) -> dict[str, object]:
        return dict(self.oracle)


def _validate(concept_id: str, seed: int, mode: str) -> None:
    if concept_id not in CONCEPTS:
        raise ValueError("unknown concept_id")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("mode must be guided or independent")


def generate(concept_id: str, seed: int, mode: str) -> Variant:
    _validate(concept_id, seed, mode)
    rng = Random(f"{NAMESPACE}:{concept_id}:{mode}:{seed}")
    band = (2, 9) if mode == "guided" else (12, 24)
    n = rng.randint(*band)
    item_id = f"{NAMESPACE}:{concept_id}:{mode}:{seed}"

    if concept_id == "G9-ABS-EQUATIONS":
        a = rng.choice((2, 3, 4))
        b = rng.randint(-6, 6)
        k = a * n
        center = Fraction(-b, a)
        d = Fraction(k, a)
        roots = sorted((center - d, center + d))
        prompt = f"Solve |{a}x + ({b})| = {k}. Give the complete real solution set and verify both branches."
        oracle = {"solutions": [_fmt(x) for x in roots], "complete_set": True}
        fields = ("solutions", "branch_reasoning", "verification")

    elif concept_id == "G9-TWO-VAR-INEQUALITIES":
        m, b = rng.choice((1, 2, 3)), rng.randint(-5, 6)
        relation = rng.choice(("<", "<=", ">", ">="))
        x0 = rng.randint(-2, 3)
        boundary_y = m * x0 + b
        test_y = boundary_y + (1 if relation in (">", ">=") else -1)
        prompt = f"Graph y {relation} {m}x + {b}. State boundary type and use ({x0},{test_y}) as a test point."
        oracle = {
            "boundary": f"y={m}x+{b}",
            "boundary_style": "SOLID" if "=" in relation else "DASHED",
            "test_point_satisfies": True,
            "half_plane": "ABOVE" if relation in (">", ">=") else "BELOW",
        }
        fields = ("boundary", "boundary_style", "half_plane", "test_point_reasoning")

    elif concept_id == "G9-SYSTEMS-INEQUALITIES":
        a, c = rng.randint(2, 6), rng.randint(7, 12)
        prompt = f"A feasible point must satisfy x>=0, y>=0, x+y<={c}, and x>={a}. Explain the intersection and give one feasible and one infeasible point."
        oracle = {"sample_feasible": [a, 0], "sample_infeasible": [a - 1, 0], "intersection_semantics": "ALL_CONSTRAINTS"}
        fields = ("feasible_point", "infeasible_point", "intersection_explanation")

    elif concept_id == "G9-LINEAR-OPTIMIZATION":
        cap = rng.randint(8, 14)
        px, py = rng.randint(2, 6), rng.randint(2, 6)
        vertices = ((0, 0), (cap, 0), (0, cap))
        scored = [(px * x + py * y, x, y) for x, y in vertices]
        best = max(scored)
        prompt = f"Maximize P={px}x+{py}y subject to x>=0, y>=0, x+y<={cap}. Justify the optimum using feasible vertices."
        oracle = {"optimal_point": [best[1], best[2]], "optimal_value": best[0], "vertices": [list(v) for v in vertices]}
        fields = ("feasible_vertices", "objective_values", "optimal_point", "context_justification")

    elif concept_id == "G9-LINEAR-EXP-INTERSECTION":
        base = 2
        x = rng.randint(2, 4)
        y = base**x
        m = rng.choice((1, 2, 3))
        b = y - m * x
        prompt = f"Find and interpret an intersection of y={m}x+{b} and y={base}^x. Verify the point in both relations."
        oracle = {"intersection": [x, y], "verified": True}
        fields = ("intersection", "technology_or_reasoning", "verification", "context_interpretation")

    elif concept_id == "G9-DOMAIN-RANGE-NOTATION":
        m, b = rng.choice((2, 3, 4)), rng.randint(-5, 5)
        lo, hi = 0, rng.randint(5, 10)
        prompt = f"Let f(x)={m}x+{b} for whole-number inputs {lo} through {hi}. State the domain, range, and f({hi})."
        oracle = {
            "domain": list(range(lo, hi + 1)),
            "range": [m * x + b for x in range(lo, hi + 1)],
            "value": m * hi + b,
        }
        fields = ("domain", "range", "function_value", "context_domain_justification")

    elif concept_id == "G9-INVERSE-LINEAR":
        m, b = rng.choice((2, 3, 4)), rng.randint(-6, 6)
        prompt = f"For f(x)={m}x+{b}, find f^(-1)(x), state its domain/range relationship to f, and verify one composition."
        oracle = {"inverse": f"(x-{b})/{m}", "composition_identity": True, "input_output_swap": True}
        fields = ("inverse_rule", "composition_check", "units_interpretation")

    elif concept_id == "G9-PIECEWISE-ABS-FUNCTIONS":
        h, k = rng.randint(-4, 4), rng.randint(-3, 5)
        x = h + rng.choice((-3, -2, 2, 3))
        value = abs(x - h) + k
        prompt = f"For g(x)=|x-({h})|+{k}, evaluate g({x}), identify the vertex, and explain the graph as a distance transformation."
        oracle = {"value": value, "vertex": [h, k], "shape": "V", "distance_meaning": True}
        fields = ("value", "vertex", "shape", "transformation_explanation")

    elif concept_id == "G9-AVERAGE-RATE-CHANGE":
        x1 = rng.randint(0, 3)
        x2 = x1 + rng.randint(2, 5)
        a = rng.choice((1, 2, 3))
        f1, f2 = a * x1 * x1, a * x2 * x2
        rate = Fraction(f2 - f1, x2 - x1)
        prompt = f"For f(x)={a}x^2, find the average rate of change from x={x1} to x={x2} and interpret it."
        oracle = {"average_rate": _fmt(rate), "delta_y": f2 - f1, "delta_x": x2 - x1}
        fields = ("delta_y", "delta_x", "average_rate", "interpretation")

    elif concept_id == "G9-SEQUENCES":
        geometric = seed % 2 == 0
        a1 = rng.randint(2, 8)
        if geometric:
            r = rng.choice((2, 3, 4))
            term = a1 * r ** (n - 1)
            prompt = f"A geometric sequence starts at {a1} with ratio {r}. Give explicit and recursive rules and term {n}."
            oracle = {"type": "GEOMETRIC", "explicit": f"{a1}*{r}^(n-1)", "recursive": f"a_n={r}a_(n-1)", "term": term}
        else:
            d = rng.choice((2, 3, 4, 5))
            term = a1 + (n - 1) * d
            prompt = f"An arithmetic sequence starts at {a1} with difference {d}. Give explicit and recursive rules and term {n}."
            oracle = {"type": "ARITHMETIC", "explicit": f"{a1}+{d}(n-1)", "recursive": f"a_n=a_(n-1)+{d}", "term": term}
        fields = ("sequence_type", "explicit_rule", "recursive_rule", "requested_term")

    elif concept_id == "G9-FUNCTION-TRANSFORMATIONS":
        h, k = rng.randint(-4, 4), rng.randint(-4, 4)
        prompt = f"Starting with y=x^2, describe the transformation to y=(x-({h}))^2+({k}) and identify the new vertex."
        oracle = {"horizontal_shift": h, "vertical_shift": k, "vertex": [h, k]}
        fields = ("horizontal_shift", "vertical_shift", "vertex", "sign_explanation")

    elif concept_id == "G9-SLOPE-GEOMETRY":
        m = rng.choice((1, 2, 3, -1, -2))
        perp = Fraction(-1, m)
        prompt = f"A line has slope {m}. State slopes for a parallel line and a perpendicular line and justify each."
        oracle = {"parallel_slope": _fmt(Fraction(m)), "perpendicular_slope": _fmt(perp)}
        fields = ("parallel_slope", "perpendicular_slope", "geometric_justification")

    elif concept_id == "G9-TRIANGLE-CONGRUENCE":
        case = rng.choice(("SSS", "SAS", "ASA", "AAS", "HL", "AAA", "SSA"))
        valid = case in {"SSS", "SAS", "ASA", "AAS", "HL"}
        prompt = f"Two triangles are claimed congruent using {case}. Is this sufficient in the stated generic case? Explain correspondence and limits."
        oracle = {"criterion": case, "sufficient": valid}
        fields = ("sufficient", "criterion", "correspondence_explanation")

    elif concept_id == "G9-RANDOM-SAMPLING":
        case = rng.choice(("random_ids", "volunteers", "first_period", "every_10th_random_start"))
        representative = case in {"random_ids", "every_10th_random_start"}
        prompt = f"A school wants to estimate a population proportion. Sampling method: {case}. Evaluate representativeness and likely bias."
        oracle = {"reasonably_random": representative, "population_parameter_not_sample_statistic": True}
        fields = ("reasonably_random", "bias_explanation", "parameter_vs_statistic")

    elif concept_id == "G9-STAT-INVESTIGATION":
        contexts = (
            ("daily study time", "quiz score"),
            ("sleep duration", "morning reaction time"),
            ("weekly practice time", "free-throw percentage"),
            ("screen time", "reported sleep quality"),
        )
        x_var, y_var = rng.choice(contexts)
        prompt = (
            f"Design a study to investigate whether {x_var} is associated with {y_var}. "
            "State population, variables, sampling plan, limitations, and what causal claim "
            "is or is not justified."
        )
        oracle = {
            "two_variables": True,
            "explanatory_variable": x_var,
            "response_variable": y_var,
            "causal_claim_allowed_from_observational": False,
            "requires_sampling_plan": True,
        }
        fields = ("population", "variables", "sampling_plan", "bias_limits", "claim_limit")

    elif concept_id == "G9-BIVARIATE-MODELING":
        slope, intercept = rng.choice((2, 3, 4)), rng.randint(1, 8)
        x = n
        y = slope * x + intercept
        prompt = f"A fitted line is y={slope}x+{intercept}. Interpret slope and intercept with units, predict y at x={x}, and state one extrapolation caution."
        oracle = {"prediction": y, "slope": slope, "intercept": intercept, "extrapolation_caution": True}
        fields = ("slope_interpretation", "intercept_interpretation", "prediction", "fit_or_extrapolation_limit")

    elif concept_id == "G9-CORRELATION-CAUSATION":
        r = rng.choice((-0.9, -0.6, -0.2, 0.2, 0.6, 0.9))
        strength = "STRONG" if abs(r) >= 0.6 else "WEAK"
        direction = "POSITIVE" if r > 0 else "NEGATIVE"
        prompt = f"A study reports correlation r={r}. Describe direction and strength and explain whether causation follows."
        oracle = {"direction": direction, "strength": strength, "causation_established": False, "r_is_not_slope": True}
        fields = ("direction", "strength", "causation_claim", "coefficient_interpretation")

    elif concept_id == "G9-QUANTITY-PRECISION":
        measured = Fraction(rng.randint(100, 300), 10)
        prompt = f"A measured length is reported as {_fmt(measured)} cm to the nearest tenth. Explain suitable precision, units, and why extra unsupported digits would be false precision."
        oracle = {"unit": "cm", "reported_precision": "nearest_tenth", "false_precision_warning": True}
        fields = ("quantity", "unit", "precision", "scale_or_origin", "justification")

    elif concept_id == "G9-FORMULA-REARRANGE":
        # A = (b*h)/2 -> h = 2A/b
        b = rng.randint(2, 10)
        area = b * n
        h = Fraction(2 * area, b)
        prompt = f"Rearrange A=bh/2 to isolate h. Then evaluate h when A={area} and b={b}; state any restriction."
        oracle = {"isolated_formula": "h=2A/b", "value": _fmt(h), "restriction": "b!=0"}
        fields = ("isolated_formula", "equivalence_steps", "value", "restriction")

    elif concept_id == "G9-TWO-VAR-EQUATIONS":
        m, b = rng.choice((2, 3, -2)), rng.randint(-5, 5)
        x = rng.randint(-3, 4)
        y = m * x + b
        prompt = f"For y={m}x+{b}, verify whether ({x},{y}) is a solution and explain why the graph represents all solutions."
        oracle = {"point": [x, y], "satisfies": True, "graph_is_solution_set": True}
        fields = ("point_check", "graph_solution_set_explanation", "axis_units")

    else:
        raise AssertionError("unreachable concept")

    return Variant(concept_id, mode, seed, item_id, prompt, tuple(fields), oracle)
