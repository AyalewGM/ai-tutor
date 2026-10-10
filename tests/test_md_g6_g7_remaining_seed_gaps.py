"""Keep remaining scoped gaps grounded in actual seed descriptions."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST = (
    ROOT
    / "docs/curriculum/standards/md_g6_g7_remaining_seed_gaps.wave1.v1.json"
)


def test_scoped_seed_gap_evidence_is_reproducible() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["findings"]) == 5
    for finding in data["findings"]:
        source = (ROOT / finding["scope_path"]).read_text(encoding="utf-8")
        code_pos = source.index('"' + finding["seed_code"] + '"')
        # All target seed descriptions occur near the code declaration.
        context = source[code_pos : code_pos + 650].lower()
        assert finding["existing_scope"]
        for phrase in finding["missing_from_seed_description"]:
            assert phrase.lower() not in context, (finding["id"], phrase)
        assert finding["repo_wide_missing"] is False
    assert data["counts"]["repo_wide_confirmed_missing"] == 0
    assert data["handoff"]["no_approved_content_authorized"] is True
    assert data["safety"]["no_mastery_changes"] is True
