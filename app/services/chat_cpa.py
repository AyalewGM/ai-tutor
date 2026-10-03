"""Sanitize LLM-emitted `json:cpa` blocks before they reach learners.

The gateway prompt allows the model to append one fenced CPA payload to a
tutor message. That payload is presentational — grading never reads it — but
it still reaches the learner's screen, so it gets the same treatment as any
untrusted content:

- malformed JSON or off-schema payloads are stripped (markup never leaks)
- at most one block survives (the frontend renders the first; extras are noise)
- a BALANCE_SCALE that renders the solved equation is stripped — the
  mirror-the-model rule says render the student's state, never the answer,
  and the application can actually check that deterministically against the
  canonical answer
"""

import json
import re
from typing import Any

_CPA_BLOCK = re.compile(
    r"```\s*json:cpa\s*([\s\S]*?)```|<cpa_visual>([\s\S]*?)</cpa_visual>",
    re.IGNORECASE,
)

_SOLVED_EQUATION = re.compile(r"^\s*([a-zA-Z])\s*=\s*(-?\d+(?:\.\d+)?)\s*$")
_BARE_VAR = re.compile(r"^\s*[a-zA-Z]\s*$")

# Payload fields render into style attributes and SVG text. React escapes
# markup, but values still get allowlist treatment — a stored message that
# predates validation must not be able to smuggle CSS or oversized content.
_SAFE_COLOR = re.compile(r"^[a-zA-Z0-9#-]{1,32}$")
_MAX_BARS = 8
_MAX_DENOMINATOR = 48
_MAX_PAN_VALUE = 1_000_000


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _safe_str(value: Any, max_len: int) -> bool:
    return isinstance(value, str) and len(value) <= max_len


def _safe_int(value: Any, lo: int, hi: int) -> bool:
    return (
        _is_number(value)
        and float(value).is_integer()
        and lo <= float(value) <= hi
    )


def _valid_fraction_bars(obj: dict) -> bool:
    bars = obj.get("fractionBars")
    if not isinstance(bars, list) or not bars or len(bars) > _MAX_BARS:
        return False
    for bar in bars:
        if not isinstance(bar, dict):
            return False
        if not _safe_int(bar.get("numerator"), 0, _MAX_DENOMINATOR):
            return False
        if not _safe_int(bar.get("denominator"), 1, _MAX_DENOMINATOR):
            return False
        if "label" in bar and not _safe_str(bar["label"], 40):
            return False
        color = bar.get("color")
        if color is not None and not _SAFE_COLOR.match(str(color)):
            return False
    return True


def _valid_balance_scale(obj: dict) -> bool:
    scale = obj.get("balanceScale")
    if not (
        isinstance(scale, dict)
        and _safe_str(scale.get("leftExpr"), 60)
        and _safe_str(scale.get("rightExpr"), 60)
    ):
        return False
    for key in ("leftValue", "rightValue"):
        value = scale.get(key)
        if value is not None and not (_is_number(value) and abs(value) <= _MAX_PAN_VALUE):
            return False
    return True


def _payload_reveals_answer(obj: dict, canonical_answer: str | None) -> bool:
    """True when a BALANCE_SCALE shows the isolated variable equaling the
    canonical value — the solved-equation form, in either a single pan
    ('x = 4' as one expr) or split across pans ('x' vs '4').

    Fraction bars legitimately display the simplified value (a '1/2' bar
    inside an equivalence visual is content, not a leaked answer), so only
    balance scales are checked.
    """
    if not canonical_answer or obj.get("type") != "BALANCE_SCALE":
        return False
    canonical = _SOLVED_EQUATION.match(canonical_answer.strip())
    if canonical is None:
        return False
    var, answer_value = canonical.group(1), canonical.group(2)
    scale = obj["balanceScale"]
    exprs = [str(scale.get(k) or "").strip() for k in ("leftExpr", "rightExpr")]
    for expr in exprs:
        match = _SOLVED_EQUATION.match(expr)
        if match and match.group(1) == var and match.group(2) == answer_value:
            return True
    bare_var = next((i for i, e in enumerate(exprs) if _BARE_VAR.match(e) and e.strip() == var), None)
    if bare_var is not None:
        other = exprs[1 - bare_var]
        if re.fullmatch(r"-?\d+(?:\.\d+)?", other) and other == answer_value:
            return True
    return False


def _valid_payload(raw: str, canonical_answer: str | None) -> bool:
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(obj, dict):
        return False
    kind = obj.get("type")
    if kind == "FRACTION_BARS":
        valid = _valid_fraction_bars(obj)
    elif kind == "BALANCE_SCALE":
        valid = _valid_balance_scale(obj)
    else:
        return False
    if not _safe_str(obj.get("title", ""), 80):
        return False
    return valid and not _payload_reveals_answer(obj, canonical_answer)


def text_reveals_answer(message: str, canonical_answer: str | None) -> bool:
    """True when message prose states the solved form (``x = 4``) of the
    canonical answer — the same leak the block validator bans, in plain text.

    Only equation-form canonicals are checked. A bare numeric canonical
    ("8") appears legitimately inside hints ("what is 8 divided by 2?"), so
    matching it would flag correct Socratic language.
    """
    if not canonical_answer:
        return False
    match = _SOLVED_EQUATION.match(canonical_answer.strip())
    if match is None:
        return False
    var, value = match.group(1), match.group(2)
    prose = _CPA_BLOCK.sub(" ", message)
    return (
        re.search(
            rf"(?<![\w]){re.escape(var)}\s*=\s*{re.escape(value)}(?![\d.])",
            prose,
        )
        is not None
    )


def sanitize_cpa_blocks(
    message: str, *, canonical_answer: str | None = None
) -> str:
    """Keep the first valid CPA block in ``message``; strip the rest.

    Mirrors the frontend parser: malformed blocks disappear entirely so the
    learner never sees markup, and only one visual survives per message.
    """
    matches = list(_CPA_BLOCK.finditer(message))
    if not matches:
        return message

    kept_index: int | None = None
    for i, match in enumerate(matches):
        raw = (match.group(1) or match.group(2) or "").strip()
        if _valid_payload(raw, canonical_answer):
            kept_index = i
            break

    cleaned = message
    for i in reversed(range(len(matches))):
        if i == kept_index:
            continue
        match = matches[i]
        cleaned = cleaned[: match.start()] + cleaned[match.end() :]
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()
