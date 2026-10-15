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


def test_direct_candidate_bypasses_blocked_landing_page(monkeypatch, tmp_path: Path):
    import json
    import sys

    import scripts.acquire_ospi_2026_standards as acquisition

    url = "https://ospi.k12.wa.us/sites/default/files/2026-08/final-math.xlsx"
    seen = []

    def fake_fetch(candidate, dest):
        seen.append(candidate)
        return {"url": candidate, "filename": dest.name,
                "status": "ACQUIRED_UNVERIFIED_SOURCE_BYTES"}

    def blocked_landing(*args, **kwargs):
        raise AssertionError("landing page must not be called for direct candidate")

    monkeypatch.setattr(acquisition, "urlopen", blocked_landing)
    monkeypatch.setattr(acquisition, "fetch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["acquire", "--output", str(tmp_path),
                                      "--candidate-url", url])
    acquisition.main()
    assert seen == [url]
    result = json.loads((tmp_path / "acquisition.json").read_text())
    assert result["accepted_expectation_rows"] == 0


def test_direct_initial_adoption_url_fails_closed_before_fetch(monkeypatch, tmp_path: Path):
    import json
    import sys

    import pytest

    import scripts.acquire_ospi_2026_standards as acquisition

    def no_fetch(*args, **kwargs):
        raise AssertionError("should never download initial-adoption document")

    monkeypatch.setattr(acquisition, "fetch", no_fetch)
    monkeypatch.setattr(sys, "argv", ["acquire", "--output", str(tmp_path),
        "--candidate-url",
        "https://ospi.k12.wa.us/sites/default/files/2025-12/math25-initial-adoption-spreadsheet.xlsx"])
    with pytest.raises(ValueError, match="Initial-adoption"):
        acquisition.main()
    failure = json.loads((tmp_path / "failure.json").read_text())
    assert failure["status"] == "BLOCKED"
    assert failure["accepted_expectation_rows"] == 0


def test_uploaded_workbook_hash_mismatch_fails_closed(monkeypatch, tmp_path: Path):
    import hashlib

    import pytest

    import scripts.acquire_ospi_2026_standards as acquisition

    url = "https://ospi.k12.wa.us/sites/default/files/2026-08/math26-final-adoption-spreadsheet.xlsx"
    content = bytes.fromhex("504B0304") + b"workbook-bytes"
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def geturl(self):
            return url
        def read(self, size):
            return content
    monkeypatch.setattr(acquisition, "urlopen", lambda *args, **kwargs: Response())
    output = tmp_path / "candidate.xlsx"
    expected = hashlib.sha256(content).hexdigest()
    result = acquisition.fetch(url, output, expected)
    assert result["sha256"] == expected
    assert result["publisher_hash_matches_uploaded_workbook"] is True
    assert result["expectation_source_fidelity"] == "PENDING_INDEPENDENT_REVIEW"
    with pytest.raises(ValueError, match="SHA256 differs"):
        acquisition.fetch(url, output, "0" * 64)
    assert not output.exists()


def test_official_ospi_label_with_narrow_no_break_space_is_discovered():
    # Publisher's visible label contains U+202F between Learning and Standards.
    html = (
        '<a href="/sites/default/files/2026-08/math26-final-adoption-spreadsheet.xlsx">'
        'Mathematics Learning\u202fStandards Spreadsheet</a>'
    )
    links = candidate_links(html)
    assert links == [(
        "https://ospi.k12.wa.us/sites/default/files/2026-08/math26-final-adoption-spreadsheet.xlsx",
        "Mathematics Learning\u202fStandards Spreadsheet",
    )]
