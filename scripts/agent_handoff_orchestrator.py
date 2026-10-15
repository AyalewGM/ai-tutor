"""Phase 1: advisory, fail-closed, exact-head GitHub PR handoff routing.

Never executes PR code, grants approval, merges, or activates content.
"""
from __future__ import annotations

import io
import json
import os
import sys
import zipfile
from enum import StrEnum
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    urlopen,
)

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


class DeliveryOutcome(StrEnum):
    DELIVERED = "delivered"
    ALREADY_PRESENT = "already_present"
    OBSOLETE = "obsolete"
    DEFERRED = "deferred"
    PENDING = "pending"


def deliver(root: str, number: int, token: str) -> DeliveryOutcome:
    pr = request("GET", f"{root}/pulls/{number}", token)
    if pr["state"] != "open":
        return DeliveryOutcome.OBSOLETE
    sha, branch = pr["head"]["sha"], pr["head"]["ref"]
    paths = [item["filename"] for item in pages(root, f"/pulls/{number}/files", token)]
    checks = checks_for(root, sha, branch, token)
    state = next_step(pr["draft"], checks, pr["title"], paths)
    tag = marker(sha, state)
    comments_url = f"/issues/{number}/comments"
    if any(tag in c.get("body", "") for c in pages(root, comments_url, token)):
        return DeliveryOutcome.ALREADY_PRESENT

    # Re-read the authoritative head and checks immediately before writing.
    latest = request("GET", f"{root}/pulls/{number}", token)
    fresh_checks = checks_for(root, sha, branch, token)
    if (latest["state"] != "open" or latest["head"]["sha"] != sha or fresh_checks != checks
            or latest["head"]["ref"] != branch or latest["draft"] != pr["draft"]):
        record_pending(number, sha, state, "CHANGED_DURING_INSPECTION")
        return DeliveryOutcome.DEFERRED
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
        if attempt:
            latest = request("GET", f"{root}/pulls/{number}", token)
            if (latest["state"] != "open" or latest["head"]["sha"] != sha
                    or latest["head"]["ref"] != branch or latest["draft"] != pr["draft"]
                    or checks_for(root, sha, branch, token) != checks):
                record_pending(number, sha, state, "CHANGED_BEFORE_RETRY")
                return DeliveryOutcome.DEFERRED
        try:
            request("POST", f"{root}{comments_url}", token, {"body": body})
            print(f"Posted {state} for #{number} at {sha}")
            return DeliveryOutcome.DELIVERED
        except (HTTPError, URLError, OSError) as exc:
            try:
                if any(tag in c.get("body", "") for c in pages(root, comments_url, token)):
                    return DeliveryOutcome.ALREADY_PRESENT
            except (HTTPError, URLError, OSError):
                # A lost POST response may mean delivery succeeded.
                # Never blindly retry if the reconciliation GET also fails.
                record_pending(number, sha, state, "COMMENT_STATUS_UNKNOWN")
                return DeliveryOutcome.PENDING
            if attempt:
                record_pending(number, sha, state, type(exc).__name__)
                return DeliveryOutcome.PENDING



def record_pending(number: int, sha: str, state: str, reason: str) -> None:
    """Persist unresolved delivery in a workflow artifact for manual reconciliation."""
    path = Path(os.environ.get("MIHUR_PENDING_FILE", "mihur-pending-handoffs.jsonl"))
    record = {"pr": number, "sha": sha, "state": state,
              "reason": reason, "delivery": "PENDING_MANUAL_RECONCILIATION"}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"::warning::PR #{number} handoff pending, not delivered: {reason}")


