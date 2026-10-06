import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class EvaluationResult:
    correct: bool
    confidence: float
    normalized_answer: str
    misconception_code: str | None = None
    misconception_confidence: float | None = None


@dataclass(frozen=True)
class MisconceptionMatch:
    code: str
    confidence: float


MisconceptionRule = Callable[[str, str, str], MisconceptionMatch | None]


def _normalize(expression: str) -> str:
    return re.sub(r"\s+", "", expression.lower())


_DISTRIBUTION_PROMPT = re.compile(r"(-?\d+)\(x([+-]\d+)\)")


def _partial_distribution(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    match = _DISTRIBUTION_PROMPT.search(prompt)
    if not match:
        return None
    multiplier = int(match.group(1))
    constant = int(match.group(2))
    incorrect_fragment = f"{multiplier}x{constant:+d}"
    correct_fragment = f"{multiplier}x{multiplier * constant:+d}"
    if incorrect_fragment in answer and correct_fragment not in answer:
        return MisconceptionMatch("DIST_001", 0.97)
    return None


def _distribution_sign_error(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    match = _DISTRIBUTION_PROMPT.search(prompt)
    if not match:
        return None
    multiplier = int(match.group(1))
    constant = int(match.group(2))
    correct_fragment = f"{multiplier}x{multiplier * constant:+d}"
    wrong_sign_fragment = f"{multiplier}x{-multiplier * constant:+d}"
    if wrong_sign_fragment in answer and correct_fragment not in answer:
        return MisconceptionMatch("DIST_002", 0.95)
    return None


_SIMPLE_EQUATION = re.compile(r"x([+-]\d+)=(-?\d+)")
_LINEAR_EQUATION = re.compile(r"(-?\d+)x([+-]\d+)=(-?\d+)")


def _inverse_direction(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    simple = _SIMPLE_EQUATION.search(prompt)
    if simple and not _LINEAR_EQUATION.search(prompt):
        addend = int(simple.group(1))
        rhs = int(simple.group(2))
        if answer in {f"x={rhs + addend}", f"x={addend - rhs}"}:
            return MisconceptionMatch("EQ_001", 0.90)
        return None

    linear = _LINEAR_EQUATION.search(prompt)
    if linear:
        coefficient = int(linear.group(1))
        constant = int(linear.group(2))
        rhs = int(linear.group(3))
        wrong_direction = rhs + constant
        if wrong_direction % coefficient == 0 and answer == f"x={wrong_direction // coefficient}":
            return MisconceptionMatch("EQ_001", 0.90)
    return None


def _skipped_inverse_step(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    linear = _LINEAR_EQUATION.search(prompt)
    if not linear:
        return None
    coefficient = int(linear.group(1))
    constant = int(linear.group(2))
    rhs = int(linear.group(3))
    if abs(coefficient) <= 1:
        return None
    if answer == f"x={rhs - constant}":
        return MisconceptionMatch("EQ_002", 0.95)
    if rhs % coefficient == 0 and answer == f"x={rhs // coefficient - constant}":
        return MisconceptionMatch("EQ_002", 0.85)
    return None


_SLOPE_INTERCEPT_PROMPT = re.compile(r"slope(-?\d+)andy-intercept(-?\d+)")
_LINE_EQUATION = re.compile(r"y=(-?\d+)x([+-]\d+)")


def _slope_intercept_swap(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    given = _SLOPE_INTERCEPT_PROMPT.search(prompt)
    if not given:
        return None
    slope = int(given.group(1))
    intercept = int(given.group(2))
    swapped = f"y={intercept}x{slope:+d}"
    if _LINE_EQUATION.fullmatch(answer) and answer == swapped:
        return MisconceptionMatch("REL_001", 0.90)
    return None


_LIKE_TERMS_PROMPT = re.compile(r"simplify(-?\d+)x([+-]\d+)([+-]\d*)x([+-]\d+)")


def _signed_coefficient(text: str) -> int:
    return int(text + "1") if len(text) == 1 else int(text)


def _unlike_terms_combined(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    match = _LIKE_TERMS_PROMPT.search(prompt)
    if not match:
        return None
    coefficient = int(match.group(1)) + _signed_coefficient(match.group(3))
    merged = coefficient + int(match.group(2)) + int(match.group(4))
    if answer == f"{merged}x":
        return MisconceptionMatch("ALG_001", 0.85)
    return None


def _constant_sign_error(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    match = _LIKE_TERMS_PROMPT.search(prompt)
    if not match:
        return None
    coefficient = int(match.group(1)) + _signed_coefficient(match.group(3))
    first_constant = int(match.group(2))
    second_constant = int(match.group(4))
    wrong_constant = first_constant - second_constant
    if wrong_constant != first_constant + second_constant and answer == (
        f"{coefficient}x{wrong_constant:+d}"
    ):
        return MisconceptionMatch("ALG_002", 0.85)
    return None


_PURE_COEFFICIENT_EQUATION = re.compile(r"(-?\d+)x=(-?\d+)")


def _multiply_instead_of_divide(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    if _SIMPLE_EQUATION.search(prompt) or _LINEAR_EQUATION.search(prompt):
        return None
    match = _PURE_COEFFICIENT_EQUATION.search(prompt)
    if not match:
        return None
    coefficient = int(match.group(1))
    rhs = int(match.group(2))
    if abs(coefficient) <= 1 or rhs == 0:
        return None
    if answer == f"x={coefficient * rhs}":
        return MisconceptionMatch("EQ_003", 0.90)
    return None


_FRACTION_ADD_PROMPT = re.compile(r"evaluate(-?\d+)/(-?\d+)\+(-?\d+)/(-?\d+)")


def _fraction_adds_across(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    match = _FRACTION_ADD_PROMPT.search(prompt)
    if not match:
        return None
    numerator = int(match.group(1)) + int(match.group(3))
    denominator = int(match.group(2)) + int(match.group(4))
    if answer == f"{numerator}/{denominator}":
        return MisconceptionMatch("NUM_003", 0.90)
    return None


_EVALUATE_LINE_PROMPT = re.compile(r"fory=(-?\d+)x([+-]\d+).*?x=(-?\d+)")


def _coefficient_added_not_multiplied(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    match = _EVALUATE_LINE_PROMPT.search(prompt)
    if not match:
        return None
    slope = int(match.group(1))
    intercept = int(match.group(2))
    value_at = int(match.group(3))
    if answer == str(slope + value_at + intercept):
        return MisconceptionMatch("REL_002", 0.85)
    return None


def _numeric_answer(answer: str) -> float | None:
    try:
        return float(answer)
    except ValueError:
        return None


_PERCENT_OF_PROMPT = re.compile(r"(\d+)%of(\d+)")
_DISCOUNT_PROMPT = re.compile(r"\$(\d+(?:\.\d+)?)\D+?discountedby(\d+)%")
_TAX_PROMPT = re.compile(r"\$(\d+(?:\.\d+)?)\D+?has(\d+)%tax")
_FINAL_PRICE_PROMPT = re.compile(r"saleprice|finalprice|pricebeforetax|totalcost")


def _percent_scaling_error(prompt: str, answer: str, _canonical: str) -> MisconceptionMatch | None:
    value = _numeric_answer(answer)
    if value is None:
        return None
    match = _PERCENT_OF_PROMPT.search(prompt)
    if match:
        percent, amount = float(match.group(1)), float(match.group(2))
    else:
        match = _DISCOUNT_PROMPT.search(prompt) or _TAX_PROMPT.search(prompt)
        if not match:
            return None
        amount, percent = float(match.group(1)), float(match.group(2))
    if value in {amount * percent, amount - percent, amount + percent}:
        return MisconceptionMatch("FIN_001", 0.85)
    return None


def _discount_amount_not_price(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    if not _FINAL_PRICE_PROMPT.search(prompt):
        return None
    match = _DISCOUNT_PROMPT.search(prompt)
    if not match:
        return None
    value = _numeric_answer(answer)
    if value is None:
        return None
    amount, percent = float(match.group(1)), float(match.group(2))
    if value == amount * percent / 100:
        return MisconceptionMatch("FIN_002", 0.90)
    return None


_INTEGER_ADD_PROMPT = re.compile(r"evaluate(-?\d+)\+(-?\d+)")


def _integer_sign_flip(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    match = _INTEGER_ADD_PROMPT.search(prompt)
    if not match:
        return None
    correct = int(match.group(1)) + int(match.group(2))
    if str(correct) != canonical:
        return None
    if answer == str(-correct):
        return MisconceptionMatch("NUM_001", 0.85)
    return None


def _integer_magnitude(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    match = _INTEGER_ADD_PROMPT.search(prompt)
    if not match:
        return None
    a = int(match.group(1))
    b = int(match.group(2))
    correct = a + b
    if str(correct) != canonical:
        return None
    magnitude_sum = abs(a) + abs(b)
    if answer == str(magnitude_sum):
        return MisconceptionMatch("NUM_002", 0.85)
    if answer == str(-magnitude_sum):
        return MisconceptionMatch("NUM_001", 0.85)
    return None


_ELEMENTARY_EQUAL_GROUPS = re.compile(r"(\d+)groupsof(\d+)", re.IGNORECASE)
_ELEMENTARY_COUNTERS = re.compile(r"(\d+)counterssharedequallyamong(\d+)groups", re.IGNORECASE)
_ELEMENTARY_RECTANGLE = re.compile(r"length(\d+)unitsandwidth(\d+)units", re.IGNORECASE)
_ELEMENTARY_COORDINATE = re.compile(r"(\d+)unitsrightand(\d+)unitsup", re.IGNORECASE)


def _elementary_equal_groups_adds(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    match = _ELEMENTARY_EQUAL_GROUPS.search(prompt)
    if not match:
        return None
    a = int(match.group(1))
    b = int(match.group(2))
    if answer == str(a + b):
        return MisconceptionMatch("MULT_ADDS_NOT_GROUPS", 0.95)
    return None


def _elementary_equal_sharing_reverse(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    match = _ELEMENTARY_COUNTERS.search(prompt)
    if not match:
        return None
    total = int(match.group(1))
    groups = int(match.group(2))
    if groups == 0:
        return None
    if answer == str(groups) and str(total // groups) != str(groups):
        return MisconceptionMatch("DIV_SMALLER_FROM_LARGER", 0.85)
    return None


def _elementary_area_perimeter_swap(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    match = _ELEMENTARY_RECTANGLE.search(prompt)
    if not match:
        return None
    length = int(match.group(1))
    width = int(match.group(2))
    area = length * width
    perimeter = 2 * (length + width)
    prompt_lower = prompt.lower()
    if "area" in prompt_lower and answer == str(perimeter) and str(area) != str(perimeter):
        return MisconceptionMatch("AREA_PERIMETER_SWAP", 0.95)
    if "perimeter" in prompt_lower and answer == str(area) and str(area) != str(perimeter):
        return MisconceptionMatch("AREA_PERIMETER_SWAP", 0.95)
    return None


def _elementary_coordinate_order_swap(
    prompt: str, answer: str, _canonical: str
) -> MisconceptionMatch | None:
    match = _ELEMENTARY_COORDINATE.search(prompt)
    if not match:
        return None
    x = int(match.group(1))
    y = int(match.group(2))
    if answer == f"({y},{x})" or answer == f"{y},{x}":
        return MisconceptionMatch("COORDINATE_ORDER_SWAP", 0.95)
    return None


_ORDERED_PAIR = re.compile(r"^\(?(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\)?$")


def _ordered_pairs_equal(answer: str, canonical: str) -> bool:
    """'(3, 4)', '(3,4)' and '3,4' are the same point."""
    a = _ORDERED_PAIR.match(answer)
    c = _ORDERED_PAIR.match(canonical)
    return bool(a and c and a.groups() == c.groups())


def _normalized_fraction(text: str) -> tuple[int, int] | None:
    """Parse to a reduced (num, den) with den > 0 so sign/inversion compare cleanly."""
    value = _fraction_value(text)
    if value is None:
        return None
    num, den = value
    if den < 0:
        num, den = -num, -den
    common = math.gcd(abs(num), den)
    return num // common, den // common


def _graph_slope_sign_flip(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    if "slopeoftheline" not in prompt:
        return None
    student = _normalized_fraction(answer)
    correct = _normalized_fraction(canonical)
    if student is None or correct is None or correct[0] == 0:
        return None
    num, den = correct
    if student == (-num, den):
        return MisconceptionMatch("GR_002", 0.95)
    if student == _normalized_fraction(f"{den}/{num}") or student == _normalized_fraction(
        f"{-den}/{num}"
    ):
        return MisconceptionMatch("GR_001", 0.95)
    return None


def _graph_vertex_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Vertex reads: (h,k) answered as (-h,k) is a sign slip, as (k,h) a swap."""
    if "vertexoftheparabola" not in prompt:
        return None
    student = _ORDERED_PAIR.match(answer)
    correct = _ORDERED_PAIR.match(canonical)
    if not student or not correct:
        return None
    sx, sy = student.groups()
    cx, cy = correct.groups()
    if (sx, sy) == (cy, cx):
        return MisconceptionMatch("QUAD_003", 0.95)
    if sx != cx and float(sx) == -float(cx):
        return MisconceptionMatch("QUAD_001", 0.95)
    return None


def _solid_pyramid_forgot_third(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Volume of a pyramid answered as base·height — the ⅓ was dropped."""
    if "pyramid" not in prompt or "volume" not in prompt:
        return None
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct or correct.group(1) == "0":
        return None
    if int(student.group(1)) == int(correct.group(1)) * 3:
        return MisconceptionMatch("SOLID_001", 0.95)
    return None


def _geo_angle_relationship_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Complementary/supplementary swaps, triangle sums off by 180, and
    linear-pair prompts answered with the equal (vertical) angle."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, c = int(student.group(1)), int(correct.group(1))
    if "complementary" in prompt and s == c + 90:
        return MisconceptionMatch("GEO_002", 0.95)
    if "supplementary" in prompt and s == c - 90:
        return MisconceptionMatch("GEO_002", 0.95)
    if "triangle" in prompt and s == c + 180:
        return MisconceptionMatch("GEO_003", 0.95)
    if "linearpair" in prompt and s == 180 - c:
        return MisconceptionMatch("GEO_004", 0.95)
    return None


_TRANSLATE_VECTORS = re.compile(r"(\d+)units(right|left)and(\d+)units(up|down)")
_SCALE_FACTOR = re.compile(r"scalefactorof(\d+)")


def _pair_ints(match: re.Match) -> tuple[int, int]:
    return int(float(match.group(1))), int(float(match.group(2)))


def _transformation_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Ordered-pair errors under transformations: wrong-coordinate
    reflection, wrong-direction or swapped-coordinate rotation, sign-flipped
    translation, and partially-applied dilation."""
    student = _ORDERED_PAIR.match(answer)
    correct = _ORDERED_PAIR.match(canonical)
    if not student or not correct:
        return None
    sx, sy = _pair_ints(student)
    cx, cy = _pair_ints(correct)
    if "reflect" in prompt and (sx, sy) == (-cx, -cy):
        # Answered the preimage — negated the coordinate the axis keeps.
        return MisconceptionMatch("TR_002", 0.95)
    if "rotate" in prompt and (sx, sy) in {
        (-cx, -cy), (cx, -cy), (-cx, cy), (cy, -cx), (-cy, cx)
    }:
        return MisconceptionMatch("TR_001", 0.95)
    if "translate" in prompt:
        vector = _TRANSLATE_VECTORS.search(prompt)
        if vector:
            dx = int(vector.group(1)) * (1 if vector.group(2) == "right" else -1)
            dy = int(vector.group(3)) * (1 if vector.group(4) == "up" else -1)
            if (sx, sy) in {
                (cx - 2 * dx, cy), (cx, cy - 2 * dy), (cx - 2 * dx, cy - 2 * dy)
            }:
                return MisconceptionMatch("TR_003", 0.95)
    if "dilate" in prompt:
        factor = _SCALE_FACTOR.search(prompt)
        if factor:
            k = int(factor.group(1))
            if k and cx % k == 0 and cy % k == 0:
                px, py = cx // k, cy // k
                if (sx, sy) in {(cx, py), (px, cy), (px + k, py + k)}:
                    return MisconceptionMatch("TR_005", 0.95)
    return None


def _system_intersection_swap(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Answered a system's solution with the coordinates swapped."""
    if "system" not in prompt and "intersect" not in prompt:
        return None
    student = _ORDERED_PAIR.match(answer)
    correct = _ORDERED_PAIR.match(canonical)
    if not student or not correct:
        return None
    sx, sy = _pair_ints(student)
    cx, cy = _pair_ints(correct)
    if (sx, sy) == (cy, cx) and cx != cy:
        return MisconceptionMatch("SYS_001", 0.95)
    return None


_BEST_FIT_EQ = re.compile(r"y=(-?\d*)x([+-]\d+)")
_PREDICT_X = re.compile(r"whenx=(-?\d+)")


def _best_fit_prediction_errors(
    prompt: str, answer: str, canonical: str
) -> MisconceptionMatch | None:
    """Predicting from y = mx + b with the intercept dropped (mx) or
    sign-flipped (mx − b)."""
    if "lineofbestfit" not in prompt:
        return None
    equation = _BEST_FIT_EQ.search(prompt)
    target = _PREDICT_X.search(prompt)
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not (equation and target and student and correct):
        return None
    m_text = equation.group(1)
    m = int(m_text) if m_text not in ("", "-") else (1 if m_text == "" else -1)
    b = int(equation.group(2))
    x = int(target.group(1))
    s = int(student.group(1))
    if s != int(correct.group(1)) and s in {m * x, m * x - b}:
        return MisconceptionMatch("STAT_004", 0.95)
    return None


_EXP_EVAL = re.compile(r"f\(x\)=(\d+)·\(?(\d+)(?:/(\d+))?\)?\^x")
_EXP_INPUT = re.compile(r"whatisf\((-?\d+)\)\?")
_EXP_SEQUENCE = re.compile(r"continues:(-?[\d,]+)\.")


def _exponential_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Exponential errors: (a·b)^x product-first evaluation, a + bx linear
    treatment, and arithmetic extrapolation of a geometric pattern."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s = int(student.group(1))
    sequence = _EXP_SEQUENCE.search(prompt)
    if sequence:
        terms = [int(t) for t in sequence.group(1).split(",") if t]
        if len(terms) >= 2 and s == terms[-1] + (terms[-1] - terms[-2]):
            return MisconceptionMatch("EXP_002", 0.95)
        return None
    equation = _EXP_EVAL.search(prompt)
    target = _EXP_INPUT.search(prompt)
    if not equation or not target:
        return None
    a = int(equation.group(1))
    b = Fraction(
        int(equation.group(2)),
        int(equation.group(3)) if equation.group(3) else 1,
    )
    x = int(target.group(1))
    if Fraction(s) == (a * b) ** x:
        return MisconceptionMatch("EXP_003", 0.95)
    if s in {a + int(b) * x, a * int(b) * x} and b.denominator == 1:
        return MisconceptionMatch("EXP_004", 0.95)
    return None


_PYTH_LEGS = re.compile(r"legsoflength(\d+)and(\d+)")
_PYTH_LEG = re.compile(r"hypotenuseoflength(\d+)andonelegoflength(\d+)")
_PYTH_DIST = re.compile(
    r"distancebetweenpointa\((-?\d+),(-?\d+)\)andpointb\((-?\d+),(-?\d+)\)"
)


def _pythagorean_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Pythagorean errors: legs added (a + b) or the sum of squares
    reported without taking the root (a² + b²); same two errors for a
    missing leg (c + a, c² ± a²) and for grid distance (|dx| + |dy|,
    dx² + dy²)."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, t = int(student.group(1)), int(correct.group(1))
    if s == t:
        return None
    legs = _PYTH_LEGS.search(prompt)
    if legs:
        a, b = int(legs.group(1)), int(legs.group(2))
        if s == a + b:
            return MisconceptionMatch("PYTH_002", 0.95)
        if s == a * a + b * b:
            return MisconceptionMatch("PYTH_001", 0.95)
        return None
    leg = _PYTH_LEG.search(prompt)
    if leg:
        c, a = int(leg.group(1)), int(leg.group(2))
        if s in {c + a, c * c + a * a}:
            return MisconceptionMatch("PYTH_002", 0.95)
        if s == c * c - a * a:
            return MisconceptionMatch("PYTH_001", 0.95)
        return None
    dist = _PYTH_DIST.search(prompt)
    if dist:
        dx = abs(int(dist.group(3)) - int(dist.group(1)))
        dy = abs(int(dist.group(4)) - int(dist.group(2)))
        if s == dx + dy:
            return MisconceptionMatch("PYTH_002", 0.95)
        if s == dx * dx + dy * dy:
            return MisconceptionMatch("PYTH_001", 0.95)
    return None


_RADICAL_BOUND = re.compile(
    r"√(\d+)liesbetweentwoconsecutivewholenumbers"
)


def _radical_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Radical estimation errors on the free-text bounding tier: halving
    the radicand (√n ≈ n/2) or answering the larger bound when the
    smaller was asked."""
    bound = _RADICAL_BOUND.search(prompt)
    if bound is None:
        return None
    n = int(bound.group(1))
    if answer == str(n // 2):
        return MisconceptionMatch("RAD_001", 0.9)
    if answer == str(math.isqrt(n) + 1):
        return MisconceptionMatch("RAD_002", 0.9)
    return None


_FUNC_PAIRS = re.compile(r"\((-?\d+),(-?\d+)\)")


def _function_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Rate-of-change errors on table prompts: y ÷ x on a single pair or
    Δx/Δy inverted (FUNC_004), or the y-intercept reported instead of
    the rate (FUNC_002)."""
    if "rateofchange" not in prompt:
        return None
    pairs = _FUNC_PAIRS.findall(prompt)
    if len(pairs) < 2:
        return None
    x1, y1 = int(pairs[0][0]), int(pairs[0][1])
    x2, y2 = int(pairs[1][0]), int(pairs[1][1])
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 or dy % dx != 0:
        return None
    m, b = dy // dx, y1 - dy // dx * x1
    if b != m and answer == str(b):
        return MisconceptionMatch("FUNC_002", 0.9)
    if x1 != 0 and y1 % x1 == 0 and y1 // x1 != m and answer == str(y1 // x1):
        return MisconceptionMatch("FUNC_004", 0.9)
    if dy != 0 and dx % dy == 0 and answer == str(dx // dy):
        return MisconceptionMatch("FUNC_004", 0.9)
    return None


def _proportional_errors(prompt: str, answer: str, canonical: str) -> MisconceptionMatch | None:
    """Constant-of-proportionality errors on table prompts: k reported
    inverted as x ÷ y (PROP_002) or found additively as y − x
    (PROP_003)."""
    if "constantofproportionality" not in prompt:
        return None
    pairs = _FUNC_PAIRS.findall(prompt)
    if len(pairs) < 2:
        return None
    x1, y1 = int(pairs[0][0]), int(pairs[0][1])
    if x1 == 0:
        return None
    student = _normalized_fraction(answer)
    if student is None:
        return None
    inverted = _normalized_fraction(f"{x1}/{y1}")
    if inverted is not None and student == inverted:
        return MisconceptionMatch("PROP_002", 0.9)
    if answer == str(y1 - x1):
        return MisconceptionMatch("PROP_003", 0.9)
    return None


_SIGNED_ADD = re.compile(r"evaluate(-?\d+)\+\(?(-?\d+)\)?\.")
_SIGNED_SUB = re.compile(r"evaluate(-?\d+)-\(?(-?\d+)\)?\.")
_SIGNED_MUL = re.compile(r"evaluate\(?(-?\d+)\)?×\(?(-?\d+)\)?\.")
_SIGNED_DIV = re.compile(r"evaluate\(?(-?\d+)\)?÷\(?(-?\d+)\)?\.")
_SIGNED_INVERSE = re.compile(r"addedto(-?\d+)gives0")
_SIGNED_DISTANCE = re.compile(
    r"pointpisat(-?\d+)andpointqisat(-?\d+)")
_SIGNED_TEMP = re.compile(
    r"temperaturewas(-?\d+)degreesand(rose|fell)by(\d+)degrees")
_SIGNED_ELEVATION = re.compile(
    r"elevationof(-?\d+)feetand(dove|climbed)(\d+)feet")


def _signed_number_errors(
    prompt: str, answer: str, canonical: str
) -> MisconceptionMatch | None:
    """Signed-arithmetic errors: a − (−b) treated as a − b (NEG_001),
    the sign rule missed on × and ÷ (NEG_002), magnitudes added while
    keeping a sign (NEG_003), and the additive inverse or a signed
    distance reported with the wrong sign (NEG_004)."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, t = int(student.group(1)), int(correct.group(1))
    if s == t:
        return None
    add = _SIGNED_ADD.search(prompt)
    if add:
        a, b = int(add.group(1)), int(add.group(2))
        if s in {-(abs(a) + abs(b)), abs(a) + abs(b)} and s != a + b:
            return MisconceptionMatch("NEG_003", 0.9)
        if s == a - b and s != a + b:
            return MisconceptionMatch("NEG_001", 0.9)
        return None
    sub = _SIGNED_SUB.search(prompt)
    if sub:
        a, b = int(sub.group(1)), int(sub.group(2))
        if b < 0 and s == a + b:
            return MisconceptionMatch("NEG_001", 0.95)
        if b > 0 and s == a + b:
            return MisconceptionMatch("NEG_001", 0.9)
        return None
    mul = _SIGNED_MUL.search(prompt)
    if mul:
        a, b = int(mul.group(1)), int(mul.group(2))
        if s == -a * b:
            return MisconceptionMatch("NEG_002", 0.95)
        return None
    div = _SIGNED_DIV.search(prompt)
    if div:
        a, b = int(div.group(1)), int(div.group(2))
        if b != 0 and s == -(a // b):
            return MisconceptionMatch("NEG_002", 0.95)
        return None
    inv = _SIGNED_INVERSE.search(prompt)
    if inv:
        a = int(inv.group(1))
        if s == a:
            return MisconceptionMatch("NEG_004", 0.95)
        return None
    dist = _SIGNED_DISTANCE.search(prompt)
    if dist:
        p, q = int(dist.group(1)), int(dist.group(2))
        if s in {p + q, -abs(q - p), abs(p) + abs(q)} and s != abs(q - p):
            return MisconceptionMatch("NEG_004", 0.9)
        return None
    temp = _SIGNED_TEMP.search(prompt)
    if temp:
        a, sign, b = int(temp.group(1)), temp.group(2), int(temp.group(3))
        moved = s - a
        if abs(moved) == b and moved != (b if sign == "rose" else -b):
            return MisconceptionMatch("NEG_003", 0.9)
        return None
    elev = _SIGNED_ELEVATION.search(prompt)
    if elev:
        a, sign, b = int(elev.group(1)), elev.group(2), int(elev.group(3))
        moved = s - a
        if abs(moved) == b and moved != (-b if sign == "dove" else b):
            return MisconceptionMatch("NEG_003", 0.9)
    return None


_MEAN_REVERSE = re.compile(
    r"themeanof(\d+)testscoresis(\d+)\.(\d+)ofthescoresare([\d,]+)\.")


def _center_spread_errors(
    prompt: str, answer: str, canonical: str
) -> MisconceptionMatch | None:
    """Missing-score errors: the mean restated, the total n·mean
    reported without subtracting the known scores, or the known
    scores re-averaged (STAT6_001)."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, t = int(student.group(1)), int(correct.group(1))
    if s == t:
        return None
    match = _MEAN_REVERSE.search(prompt)
    if not match:
        return None
    n, mean = int(match.group(1)), int(match.group(2))
    known = [int(v) for v in match.group(4).split(",")]
    reaveraged = round(sum(known) / len(known)) if known else None
    if s in {n * mean, mean, reaveraged}:
        return MisconceptionMatch("STAT6_001", 0.9)
    return None


_GEO_TRIANGLE = re.compile(
    r"atrianglehasabaseof(\d+)unitsandaheightof(\d+)units")
_GEO_PARALLELOGRAM = re.compile(
    r"aparallelogramhasabaseof(\d+)units,aslantsideof(\d+)units"
    r"andaheightof(\d+)units")
_GEO_TRAPEZOID = re.compile(
    r"atrapezoidhasbasesof(\d+)and(\d+)unitsandaheightof(\d+)units")
_GEO_DISTANCE = re.compile(
    r"whatisthedistancebetweenthepoints\((-?\d+),(-?\d+)\)"
    r"and\((-?\d+),(-?\d+)\)")
_GEO_PRISM = re.compile(
    r"arectangularprismis(\d+)unitslong,(\d+)unitswideand(\d+)unitstall\.")
_GEO_VOLUME = re.compile(r"whatisitsvolume")
_GEO_SURFACE = re.compile(r"whatisitssurfacearea")


def _geometry6_errors(
    prompt: str, answer: str, canonical: str
) -> MisconceptionMatch | None:
    """Grade-6 measurement errors: the halving or doubling step missed
    (GEO6_001), a perimeter or side sum reported for an area (GEO6_002),
    volume and surface area swapped (GEO6_003) and the wrong dimension or
    a miscounted axis distance used (GEO6_004)."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, t = int(student.group(1)), int(correct.group(1))
    if s == t:
        return None
    match = _GEO_TRIANGLE.search(prompt)
    if match:
        b, h = int(match.group(1)), int(match.group(2))
        if s == b * h:
            return MisconceptionMatch("GEO6_001", 0.9)
        if s in {b + h, 2 * (b + h)}:
            return MisconceptionMatch("GEO6_002", 0.9)
        return None
    match = _GEO_PARALLELOGRAM.search(prompt)
    if match:
        b, slant, h = (int(match.group(i)) for i in (1, 2, 3))
        if s in {2 * (b + slant), 2 * (b + h), b + h}:
            return MisconceptionMatch("GEO6_002", 0.9)
        if s == b * slant:
            return MisconceptionMatch("GEO6_004", 0.9)
        return None
    match = _GEO_TRAPEZOID.search(prompt)
    if match:
        top, b, h = (int(match.group(i)) for i in (1, 2, 3))
        if s == (b + top) * h:
            return MisconceptionMatch("GEO6_001", 0.9)
        if s == b + top + h:
            return MisconceptionMatch("GEO6_002", 0.9)
        if s == b * top:
            return MisconceptionMatch("GEO6_004", 0.9)
        return None
    match = _GEO_DISTANCE.search(prompt)
    if match:
        x1, y1, x2, y2 = (int(match.group(i)) for i in (1, 2, 3, 4))
        if x1 == x2:
            added, subtracted = abs(y1) + abs(y2), abs(abs(y1) - abs(y2))
        else:
            added, subtracted = abs(x1) + abs(x2), abs(abs(x1) - abs(x2))
        if s in {added, subtracted}:
            return MisconceptionMatch("GEO6_004", 0.9)
        return None
    match = _GEO_PRISM.search(prompt)
    if not match:
        return None
    l, w, h = (int(match.group(i)) for i in (1, 2, 3))
    faces = 2 * (l * w + l * h + w * h)
    if _GEO_VOLUME.search(prompt):
        if s == l + w + h:
            return MisconceptionMatch("GEO6_002", 0.9)
        if s in {faces, l * w}:
            return MisconceptionMatch("GEO6_003", 0.9)
        return None
    if _GEO_SURFACE.search(prompt):
        if s == l * w * h:
            return MisconceptionMatch("GEO6_003", 0.9)
        if s == faces // 2:
            return MisconceptionMatch("GEO6_001", 0.9)
        if s == l + w + h:
            return MisconceptionMatch("GEO6_002", 0.9)
    return None


_SEQ_NEXT = re.compile(r"whatisthenextterminthesequence(-?\d+(?:,-?\d+)+),\.\.\.")
_SEQ_DIFF = re.compile(r"whatisthecommondifferenceofthesequence(-?\d+(?:,-?\d+)+)")
_SEQ_RATIO = re.compile(r"whatisthecommonratioofthesequence(-?\d+(?:,-?\d+)+)")
_SEQ_NTH = re.compile(r"findthe(\d+)thtermofthesequence(-?\d+(?:,-?\d+)+)")


def _seq_list(text: str) -> list[int]:
    return [int(v) for v in text.split(",")]


def _sequence_errors(
    prompt: str, answer: str, canonical: str
) -> MisconceptionMatch | None:
    """Sequence errors: the index off by one in a(n) = a1 + (n-1)d or
    a1·r^(n-1) (SEQ_001), additive/multiplicative growth confused
    (SEQ_002), the common difference, ratio or first term reported as
    a term (SEQ_003) and the common difference's sign dropped
    (SEQ_004)."""
    student = _INTEGER_ANSWER.match(answer)
    correct = _INTEGER_ANSWER.match(canonical)
    if not student or not correct:
        return None
    s, t = int(student.group(1)), int(correct.group(1))
    if s == t:
        return None
    match = _SEQ_NEXT.search(prompt)
    if match:
        seq = _seq_list(match.group(1))
        a1, last = seq[0], seq[-1]
        if len(seq) > 1 and seq[1] != 0 and all(
                seq[i - 1] != 0 and seq[i] % seq[i - 1] == 0
                for i in range(1, len(seq))):
            r = seq[1] // seq[0]
            if a1 != 0 and all(seq[i] == a1 * r ** i for i in range(len(seq))):
                if s == last + r:
                    return MisconceptionMatch("SEQ_002", 0.9)
                if s in {r, a1}:
                    return MisconceptionMatch("SEQ_003", 0.9)
                if s == last * r * r:
                    return MisconceptionMatch("SEQ_001", 0.9)
                return None
        d = seq[1] - seq[0]
        if not all(seq[i] - seq[i - 1] == d for i in range(1, len(seq))):
            return None
        if s == last * d:
            return MisconceptionMatch("SEQ_002", 0.9)
        if s in {d, a1}:
            return MisconceptionMatch("SEQ_003", 0.9)
        if s == last + 2 * d:
            return MisconceptionMatch("SEQ_001", 0.9)
        return None
    match = _SEQ_DIFF.search(prompt)
    if match:
        seq = _seq_list(match.group(1))
        d = seq[1] - seq[0]
        if s == seq[0]:
            return MisconceptionMatch("SEQ_003", 0.9)
        if s == abs(d) and s != d:
            return MisconceptionMatch("SEQ_004", 0.9)
        return None
    match = _SEQ_RATIO.search(prompt)
    if match:
        seq = _seq_list(match.group(1))
        if s == seq[0]:
            return MisconceptionMatch("SEQ_003", 0.9)
        if s == seq[1] - seq[0]:
            return MisconceptionMatch("SEQ_002", 0.9)
        return None
    match = _SEQ_NTH.search(prompt)
    if not match:
        return None
    n, seq = int(match.group(1)), _seq_list(match.group(2))
    a1 = seq[0]
    if len(seq) > 1 and a1 != 0 and all(
            seq[i - 1] != 0 and seq[i] % seq[i - 1] == 0
            for i in range(1, len(seq))):
        r = seq[1] // a1
        if all(seq[i] == a1 * r ** i for i in range(len(seq))):
            if s in {a1 * r ** n, a1 * r ** max(n - 2, 0)}:
                return MisconceptionMatch("SEQ_001", 0.9)
            if s == a1 + (n - 1) * r:
                return MisconceptionMatch("SEQ_002", 0.9)
            if s in {r, a1}:
                return MisconceptionMatch("SEQ_003", 0.9)
            return None
    if len(seq) < 2:
        return None
    d = seq[1] - seq[0]
    if not all(seq[i] - seq[i - 1] == d for i in range(1, len(seq))):
        return None
    if s == a1 + n * d:
        return MisconceptionMatch("SEQ_001", 0.9)
    if s in {d, a1}:
        return MisconceptionMatch("SEQ_003", 0.9)
    return None


MISCONCEPTION_RULES: tuple[MisconceptionRule, ...] = (
    _partial_distribution,
    _distribution_sign_error,
    _unlike_terms_combined,
    _constant_sign_error,
    _inverse_direction,
    _skipped_inverse_step,
    _multiply_instead_of_divide,
    _slope_intercept_swap,
    _coefficient_added_not_multiplied,
    _integer_sign_flip,
    _integer_magnitude,
    _fraction_adds_across,
    _percent_scaling_error,
    _discount_amount_not_price,
    _elementary_equal_groups_adds,
    _elementary_equal_sharing_reverse,
    _elementary_area_perimeter_swap,
    _elementary_coordinate_order_swap,
    _graph_slope_sign_flip,
    _graph_vertex_errors,
    _solid_pyramid_forgot_third,
    _geo_angle_relationship_errors,
    _transformation_errors,
    _system_intersection_swap,
    _best_fit_prediction_errors,
    _exponential_errors,
    _pythagorean_errors,
    _radical_errors,
    _function_errors,
    _proportional_errors,
    _signed_number_errors,
    _center_spread_errors,
    _geometry6_errors,
    _sequence_errors,
)


_FRACTION_ANSWER = re.compile(r"^\s*(-?\d+)\s*/\s*(-?\d+)\s*$")
_INTEGER_ANSWER = re.compile(r"^\s*(-?\d+)\s*$")


def _fraction_value(answer: str) -> tuple[int, int] | None:
    """Parse 'a/b' (or a bare integer) into a rational; None if unparseable."""
    match = _FRACTION_ANSWER.match(answer)
    if match:
        numerator, denominator = int(match.group(1)), int(match.group(2))
        return None if denominator == 0 else (numerator, denominator)
    match = _INTEGER_ANSWER.match(answer)
    if match:
        return int(match.group(1)), 1
    return None


def _fractions_equal(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Deterministic equivalence: equivalent fractions count as correct."""
    return a[0] * b[1] == b[0] * a[1]


def _choice_misconception(choices: list | None, answer: str) -> MisconceptionMatch | None:
    """Map a wrong multiple-choice selection to its authored distractor code."""
    if not choices:
        return None
    normalized = _normalize(answer)
    for choice in choices:
        if _normalize(str(choice.get("id", ""))) == normalized:
            code = choice.get("misconception_code")
            if code:
                return MisconceptionMatch(code=code, confidence=0.9)
            return None
    return None


def _evaluate_typed(
    answer_kind: str,
    answer: str,
    canonical_answer: str,
    normalized: str,
) -> EvaluationResult | None:
    """Kind-aware grading; returns None to fall through to text/misconception rules."""
    if answer_kind == "MULTIPLE_CHOICE":
        return EvaluationResult(normalized == _normalize(canonical_answer), 0.99, normalized)
    if answer_kind == "FRACTION":
        student_value = _fraction_value(answer)
        canonical_value = _fraction_value(canonical_answer)
        if student_value is None or canonical_value is None:
            return None
        return EvaluationResult(
            _fractions_equal(student_value, canonical_value), 0.99, normalized
        )
    if answer_kind == "INTEGER":
        student_int = _INTEGER_ANSWER.match(answer)
        canonical_int = _INTEGER_ANSWER.match(canonical_answer)
        if student_int is None or canonical_int is None:
            return None
        return EvaluationResult(
            int(student_int.group(1)) == int(canonical_int.group(1)), 0.99, normalized
        )
    return None


def evaluate_problem(
    prompt: str,
    answer: str,
    canonical_answer: str,
    *,
    answer_kind: str = "FREE_TEXT",
    choices: list | None = None,
) -> EvaluationResult:
    normalized = _normalize(answer)
    canonical = _normalize(canonical_answer)
    normalized_prompt = _normalize(prompt)

    if normalized == canonical or _ordered_pairs_equal(normalized, canonical):
        return EvaluationResult(True, 0.99, normalized)

    typed = _evaluate_typed(answer_kind, answer, canonical_answer, normalized)
    if typed is not None and typed.correct:
        return typed

    if answer_kind == "MULTIPLE_CHOICE":
        distractor = _choice_misconception(choices, answer)
        return EvaluationResult(
            False,
            0.99 if distractor else 0.90,
            normalized,
            misconception_code=distractor.code if distractor else None,
            misconception_confidence=distractor.confidence if distractor else None,
        )

    for rule in MISCONCEPTION_RULES:
        match = rule(normalized_prompt, normalized, canonical)
        if match is not None:
            return EvaluationResult(
                False,
                0.99,
                normalized,
                misconception_code=match.code,
                misconception_confidence=match.confidence,
            )

    if typed is not None:
        return EvaluationResult(False, 0.90, normalized)

    return EvaluationResult(False, 0.90, normalized)


def evaluate_distributive_property(
    prompt: str,
    answer: str,
    canonical_answer: str,
    *,
    answer_kind: str = "FREE_TEXT",
    choices: list | None = None,
) -> EvaluationResult:
    return evaluate_problem(
        prompt, answer, canonical_answer, answer_kind=answer_kind, choices=choices
    )
