"""California Mathematics I printed p.93 author-source parity and fail-closed tests.

Structural assertions are not independent CDE publisher-fidelity acceptance.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
BATCHES = (
    "ca_math1_p93_functions_3_author_notes.v1.json",
    "ca_math1_p93_gco1_8_author_notes.v1.json",
    "ca_math1_p93_gco12_13_author_notes.v1.json",
)
EXPECTED_IDS = (
    "F-LE.2", "F-LE.3", "F-LE.5",
    "G-CO.1", "G-CO.2", "G-CO.3", "G-CO.4",
    "G-CO.5", "G-CO.6", "G-CO.7", "G-CO.8",
    "G-CO.12", "G-CO.13",
)


def _read(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))


def test_ca_math1_page93_ids_match_existing_author_audit():
    batches = [_read(filename) for filename in BATCHES]
    ids = [row["expectation_id"] for batch in batches for row in batch["rows"]]
    audit = _read("ca_2013_mathematics1_pages90_94_author_audit.v1.json")
    assert ids == list(EXPECTED_IDS)
    assert len(ids) == len(set(ids)) == 13
    assert ids == [
        row["expectation_id"]
        for row in audit["rows"]
        if row["source_printed_page"] == 93
    ]
    matrix = _read("national_ca_tx_wa_completion_matrix.v1.json")["states"]["CA"]
    assert matrix["author_source_scope_rows_by_track"]["MATHEMATICS_I"] == 59
    assert matrix["author_scope_total_staged"] == 334


def test_ca_math1_page93_publisher_locators_and_gates_remain_provisional():
    for batch in (_read(filename) for filename in BATCHES):
        assert batch["jurisdiction"] == "CA"
        assert batch["track"] == "MATHEMATICS_I"
        assert batch["source_printed_page"] == 93
        assert batch["source_pdf_zero_based_page_index"] == 99
        assert batch["supplemental_existing_placements_only"] is True
        assert batch["independent_source_fidelity"] == "PENDING"
        assert batch["activation"] == "FORBIDDEN"
        assert all(
            batch[key] == "UNVERIFIED"
            for key in ("canonical_equivalence", "assessment", "mastery")
        )


def test_ca_math1_page93_material_boundaries_are_not_lost():
    rows = {
        row["expectation_id"]: " ".join(row["material_conditions"]).lower()
        for batch in (_read(filename) for filename in BATCHES)
        for row in batch["rows"]
    }
    assert all(token in rows["F-LE.2"] for token in ("arithmetic", "geometric", "input-output"))
    assert all(token in rows["F-LE.3"] for token in ("eventually", "quadratic", "polynomial"))
    assert "f(x)=b^x+k" in rows["F-LE.5"]
    assert all(token in rows["G-CO.2"] for token in ("distance", "angle", "stretch"))
    assert "if and only if" in rows["G-CO.7"]
    assert all(token in rows["G-CO.8"] for token in ("asa", "sas", "sss", "rigid"))
    assert all(token in rows["G-CO.12"] for token in ("perpendicular bisector", "parallel line"))
    assert all(token in rows["G-CO.13"] for token in ("equilateral", "square", "hexagon", "inscribed"))
