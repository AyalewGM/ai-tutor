"""Executable separation contracts for #282; no learner or DB writes."""
import pytest

from app.canonical_skill_taxonomy import (
    TAXONOMY,
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
    TaxonomyError,
)


def _skill(code: str, *, reviewed: bool = True) -> CanonicalSkillDefinition:
    return CanonicalSkillDefinition(
        code=code,
        name="Sample mathematical concept",
        description="An explicit mathematical definition for isolated contract testing",
        review_state=SkillReviewState.REVIEWED if reviewed else SkillReviewState.DRAFT,
        reviewed_by="independent-reviewer" if reviewed else None,
    )


def test_reviewed_skill_can_exist_without_generator():
    code = "MATH.TEST.GENERATORLESS"
    taxonomy = CanonicalTaxonomy("1.0.0", {code: _skill(code)})
    assert taxonomy.capability(code, set()) == (True, False)
    assert taxonomy.capability("MATH.TEST.NONEXISTENT", set()) == (False, False)


def test_generator_cannot_confer_mathematical_review():
    code = "MATH.TEST.UNREVIEWED"
    taxonomy = CanonicalTaxonomy("1.0.0", {code: _skill(code, reviewed=False)})
    assert taxonomy.capability(code, {code}) == (False, True)
    assert not taxonomy.contains(code)
    assert taxonomy.contains(code, reviewed_only=False)


def test_independent_taxonomy_not_generated_from_families():
    assert TAXONOMY.version == "0.1.0-draft"
    assert TAXONOMY.skills == {}


@pytest.mark.parametrize(
    ("code", "skill"),
    [
        ("MATH.TEST.A", _skill("MATH.TEST.B")),
        ("OTHER.TEST.A", _skill("OTHER.TEST.A")),
        ("MATH.TEST.A", CanonicalSkillDefinition(
            "MATH.TEST.A", "Name", "Definition", SkillReviewState.REVIEWED
        )),
    ],
)
def test_invalid_registry_fails_closed(code, skill):
    with pytest.raises(TaxonomyError):
        CanonicalTaxonomy("1.0.0", {code: skill})


def test_version_required():
    with pytest.raises(TaxonomyError):
        CanonicalTaxonomy("", {})
