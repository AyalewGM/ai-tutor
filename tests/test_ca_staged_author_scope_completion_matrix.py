"""Cross-file California author draft inventory parity; never an approval oracle."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_california_staged_scope_counts_are_unique_and_unaccepted():
    matrix = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())
    ca = matrix["states"]["CA"]
    expected = {"GRADE_1": 21, "GRADE_2": 27, "GRADE_3": 29, "GRADE_4": 11, "GRADE_7": 24, "GRADE_8": 28,
                "ALGEBRA_I": 62, "MATHEMATICS_I": 59}
    assert ca["author_source_scope_rows_by_track"] == expected
    assert ca["author_scope_total_staged"] == sum(expected.values()) == 261
    assert ca["accepted_source_fidelity_rows"] == 0
    assert ca["grade2_partial_author_source_scope_rows"] == 10
    assert ca["grade2_author_scope_total"] == 27
    assert ca["grade2_partial_not_complete"] is False
    assert ca["grade2_scope_fidelity_accepted_rows"] == 0
    assert ca["grade2_author_scope_status"].endswith("ZERO_INDEPENDENT_SOURCE_ACCEPTANCE")
    assert ca["grade9_course_equivalence"] == "NOT_ASSUMED"
    for track, count in expected.items():
        rows = []
        for filename in ca["author_source_scope_files"][track]:
            data = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            if track == "MATHEMATICS_I":
                assert data["gates"]["publisher_source_fidelity"] == "AUTHOR_ONLY_NOT_INDEPENDENT"
                assert data["gates"]["curriculum_activation"] == "FORBIDDEN"
            else:
                assert data["independent_source_fidelity"] == "PENDING"
                assert data["activation"] == "FORBIDDEN"
            rows.extend(data["rows"])
        identifiers = [r["expectation_id"] for r in rows]
        assert len(identifiers) == len(set(identifiers)) == count
    assert ca["unextracted_tracks"] == [
        "GRADE_4", "GRADE_5", "GRADE_6"
    ]
