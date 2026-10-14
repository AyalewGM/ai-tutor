"""Fail-closed GitHub PR handoff coordinator (Phase 1: routing only).

No agent execution, approvals, merging, deployment, or activation.
Reads PR metadata and exact-head checks; writes idempotent handoff comments.
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MARKER = "<!-- mihur-orchestrator-v1:"
STANDARDS = ("standards", "curriculum/standards")
MATH = ("content", "learning", "assessment", "mve")
BLOCKED = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
PASS = "success"


def lane(title: str, paths: list[str]) -> str:
    words = (title + " " + " ".join(paths)).lower()
    if any(token in words for token in STANDARDS):
        return "Independent Standards Source-Fidelity Reviewer"
    if "assessment" in words or "mastery" in words:
        return "Assessment Backend / Architecture"
    if any(token in words for token in MATH):
        return "Independent Mathematical Review, then Pedagogical Review"
    return "Engineering Lead (scope triage)"


def next_step(draft: bool, checks: dict[str, str], title: str, paths: list[str]) -> str:
    required = ("CI", "AppSec Baseline")
    if any(checks.get(name) in BLOCKED for name in required):
        return "AUTHOR_CORRECTION"
    if any(checks.get(name) != PASS for name in required):
        return "WAIT_CHECKS"
    if draft:
        return "INDEPENDENT_REVIEW_DRAFT"
    return "INDEPENDENT_REVIEW"


def marker(sha: str, state: str) -> str:
    return f"{MARKER}{sha}:{state} -->"


def request(method: str, url: str, token: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mihur-phase1-handoff",
        **({"Content-Type": "application/json"} if body is not None else {}),
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def main() -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event_file:
        event = json.load(event_file)
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    if "pull_request" in event:
        number = event["pull_request"]["number"]
    elif event.get("workflow_run", {}).get("pull_requests"):
        number = event["workflow_run"]["pull_requests"][0]["number"]
    else:
        print("No linked PR; fail closed")
        return 0
    root = f"{api}/repos/{repo}"
    pr = request("GET", f"{root}/pulls/{number}", token)
    if pr["state"] != "open":
        return 0
    sha = pr["head"]["sha"]
    files = request("GET", f"{root}/pulls/{number}/files?per_page=100", token)
    if len(files) == 100:
        print("PR has >=100 changed files: manual triage")
        return 0
    runs = request("GET", f"{root}/actions/runs?head_sha={sha}&per_page=100", token)
    checks = {}
    for run in runs.get("workflow_runs", []):
        if run["name"] in ("CI", "AppSec Baseline"):
            checks[run["name"]] = run["conclusion"] or "pending"
    paths = [f["filename"] for f in files]
    state = next_step(pr["draft"], checks, pr["title"], paths)
    tag = marker(sha, state)
    comments = request("GET", f"{root}/issues/{number}/comments?per_page=100", token)
    if any(tag in comment.get("body", "") for comment in comments):
        print("Existing handoff for exact SHA/state; no-op")
        return 0
    if len(comments) == 100:
        print("Comment pagination required; avoid duplicate write")
        return 0
    body = (
        f"{tag}\n### Mihur automated handoff (routing only)\n"
        f"- Exact head: `{sha}`\n"
        f"- State: **{state}**\n"
        f"- CI: {checks.get('CI', 'unknown')}; AppSec: {checks.get('AppSec Baseline', 'unknown')}\n"
        f"- Suggested next lane: **{lane(pr['title'], paths)}**\n"
        "- This is a task handoff, **not** independent approval, agent execution, "
        "merge authorization, mastery credit, or activation.\n"
        "- Reviewers must inspect changed scope and post their own exact-SHA verdict. "
        "An author cannot approve their own changes.\n"
    )
    request("POST", f"{root}/issues/{number}/comments", token, {"body": body})
    print(f"Posted {state} for PR #{number} at {sha}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (HTTPError, OSError, ValueError, KeyError) as exc:
        print(f"Fail-closed orchestration error: {exc}", file=sys.stderr)
        sys.exit(1)
