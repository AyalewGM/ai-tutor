"""Contract tests for the Maryland Grades 6-8 2025 seed reconciliation."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "docs"
    / "curriculum"
    / "standards"
    / "md_grades6_8_2025.seed_skill_reconciliation.v1.json"
)


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_is_complete_for_current_local_seed_inventory() -> None:
    data = _load()
    assert data["row_count"] == 28
    assert data["grade_counts"] == {"6": 7, "7": 15, "8": 6}
    assert len(data["rows"]) == data["row_count"]

    expected_codes = {
        "M6.RP.RATIO",
        "M6.RP.UNIT_RATE",
        "M6.NS.FRACTION",
        "M6.EE.EXPR",
        "M6.EE.EQUATION",
        "M6.SP.STAT",
        "M6.G.GEO",
        "M7.RP.PROP",
        "M7.RP.PERCENT",
        "M7.EE.EXPR",
        "M7.EE.EQUATION",
        "M7.RP.PROP.RATE",
        "M7.RP.PERCENT.OF",
        "M7.EE.EXPR.DIST",
        "M7.EE.EXPR.COMBINE",
        "M7.EE.EQUATION.ONE",
        "M7.EE.EQUATION.TWO",
        "M7.G.SOLID",
        "M7.G.GEO",
        "M7.SP.PROB",
        "M7.RP.GRAPH",
        "M7.NS.RAT",
        "M8.G.TRANS",
        "M8.G.SIM",
        "M8.SP.STAT",
        "M8.G.PYTH",
        "M8.NS.RAD",
        "M8.F.FN",
    }
    assert {row["local_seed_code"] for row in data["rows"]} == expected_codes


def test_sources_are_official_versioned_msde_documents() -> None:
    source = _load()["source"]
    assert source["issuing_authority"] == "Maryland State Department of Education"
    assert source["adoption_date"] == "2025-07-29"
    assert source["implementation_school_year"] == "2026-2027"
    assert source["landing_page"].startswith("https://msde.maryland.gov/")

    expected_media = {
        "6": ("17816", "17817"),
        "7": ("17818", "17819"),
        "8": ("17820", "17821"),
    }
    for grade, (crosswalk_id, companion_id) in expected_media.items():
        docs = source["grade_documents"][grade]
        assert docs["crosswalk"].endswith(f"/media/{crosswalk_id}")
        assert docs["companion"].endswith(f"/media/{companion_id}")


def test_all_relations_fail_closed() -> None:
    rows = _load()["rows"]
    assert {row["mapping_status"] for row in rows} == {
        "PROVISIONAL_NOT_ACCEPTED"
    }

    for row in rows:
        readiness = row["readiness"]
        assert readiness["source_expectation"] == "SOURCE_VERIFIED"
        assert readiness["canonical_identity"] == "NOT_REVIEWED"
        assert readiness["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
        assert readiness["generator"] == "NOT_AUDITED"
        assert readiness["validated_practice"] == "NOT_AUDITED"
        assert readiness["assessment"] == "NOT_AUDITED"
        assert readiness["verified_mastery"] == "NOT_ESTABLISHED"
        assert "canonical_skill_id" not in row
        assert "student" not in json.dumps(row).lower()


def test_only_explicit_out_of_grade_rows_lack_current_targets() -> None:
    rows = _load()["rows"]
    empty = {
        row["local_seed_code"]
        for row in rows
        if not row["official_targets"]
    }
    assert empty == {"M8.G.TRANS", "M8.G.SIM"}

    for row in rows:
        if row["local_seed_code"] in empty:
            assert row["relation"] == "OUT_OF_GRADE_CURRENT_2025"
            assert row["displaced_or_extra_scope"]
        else:
            assert row["official_targets"]
            assert all(target[0] in {"6", "7", "8"} for target in row["official_targets"])


def test_cross_grade_risks_are_machine_readable() -> None:
    by_code = {row["local_seed_code"]: row for row in _load()["rows"]}

    assert by_code["M7.G.GEO"]["official_targets"] == ["7.GR.B.3"]
    assert {
        item["current_md_target"]
        for item in by_code["M7.G.GEO"]["displaced_or_extra_scope"]
    } == {"8.GR.A.1", "8.GR.A.3"}

    assert "8.DS.C.6" in {
        item["current_md_target"]
        for item in by_code["M7.SP.PROB"]["displaced_or_extra_scope"]
    }
    assert by_code["M8.G.TRANS"]["relation"] == "OUT_OF_GRADE_CURRENT_2025"
    assert by_code["M8.G.SIM"]["relation"] == "OUT_OF_GRADE_CURRENT_2025"

def test_architecture_decision_preserves_legacy_composites_and_fails_closed() -> None:
    data = _load()
    decision = data["architecture_decision"]
    assert decision["issue"] == 282
    assert decision["comment_id"] == 6093222041
    assert decision["status"] == (
        "IDENTITY_BOUNDARIES_DECIDED_MAPPINGS_NOT_ACCEPTED"
    )

    by_code = {row["local_seed_code"]: row for row in data["rows"]}
    for code in {"M7.G.GEO", "M7.SP.PROB"}:
        disposition = by_code[code]["architecture_disposition"]
        assert disposition["disposition"] == (
            "PRESERVED_CROSS_GRADE_LEGACY_COMPOSITE_NOT_CANONICAL"
        )
        assert disposition["mapping_consequence"] == (
            "NO_SINGLE_GRADE_7_EQUIVALENCE"
        )
        assert disposition["required_scope_boundaries"]
        assert "ALL_OF" in disposition["reporting_policy"]

    for code in {"M8.G.TRANS", "M8.G.SIM"}:
        disposition = by_code[code]["architecture_disposition"]
        assert disposition["disposition"] == (
            "PRESERVED_LEGACY_PLACEMENT_IDENTIFIER"
        )
        assert disposition["mapping_consequence"] == (
            "NO_CURRENT_MARYLAND_GRADE_8_EQUIVALENCE"
        )

    assert all(
        row["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
        for row in data["rows"]
    )
    assert all("canonical_skill_id" not in row for row in data["rows"])
