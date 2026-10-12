"""Fail-closed checks for partial Grade 6–8 local seed evidence."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST = (
    ROOT
    / "docs"
    / "curriculum"
    / "standards"
    / "grades6_8_existing_seed_evidence.wave1.v1.json"
)


def test_seed_evidence_matches_source_scripts_without_claiming_standards() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["summary"]["source_scripts"] == 5
    assert data["summary"]["local_skill_rows"] == 38
    assert data["summary"]["accepted_standards_mappings"] == 0
    for entry in data["entries"]:
        source = (ROOT / entry["path"]).read_text(encoding="utf-8")
        prefix = re.escape(entry["pattern"])
        codes = re.findall(
            r'_skill\(\s*db,\s*curriculum,\s*"(' + prefix + r'\.[^"]+)"',
            source,
        )
        assert codes == entry["local_skill_codes"]
        assert entry["official_expectation_ids"] == []
        assert entry["accepted_mapping_count"] == 0
        assert entry["source_role"] == (
            "EXISTING_LOCAL_SEED_ONLY_NOT_STANDARDS_CROSSWALK"
        )


def test_partial_inventory_is_never_activation_or_mastery_evidence() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_PARTIAL_GRADE6_8_SEED_EVIDENCE_INVENTORY"
    assert data["safety"] == {
        "source_identity_not_inferred": True,
        "grade_level_completeness_not_claimed": True,
        "accepted_mapping_count": 0,
        "activation": "FORBIDDEN",
        "mastery_changes": False,
    }
