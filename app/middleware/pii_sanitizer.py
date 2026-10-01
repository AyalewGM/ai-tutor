"""PII minimization for learner-authored text before application processing.

This is a defense-in-depth filter, not a claim of complete PII detection. It only
rewrites configured free-text JSON fields and never stores the original body.
"""

from __future__ import annotations

import json
import re
from typing import Any

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_TEXT_KEYS = {"prompt", "message", "answer", "student_answer", "text"}
_MAX_JSON_BODY_BYTES = 1_000_000

_EMAIL = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
_SSN = re.compile(r"(?<!\d)(?:\d{3}[- ]?\d{2}[- ]?\d{4})(?!\d)")
_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
)
_STREET_ADDRESS = re.compile(
    r"(?<!\w)\d{1,6}\s+[A-Z0-9][A-Z0-9.'-]*(?:\s+[A-Z0-9][A-Z0-9.'-]*){0,4}\s+"
    r"(?:STREET|ST|ROAD|RD|AVENUE|AVE|BOULEVARD|BLVD|DRIVE|DR|LANE|LN|COURT|CT|"
    r"CIRCLE|CIR|WAY|PLACE|PL)\b(?:\s*,?\s*[A-Z][A-Z .'-]+)?",
    re.I,
)
_EXPLICIT_FULL_NAME = re.compile(
    r"\b(?P<prefix>my\s+(?:full\s+)?name\s+is\s+)"
    r"(?P<name>[A-Z][A-Za-z'-]{1,30}\s+[A-Z][A-Za-z'-]{1,30}(?:\s+[A-Z][A-Za-z'-]{1,30})?)",
    re.I,
)


def sanitize_text(value: str) -> str:
    sanitized = _EMAIL.sub("[REDACTED_EMAIL]", value)
    sanitized = _PHONE.sub("[REDACTED_PHONE]", sanitized)
    sanitized = _SSN.sub("[REDACTED_GOV_ID]", sanitized)
    sanitized = _STREET_ADDRESS.sub("[REDACTED_ADDRESS]", sanitized)

    def _name_replacement(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}[REDACTED_NAME]"

    return _EXPLICIT_FULL_NAME.sub(_name_replacement, sanitized)


def sanitize_json_payload(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_json_payload(item, parent_key=str(key).lower())
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_json_payload(item, parent_key=parent_key) for item in value]
    if isinstance(value, str) and parent_key in _TEXT_KEYS:
        return sanitize_text(value)
    return value


class PIISanitizerMiddleware:
    """Sanitize learner free-text fields in JSON request bodies before routing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "")).upper()
        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }
        content_type = headers.get(b"content-type", b"").decode("latin-1").lower()
        if method not in {"POST", "PUT", "PATCH"} or "application/json" not in content_type:
            await self.app(scope, receive, send)
            return

        body = bytearray()
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if len(body) > _MAX_JSON_BODY_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "JSON request body is too large"},
                )
                await response(scope, receive, send)
                return
            more_body = bool(message.get("more_body", False))

        sanitized_body = bytes(body)
        try:
            payload = json.loads(body)
            sanitized = sanitize_json_payload(payload)
            sanitized_body = json.dumps(
                sanitized,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            # FastAPI will return its normal validation/parsing response.
            pass

        new_scope = dict(scope)
        new_headers = [
            (key, value)
            for key, value in scope.get("headers", [])
            if key.lower() != b"content-length"
        ]
        new_headers.append((b"content-length", str(len(sanitized_body)).encode("ascii")))
        new_scope["headers"] = new_headers
        await self.app(new_scope, _single_body_receive(sanitized_body), send)


def _single_body_receive(body: bytes) -> Receive:
    sent = False

    async def receive() -> Message:
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive
