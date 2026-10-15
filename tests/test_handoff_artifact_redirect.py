"""Regression for GitHub artifact 302 redirects to SAS-signed blob storage."""
import importlib.util
from pathlib import Path
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mihur_handoff", ROOT / "scripts" / "agent_handoff_orchestrator.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size):
        assert size > 0
        return b"zip-content"


def test_artifact_redirect_strips_bearer_on_cross_host(monkeypatch):
    seen = {}

    class _Opener:
        def open(self, request, timeout):
            assert timeout == 30
            assert request.get_header("Authorization") == "Bearer secret"
            handler = seen["handler"]
            moved = handler.redirect_request(
                request, None, 302, "Found", {},
                "https://example.blob.core.windows.net/a.zip?sig=redacted",
            )
            assert moved.get_header("Authorization") is None
            assert moved.full_url.endswith("sig=redacted")
            return _Response()

    def make_opener(handler):
        seen["handler"] = handler
        return _Opener()

    monkeypatch.setattr(module, "build_opener", make_opener)
    assert module.artifact_bytes("https://api.github.com/artifacts/1/zip", "secret") == b"zip-content"


def test_artifact_redirect_preserves_bearer_within_same_host(monkeypatch):
    seen = {}

    class _Opener:
        def open(self, request, timeout):
            moved = seen["handler"].redirect_request(
                request, None, 302, "Found", {},
                "https://api.github.com/artifacts/other",
            )
            assert moved.get_header("Authorization") == "Bearer secret"
            return _Response()

    def make_opener(handler):
        seen["handler"] = handler
        return _Opener()

    monkeypatch.setattr(module, "build_opener", make_opener)
    assert module.artifact_bytes("https://api.github.com/artifacts/1/zip", "secret") == b"zip-content"
