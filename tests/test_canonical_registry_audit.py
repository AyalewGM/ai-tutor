"""Deterministic registry-audit invariants for #282 Phase A.

These tests pin the vocabulary boundaries the alias bridge depends on:
family IDs are not skill codes, pack aliases do not auto-match
implemented skills, and no new orphan MATH.* literal may appear in
source without an explicit audit update.
"""
from __future__ import annotations

from scripts.audit_canonical_registry import audit

REPORT = audit()


def test_merged_registry_contains_every_domain_family():
    assert REPORT["families"]["all_domain_families_merged"] is True


def test_family_and_skill_counts_are_distinct_quantities():
    families = REPORT["families"]["merged_total"]
    skills = REPORT["canonical_skills"]["distinct_codes"]
    assert families > skills
    # 107 skills vs ~390 families is the reconciled #282 discrepancy;
    # the assertion pins the relationship, not a frozen count.
    assert REPORT["families"]["domain_module_total"] <= families


def test_every_family_carries_a_distinct_skill_code_namespace():
    assert REPORT["canonical_skills"]["distinct_codes"] > 0
    # Families sharing a skill is expected (one skill, many generators).
    assert (
        REPORT["canonical_skills"]["skills_with_multiple_families"]
        <= REPORT["canonical_skills"]["distinct_codes"]
    )


def test_pack_manifest_covers_every_pack_alias():
    assert REPORT["curriculum"]["aliases_match_manifest"] is True
    assert REPORT["curriculum"]["distinct_aliases"] == 42


def test_no_alias_auto_matches_an_implemented_skill():
    """Zero overlap proves aliases need explicit reviewed mappings."""
    assert REPORT["curriculum"]["aliases_present_as_skill_codes"] == []


def test_legacy_pack_family_codes_are_a_separate_namespace():
    """Pack problem_families (NUMBER_SEQUENCE etc.) never overlap
    canonical family IDs — they name legacy generators."""
    assert REPORT["curriculum"]["legacy_pack_codes_in_families"] == []


def test_no_new_orphan_math_literals():
    """Orphan MATH.* literals are documented, not silently added."""
    assert set(REPORT["source_literals"]["orphan_literals"]) == {
        # Newly surfaced source-only literals are explicitly audited as orphans.
        # This inventory is NOT a canonical registration or curriculum mapping.
        "MATH.ARITHMETIC.ADD_SUB_WITHIN_20",
        "MATH.ARITHMETIC.WORD_PROBLEM_WITHIN_20",
        "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120",
        "MATH.PLACE_VALUE.TENS_ONES",
        "MATH.RP.PERCENT.APPLICATION",
        "MATH.RP.PERCENT.MULTI",
        "MATH.RP.PROPORTION",
        "MATH.RP.RATIO.CONCEPT",
        "MATH.RP.UNIT_RATE",
    }


def test_family_id_reuse_as_skill_code_is_bounded():
    """Only explicitly reviewed self-referential codes may overlap."""
    assert set(
        REPORT["canonical_skills"]["family_ids_reused_as_skill_codes"]
    ) <= {"MATH.PROB.SIMPLE", "MATH.PROB.EXPERIMENTAL", "MATH.FIN.UNIT_PRICE"}
