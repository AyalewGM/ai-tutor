"""Safety, provenance and mocked GitHub event/API regression tests."""
from unittest.mock import patch

import pytest

from scripts import agent_handoff_orchestrator as orchestrator


def test_lane_is_advisory_and_mixed_scope_is_manual():
    assert "Standards" in orchestrator.lane("standards inventory", ["docs/curriculum/standards/md.json"])
    assert "Assessment" in orchestrator.lane("mastery gate", ["app/services/assessment.py"])
    assert orchestrator.lane("standards and assessment", ["app/services/assessment.py"]) == orchestrator.MANUAL


def test_checks_fail_closed():
    next_step = orchestrator.next_step
    assert next_step(False, {"CI": "success"}, "content", []) == "WAIT_CHECKS"
    assert next_step(False, {"CI": "failure", "AppSec Baseline": "success"}, "content", []) == "AUTHOR_CORRECTION"
    assert next_step(True, {"CI": "success", "AppSec Baseline": "success"}, "content", []) == "INDEPENDENT_REVIEW_DRAFT"


def test_marker_changes_with_sha_and_state():
    assert orchestrator.marker("abc", "WAIT_CHECKS") != orchestrator.marker("abc", "INDEPENDENT_REVIEW")
    assert orchestrator.marker("abc", "WAIT_CHECKS") != orchestrator.marker("def", "WAIT_CHECKS")


def _run(name, status, *, created, attempt=1, ident=1, branch="topic", sha="head"):
    return {
        "name": name, "conclusion": status, "head_sha": sha, "head_branch": branch,
        "created_at": created, "run_attempt": attempt, "id": ident,
    }


def test_latest_check_selection_is_deterministic():
    older = _run("CI", "success", created="2026-01-01T00:00:00Z")
    newer = _run("CI", "failure", created="2026-01-02T00:00:00Z", ident=2)
    appsec = _run("AppSec Baseline", "success", created="2026-01-02T00:00:00Z")
    assert orchestrator.select_checks([newer, older, appsec], "head", "topic")["CI"] == "failure"
    assert orchestrator.select_checks([older, newer, appsec], "head", "topic")["CI"] == "failure"
    newer["conclusion"] = "success"
    assert orchestrator.select_checks([newer, older], "head", "topic")["CI"] == "success"
    newer["conclusion"] = None
    assert orchestrator.select_checks([older, newer], "head", "topic")["CI"] == "pending"
    assert orchestrator.select_checks([older], "other-head", "topic")["CI"] == "pending"


def test_all_workflow_run_pr_associations_are_processed():
    event = {"workflow_run": {"pull_requests": [{"number": 18}, {"number": 12}, {"number": 18}]}}
    assert orchestrator.event_pr_numbers(event) == [12, 18]
    assert orchestrator.event_pr_numbers({"workflow_run": {"pull_requests": []}}) == []


def _pr(sha="head"):
    return {"state": "open", "head": {"sha": sha, "ref": "topic"},
            "draft": True, "title": "content package"}


def test_mocked_api_posts_once_and_does_not_execute_pr_code():
    posted = []
    calls = []

    def fake(method, url, token, payload=None):
        calls.append((method, url))
        if url.endswith("/pulls/17"):
            return _pr()
        if method == "POST":
            posted.append(payload["body"])
            return {"id": 5}
        raise AssertionError(url)

    def fake_pages(root, suffix, token):
        if "/files" in suffix:
            return [{"filename": "docs/curriculum/drafts/lesson.json"}]
        return [{"body": posted[0]}] if posted else []

    with (
        patch.object(orchestrator, "request", side_effect=fake),
        patch.object(orchestrator, "pages", side_effect=fake_pages),
        patch.object(orchestrator, "checks_for", return_value={"CI": "success", "AppSec Baseline": "success"}),
    ):
        orchestrator.deliver("https://api.github.com/repos/org/repo", 17, "token")
        orchestrator.deliver("https://api.github.com/repos/org/repo", 17, "token")
    assert len(posted) == 1
    assert all("contents" not in url for _, url in calls)
    assert "INDEPENDENT_REVIEW_DRAFT" in posted[0]


def test_changed_head_does_not_post():
    reads = iter([_pr(), _pr("changed")])
    posted = []

    def fake(method, url, token, payload=None):
        if url.endswith("/pulls/17"):
            return next(reads)
        if method == "POST":
            posted.append(payload)
        return {}

    with (
        patch.object(orchestrator, "request", side_effect=fake),
        patch.object(orchestrator, "pages", return_value=[]),
        patch.object(orchestrator, "checks_for", return_value={"CI": "success", "AppSec Baseline": "success"}),
    ):
        orchestrator.deliver("root", 17, "token")
    assert not posted


def test_pagination_limit_fails_closed():
    with patch.object(orchestrator, "request", return_value=[{"body": "other"}] * 100):
        with pytest.raises(ValueError, match="Pagination limit"):
            orchestrator.pages("root", "/issues/17/comments", "token")


def test_write_failure_reconciles_and_retries_once():
    posted = []
    calls = []

    def fake(method, url, token, payload=None):
        if url.endswith("/pulls/17"):
            return _pr()
        if method == "POST":
            calls.append(method)
            if len(calls) == 1:
                raise OSError("transient")
            posted.append(payload["body"])
            return {"id": 5}
        raise AssertionError(url)

    with (
        patch.object(orchestrator, "request", side_effect=fake),
        patch.object(orchestrator, "pages", return_value=[]),
        patch.object(orchestrator, "checks_for", return_value={"CI": "success", "AppSec Baseline": "success"}),
    ):
        orchestrator.deliver("root", 17, "token")
    assert len(calls) == 2
    assert len(posted) == 1
