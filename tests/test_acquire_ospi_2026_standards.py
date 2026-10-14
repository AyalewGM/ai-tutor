"""Local-only tests for the OSPI source acquisition helper."""
from pathlib import Path

from scripts.acquire_ospi_2026_standards import (
    candidate_links,
    official_url,
    signature_matches,
    validate_candidate_url,
)


def test_only_official_https_ospi_sources_allowed():
    assert official_url("https://ospi.k12.wa.us/sites/default/files/final.xlsx")
    assert not official_url("http://ospi.k12.wa.us/final.xlsx")
    assert not official_url("https://ospi.k12.wa.us.evil.test/final.xlsx")
    assert not official_url("https://example.org/final.xlsx")


def test_candidate_links_filter_off_domain_and_preserve_labels():
    html = """
    <a href="/sites/default/files/2026/final.xlsx">Mathematics Learning Standards Spreadsheet</a>
    <a href="https://example.org/fake.xlsx">Mathematics Learning Standards Spreadsheet</a>
    <a href="/sites/default/files/2025/initial.pdf">Old draft</a>
    """
    links = candidate_links(html)
    assert len(links) == 1
    assert links[0][0] == "https://ospi.k12.wa.us/sites/default/files/2026/final.xlsx"


def test_source_signature_validation(tmp_path: Path):
    workbook = tmp_path / "final.xlsx"
    workbook.write_bytes(bytes.fromhex("504B0304") + b"sample")
    assert signature_matches(workbook)
    workbook.write_text("<html>blocked</html>")
    assert not signature_matches(workbook)
    pdf = tmp_path / "final.pdf"
    pdf.write_bytes(b"%PDF-1.7 example")
    assert signature_matches(pdf)


def test_direct_candidate_url_is_restricted_to_ospi_non_initial_documents():
    valid = "https://ospi.k12.wa.us/sites/default/files/2026-06/final-math.xlsx"
    assert validate_candidate_url(valid) == valid
    import pytest

    for bad in (
        "https://example.org/final-math.xlsx",
        "http://ospi.k12.wa.us/sites/default/files/final.xlsx",
        "https://ospi.k12.wa.us/sites/default/files/2025-12/math25-initial-adoption-spreadsheet.xlsx",
        "https://ospi.k12.wa.us/sites/default/files/index.html",
    ):
        with pytest.raises(ValueError):
            validate_candidate_url(bad)
