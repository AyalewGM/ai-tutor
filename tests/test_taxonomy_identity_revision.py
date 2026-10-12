"""Historical canonical identity invariants for #282, without DB writes."""
from uuid import UUID

import pytest

from app.canonical_skill_taxonomy import (
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
    TaxonomyError,
)
from app.canonical_taxonomy_reconciliation import (
    PersistedSkillIdentity,
    validate_identity_revision,
)


def _taxonomy():
    code = "MATH.TEST.NEW"
    return CanonicalTaxonomy(
        "1.0.0",
        {code: CanonicalSkillDefinition(
            code, "New skill", "Independently defined mathematics",
            SkillReviewState.REVIEWED, "math-reviewer"
        )},
    )


def test_existing_uuid_preserved_and_reviewed_generatorless_skill_added():
    old = PersistedSkillIdentity("MATH.TEST.EXISTING", UUID(int=1))
    new = PersistedSkillIdentity("MATH.TEST.NEW", UUID(int=2))
    validate_identity_revision(
        {old.code: old}, {old.code: old, new.code: new}, _taxonomy()
    )


@pytest.mark.parametrize(
    "proposed",
    [
        {},
        {"MATH.TEST.EXISTING": PersistedSkillIdentity("MATH.TEST.EXISTING", UUID(int=9))},
        {"MATH.TEST.EXISTING": PersistedSkillIdentity("MATH.TEST.EXISTING", UUID(int=1)),
         "MATH.TEST.NEW": PersistedSkillIdentity("MATH.TEST.NEW", UUID(int=1))},
        {"MATH.TEST.EXISTING": PersistedSkillIdentity("MATH.TEST.EXISTING", UUID(int=1)),
         "MATH.TEST.UNREVIEWED": PersistedSkillIdentity("MATH.TEST.UNREVIEWED", UUID(int=3))},
    ],
)
def test_unsafe_identity_revision_rejected(proposed):
    old = PersistedSkillIdentity("MATH.TEST.EXISTING", UUID(int=1))
    with pytest.raises(TaxonomyError):
        validate_identity_revision({old.code: old}, proposed, _taxonomy())
