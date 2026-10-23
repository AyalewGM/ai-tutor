"""Read-only GitHub PR/CI adapter for Mihur's offline content handoff.

Never interprets comments, labels, reviews, checkmarks, or AI text as
independent approval. Exact-SHA CI is evidence only. No source checkout,
agent invocation, writes, dispatch, database, staging, or deployment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from collections.abc import Callable
from typing import Any

REPO = "AyalewGM/ai-tutor"
_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _validate_pr(pr_number: int) -> None:
    if type(pr_number) is not int or not 1 <= pr_number <= 1_000_000:
        raise ValueError("invalid PR number")


def _api(
    path: str, token: str, fetch: Callable[..., Any] = urllib.request.urlopen
) -> Any:
    if not path.startswith(f"/repos/{REPO}/") or "?" in path and "\n" in path:
        raise ValueError("untrusted API path")
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mihur-content-director-read-only",
        },
        method="GET",
    )
    with fetch(req, timeout=15) as stream:
        return json.load(stream)


def fetch_evidence(
    pr_number: int,
    *,
    token: str,
    fetch: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    """Fetch trusted REST facts, never hallucinate or grant specialist verdicts."""
    _validate_pr(pr_number)
    if not token:
        raise ValueError("read-only GitHub token required")
    pr = _api(f"/repos/{REPO}/pulls/{pr_number}", token, fetch)
    sha = pr.get("head", {}).get("sha", "")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise ValueError("GitHub PR head has no exact commit SHA")
    if pr.get("base", {}).get("repo", {}).get("full_name") != REPO:
        raise ValueError("unexpected PR destination")
    runs = _api(
        f"/repos/{REPO}/actions/runs?head_sha={sha}&per_page=100",
        token, fetch,
    )
    if not isinstance(runs, dict) or not isinstance(runs.get("workflow_runs"), list):
        raise TypeError("missing workflow evidence")
    # A completed successful exact-head CI is necessary, not sufficient.
    ci_runs = [
        run for run in runs["workflow_runs"]
        if run.get("head_sha") == sha and run.get("name") == "CI"
        and run.get("event") == "pull_request"
    ]
    ci_runs.sort(key=lambda run: (run.get("run_started_at") or "", run.get("id", 0)),
                 reverse=True)
    ci = ci_runs[0] if ci_runs else None
    status = "success" if ci and ci.get("status") == "completed" and (
        ci.get("conclusion") == "success"
    ) else "NOT_VERIFIED"
    result = {
        "repository": REPO,
        "pull_request": pr_number,
        "content_sha": sha,
        "ci": {"sha": sha, "status": status, "run_id": ci.get("id") if ci else None},
        "specialist_reviews": "PENDING_INDEPENDENT_ATTESTATION",
        # Leave all independent reviewers absent. Never infer an ACCEPTED gate
        # from a comment, PR author, CI result, changed file, or bot identity.
        "release_authority": "NONE",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only exact-PR evidence adapter")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = fetch_evidence(args.pr_number, token=os.environ.get("GITHUB_TOKEN", ""))
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
