"""Phase 1: advisory, fail-closed, exact-head GitHub PR handoff routing.

Never executes PR code, grants approval, merges, or activates content.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REQUIRED = ("CI", "AppSec Baseline")
FAILURES = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
MARKER = "<!-- mihur-orchestrator-v2:"
MANUAL = "Engineering Lead (manual multi-lane triage)"
MAX_PAGES = 10


def lane(title: str, paths: list[str]) -> str:
    """Only an advisory hint: titles and paths are attacker-controlled."""
    words = (title + " " + " ".join(paths)).lower()
    standards = any(t in words for t in ("standards", "curriculum/standards"))
    assessment = any(t in words for t in ("assessment", "mastery", "scorer"))
    content = any(t in words for t in ("content", "learning", "mve"))
    if sum((standards, assessment, content)) > 1:
        return MANUAL
    if standards:
        return "Independent Standards Source-Fidelity Reviewer (suggested)"
    if assessment:
        return "Assessment Backend / Architecture (suggested)"
    if content:
        return "Independent Mathematical Review, then Pedagogy (suggested)"
    return MANUAL


def next_step(draft: bool, checks: dict[str, str], title: str, paths: list[str]) -> str:
    del title, paths
    if any(checks.get(name) in FAILURES for name in REQUIRED):
        return "AUTHOR_CORRECTION"
    if any(checks.get(name) != "success" for name in REQUIRED):
        return "WAIT_CHECKS"
    return "INDEPENDENT_REVIEW_DRAFT" if draft else "INDEPENDENT_REVIEW"


def marker(sha: str, state: str) -> str:
    return f"{MARKER}{sha}:{state} -->"


def select_checks(runs: list[dict], sha: str, branch: str) -> dict[str, str]:
    """Pick latest run and attempt; ambiguous or missing evidence stays pending."""
    selected: dict[str, dict] = {}
    for run in runs:
        name = run.get("name")
        if name not in REQUIRED or run.get("head_sha") != sha:
            continue
        if run.get("head_branch") != branch:
            continue
        current = selected.get(name)
        key = (run.get("created_at") or "", run.get("run_attempt") or 0, run.get("id") or 0)
        if current is None:
            selected[name] = run
            continue
        old_key = (
            current.get("created_at") or "",
            current.get("run_attempt") or 0,
            current.get("id") or 0,
        )
        if key > old_key:
            selected[name] = run
        elif key == old_key and run != current:
            selected[name] = {"conclusion": None, "status": "ambiguous"}
    return {
        name: (selected[name].get("conclusion") or "pending") if name in selected else "pending"
        for name in REQUIRED
    }


def event_pr_numbers(event: dict) -> list[int]:
    if "pull_request" in event:
        return [int(event["pull_request"]["number"])]
    linked = event.get("workflow_run", {}).get("pull_requests", [])
    return sorted({int(pr["number"]) for pr in linked})


def request(method: str, url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mihur-phase1-handoff",
        **({"Content-Type": "application/json"} if data is not None else {}),
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def pages(root: str, suffix: str, token: str) -> list[dict]:
    collected: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        sep = "&" if "?" in suffix else "?"
        batch = request("GET", f"{root}{suffix}{sep}{urlencode({'per_page': 100, 'page': page})}", token)
        if not isinstance(batch, list):
            raise TypeError("Unexpected paginated response")
        collected.extend(batch)
        if len(batch) < 100:
            return collected
    raise ValueError("Pagination limit reached; manual handoff required")


def checks_for(root: str, sha: str, branch: str, token: str) -> dict[str, str]:
    result = request(
        "GET", f"{root}/actions/runs?{urlencode({'head_sha': sha, 'per_page': 100})}", token
    )
    if result.get("total_count", 0) > 100 or len(result.get("workflow_runs", [])) >= 100:
        raise ValueError("Too many workflow runs: manual check required")
    return select_checks(result.get("workflow_runs", []), sha, branch)


def deliver(root: str, number: int, token: str) -> None:
    pr = request("GET", f"{root}/pulls/{number}", token)
    if pr["state"] != "open":
        return
    sha, branch = pr["head"]["sha"], pr["head"]["ref"]
    paths = [item["filename"] for item in pages(root, f"/pulls/{number}/files", token)]
    checks = checks_for(root, sha, branch, token)
    state = next_step(pr["draft"], checks, pr["title"], paths)
    tag = marker(sha, state)
    comments_url = f"/issues/{number}/comments"
    if any(tag in c.get("body", "") for c in pages(root, comments_url, token)):
        return

    # Re-read the authoritative head and checks immediately before writing.
    latest = request("GET", f"{root}/pulls/{number}", token)
    fresh_checks = checks_for(root, sha, branch, token)
    if latest["state"] != "open" or latest["head"]["sha"] != sha or fresh_checks != checks:
        print(f"PR #{number} changed during inspection; no handoff")
        return
    body = (
        f"{tag}\n### Mihur automated handoff — advisory only\n"
        f"- Exact head: `{sha}`\n- State: **{state}**\n"
        f"- CI: {checks['CI']}; AppSec: {checks['AppSec Baseline']}\n"
        f"- Suggested lane (untrusted title/path hints): **{lane(pr['title'], paths)}**\n"
        "- No independent approval, agent execution, merge, mastery, or activation is implied.\n"
        "- Reviewer must verify scope and independently post an exact-SHA verdict.\n"
    )
    # A single repository-wide concurrency group serializes all workflow dispatches.
    # Re-read on transient failures; retry once, never blindly duplicate a POST.
    for attempt in range(2):
        try:
            request("POST", f"{root}{comments_url}", token, {"body": body})
            print(f"Posted {state} for #{number} at {sha}")
            return
        except (HTTPError, URLError, OSError) as exc:
            try:
                if any(tag in c.get("body", "") for c in pages(root, comments_url, token)):
                    return
            except (HTTPError, URLError, OSError):
                # A lost POST response may mean delivery succeeded.
                # Never blindly retry if the reconciliation GET also fails.
                record_pending(number, sha, state, "COMMENT_STATUS_UNKNOWN")
                return
            if attempt:
                record_pending(number, sha, state, type(exc).__name__)
                return



def record_pending(number: int, sha: str, state: str, reason: str) -> None:
    """Persist unresolved delivery in a workflow artifact for manual reconciliation."""
    path = Path(os.environ.get("MIHUR_PENDING_FILE", "mihur-pending-handoffs.jsonl"))
    record = {"pr": number, "sha": sha, "state": state,
              "reason": reason, "delivery": "PENDING_MANUAL_RECONCILIATION"}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"::warning::PR #{number} handoff pending, not delivered: {reason}")

def main() -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event_file:
        event = json.load(event_file)
    numbers = event_pr_numbers(event)
    if not numbers:
        print("No linked PR; manual workflow-run association may be needed")
        return 0
    root = f"{os.environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/{repo}"
    for number in numbers:
        deliver(root, number, token)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
        print(f"Fail-closed; manual intervention required: {exc}", file=sys.stderr)
        sys.exit(1)
