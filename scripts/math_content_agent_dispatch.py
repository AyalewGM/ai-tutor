"""Manual, explicitly authorized GitHub Copilot content-task dispatch.

No automatic execution from issues/PR/reviews. The caller must supply a
separate user-controlled dispatch credential, a pre-approved issue label, and
exact confirmation. Only assigns Copilot on a verified existing open issue.
Never merges PRs, grants content authority, or touches learner/release state.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from typing import Any, Callable

from scripts.math_content_github_evidence import REPO, _api
from scripts.math_content_pre_pr import plan_from_issue

COPILOT_LOGIN = "copilot-swe-agent[bot]"
CONFIRMATION = "ASSIGN_COPILOT_EQ3"
BOUNDED_INSTRUCTIONS = (
    "Mihur Math Content Factory, one bounded task for "
    "MATH.EE.EQUATION.MULTISTEP. First inspect current main, existing approved "
    "family generators, accepted reviews, #313, #337, #446, #462 and draft #484. "
    "Follow docs/content_factory/mth1w_eq3_factory.v1.json after it is merged. "
    "Research official scope as reference only; do not copy assessment items. "
    "Prepare an evidence-backed depth-gap report and, only if verified, original "
    "missing mathematical structures on a draft PR. Deterministic exact SymPy "
    "oracles, misconceptions, target-preserving repair and independent tests "
    "required. Never authorize mode metadata, runtime, mastery, database "
    "mutations, deployment, merge, or independent reviewer approvals."
)


def prepare_dispatch(issue: dict[str, Any], number: int, confirmation: str) -> dict:
    if confirmation != CONFIRMATION:
        raise PermissionError("dispatch must be explicitly confirmed")
    plan = plan_from_issue(issue, issue_number=number)
    if any(a.get("login") in {COPILOT_LOGIN, "copilot-swe-agent"}
           for a in issue.get("assignees", []) if isinstance(a, dict)):
        return {"status": "ALREADY_ASSIGNED", "issue": number, "invoked": False}
    if plan["runtime_activation"] is not False:
        raise PermissionError("intake is not safe for dispatch")
    return {
        "status": "READY",
        "issue": number,
        "invoked": False,
        "request": {
            "assignees": [COPILOT_LOGIN],
            "agent_assignment": {
                "target_repo": REPO,
                "base_branch": "main",
                "custom_instructions": BOUNDED_INSTRUCTIONS,
            },
        },
    }


def dispatch(
    issue_number: int, *,
    confirmation: str,
    token: str,
    fetch: Callable[..., Any] = urllib.request.urlopen,
) -> dict:
    """Explicit assignment via GitHub REST; all other execution stays external."""
    if not token:
        raise ValueError("a separate, authorized Copilot dispatch token is required")
    if type(issue_number) is not int or not 1 <= issue_number <= 1_000_000:
        raise ValueError("invalid issue number")
    issue = _api(f"/repos/{REPO}/issues/{issue_number}", token, fetch)
    prepared = prepare_dispatch(issue, issue_number, confirmation)
    if prepared["status"] == "ALREADY_ASSIGNED":
        return prepared
    body = json.dumps(prepared["request"]).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue_number}/assignees",
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mihur-content-director-authorized-dispatch",
        },
    )
    with fetch(req, timeout=20) as stream:
        result = json.load(stream)
    assignees = result.get("assignees", [])
    assigned = any(
        a.get("login") in {COPILOT_LOGIN, "copilot-swe-agent"}
        for a in assignees if isinstance(a, dict)
    )
    if not assigned:
        raise RuntimeError("GitHub did not confirm the Copilot assignment")
    return {
        "status": "ASSIGNED_CONFIRMED_BY_GITHUB",
        "issue": issue_number,
        "invoked": True,
        "copilot_assignment_only": True,
        "review_authority": "NONE",
        "release_authority": "NONE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually authorized Mihur Copilot assignment")
    parser.add_argument("--issue-number", required=True, type=int)
    parser.add_argument("--confirmation", required=True)
    args = parser.parse_args()
    result = dispatch(
        args.issue_number,
        confirmation=args.confirmation,
        token=os.environ.get("MIHUR_COPILOT_DISPATCH_TOKEN", ""),
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
