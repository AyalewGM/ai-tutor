"""Deterministic tests for #282 alias contract (no runtime mapping credit)."""
from scripts.validate_canonical_alias_map import validate_manifest


def record(
    status="UNMAPPED", relation=None, targets=None, evidence=None, reviewer=None
):
    return {
        "alias": "MATH.ELEMENTARY.TEST",
        "status": status,
        "relation": relation,
        "target_skill_codes": [] if targets is None else targets,
        "evidence": [] if evidence is None else evidence,
        "reviewed_by": reviewer,
    }


def check(items, *, publication_gate=False, pack_aliases=None, known_skills=None):
    return validate_manifest(
        {"schema_version": 1, "mapping_version": "draft-1", "aliases": items},
        {"MATH.ELEMENTARY.TEST"} if pack_aliases is None else pack_aliases,
        {"MATH.ARITHMETIC.ADD"} if known_skills is None else known_skills,
        publication_gate=publication_gate,
    )


def test_unmapped_inventory_valid_but_publication_blocked():
    assert check([record()]) == []
    assert any("publication blocked" in e for e in check([record()], publication_gate=True))


def test_reviewed_all_of_requires_real_targets_evidence_and_reviewer():
    valid = record(
        status="REVIEWED", relation="ALL_OF",
        targets=["MATH.ARITHMETIC.ADD"], evidence=["curriculum evidence"],
        reviewer="qualified-reviewer",
    )
    assert check([valid], publication_gate=True) == []
    assert any("unknown application skill" in e for e in check(
        [valid], known_skills=set()
    ))


def test_duplicates_missing_aliases_and_alternatives_fail_closed():
    errors = check(
        [record(), record()],
        pack_aliases={"MATH.ELEMENTARY.OTHER"},
    )
    assert any("duplicate alias" in e for e in errors)
    assert any("missing pack alias" in e for e in errors)
    assert any("alias not present" in e for e in errors)
    invalid = record(
        status="REVIEWED", relation="ALTERNATIVE",
        targets=["MATH.ARITHMETIC.ADD"], evidence=["unreviewed alternative"],
        reviewer="qualified-reviewer",
    )
    assert any("requires ALL_OF" in e for e in check([invalid]))


def test_unreviewed_mapping_cannot_publish():
    proposed = record(
        status="PROPOSED", relation="ALL_OF",
        targets=["MATH.ARITHMETIC.ADD"], evidence=["pending review"],
    )
    assert check([proposed]) == []
    assert any("publication blocked" in e for e in check(
        [proposed], publication_gate=True
    ))
