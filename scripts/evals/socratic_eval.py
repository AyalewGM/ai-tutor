"""Socratic/CPA behavior eval for the LLM gateway's render endpoint.

Runs a fixed scenario set against a live gateway (`POST /v1/render`) and
scores each response on the contract:

- exactly-zero-or-one ```json:cpa block, valid against the payload schema
- the block is required/forbidden per scenario
- the canonical answer never appears verbatim in the learner-facing text
  (the sanitizer is the authority — if it would change the message, that's
  a violation)
- a scaffolding question is present (heuristic Socratic check)

Usage:
    python scripts/evals/socratic_eval.py [--gateway-url http://localhost:8001] [--json]

Exits non-zero when any scenario fails. Meaningful only when the gateway
runs a real provider; the fallback voice emits no visuals by design.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field

import httpx

from app.services.chat_cpa import sanitize_cpa_blocks


@dataclass
class Scenario:
    name: str
    request: dict
    canonical_answer: str | None = None
    cpa_required: bool = False
    cpa_forbidden: bool = False
    expect_question: bool = True
    notes: str = field(default="")


SCENARIOS = [
    Scenario(
        name="hint_on_equation_invites_visual",
        request={
            "action": "GIVE_HINT",
            "curriculum_name": "MCPS Math 8",
            "grade_level": "8",
            "skill_name": "Multi-Step Equations",
            "problem_prompt": "Solve 2x + 3 = 11.",
            "hint_level": 1,
            "hint_constraint": "Ask what is being done to x; do not name the operation.",
            "cpa_level": "PICTORIAL",
        },
        canonical_answer="x=4",
    ),
    Scenario(
        name="misconception_should_mirror_wrong_state",
        request={
            "action": "CORRECT_ANSWER",
            "curriculum_name": "MCPS Math 8",
            "grade_level": "8",
            "skill_name": "Multi-Step Equations",
            "problem_prompt": "Solve 2x + 3 = 11.",
            "step_evidence": "Learner wrote '2x = 11' after '2x + 3 = 11' — "
            "applied the inverse on one side only (EQ_002).",
            "cpa_level": "PICTORIAL",
        },
        canonical_answer="x=4",
        notes="If a block is emitted it must not render x = 4.",
    ),
    Scenario(
        name="correct_feedback_stays_textual",
        request={
            "action": "PRAISE",
            "curriculum_name": "MCPS Math 8",
            "grade_level": "8",
            "skill_name": "Multi-Step Equations",
            "problem_prompt": "Solve 2x + 3 = 11.",
            "cpa_level": "ABSTRACT",
        },
        canonical_answer="x=4",
        cpa_forbidden=True,
        expect_question=False,
    ),
    Scenario(
        name="fraction_misconception_invites_bars",
        request={
            "action": "CORRECT_ANSWER",
            "curriculum_name": "MCPS Math 6",
            "grade_level": "6",
            "skill_name": "Fraction equivalence",
            "problem_prompt": "Is 2/4 the same as 1/2? Explain.",
            "misconception_description": "Learner believes 2/4 > 1/2 because 4 > 2.",
            "cpa_level": "PICTORIAL",
        },
        canonical_answer=None,
    ),
]


def check_message(message: str, scenario: Scenario) -> list[str]:
    """Return the list of contract violations for one rendered message."""
    violations: list[str] = []
    block_count = message.count("```json:cpa") + message.count("<cpa_visual>")
    if block_count > 1:
        violations.append(f"{block_count} CPA blocks emitted (max 1)")
    if scenario.cpa_required and block_count == 0:
        violations.append("expected a CPA block but none was emitted")
    if scenario.cpa_forbidden and block_count > 0:
        violations.append("CPA block emitted in a text-only scenario")

    cleaned = sanitize_cpa_blocks(message, canonical_answer=scenario.canonical_answer)
    if cleaned != message.strip():
        violations.append("sanitizer would alter the message (invalid/extra/leaky block)")

    text_only = cleaned.split("```json:cpa")[0]
    if scenario.canonical_answer and scenario.canonical_answer.replace(
        " ", ""
    ) in text_only.replace(" ", ""):
        violations.append(f"canonical answer leaked: {scenario.canonical_answer}")
    if scenario.expect_question and "?" not in text_only:
        violations.append("no scaffolding question found")
    if not message.strip():
        violations.append("empty message")
    return violations


def run(gateway_url: str, timeout: float = 30.0) -> list[dict]:
    results = []
    for scenario in SCENARIOS:
        try:
            response = httpx.post(
                f"{gateway_url.rstrip('/')}/v1/render",
                json=scenario.request,
                timeout=timeout,
            )
            response.raise_for_status()
            message = str(response.json()["message"])
            violations = check_message(message, scenario)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            message, violations = "", [f"request failed: {exc}"]
        results.append(
            {
                "scenario": scenario.name,
                "ok": not violations,
                "violations": violations,
                "message": message,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-url", default="http://localhost:8001")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args()

    results = run(args.gateway_url)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            mark = "PASS" if r["ok"] else "FAIL"
            print(f"[{mark}] {r['scenario']}")
            for violation in r["violations"]:
                print(f"        - {violation}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
