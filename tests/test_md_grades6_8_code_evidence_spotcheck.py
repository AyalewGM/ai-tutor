"""Verify code-evidence claims against actual seed sources."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PATH = ROOT / "docs/curriculum/standards/md_grades6_8_code_evidence_spotcheck.wave1.v1.json"


def test_literal_code_evidence_is_present_and_not_accepted_coverage() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 6
    assert data["summary"]["confirmed_missing_repo_wide"] == 0
    for row in data["entries"]:
        source = (ROOT / row["source_path"]).read_text(encoding="utf-8")
        for term in row["search_terms"]:
            assert term.lower() in source.lower(), (row["candidate_id"], term)
    assert data["safety"] == {
        "no_runtime_changes": True,
        "no_mastery_changes": True,
        "no_accepted_mappings": True,
    }
