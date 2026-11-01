"""Regression contracts for the independent executable QA agent configuration.

These tests validate the agent profile itself. They do NOT claim that an audit
has run, that a browser is accessible, or that any PR is ready to merge.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / ".github/agents/mihur-independent-system-qa.agent.md"
RUNBOOK = ROOT / "docs/qa/INDEPENDENT_SYSTEM_QA.md"


def _profile_parts() -> tuple[str, str]:
    content = PROFILE.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)\Z", content, re.DOTALL)
    assert match is not None, "valid YAML-style frontmatter is required"
    return match["frontmatter"], match["body"]


def test_agent_is_explicit_manually_invoked_custom_profile() -> None:
    header, body = _profile_parts()
    assert "name: Mihur Independent System QA" in header
    assert "description:" in header
    assert "target: github-copilot" in header
    assert "disable-model-invocation: true" in header
    assert "user-invocable: true" in header
    assert "https://github.com/AyalewGM/ai-tutor/issues/465" in body


def test_agent_can_execute_tests_but_cannot_edit_or_delegate() -> None:
    header, body = _profile_parts()
    tools_line = next(line for line in header.splitlines() if line.startswith("tools:"))
    for name in ('"read"', '"search"', '"execute"', '"github/*"', '"playwright/*"'):
        assert name in tools_line
    for forbidden in ('"edit"', '"agent"', '"*"'):
        assert forbidden not in tools_line
    assert "never" in body.lower()
    assert "No permissions to deploy" in RUNBOOK.read_text(encoding="utf-8")


def test_agent_requires_every_open_pr_and_exact_main_sha() -> None:
    _, body = _profile_parts()
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "EVERY open PR" in body
    assert "full current main SHA" in body
    assert "one row per PR plus main" in body
    assert "one row for EVERY open PR" in runbook
    assert "headRefOid" in runbook
    assert "EXPECTED_40_HEX_SHA" in runbook


def test_agent_explicitly_refuses_unsafe_test_and_release_shortcuts() -> None:
    _, body = _profile_parts()
    runbook = RUNBOOK.read_text(encoding="utf-8")
    for required in (
        "NOT_EXECUTED",
        "disposable",
        "no production secrets",
        "independent",
        "mastery",
        "cross-family",
        "WebSocket",
        "Playwright",
    ):
        assert required.lower() in body.lower() or required.lower() in runbook.lower()
    assert "A custom agent definition does **not** run itself." in body
    assert "No changes to learner history, production" in runbook
