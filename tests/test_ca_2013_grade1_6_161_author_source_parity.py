"""CA Grades 1-6 author-source parity; NOT independent publisher acceptance."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
EXPECTED = {
    "GRADE_1": 21,
    "GRADE_2": 27,
    "GRADE_3": 29,
    "GRADE_4": 28,
    "GRADE_5": 27,
    "GRADE_6": 29,
}


def _pages(row, singular, plural):
    if plural in row:
        return row[plural]
    if singular in row:
        return [row[singular]]
    return None


def _locators(row):
    printed = (
        _pages(row, "source_printed_page", "source_printed_pages")
        or _pages(row, "printed_page", "printed_pages")
    )
    pdf = (
        _pages(row, "source_pdf_zero_based_page_index", "source_pdf_zero_based_indices")
        or _pages(row, "source_pdf_zero_based_index", "source_pdf_zero_based_pages")
        or _pages(row, "pdf_page_index", "pdf_page_indices")
    )
    return printed, pdf


def test_all_161_ca_grade1_6_author_rows_have_unique_ids_and_pdf_locators():
    matrix = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())
    ca = matrix["states"]["CA"]
    assert ca["accepted_source_fidelity_rows"] == 0
    assert ca["author_scope_acceptance"] == "DRAFT_ALL_ROWS_PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert ca["author_scope_total_staged"] == 334

    seen = set()
    counts = Counter()
    files = ca["author_source_scope_files"]
    for track, expected in EXPECTED.items():
        assert ca["author_source_scope_rows_by_track"][track] == expected
        for filename in files[track]:
            document = json.loads((ROOT / filename).read_text())
            assert document["independent_source_fidelity"] == "PENDING"
            assert document["activation"] == "FORBIDDEN"
            for row in document["rows"]:
                identifier = row["expectation_id"]
                assert identifier.startswith(track.split("_")[1] + ".")
                assert (track, identifier) not in seen
                seen.add((track, identifier))
                counts[track] += 1
                printed, pdf = _locators(row)
                assert printed and pdf, (filename, identifier)
                assert len(printed) == len(pdf), (filename, identifier)
                assert all(p + 6 == q for p, q in zip(printed, pdf)), (filename, identifier)
        assert counts[track] == expected

    assert len(seen) == sum(EXPECTED.values()) == 161
    assert dict(counts) == EXPECTED
    assert matrix["acceptance_contract"]["runtime_activation"] == "FORBIDDEN"
