"""photo_ocr: OCR output is a suggestion — normalize conservatively, flag
anything the step checker can't grade, and never invent math content."""

from app.services.photo_ocr import (
    DisabledProvider,
    PhotoOcrUnavailable,
    StubProvider,
    parse_mathpix_response,
)


def _texts(result):
    return [line.text for line in result.lines]


def test_asciimath_lines_normalize_to_checkable_syntax() -> None:
    result = parse_mathpix_response(
        {
            "asciimath": "`3x+12=30`\n`3x=18`\n`x=6`",
            "confidence": 0.97,
        }
    )
    assert _texts(result) == ["3x+12=30", "3x=18", "x=6"]
    assert all(not line.needs_review for line in result.lines)
    assert result.engine == "mathpix"


def test_asciimath_operators_and_fractions_convert() -> None:
    result = parse_mathpix_response({"asciimath": "`3 xx x=18`", "confidence": 0.9})
    assert _texts(result) == ["3 * x=18"]

    frac = parse_mathpix_response({"text": "$\\frac{1}{2}+\\frac{1}{3}=\\frac{5}{6}$"})
    assert _texts(frac) == ["(1)/(2)+(1)/(3)=(5)/(6)"]


def test_caption_and_prose_lines_are_dropped() -> None:
    result = parse_mathpix_response(
        {"asciimath": "Homework page 3\n`2x+6=14`\nsolve it"}
    )
    assert _texts(result) == ["2x+6=14"]


def test_unsupported_constructs_flag_for_review_not_guess() -> None:
    result = parse_mathpix_response({"asciimath": "`x^2=9`\n`3x=18`"})
    flagged = [l for l in result.lines if l.needs_review]
    clean = [l for l in result.lines if not l.needs_review]
    # The exponent line can't be normalized — surfaced raw for the learner
    # to fix rather than silently mangled or misgraded.
    assert flagged and "x^2" in flagged[0].text
    assert _texts(result)[-1] == "3x=18" and not clean[0].needs_review


def test_low_confidence_marks_every_line_for_review() -> None:
    result = parse_mathpix_response({"asciimath": "`2x=8`", "confidence": 0.5})
    assert result.lines and all(l.needs_review for l in result.lines)


def test_empty_scan_yields_no_lines() -> None:
    assert parse_mathpix_response({"asciimath": "thanks!"}).lines == []
    assert parse_mathpix_response({}).lines == []


def test_stub_provider_returns_reviewable_lines() -> None:
    result = StubProvider().scan(b"fake", "image/png")
    assert result.engine == "stub" and len(result.lines) == 2


def test_disabled_provider_raises_unavailable() -> None:
    import pytest

    with pytest.raises(PhotoOcrUnavailable):
        DisabledProvider().scan(b"fake", "image/png")
