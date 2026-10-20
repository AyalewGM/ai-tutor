"""Help Center guide-to-site parity and public navigation contracts.

These source-only checks do not replace a real browser accessibility review.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDES_DIR = ROOT / "docs" / "user-guides"
BUNDLE = ROOT / "frontend" / "src" / "help" / "guides.generated.json"
APP = ROOT / "frontend" / "src" / "App.tsx"
PAGES = ROOT / "frontend" / "src" / "pages"
SYNC_SCRIPT = ROOT / "frontend" / "scripts" / "sync-help-guides.mjs"


def _guides() -> list[dict]:
    content = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert content["schemaVersion"] == 1
    return content["guides"]


def test_five_public_pilot_articles_match_versioned_markdown_exactly() -> None:
    expected = {
        "welcome",
        "parent-first-day",
        "student-first-session",
        "progress-and-mastery",
        "privacy-and-faq",
    }
    guides = _guides()
    assert len(guides) == len(expected)
    assert {guide["slug"] for guide in guides} == expected
    for item in guides:
        body = (GUIDES_DIR / f'{item["slug"]}.md').read_text(encoding="utf-8")
        assert item["body"] == body, f'Drift between source and public guide: {item["slug"]}'
        assert item["title"] == re.search(r"^# (.+)$", body, re.MULTILINE).group(1)
        assert item["summary"].strip()
        assert item["audience"].strip()
        assert len(body) > 600


def test_help_routes_are_public_and_named_links_are_real() -> None:
    app = APP.read_text(encoding="utf-8")
    for route in ('path="/help"', 'path="/help/:slug"'):
        assert route in app
    assert 'element={<HelpCenter />}' in app
    docs = {entry["slug"] for entry in _guides()}
    for item in _guides():
        for slug in re.findall(r"\]\(/help/([^/#)]+)", item["body"]):
            assert slug in docs, f'{item["slug"]} links to nonexistent guide {slug}'
        assert "example.org/practice/" not in item["body"]
    assert "docs/user-guides" in SYNC_SCRIPT.read_text(encoding="utf-8")


def test_parent_and_learner_have_contextual_help_without_new_auth_gates() -> None:
    targets = {
        "Landing.tsx": 'to="/help"',
        "Login.tsx": 'to="/help/parent-first-day"',
        "ParentDashboard.tsx": 'to="/help/parent-first-day"',
        "ParentSettings.tsx": 'to="/help/parent-first-day#3-share-each-childs-private-practice-link"',
        "LearnEntry.tsx": 'to="/help/student-first-session"',
        "Workspace.tsx": 'to="/help/progress-and-mastery"',
        "Privacy.tsx": 'to="/help/privacy-and-faq"',
    }
    for page, link in targets.items():
        assert link in (PAGES / page).read_text(encoding="utf-8"), page
    assert 'navLink("/help", "Help")' in (
        ROOT / "frontend/src/components/NavBar.tsx"
    ).read_text(encoding="utf-8")


def test_draft_status_is_honest_and_screen_captures_not_fabricated() -> None:
    articles = {item["slug"]: item["body"].lower() for item in _guides()}
    assert "screenshots" in articles["student-first-session"]
    assert "synthetic" in articles["student-first-session"]
    assert "seven days" in articles["parent-first-day"]
    assert "four-digit parent pin" in articles["parent-first-day"]
    assert "independent" in articles["progress-and-mastery"]
    assert "subject to staging websocket" in articles["privacy-and-faq"]


def test_unavailable_region_does_not_claim_curriculum_equivalence() -> None:
    source = (PAGES / "LearnEntry.tsx").read_text(encoding="utf-8")
    assert "pick the closest grade-level fit" not in source
    assert "another region's curriculum is not automatically equivalent" in source
    assert "Content in progress" in source
    parent = (GUIDES_DIR / "parent-first-day.md").read_text(encoding="utf-8")
    assert "Do not select an unrelated grade" in parent