def artifact_bytes(url: str, token: str) -> bytes:
    # The token must only be sent to the configured GitHub API's artifact endpoint.
    api = urlsplit(os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    source = urlsplit(url)
    repo = os.environ.get("GITHUB_REPOSITORY", "AyalewGM/ai-tutor")
    prefix = f"{api.path.rstrip('/')}/repos/{repo}/actions/artifacts/"
    if (source.scheme != "https" or api.scheme != "https"
            or source.netloc != api.netloc or source.username is not None
            or source.password is not None
            or not source.path.startswith(prefix)
            or not source.path[len(prefix):].split("/")[:1][0].isdigit()
            or not source.path.endswith("/zip")):
        raise ValueError("Untrusted GitHub artifact archive URL")
    # archive_download_url redirects to Azure Blob Storage. urllib forwards
    # the Authorization header across the redirect, and Azure rejects requests
    # carrying both SAS credentials and an auth header (HTTP 401 "Server
    # failed to authenticate"). Strip the header on redirect to other hosts.
    class _StripAuthOnCrossHostRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urlsplit(newurl).scheme != "https":
                raise ValueError("Insecure artifact redirect")
            new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
            if new_req is not None and new_req.host != req.host:
                new_req.headers.pop("Authorization", None)
            return new_req

    req = Request(url, headers={"Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json", "User-Agent": "mihur-recovery"})
    with build_opener(_StripAuthOnCrossHostRedirect).open(req, timeout=30) as response:
        return response.read(5 * 1024 * 1024 + 1)


def pending_records(root: str, token: str) -> list[dict]:
    """Recover prior pending deliveries from GitHub Actions artifacts."""
    records: dict[tuple[int, str, str], dict] = {}
    for page in range(1, MAX_PAGES + 1):
        result = request("GET", f"{root}/actions/artifacts?"
                         f"{urlencode({'per_page': 100, 'page': page})}", token)
        artifacts = result.get("artifacts", [])
        for artifact in artifacts:
            if artifact.get("expired") or not artifact.get("name", "").startswith(
                "mihur-pending-handoffs-"
            ):
                continue
            data = artifact_bytes(artifact["archive_download_url"], token)
            if len(data) > 5 * 1024 * 1024:
                raise ValueError("Recovery artifact too large")
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if archive.namelist() != ["mihur-pending-handoffs.jsonl"]:
                    raise ValueError("Unexpected recovery artifact contents")
                with archive.open("mihur-pending-handoffs.jsonl") as pending_file:
                    raw = pending_file.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise ValueError("Pending ledger too large")
                for line in raw.decode("utf-8").splitlines():
                    record = json.loads(line)
                    if record.get("delivery") != "PENDING_MANUAL_RECONCILIATION":
                        raise ValueError("Invalid pending delivery state")
                    number, sha, state = record["pr"], record["sha"], record["state"]
                    if not isinstance(number, int) or number < 1:
                        raise ValueError("Invalid pending PR")
                    if not isinstance(sha, str) or len(sha) != 40:
                        raise ValueError("Invalid pending SHA")
                    if state not in ("AUTHOR_CORRECTION", "WAIT_CHECKS",
                                     "INDEPENDENT_REVIEW", "INDEPENDENT_REVIEW_DRAFT"):
                        raise ValueError("Invalid pending workflow state")
                    records[(number, sha, state)] = record
        if len(artifacts) < 100:
            return list(records.values())
    raise ValueError("Recovery pagination exceeded; manual intervention required")


def reconcile_pending(root: str, token: str) -> None:
    """Reconcile old pending work before processing the current event."""
    for record in pending_records(root, token):
        number, sha, state = record["pr"], record["sha"], record["state"]
        pr = request("GET", f"{root}/pulls/{number}", token)
        if pr["state"] != "open" or pr["head"]["sha"] != sha:
            print(f"Obsolete pending handoff for #{number}; skip stale SHA")
            continue
        tag = marker(sha, state)
        if any(tag in c.get("body", "") for c in pages(root, f"/issues/{number}/comments", token)):
            print(f"Pending #{number} already delivered")
            continue
        # deliver() independently revalidates head, checks, and duplicate markers.
        outcome = deliver(root, number, token)
        if outcome not in {DeliveryOutcome.DELIVERED, DeliveryOutcome.ALREADY_PRESENT,
                           DeliveryOutcome.OBSOLETE}:
            raise ValueError("Recovery still pending; defer new handoffs")


def main() -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event_file:
        event = json.load(event_file)
    numbers = event_pr_numbers(event)
    root = f"{os.environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/{repo}"
    reconcile_pending(root, token)
    if not numbers:
        print("No linked PR; pending reconciliation completed")
        return 0
    for number in numbers:
        outcome = deliver(root, number, token)
        if outcome not in {DeliveryOutcome.DELIVERED, DeliveryOutcome.ALREADY_PRESENT,
                           DeliveryOutcome.OBSOLETE}:
            return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
        print(f"Fail-closed; manual intervention required: {exc}", file=sys.stderr)
        sys.exit(1)
