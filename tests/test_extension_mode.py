import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.canonical_problem_families import ALL_MODES, LearningMode
from app.elementary_pack import ElementaryPack, parse_pack, validate_pack
from app.models import TutorState

EXAMPLE = (
    Path(__file__).parents[1]
    / "docs/curriculum/examples/elementary_pack.schema-v1.example.json"
)


def _payload():
    return json.loads(EXAMPLE.read_text())


def _extension_problem():
    return {
        "key": "ext-001",
        "family": "WORD_PROBLEM",
        "prompt": "Harder variant: a two-step word problem beyond the mastery band.",
        "canonical_answer": "42",
        "difficulty": 9,
        "objective": "Stretch: multi-step modeling above grade band.",
        "modes": ["extension"],
    }


def test_extension_mode_enum_exists():
    assert LearningMode.EXTENSION == "EXTENSION"
    assert TutorState.EXTENSION == "EXTENSION"


def test_families_can_generate_extension_variants():
    # Family modes are generation capability: any family can produce a
    # stretch variant, and extension variants are distinct from evidence
    # variants so the opt-in tier can always draw fresh items. Pool
    # isolation is enforced at selection and evidence layers.
    from app.canonical_problem_families import FAMILIES, generate

    assert LearningMode.EXTENSION in ALL_MODES
    spec = FAMILIES["MATH.DATA.BAR.READ"]
    difficulty = spec.min_difficulty
    extension_variant = generate("MATH.DATA.BAR.READ", seed=7, difficulty=difficulty, mode=LearningMode.EXTENSION)
    evidence_variant = generate("MATH.DATA.BAR.READ", seed=7, difficulty=difficulty, mode=LearningMode.INDEPENDENT)
    assert extension_variant.variant_id != evidence_variant.variant_id


def test_pack_accepts_extension_only_problem():
    payload = _payload()
    payload["skills"][0]["problems"].append(_extension_problem())
    pack = ElementaryPack.model_validate(payload)
    validate_pack(pack)


def test_extension_cannot_be_required():
    payload = _payload()
    payload["readiness"] = {
        "minimum_curated_per_skill": 4,
        "required_modes": ["diagnostic", "guided", "independent", "mastery", "extension"],
    }
    with pytest.raises(ValidationError, match="extension"):
        ElementaryPack.model_validate(payload)


def test_extension_cannot_share_required_pool():
    payload = _payload()
    bad = _extension_problem()
    bad["modes"] = ["extension", "mastery"]
    payload["skills"][0]["problems"].append(bad)
    with pytest.raises(ValidationError, match="extension"):
        ElementaryPack.model_validate(payload)


def test_pack_still_validates_without_extension():
    pack = parse_pack(EXAMPLE)
    validate_pack(pack)
