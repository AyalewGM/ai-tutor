"""Coverage audit must not conflate generators with verified curriculum coverage."""
from __future__ import annotations

from app.canonical_problem_families import FAMILIES
from scripts.audit_skill_depth_coverage import build_report


def test_inventory_is_exactly_registry_derived() -> None:
    report = build_report()
    skills = report["skill_rows"]
    assert report["family_count"] == len(FAMILIES)
    assert report["distinct_generator_backed_skill_codes"] == len({
        family.canonical_skill_code for family in FAMILIES.values()
    })
    assert len(skills) == report["distinct_generator_backed_skill_codes"]
    assert sum(x["generator_family_count"] for x in skills) == len(FAMILIES)
    assert len({x["canonical_skill_code"] for x in skills}) == len(skills)
    assert {code for x in skills for code in x["generator_family_ids"]} == set(FAMILIES)


def test_inventory_does_not_claim_unverified_skill_depth() -> None:
    report = build_report()
    assert report["report_type"] == "GENERATOR_DERIVED_SKILL_DEPTH_INVENTORY"
    assert report["all_mathematical_skills_count"] is None
    assert report["verified_curriculum_coverage_count"] is None
    assert report["verified_rich_content_count"] == 0
    assert "no generator" in report["authority_warning"]
    for row in report["skill_rows"]:
        assert row["generator_available"] is True
        assert row["rich_content_review_status"] == "UNVERIFIED_CONTENT_DEPTH"
        assert row["mathematical_review"] == "NOT_ASSESSED"
        assert row["curriculum_mapping_review"] == "NOT_ASSESSED"
        assert row["interactive_lesson_review"] == "NOT_ASSESSED"
        assert row["assessment_quality_review"] == "NOT_ASSESSED"
        assert set(row["mode_flags"]) == {
            "diagnostic", "guided", "independent", "mastery", "review"
        }
        assert all(isinstance(flag, bool) for flag in row["mode_flags"].values())


def test_mode_and_dimension_evidence_is_exact_not_inferred() -> None:
    report = build_report()
    for row in report["skill_rows"]:
        families = [
            family for family in FAMILIES.values()
            if family.canonical_skill_code == row["canonical_skill_code"]
        ]
        assert row["generator_family_ids"] == sorted(
            family.code for family in families
        )
        assert row["supported_modes"] == sorted({
            mode.value for family in families for mode in family.modes
        })
        assert row["evidence_dimensions_declared"] == sorted({
            dimension for family in families
            for dimension in family.evidence_dimensions
        })
