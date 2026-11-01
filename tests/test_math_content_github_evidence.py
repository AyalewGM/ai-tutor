"""Mocked GitHub API evidence; no network, student records or release side effects."""
from __future__ import annotations

import io
import json
from contextlib import contextmanager

import pytest

from scripts.math_content_github_evidence import fetch_evidence

SHA = "a" * 40
REPO = "AyalewGM/ai-tutor"


@contextmanager
def _stream(data: object):
    yield io.BytesIO(json.dumps(data).encode())


def fixture_api(*, status: str = "completed", conclusion: str = "success",
                head: str = SHA, repository: str = REPO):
    def fetch(request, timeout=15):
        assert request.get_method() == "GET"
        assert request.full_url.startswith("https://api.github.com/repos/AyalewGM/ai-tutor/")
        if "/pulls/" in request.full_url:
            return _stream({"head": {"sha": head},
                            "base": {"repo": {"full_name": repository}}})
        if "/actions/runs" in request.full_url:
            return _stream({"workflow_runs": [
                {"id": 99, "head_sha": head, "name": "CI", "event": "pull_request",
                 "status": status, "conclusion": conclusion,
                 "run_started_at": "2026-10-21T23:00:00Z"}
            ]})
        raise AssertionError("unknown API request")
    return fetch


def test_successful_ci_is_not_independent_review() -> None:
    result = fetch_evidence(484, token="synthetic", fetch=fixture_api())
    assert result["content_sha"] == SHA
    assert result["ci"]["status"] == "success"
    assert result["specialist_reviews"] == "PENDING_INDEPENDENT_ATTESTATION"
    assert result["release_authority"] == "NONE"
    for gate in ("math", "pedagogy", "standards", "assessment", "frontend", "muse"):
        assert gate not in result


@pytest.mark.parametrize(("status", "conclusion"), [
    ("queued", None), ("in_progress", None), ("completed", "failure"),
    ("completed", "cancelled"),
])
def test_no_ci_success_from_incomplete_failed_or_cancelled(status, conclusion) -> None:
    result = fetch_evidence(
        484, token="synthetic",
        fetch=fixture_api(status=status, conclusion=conclusion),
    )
    assert result["ci"]["status"] == "NOT_VERIFIED"


def test_untrusted_repository_or_invalid_sha_fails_closed() -> None:
    with pytest.raises(ValueError):
        fetch_evidence(484, token="synthetic",
                       fetch=fixture_api(repository="someone/fork"))
    with pytest.raises(ValueError):
        fetch_evidence(484, token="synthetic", fetch=fixture_api(head="bad"))


@pytest.mark.parametrize("number", [0, -1, True, "484", 1_000_001])
def test_invalid_pr_number_fails_closed(number) -> None:
    with pytest.raises(ValueError):
        fetch_evidence(number, token="synthetic", fetch=fixture_api())


def test_missing_token_not_allowed() -> None:
    with pytest.raises(ValueError):
        fetch_evidence(484, token="", fetch=fixture_api())
