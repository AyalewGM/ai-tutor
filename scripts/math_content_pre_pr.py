"""Read-only, explicitly requested pre-PR Mihur Content Factory intake.

Consumes an approved GitHub issue (maintainer-controlled label), never its
untrusted text as instructions or shell input. Produces one bounded EQ3 plan.
No PR creation, agent invocation, label mutation, reviewer spoofing or release.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Callable

from scripts.math_content_github_evidence import REPO, _api

INTAKE_LABEL = "mihur-content-request"
SKILL = "MATH.EE.EQUATION.MULTISTEP"
OWNER = "Math Content Director"


def plan_from_issue(issue: dict[str, Any], *, issue_number: int) -> dict[str, Any]:
    if type(issue_number) is not int or not 1 <= issue_number <= 1_000_000:
        raise ValueError("invalid issue number")
    if not isinstance(issue, dict) or "pull_request" in issue:
        raise ValueError("issue intake must not be a pull request")
    labels = issue.get("labels")
    if not isinstance(labels, list) or INTAKE_LABEL not in {
        x.get("name") for x in labels if isinstance(x, dict)
    }:
        raise PermissionError("only explicitly labelled content requests are eligible")
    if issue.get("state") != "open":
        raise ValueError("issue must be open")
    if issue.get("number") != issue_number:
        raise ValueError("GitHub issue identity mismatch")
    return {
        "kind": "MIHUR_PRE_PR_INTAKE_V1",
        "issue_number": issue_number,
        "canonical_skill": SKILL,
        "source":"EXISTING_GITHUB_ISSUE_LABEL_ONLY",
        "content_request_body": "NOT_EXECUTED_AS_INSTRUCTIONS",
        "existing_canonical_reuse": True,
        "existing_family_audit": "REQUIRED",
        "official_source_licensing": "REQUIRED",
        "initial_factory_blueprint": "docs/content_factory/mth1w_eq3_factory.v1.json",
        "next_owner": OWNER,
        "next_action": "Reconcile existing math families and verified depth gaps; prepare a bounded original-family authoring plan with independent gates.",
        "implementation_pr": "NOT_CREATED",
        "agent_execution": "NOT_EXECUTED",
        "review_status": "PENDING",
        "runtime_activation": False,
        "release_authority": "NONE",
    }


def fetch_plan(
    issue_number: int, *, token: str,
    fetch: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    if type(issue_number) is not int or not 1 <= issue_number <= 1_000_000:
        raise ValueError("invalid issue number")
    if not token:
        raise ValueError("read-only GitHub token required")
    issue = _api(f"/repos/{REPO}/issues/{issue_number}", token, fetch)
    return plan_from_issue(issue, issue_number=issue_number)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-PR content factory issue intake")
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = fetch_plan(args.issue_number, token=os.environ.get("GITHUB_TOKEN", ""))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
