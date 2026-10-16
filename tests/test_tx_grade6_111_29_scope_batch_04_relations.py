"""Fail-closed source-intake tests: TX Advanced Grade 6 §111.29(c)(8)-(10).

Author editorial scope evidence only; these assertions do not approve TEKS fidelity,
canonical mathematics, learner experiences, assessments, or mastery.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
QUEUE = BASE / "tx_advanced_2025_grade6_111_29_id_author_queue.v1.json"
BATCHES = [
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_01.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_02.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_03_expressions.v1.json",
    BASE / "tx_advanced_2025_grade6_111_29_scope_batch_04_relations.v1.json",
]


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_advanced_grade6_relations_identifiers_from_official_author_queue():
    queue, batch = _read(QUEUE), _read(BATCHES[-1])
    expected = [f"111.29(c)(8)({p})" for p in "ABCDEF"]
    expected += [f"111.29(c)(9)({p})" for p in "ABCD"]
    expected += ["111.29(c)(10)"]
    assert [r["expectation_id"] for r in batch["rows"]] == expected
    index = {r["expectation_id"]: r for r in queue["rows"]}
    assert len(index) == 68
    for row in batch["rows"]:
        indexed = index[row["expectation_id"]]
        assert row["parent_group"] == indexed["parent_group"]
        assert row["lettered_subpart"] == indexed["lettered_subpart"]
        assert row["source_pdf_zero_based_pages"] == indexed["source_pdf_zero_based_pages"]
        assert row["author_mathematical_scope"].strip()
    assert batch["rows"][-1]["lettered_subpart"] is None
    assert "111.29(c)(10)(A)" not in index


def test_advanced_grade6_author_scope_accounting_and_isolation():
    batches = [_read(path) for path in BATCHES]
    identifiers = [r["expectation_id"] for b in batches for r in b["rows"]]
    assert len(identifiers) == len(set(identifiers)) == 40
    assert [len(b["rows"]) for b in batches] == [17, 9, 3, 11]
    b = batches[-1]
    assert (b["previous_author_scoped"], b["new_author_scoped"], b["remaining_unscoped"]) == (29, 11, 28)
    assert b["total_grade6_advanced_candidate_ids"] == 68
    assert b["independent_source_fidelity"] == "PENDING"
    assert b["source_fidelity_status"] == "AUTHOR_EDITORIAL_NOT_INDEPENDENTLY_VERIFIED"
    assert b["activation"] == "FORBIDDEN"
    assert all(b[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
    for row in b["rows"]:
        assert row["source_scope_status"] == "AUTHOR_EDITORIAL_PARAPHRASE_AWAITING_INDEPENDENT_SOURCE_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))


def test_advanced_grade6_required_relation_distinctions():
    batch = _read(BATCHES[-1])
    scopes = {r["expectation_id"]: r["author_mathematical_scope"].lower() for r in batch["rows"]}
    assert all("inequalit" in scopes[f"111.29(c)(8)({p})"] for p in "ABCDEF")
    assert "number lines" in scopes["111.29(c)(8)(C)"]
    assert "geometric" in scopes["111.29(c)(8)(D)"]
    assert "substitute" in scopes["111.29(c)(8)(F)"]
    assert "independent" in scopes["111.29(c)(9)(A)"]
    assert "dependent" in scopes["111.29(c)(9)(B)"]
    assert "y = kx" in scopes["111.29(c)(9)(C)"]
    assert "y = x + b" in scopes["111.29(c)(9)(C)"]
    assert "y = ax" in scopes["111.29(c)(9)(D)"]
    assert "y = x + a" in scopes["111.29(c)(9)(D)"]
    assert "d = rt" in scopes["111.29(c)(10)"]
    assert "pictorial" in scopes["111.29(c)(10)"]
    assert "graphical" in scopes["111.29(c)(10)"]
