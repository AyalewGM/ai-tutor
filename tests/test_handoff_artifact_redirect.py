"""Regression for GitHub artifact 302 redirects to SAS-signed blob storage."""
import importlib.util
from pathlib import Path

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
        seen["handler"] = handler()
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
        seen["handler"] = handler()
        return _Opener()

    monkeypatch.setattr(module, "build_opener", make_opener)
    assert module.artifact_bytes("https://api.github.com/artifacts/1/zip", "secret") == b"zip-content"


def test_artifact_rejects_untrusted_origin_before_sending_token(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Must not construct opener for untrusted URL")

    monkeypatch.setattr(module, "build_opener", forbidden)
    for url in (
        "https://attacker.example/repos/AyalewGM/ai-tutor/actions/artifacts/1/zip",
        "http://api.github.com/repos/AyalewGM/ai-tutor/actions/artifacts/1/zip",
        "https://api.github.com/repos/other/repo/actions/artifacts/1/zip",
    ):
        try:
            module.artifact_bytes(url, "secret")
        except ValueError:
            pass
        else:
            raise AssertionError(f"Untrusted URL accepted: {url}")


def test_artifact_redirect_rejects_http_downgrade(monkeypatch):
    seen = {}

    class _Opener:
        def open(self, request, timeout):
            try:
                seen["handler"].redirect_request(
                    request, None, 302, "Found", {},
                    "http://api.github.com/repos/AyalewGM/ai-tutor/actions/artifacts/1/zip",
                )
            except ValueError:
                return _Response()
            raise AssertionError("HTTP downgrade was accepted")

    def make_opener(handler):
        seen["handler"] = handler()
        return _Opener()

    monkeypatch.setattr(module, "build_opener", make_opener)
    assert module.artifact_bytes(
        "https://api.github.com/repos/AyalewGM/ai-tutor/actions/artifacts/1/zip",
        "secret",
    ) == b"zip-content"
