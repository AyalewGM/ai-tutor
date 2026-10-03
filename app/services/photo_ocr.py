"""OCR of photographed handwritten work — suggestion only, never grading.

A photo of written work is scanned by an OCR provider and returned to the
learner as editable text lines. The learner confirms or corrects each line;
only confirmed lines flow through the deterministic step checker
(``app.services.stepwork``). OCR output is therefore never graded directly —
a misread cannot be recorded as a learner misconception.

Images are processed in memory and never persisted or logged.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.core.settings import settings

MATHPIX_URL = "https://api.mathpix.com/v3/text"

MAX_PHOTO_BYTES = 8 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Characters the step checker can actually parse. Anything else means the
# OCR read constructs our checker can't grade — flag for the learner to fix.
_CHECKABLE = re.compile(r"^[0-9a-zA-Z+\-*/().= ]+$")


class PhotoOcrError(Exception):
    """Provider returned an error or an unreadable result."""


class PhotoOcrUnavailable(PhotoOcrError):
    """No OCR provider is configured — the feature is off, not broken."""


@dataclass
class OcrLine:
    text: str
    needs_review: bool = False


@dataclass
class ScanResult:
    lines: list[OcrLine] = field(default_factory=list)
    engine: str = "none"


class PhotoOcrProvider(Protocol):
    def scan(self, image: bytes, content_type: str) -> ScanResult: ...


def _latex_to_line(text: str) -> str | None:
    """Best-effort conversion of an OCR math line to checkable syntax.

    Returns None when the line uses constructs the checker can't grade —
    the caller flags it for learner review instead of guessing.
    """
    s = text.strip()
    if not s:
        return None
    # Strip display/inline math wrappers Mathpix emits.
    s = s.replace("\\(", "").replace("\\)", "").replace("$", "").strip()
    # Common environments -> plain operators.
    s = s.replace("\\times", "*").replace("\\cdot", "*")
    s = s.replace("\\div", "/").replace("xx", "*").replace(":-", "/")
    s = s.replace("\\left", "").replace("\\right", "")
    # \frac{a}{b} and \dfrac -> (a)/(b); non-numeric/grouped args stay
    # parenthesized so precedence survives the rewrite.
    frac = re.compile(r"\\[dt]?frac\{([^{}]+)\}\{([^{}]+)\}")
    for _ in range(4):  # bounded nesting depth
        s = frac.sub(lambda m: f"({m.group(1)})/({m.group(2)})", s)
    # Remove stray braces left from \frac args or grouped exponent hints.
    s = s.replace("{", "").replace("}", "")
    if re.search(r"[\^\\_]|sqrt|\d[ ]\d", s):
        # Exponents, radicals, multi-digit spacing artifacts: don't guess.
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def _line_from_asciimath(text: str) -> str | None:
    """Normalize an ASCIIMath line (Mathpix `asciimath` format) to syntax."""
    s = text.strip()
    if not s or s.startswith("#"):
        return None
    s = s.replace("`", "")
    s = re.sub(r"\bfrac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = s.replace("xx", "*").replace("//", "/").replace("div", "/")
    s = s.replace("{", "").replace("}", "")
    if re.search(r"[\^\\]|sqrt", s):
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def _looks_like_work(text: str) -> bool:
    """A work line needs math content — an equals sign or an arithmetic op
    with digits — so captions like 'Homework p.3' don't become steps."""
    return "=" in text or bool(re.search(r"\d\s*[+\-*/]\s*[\dxX]", text))


def parse_mathpix_response(data: dict) -> ScanResult:
    """Turn a Mathpix /v3/text payload into reviewable lines."""
    lines: list[OcrLine] = []
    confidence = data.get("confidence", 1.0)
    low_confidence = isinstance(confidence, (int, float)) and confidence < 0.8
    raw_lines: list[str] = []
    for key in ("asciimath", "text"):
        raw = data.get(key)
        if isinstance(raw, str) and raw.strip():
            raw_lines = [ln for ln in raw.splitlines()]
            break
    for raw in raw_lines:
        text = _line_from_asciimath(raw) or _latex_to_line(raw)
        if text is None:
            stripped = raw.strip().strip("$`").strip()
            if stripped and _looks_like_work(stripped):
                lines.append(OcrLine(text=stripped, needs_review=True))
            continue
        if not _looks_like_work(text):
            continue
        lines.append(OcrLine(text=text, needs_review=low_confidence or not _CHECKABLE.match(text)))
    return ScanResult(lines=lines, engine="mathpix")


class MathpixProvider:
    """Handwritten-math OCR via Mathpix. Images are sent, read, discarded."""

    def __init__(self, app_id: str, app_key: str, timeout_seconds: float) -> None:
        self._headers = {
            "app_id": app_id,
            "app_key": app_key,
            "Content-type": "application/json",
        }
        self._timeout = timeout_seconds

    def scan(self, image: bytes, content_type: str) -> ScanResult:
        payload = {
            "src": f"data:{content_type};base64,{base64.b64encode(image).decode()}",
            "formats": ["asciimath", "text"],
            "metadata": {"improve_mathpix": False},
        }
        try:
            response = httpx.post(
                MATHPIX_URL, json=payload, headers=self._headers, timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PhotoOcrError("OCR service unavailable") from exc
        if isinstance(data.get("error"), str):
            raise PhotoOcrError(data["error"])
        return parse_mathpix_response(data)


class StubProvider:
    """Deterministic provider for local dev/tests without OCR keys.

    Returns a fixed two-line scan so the confirm-and-check flow can be
    exercised end-to-end; never enabled unless explicitly configured.
    """

    def scan(self, image: bytes, content_type: str) -> ScanResult:
        return ScanResult(
            lines=[
                OcrLine("3x + 12 = 30"),
                OcrLine("3x = 18", needs_review=True),
            ],
            engine="stub",
        )


class DisabledProvider:
    def scan(self, image: bytes, content_type: str) -> ScanResult:
        raise PhotoOcrUnavailable("Photo intake is not configured")


def get_ocr_provider() -> PhotoOcrProvider:
    """Pick the provider from settings; injectable via FastAPI Depends."""
    if settings.photo_ocr_provider == "stub":
        return StubProvider()
    if settings.mathpix_app_id and settings.mathpix_app_key:
        return MathpixProvider(
            settings.mathpix_app_id,
            settings.mathpix_app_key,
            settings.photo_ocr_timeout_seconds,
        )
    return DisabledProvider()
