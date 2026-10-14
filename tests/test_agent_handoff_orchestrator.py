"""Phase-1 orchestrator safety and deterministic routing."""
from scripts.agent_handoff_orchestrator import lane, marker, next_step


def test_standards_are_reviewed_by_independent_source_reviewer():
    assert lane("draft standards inventory", ["docs/curriculum/standards/md.json"]) == (
        "Independent Standards Source-Fidelity Reviewer"
    )


def test_assessment_routes_to_backend():
    assert lane("mastery gate", ["app/services/assessment.py"]) == "Assessment Backend / Architecture"


def test_checks_fail_closed():
    assert next_step(False, {"CI": "success"}, "content", []) == "WAIT_CHECKS"
    assert next_step(False, {"CI": "failure", "AppSec Baseline": "success"}, "content", []) == "AUTHOR_CORRECTION"
    assert next_step(True, {"CI": "success", "AppSec Baseline": "success"}, "content", []) == "INDEPENDENT_REVIEW_DRAFT"


def test_exact_sha_state_dedup_key():
    assert marker("abc", "WAIT_CHECKS") != marker("abc", "INDEPENDENT_REVIEW")
    assert marker("abc", "WAIT_CHECKS") != marker("def", "WAIT_CHECKS")
