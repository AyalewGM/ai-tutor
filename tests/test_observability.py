"""Tests for F-026 structured observability logging."""

import json
import logging
from unittest.mock import MagicMock

from app.core.observability import _JsonFormatter, _route_template


def test_json_formatter_produces_valid_json() -> None:
    """Structured log records must be parseable JSON."""
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="ai_tutor.ops",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    record.method = "GET"
    record.route = "/api/v1/learners/{id}"
    record.status = 200
    record.latency_ms = 42
    record.service = "tutor-api"

    output = formatter.format(record)
    data = json.loads(output)
    assert data["request_id"] == "req-123"
    assert data["method"] == "GET"
    assert data["route"] == "/api/v1/learners/{id}"
    assert data["status"] == 200
    assert data["latency_ms"] == 42
    assert data["service"] == "tutor-api"


def test_json_formatter_minimal_record() -> None:
    """Formatter works with only the standard LogRecord fields."""
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="ai_tutor",
        level=logging.WARNING,
        pathname="test.py",
        lineno=1,
        msg="warning",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["level"] == "WARNING"
    assert "request_id" not in data


def test_route_template_uses_route_path() -> None:
    """Route template strips identifiers — never log raw paths with names."""
    request = MagicMock()
    route = MagicMock()
    route.path = "/api/v1/learners/{student_id}/skills"
    request.scope = {"route": route}
    assert _route_template(request) == "/api/v1/learners/{student_id}/skills"


def test_route_template_strips_query_string() -> None:
    """Query strings may contain identifiers; they must never be logged."""
    request = MagicMock()
    request.scope = {}
    request.url.path = "/api/v1/learners/abc-123/skills?token=secret"
    result = _route_template(request)
    assert "token" not in result
    assert "secret" not in result
    assert "?" not in result


def test_route_template_falls_back_to_path() -> None:
    """Unmatched routes fall back to the sanitized path."""
    request = MagicMock()
    request.scope = {}
    request.url.path = "/unknown/path"
    assert _route_template(request) == "/unknown/path"
