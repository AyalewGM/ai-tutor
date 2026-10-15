"""Course standards have no automatically inferred numeric grade."""
from scripts import audit_curriculum_mapping_coverage as mod


def test_course_manifest_without_grade_keeps_null_grade(tmp_path, monkeypatch):
    standards = tmp_path / "standards"
    standards.mkdir()
    (standards / "md_algebra1_expectations.v1.json").write_text(
        '{"jurisdiction":"Maryland","expectations":['
        '{"expectation_id":"N.RN.B.3","grade_course":"Algebra I",'
        '"scope":"unverified"}]}'
    )
    packs = tmp_path / "packs"
    packs.mkdir()
    seeds = tmp_path / "seeds"
    seeds.mkdir()
    monkeypatch.setattr(mod, "STANDARDS_DIR", standards)
    monkeypatch.setattr(mod, "PACKS_DIR", packs)
    monkeypatch.setattr(mod, "SEEDS_DIR", seeds)
    monkeypatch.setattr(mod, "CANONICAL_GLOBS", [])
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    result = mod.audit()
    assert result["totals"]["inventoried_expectations"] == 1
    md = [c for c in result["cells"] if c["jurisdiction"] == "MD"]
    assert len(md) == 1
    assert md[0]["grade"] is None  # not inferred as Grade 9
    assert md[0]["inventoried_expectations"] == 1
    assert md[0]["accepted_mappings"] == 0
    assert md[0]["with_provisional_candidate"] == 0
    assert md[0]["status"] != "ACCEPTED_FULL"
