"""Keep Mihur reviewer agents least-privilege and manually invoked.

This checks YAML frontmatter's intentionally simple, fixed key/value subset
without a YAML parser dependency. It never invokes an agent or GitHub.
"""

import ast
from pathlib import Path

import pytest

AGENTS = Path(__file__).resolve().parents[1] / ".github" / "agents"
NAMES = (
    "mihur-bug-hunter",
    "mihur-security-auditor",
    "mihur-math-auditor",
    "mihur-pedagogy-auditor",
    "mihur-muse-auditor",
    "mihur-standards-auditor",
)


@pytest.mark.parametrize("agent", NAMES)
def test_post_merge_auditor_profiles_are_manual_and_least_privilege(agent: str) -> None:
    path = AGENTS / f"{agent}.agent.md"
    raw = path.read_text(encoding="utf-8")
    assert raw.startswith("---\n"), path
    frontmatter = raw.split("---\n", 2)[1]
    fields = dict(line.split(": ", 1) for line in frontmatter.splitlines() if ": " in line)
    assert fields.get("target") == "github-copilot"
    assert fields.get("disable-model-invocation") == "true"
    assert fields.get("user-invocable") == "true"
    assert fields.get("name")
    assert fields.get("description")
    tools = ast.literal_eval(fields["tools"])
    expected = ["read", "search", "github/*"]
    if agent == "mihur-muse-auditor":
        expected.append("playwright/*")
    assert tools == expected
    assert not {"execute", "shell", "edit", "write", "agent", "*"} & set(tools)
