"""Pure, offline review-handoff coordinator for Mihur Mathematics Content Factory.

No GitHub writes, network calls, DB, agent invocation or release actions.
Consumes evidence obtained by separately authorized integrations, emits one
fail-closed owner report plus routing intents for human/agent execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

GATES = (
    ("math", "Independent Math"),
    ("pedagogy", "Independent Pedagogy"),
    ("standards", "Standards Source-Fidelity"),
    ("assessment", "Assessment Backend"),
    ("frontend", "Frontend/MVE"),
    ("muse", "Independent Muse QA"),
    ("engineering", "Engineering Lead"),
)
VALUES = {"PENDING", "ACCEPTED", "CHANGES_REQUIRED"}
RELEASE_KEYS = ("staging", "production")


def _verdict(evidence: dict[str, Any], gate: str, sha: str) -> str:
    item = evidence.get(gate)
    if not isinstance(item, dict):
        return "PENDING"
    status = item.get("status")
    if status not in VALUES:
        return "PENDING"
    if item.get("source_sha") != sha:
        return "PENDING"
    # Reviewer attestation cannot be inferred from CI, agent intent or issue text.
    if not isinstance(item.get("review_url"), str) or not item["review_url"].startswith(
        "https://github.com/AyalewGM/ai-tutor/"
    ):
        return "PENDING"
    return status


def reconcile(factory: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Give one actionable next owner, preserving each independent review gate."""
    if not isinstance(factory, dict) or not isinstance(evidence, dict):
        raise TypeError("factory/evidence must be objects")
    if factory.get("runtime_activation") is not False or factory.get("status") != "DRAFT_UNVERIFIED":
        raise ValueError("orchestrator refuses runtime authorization")
    if factory.get("release_authority") != "NONE":
        raise ValueError("factory must have zero release authority")
    skill = factory.get("source_canonical_skill")
    if skill != "MATH.EE.EQUATION.MULTISTEP":
        raise ValueError("this first coordinator is scoped to the EQ3 factory")
    sha = evidence.get("content_sha")
    if not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise ValueError("valid exact reviewed content SHA is mandatory")

    quality = factory.get("quality_gates")
    if not isinstance(quality, dict):
        raise TypeError("missing factory mathematical quality evidence")
    mathematically_safe = factory.get("automated_math_checks_passed") is True
    # CI is informative only; it cannot substitute for math/pedagogy authority.
    ci = evidence.get("ci", {})
    if not isinstance(ci, dict):
        ci = {}
    ci_ok = ci.get("sha") == sha and ci.get("status") == "success"
    verdicts = {gate: _verdict(evidence, gate, sha) for gate, _ in GATES}
    next_owner = "Content Production"
    reason = "Fix the independently evidenced mathematical defects or insufficient variation."
    if mathematically_safe:
        if not ci_ok:
            next_owner, reason = "Engineering / CI", "Verify full CI at the exact source revision."
        else:
            for gate, owner in GATES:
                if verdicts[gate] == "CHANGES_REQUIRED":
                    next_owner, reason = "Content Production", f"Resolve {owner} findings on the original authored branch."
                    break
                if verdicts[gate] != "ACCEPTED":
                    next_owner, reason = owner, f"Obtain an independent, exact-SHA {gate} verdict."
                    break
            else:
                next_owner = "Engineering Lead / DevOps"
                reason = "All reported specialist gates accepted; staging still needs independent operator authorization."
    releases = {
        target: "NOT_VERIFIED"
        for target in RELEASE_KEYS
    }
    # This tool *never* interprets even a claimed release flag as activation.
    return {
        "coordinator_version": "MIHUR_CONTENT_HANDOFF_V1",
        "skill": skill,
        "content_sha": sha,
        "factory_math_safe": mathematically_safe,
        "ci_at_exact_sha": "SUCCESS" if ci_ok else "NOT_VERIFIED",
        "gates": verdicts,
        "next_owner": next_owner,
        "next_action": reason,
        "release": releases,
        "production_ready": False,
        "runtime_activation": False,
        "requires_owner_to_switch_chats": False,
        "routing_intent_only": True,
        "agent_execution": "NOT_EXECUTED",
        "note": "Independent acceptance and orchestration executions require real authorized integrations.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline factory review handoff")
    parser.add_argument("--factory-report", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = reconcile(
        json.loads(args.factory_report.read_text(encoding="utf-8")),
        json.loads(args.evidence.read_text(encoding="utf-8")),
    )
    data = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
