"""Author-only CA historical source inventory parity; not publisher acceptance."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
SOURCE_FILES = {
    "GRADE_7": ["ca_2013_grade7_24_source_author_slice.v1.json"],
    "GRADE_8": ["ca_2013_grade8_28_source_author_slice.v1.json"],
    "ALGEBRA_I": [
        "ca_2013_algebra1_pages64_65_source_author_slice.v1.json",
        "ca_2013_algebra1_pages66_68_source_author_slice.v1.json",
    ],
    "MATHEMATICS_I": ["ca_2013_mathematics1_pages90_94_author_audit.v1.json"],
}
EXPECTED = {"GRADE_7": 24, "GRADE_8": 28, "ALGEBRA_I": 62, "MATHEMATICS_I": 59}


def test_all_173_historic_ids_have_unique_provisional_source_locators():
    historic = json.loads((ROOT / "national_ca_grades7_9.author_intake.v1.json").read_text())
    historic_keys = [(row["track"], row["expectation_id"]) for row in historic["expectations"]]
    assert len(historic_keys) == len(set(historic_keys)) == 173
    assert dict(Counter(track for track, _ in historic_keys)) == EXPECTED

    authored = []
    for track, files in SOURCE_FILES.items():
        for filename in files:
            source = json.loads((ROOT / filename).read_text())
            assert source.get("independent_source_fidelity") == "PENDING" or (
                source.get("gates", {}).get("publisher_source_fidelity")
                == "AUTHOR_ONLY_NOT_INDEPENDENT"
            )
            assert source.get("activation") == "FORBIDDEN" or (
                source.get("gates", {}).get("curriculum_activation") == "FORBIDDEN"
            )
            for row in source["rows"]:
                assert row["track"] == track
                assert row["source_pdf_page_index"] == row["source_printed_page"] + 6
                assert row["source_review_status"].startswith("AUTHOR_")
                assert row["canonical_equivalence"] == "UNVERIFIED"
                assert row["assessment"] == "UNVERIFIED"
                assert row["mastery"] == "UNVERIFIED"
                authored.append((track, row["expectation_id"]))

    assert len(authored) == len(set(authored)) == 173
    assert dict(Counter(track for track, _ in authored)) == EXPECTED
    assert set(authored) == set(historic_keys)
    assert historic["status"] == "DRAFT_INCOMPLETE_SOURCE_FIDELITY"
