"""Maryland 2025 source-fidelity completeness gate; author corrections are not approval."""
import json
from collections import Counter
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "md_grades6_8_2025.source_fidelity_locators.v1.json")


def test_maryland_79_parent_113_subpart_review_gate_remains_closed():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = data["records"]
    assert len(rows) == 79
    assert Counter(row["grade"] for row in rows) == {6: 30, 7: 22, 8: 27}
    assert len({row["expectation_id"] for row in rows}) == 79
    indexed = [code for row in rows for code in row["official_subpart_ids"]]
    assert len(indexed) == len(set(indexed)) == 113
    assert all(code.startswith(row["expectation_id"] + ".")
               for row in rows for code in row["official_subpart_ids"])
    assert all(row["independent_acceptance"] == "PENDING" for row in rows)

    # Structured reviewer corrections are evidence, never an acceptance switch.
    corrections = [row for row in rows
                   if "retrospective_reviewer_requested_2025_scope" in row]
    assert len(corrections) == 15
    for row in corrections:
        evidence = row["retrospective_reviewer_requested_2025_scope"]
        assert evidence["independent_source_fidelity"] == "PENDING"
        assert evidence["activation"] == "FORBIDDEN"
        assert evidence["canonical_equivalence"] == "UNVERIFIED"
        assert evidence["assessment"] == "UNVERIFIED"
        assert evidence["mastery"] == "UNVERIFIED"
        assert evidence["publisher_column"] == "2025 Standards Statement"
        assert evidence["source_url"] == row["source_url"]
        assert evidence["printed_page_start"] == row["printed_page_start"]
        assert evidence["printed_page_end"] == row["printed_page_end"]
        assert set(evidence["requirements"]) <= (
            set(row["official_subpart_ids"]) | {"parent"}
        )
