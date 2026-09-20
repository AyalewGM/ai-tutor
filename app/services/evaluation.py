import re
from collections.abc import Callable
from dataclasses import dataclass


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
)


def evaluate_problem(prompt: str, answer: str, canonical_answer: str) -> EvaluationResult:
    normalized = _normalize(answer)
    canonical = _normalize(canonical_answer)
    normalized_prompt = _normalize(prompt)

    if normalized == canonical:
        return EvaluationResult(True, 0.99, normalized)

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

    return EvaluationResult(False, 0.90, normalized)


def evaluate_distributive_property(
    prompt: str,
    answer: str,
    canonical_answer: str,
) -> EvaluationResult:
    return evaluate_problem(prompt, answer, canonical_answer)
