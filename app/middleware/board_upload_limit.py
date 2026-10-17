"""Bound multipart bodies before FastAPI spools homework photo uploads."""

from fastapi import HTTPException
from starlette.responses import JSONResponse

MAX_MULTIPART_BYTES = 6 * 1024 * 1024


class BoardUploadLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if not (
            scope["type"] == "http"
            and scope.get("method") == "POST"
            and "/together/boards/" in path
            and path.endswith("/photos")
        ):
            return await self.app(scope, receive, send)
        size = 0

        async def limited_receive():
            nonlocal size
            message = await receive()
            size += len(message.get("body", b""))
            if size > MAX_MULTIPART_BYTES:
                raise HTTPException(413, "Photo request is too large")
            return message

        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            length = MAX_MULTIPART_BYTES + 1
        if length > MAX_MULTIPART_BYTES:
            return await JSONResponse({"detail": "Photo request is too large"}, status_code=413)(
                scope, receive, send
            )
        return await self.app(scope, limited_receive, send)
