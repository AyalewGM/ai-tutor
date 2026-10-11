import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/curriculum/standards/dmv_original_task_structure_crosswalk.v1.json"


def _load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_dmv_crosswalk_is_fail_closed_and_ranked():
    data = _load()
    assert data["status"] == "DRAFT_UNVERIFIED_RESEARCH_ONLY_RUNTIME_DISABLED"
    assert data["governance"]["runtime_activation"] == "NOT_AUTHORIZED"
    assert data["governance"]["self_approval"] is False
    rows = data["task_structures"]
    assert 10 <= len(rows) <= 15
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))
    assert {row["canonical_disposition"] for row in rows} <= {
        "REUSE",
        "EXTEND",
        "PROPOSE_IDENTITY_REVIEW",
    }


def test_dmv_crosswalk_has_traceability_without_claiming_acceptance():
    data = _load()
    assert data["summary"]["accepted_standards_mappings"] == 0
    assert data["summary"]["qa_approved_packages"] == 0
    for row in data["task_structures"]:
        assert row["owners"]
        assert row["variability"]
        assert row["gap"]
        assert row["implementation"]["backend_independent_assessment"] != "APPROVED"
        assert row["implementation"]["qa"] == "NOT_REVIEWED"


def test_sources_are_official_and_research_only():
    data = _load()
    allowed_hosts = ("msde.maryland.gov", "mcap.msde.maryland.gov", "montgomeryschoolsmd.org", "doe.virginia.gov", "osse.dc.gov")
    for source in data["source_registry"]:
        assert source["url"].startswith("https://")
        assert any(host in source["url"] for host in allowed_hosts)
        assert "REFERENCE_ONLY" in source["license"]
        assert source["use_constraint"]


def test_legacy_virginia_task_codes_are_not_current_mappings():
    data = _load()
    source = next(s for s in data["source_registry"] if s["source_id"] == "VA_RICH_TASKS_2016")
    assert "2016" in source["publication_or_version"]
    assert "MUST NOT" in source["use_constraint"]
