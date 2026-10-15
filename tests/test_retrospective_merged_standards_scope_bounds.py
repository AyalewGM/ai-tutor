"""Retrospective source fidelity after merged standards PRs; no mapping approval."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def _rows(file):
    data = json.loads((ROOT / file).read_text(encoding="utf-8"))
    return {r["expectation_id"]: r for r in data["records"]}


def test_dc_original_ccss_subpart_boundaries():
    r = _rows("dc_grades6_8_ccss.source_fidelity_locators.v1.json")
    assert "unknown number" in r["6.EE.B.6"]["retrospective_bounded_scope_evidence"]["requirements"]["variable_role"]
    assert "unit-fraction cubes" in r["6.G.A.2"]["retrospective_bounded_scope_evidence"]["requirements"]["unit_fraction_cube_packing"]
    for id_, suffix in (("6.SP.B.5", ["a", "b", "c", "d"]),
                        ("7.SP.C.8", ["a", "b", "c"]),
                        ("8.EE.C.7", ["a", "b"]),
                        ("8.EE.C.8", ["a", "b", "c"])):
        ev = r[id_]["retrospective_bounded_scope_evidence"]
        assert all(f"{id_}.{s}" in ev["requirements"] for s in suffix)
        assert ev["downstream_full_coverage_allowed"] is False
        assert ev["scope_verification"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert "non-complex" in r["6.RP.A.2"]["retrospective_bounded_scope_evidence"]["requirements"]["unit_rate_noncomplex"]


def test_maryland_2025_is_not_historical_2010_requirements():
    r = _rows("md_grades6_8_2025.source_fidelity_locators.v1.json")
    for id_ in ("6.NOS.B.4", "6.AT.C.8", "6.AT.C.10", "6.DS.B.6",
                "8.DS.B.2", "8.DS.C.5", "8.DS.C.6"):
        ev = r[id_]["retrospective_source_scope_evidence"]
        assert ev["source_column"].startswith("2025 MD Standards Statement")
        assert ev["downstream_full_coverage_allowed"] is False
        assert ev["independent_acceptance"] == "PENDING"
    assert "MAD" in r["6.DS.B.6"]["retrospective_source_scope_evidence"]["requirements"]["6.DS.B.6.c"]
    assert "same subjects" in r["8.DS.C.5"]["retrospective_source_scope_evidence"]["requirements"]["two_way_table_population"]


def test_ontario_c42_nonlinear_and_boundary_families():
    r = _rows("on_mth1w_2021.source_fidelity_locators.v1.json")
    ev = r["MTH1W.C4.2"]["retrospective_bounded_scope_evidence"]
    assert ev["equation_families"] == ["x=k", "y=k", "x+y=k", "x-y=k", "ax+by=k", "xy=k"]
    assert "nonlinear" in ev["nonlinear_boundary"]
    assert ev["mastery"] == "UNVERIFIED"
    assert ev["runtime_activation"] == "FORBIDDEN"
