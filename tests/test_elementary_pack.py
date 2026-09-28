import json
from pathlib import Path

import pytest

from app.content_validation import ContentValidationError
from app.elementary_pack import ElementaryPack, parse_pack, validate_pack

EXAMPLE = (
    Path(__file__).parents[1]
    / "docs/curriculum/examples/elementary_pack.schema-v1.example.json"
)


def _payload():
    return json.loads(EXAMPLE.read_text())


def test_example_pack_parses_and_validates():
    pack = parse_pack(EXAMPLE)
    assert pack.schema_version == 1
    assert pack.curriculum.grade_level == "3"
    assert pack.skills[0].problem_families == ("WORD_PROBLEM",)


def test_schema_rejects_unknown_fields(tmp_path):
    payload = _payload()
    payload["unexpected"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ContentValidationError, match="Invalid elementary curriculum pack"):
        parse_pack(path)


def test_validation_rejects_unknown_problem_family():
    payload = _payload()
    payload["skills"][0]["problem_families"] = ["LLM_DECIDES_MATH"]
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="unsupported problem families"):
        validate_pack(pack)


def test_validation_rejects_problem_outside_skill_family_allowlist():
    payload = _payload()
    payload["skills"][0]["problems"][0]["family"] = "INTEGER_OPERATIONS"
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="not eligible"):
        validate_pack(pack)


def test_validation_rejects_thin_or_reused_mode_inventory():
    payload = _payload()
    payload["skills"][0]["problems"] = payload["skills"][0]["problems"][:3]
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="thin curated inventory"):
        validate_pack(pack)

    payload = _payload()
    payload["skills"][0]["problems"][0]["modes"] = ["diagnostic", "mastery"]
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="reuses problems"):
        validate_pack(pack)


def test_validation_rejects_unknown_and_cyclic_prerequisites():
    payload = _payload()
    payload["skills"][0]["prerequisite_codes"] = ["OUTSIDE.PACK"]
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="outside this pack"):
        validate_pack(pack)

    payload = _payload()
    second = json.loads(json.dumps(payload["skills"][0]))
    second["code"] = "SYNTH3.NUM.SECOND"
    second["canonical"]["code"] = "MATH.SYNTHETIC.SECOND"
    second["prerequisite_codes"] = [payload["skills"][0]["code"]]
    for problem in second["problems"]:
        problem["key"] += "-second"
    payload["skills"][0]["prerequisite_codes"] = [second["code"]]
    payload["skills"].append(second)
    pack = ElementaryPack.model_validate(payload)
    with pytest.raises(ContentValidationError, match="contains a cycle"):
        validate_pack(pack)
