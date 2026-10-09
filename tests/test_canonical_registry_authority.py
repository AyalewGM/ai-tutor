"""Tests for authoritative canonical target registry in #282."""
from app.canonical_problem_families import _DOMAIN_MODULES, FAMILIES


def test_all_domain_families_registered_in_public_registry():
    for module in _DOMAIN_MODULES:
        for family_code, family in module.FAMILIES.items():
            assert FAMILIES[family_code] is family


def test_authoritative_targets_come_from_merged_registry():
    targets = {family.canonical_skill_code for family in FAMILIES.values()}
    assert targets
    assert all(isinstance(code, str) and code.startswith("MATH.") for code in targets)


def test_family_codes_are_not_interchangeable_with_skill_codes():
    # The mapping validator must target a skill code, never a family ID.
    family_codes = set(FAMILIES)
    target_codes = {family.canonical_skill_code for family in FAMILIES.values()}
    assert family_codes != target_codes
