"""
QA taxonomy separation tests for ARCH #282.

These tests enforce the architectural rule:
**Canonical skill existence is independent of problem generator availability.**

Five distinct states:
1. Skill exists in approved mathematical taxonomy
2. Problem generator exists for the skill
3. Practice is available and validated
4. Assessment and mastery are supported
5. Jurisdiction coverage has been demonstrated

Currently, the taxonomy (CanonicalSkill table) is populated FROM FAMILIES
via register_problem_families(). This means a skill without a generator
cannot exist in the taxonomy. Tests marked xfail define the REQUIRED
separation.

Do not modify product code to make these tests pass. Report failures to
the Architecture owner.
"""

import pytest

from app.canonical_problem_families import FAMILIES


def test_taxonomy_distinct_from_generator_registry():
    """
    The approved skill taxonomy must be queryable independently of FAMILIES.
    Currently FAILS: CanonicalSkill rows are created from FAMILIES, so the
    taxonomy cannot contain a skill without a generator.
    """
    # This test documents the architectural limitation.
    # When a separate TAXONOMY registry exists, this should verify that
    # taxonomy skills can exist without corresponding FAMILIES entries.
    pytest.xfail("Taxonomy is currently derived from FAMILIES; no independent registry")


def test_generator_registry_covers_registered_families():
    """FAMILIES contains the registered problem generators. (Currently passes.)"""
    assert len(FAMILIES) > 0
    for spec in FAMILIES.values():
        assert spec.canonical_skill_code.startswith("MATH.")


def test_mapping_target_may_lack_generator():
    """
    A valid mapping target must be allowed even if no generator exists.
    Currently FAILS: validator rejects skills not in FAMILIES.
    """
    # When the architecture separates TAXONOMY from FAMILIES, the validator
    # must accept taxonomy skills without generators.
    pytest.xfail("Validator currently requires generator; taxonomy separation needed")


def test_assessment_readiness_independent_of_generator():
    """
    Assessment support for a skill must not require a problem generator.
    A skill can be assessable (via authored items) without a generator.
    """
    # Placeholder for future assessment-readiness registry.
    # Currently, assessment items are tied to problem families.
    pytest.xfail("No independent assessment-readiness registry exists")


def test_coverage_requires_evidence_not_just_generator():
    """
    Curriculum coverage credit must require evidence, not just generator
    availability. A generator existing does not prove coverage.
    """
    # This is enforced by the #283 coverage gate (8 predicates).
    # This test documents the requirement.
    assert True  # Placeholder: coverage gate is separate (#283)


def test_skill_without_generator_not_silently_nonexistent():
    """
    A valid curriculum skill without a generator must not be treated as
    mathematically nonexistent. The system must distinguish:
    - Skill exists, no generator (valid, but no practice)
    - Skill does not exist (invalid)
    """
    pytest.xfail("No distinction between 'no generator' and 'nonexistent skill'")
