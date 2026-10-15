"""Grade 6 source-draft integration: author inventory only, not publisher acceptance."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
NEW = [
    "ca_2013_grade6_pages43_44_ee2_9_author_slice.v1.json",
    "ca_2013_grade6_pages44_45_geometry_statistics_author_slice.v1.json",
]


def test_grade6_new_author_records_and_boundaries():
    docs = [json.loads((BASE / name).read_text(encoding="utf-8")) for name in NEW]
    ids = [r["expectation_id"] for doc in docs for r in doc["rows"]]
    assert ids == ([f"6.EE.{i}" for i in range(2, 10)] +
                   [f"6.G.{i}" for i in range(1, 5)] +
                   [f"6.SP.{i}" for i in range(1, 6)])
    assert len(ids) == len(set(ids)) == 17
    assert next(r for r in docs[0]["rows"] if r["expectation_id"] == "6.EE.2")["source_printed_pages"] == [43, 44]
    assert "nonnegative rational" in next(r for r in docs[0]["rows"] if r["expectation_id"] == "6.EE.7")["author_mathematical_scope"]
    assert "strict inequalities" in next(r for r in docs[0]["rows"] if r["expectation_id"] == "6.EE.8")["required_material_conditions"]
    assert "fractional edges" in next(r for r in docs[1]["rows"] if r["expectation_id"] == "6.G.2")["required_material_conditions"]
    assert "subparts a b c d" in next(r for r in docs[1]["rows"] if r["expectation_id"] == "6.SP.5")["required_material_conditions"]
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        assert doc["canonical_equivalence"] == doc["assessment"] == doc["mastery"] == "UNVERIFIED"


def test_grade6_matrix_counts_unaccepted():
    matrix = json.loads((BASE / "national_ca_tx_wa_completion_matrix.v1.json").read_text(encoding="utf-8"))
    ca = matrix["states"]["CA"]
    assert ca["author_source_scope_rows_by_track"]["GRADE_6"] == 29
    assert ca["author_scope_total_staged"] == 334
    assert ca["accepted_source_fidelity_rows"] == 0
    assert all(name in ca["author_source_scope_files"]["GRADE_6"] for name in NEW)
    assert matrix["acceptance_contract"]["runtime_activation"] == "FORBIDDEN"


def test_grade6_independent_review_scope_defects_preserved():
    ee = json.loads((BASE / NEW[0]).read_text(encoding="utf-8"))
    geometry = json.loads((BASE / NEW[1]).read_text(encoding="utf-8"))
    e = next(r for r in ee["rows"] if r["expectation_id"] == "6.EE.2")
    e_material = set(e["required_material_conditions"])
    assert "sum term product factor quotient coefficient" in e_material
    assert "view one or more expression parts as a single entity" in e_material
    assert "sums/terms/products/factors/quotients/coefficients" in e["author_mathematical_scope"]
    g = {r["expectation_id"]: r for r in geometry["rows"]}
    assert {"compose into rectangles", "decompose into triangles and other shapes",
            "apply to real-world and mathematical problems"} <= set(g["6.G.1"]["required_material_conditions"])
    for code in ("6.G.3", "6.G.4"):
        assert "apply to real-world and mathematical problems" in g[code]["required_material_conditions"]
        assert "real-world and mathematical problems" in g[code]["author_mathematical_scope"]
    assert ee["independent_source_fidelity"] == geometry["independent_source_fidelity"] == "PENDING"
    assert ee["activation"] == geometry["activation"] == "FORBIDDEN"
