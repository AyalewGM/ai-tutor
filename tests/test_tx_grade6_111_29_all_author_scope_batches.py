"""Cross-batch author editorial coverage for TX 2025 Advanced Grade 6 §111.29.

This is not independent publisher source fidelity, curriculum activation,
or evidence that canonical learning packages assess these expectations.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
INDEX = BASE / "tx_advanced_2025_grade6_111_29_id_author_queue.v1.json"
BATCHES = [
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_01.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_02.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_03_expressions.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_04_relations.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_05_geometry_data_finance.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_06_process.v1.json",
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_sixty_eight_author_scopes_match_unique_queue_ids_not_accepted():
    queue = read(INDEX)
    author = [read(path) for path in BATCHES]
    expected = {r["expectation_id"]: r for r in queue["rows"]}
    rows = [r for batch in author for r in batch["rows"]]
    ids = [r["expectation_id"] for r in rows]
    assert len(expected) == len(ids) == len(set(ids)) == 68
    assert set(ids) == set(expected)
    assert [len(b["rows"]) for b in author] == [17, 9, 3, 11, 21, 7]
    for row in rows:
        source = expected[row["expectation_id"]]
        assert row["parent_group"] == source["parent_group"]
        assert row["lettered_subpart"] == source["lettered_subpart"]
        assert row["source_pdf_zero_based_pages"] == source["source_pdf_zero_based_pages"]
        assert row["author_mathematical_scope"].strip()
        assert row["source_scope_status"] == "AUTHOR_EDITORIAL_PARAPHRASE_AWAITING_INDEPENDENT_SOURCE_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
    assert queue["independent_source_fidelity"] == "PENDING"
    assert all(b["independent_source_fidelity"] == "PENDING" for b in author)
    assert all(b["activation"] == "FORBIDDEN" for b in author)
    assert all(all(b[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery")) for b in author)


def test_grade6_advanced_geometry_data_finance_boundary_conditions():
    b = read(BATCHES[-2])
    assert (b["previous_author_scoped"], b["new_author_scoped"], b["remaining_unscoped"]) == (40, 21, 7)
    scopes = {r["expectation_id"]: r["author_mathematical_scope"].lower() for r in b["rows"]}
    assert "decomposing" in scopes["111.29(c)(11)(A)"]
    assert "positive rational" in scopes["111.29(c)(11)(B)"]
    assert "triangle" in scopes["111.29(c)(12)(A)"]
    assert "triangular prisms" in scopes["111.29(c)(12)(C)"]
    assert "variability" in scopes["111.29(c)(13)(A)"]
    assert all(t in scopes["111.29(c)(13)(B)"] for t in ("dot plots", "stem-and-leaf", "histograms", "box plots"))
    assert all(t in scopes["111.29(c)(14)(B)"] for t in ("mean", "median", "range", "interquartile range"))
    assert all(t in scopes["111.29(c)(14)(F)"] for t in ("categorical", "relative frequency", "percent bar"))
    assert "how long" in scopes["111.29(c)(15)(D)"]
    assert "lifetime income" in scopes["111.29(c)(15)(G)"]


def test_grade6_advanced_process_expectations_are_not_new_canonical_skills():
    b = read(BATCHES[-1])
    expected = [f"111.29(c)(1)({p})" for p in "ABCDEFG"]
    assert [r["expectation_id"] for r in b["rows"]] == expected
    assert (b["previous_author_scoped"], b["new_author_scoped"], b["remaining_unscoped"]) == (61, 7, 0)
    assert b["total_grade6_advanced_candidate_ids"] == 68
    assert "not new canonical mathematical skills" in b["source_provenance"]
    scopes = {r["lettered_subpart"]: r["author_mathematical_scope"].lower() for r in b["rows"]}
    assert "reasonableness" in scopes["B"]
    assert "technology" in scopes["C"]
    assert "representations" in scopes["E"]
    assert "oral" in scopes["G"]
