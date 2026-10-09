"""Draft candidates are visible without conferring mathematical authority."""
from app.canonical_skill_taxonomy import TAXONOMY
from app.canonical_taxonomy_candidates import CANDIDATE_TAXONOMY


def test_candidates_are_not_approved_taxonomy():
    assert len(CANDIDATE_TAXONOMY.skills) == 6
    assert all(not CANDIDATE_TAXONOMY.contains(code) for code in CANDIDATE_TAXONOMY.skills)
    assert all(CANDIDATE_TAXONOMY.contains(code, reviewed_only=False) for code in CANDIDATE_TAXONOMY.skills)
    assert not TAXONOMY.skills


def test_candidate_with_generator_does_not_gain_review():
    code = "MATH.ARITHMETIC.ADD_WITHIN_20"
    assert CANDIDATE_TAXONOMY.capability(code, {code}) == (False, True)


def test_architecture_rejected_composites_are_not_candidates():
    assert "MATH.ARITHMETIC.ADD_SUB_WITHIN_20" not in CANDIDATE_TAXONOMY.skills
    assert "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120" not in CANDIDATE_TAXONOMY.skills
