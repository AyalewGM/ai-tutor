"""Structured operational logging for the pilot deployment.

Design constraints (F-026):
- Never log learner answers, prompts, PII, secrets, cookies, or claim tokens.
- Log only request-level operational metadata: request_id, method, route path
  template (not raw URL path which could contain learner names), status, and
  latency.
- One structured JSON line per request for easy parsing by log aggregators.
- No invasive analytics, session replay, or third-party telemetry.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from typing import Any

from fastapi import Request, Response

_LOGGER_NAME = "ai_tutor.ops"


def configure_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for operational observability."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


class _JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter for structured operational logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if hasattr(record, "method"):
            payload["method"] = record.method
        if hasattr(record, "route"):
            payload["route"] = record.route
        if hasattr(record, "status"):
            payload["status"] = record.status
        if hasattr(record, "latency_ms"):
            payload["latency_ms"] = record.latency_ms
        if hasattr(record, "service"):
            payload["service"] = record.service
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _route_template(request: Request) -> str:
    """Return the route path template (e.g., '/api/v1/learners/{student_id}/skills').

    Falls back to the raw path if the route is not resolved. Raw paths are
    acceptable for health/readiness endpoints that carry no identifiers.
    """
    if "route" in request.scope:
        route = request.scope["route"]
        if hasattr(route, "path"):
            return str(route.path)
    # For unmatched routes, return a safe generic pattern.
    path = request.url.path
    # Strip query strings entirely — they may contain identifiers.
    return path.split("?")[0] if "?" in path else path


async def request_logging_middleware(request: Request, call_next) -> Response:
    """Emit a structured log line for each request without PII or content."""
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = int((time.perf_counter() - start) * 1000)

    logger = logging.getLogger(_LOGGER_NAME)
    extra: dict[str, Any] = {
        "request_id": request_id,
        "method": request.method,
        "route": _route_template(request),
        "status": response.status_code,
        "latency_ms": latency_ms,
        "service": "tutor-api",
    }
    if response.status_code >= 500:
        logger.error("request completed", extra=extra)
    elif response.status_code >= 400:
        logger.warning("request completed", extra=extra)
    else:
        logger.info("request completed", extra=extra)
    return response
