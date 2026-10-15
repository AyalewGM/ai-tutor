"""Read-only OSPI final-2026 standards source acquisition; never promotes coverage.

Run manually on an authorized runner with network access. Downloads are evidence
candidates requiring publisher version and expectation-level human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

OFFICIAL_PAGE = (
    "https://ospi.k12.wa.us/student-success/resources-subject-area/"
    "mathematics/mathematics-k-12-learning-standards"
)
ALLOWED_HOST = "ospi.k12.wa.us"
EXTENSIONS = (".xlsx", ".xls", ".pdf", ".docx", ".doc")
MAX_BYTES = 35 * 1024 * 1024


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.label.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(self.label).strip()))
            self.href = None
            self.label = []


def official_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == ALLOWED_HOST


def candidate_links(html: str, page: str = OFFICIAL_PAGE) -> list[tuple[str, str]]:
    parser = Links()
    parser.feed(html)
    result = []
    for href, label in parser.links:
        url = urljoin(page, href)
        if (
            official_url(url)
            and "mathematics learning standards" in " ".join(label.lower().split())
            and "initial" not in label.lower()
            and "initial" not in url.lower()
        ):
            result.append((url, label))
    return list(dict.fromkeys(result))


def validate_candidate_url(url: str) -> str:
    """Accept publisher-hosted document URLs, never the 2025 initial draft."""
    parsed = urlparse(url)
    if not official_url(url) or not parsed.path.lower().endswith(EXTENSIONS):
        raise ValueError("Candidate must be an OSPI-hosted Office/PDF file")
    if "initial" in url.lower():
        raise ValueError("Initial-adoption documents are not final 2026 authority")
    return url


def signature_matches(path: Path) -> bool:
    suffix = path.suffix.lower()
    with path.open("rb") as stream:
        header = stream.read(8)
    if suffix in (".xlsx", ".docx"):
        return header.startswith(bytes.fromhex("504B0304"))
    if suffix == ".pdf":
        return header.startswith(b"%PDF-")
    if suffix in (".xls", ".doc"):
        return header.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))
    return False


def fetch(url: str, dest: Path, expected_sha256: str | None = None) -> dict:
    if not official_url(url):
        raise ValueError("Only the official OSPI HTTPS host is allowed")
    request = Request(url, headers={"User-Agent": "MihurStandardsEvidence/1.0"})
    with urlopen(request, timeout=35) as response:
        if not official_url(response.geturl()):
            raise ValueError("Redirect left official OSPI host")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds maximum size")
    dest.write_bytes(data)
    if not signature_matches(dest):
        dest.unlink(missing_ok=True)
        raise ValueError("Downloaded bytes do not match expected file signature")
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256.lower():
        dest.unlink(missing_ok=True)
        raise ValueError("Publisher candidate SHA256 differs from uploaded workbook")
    return {"url": url, "filename": dest.name, "bytes": len(data),
            "sha256": digest,
            "publisher_hash_matches_uploaded_workbook": expected_sha256 is not None,
            "status": "ACQUIRED_UNVERIFIED_SOURCE_BYTES",
            "expectation_source_fidelity": "PENDING_INDEPENDENT_REVIEW"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="source-evidence/ospi-2026")
    parser.add_argument("--candidate-url", action="append", default=[], help="Publisher-hosted final source candidate URL")
    parser.add_argument("--expected-sha256", default=None, help="Optional uploaded-workbook SHA256; mismatches fail closed")
    args = parser.parse_args()
    if args.expected_sha256 is not None:
        expected = args.expected_sha256.lower()
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            parser.error("--expected-sha256 must be a 64-character hexadecimal digest")
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    try:
        # Explicit publisher document candidates bypass landing-page access failures.
        # Acquired bytes remain unverified and never establish standards coverage.
        if args.candidate_url:
            candidates = [(validate_candidate_url(url), "Explicit OSPI document candidate")
                          for url in args.candidate_url]
        else:
            with urlopen(Request(OFFICIAL_PAGE, headers={"User-Agent": "MihurStandardsEvidence/1.0"}), timeout=35) as response:
                if not official_url(response.geturl()):
                    raise ValueError("OSPI page redirected outside publisher host")
                html = response.read(3_000_000).decode("utf-8", "replace")
            candidates = candidate_links(html)
        evidence = []
        for i, (url, label) in enumerate(candidates):
            suffix = Path(urlparse(url).path).suffix.lower()
            if suffix not in EXTENSIONS:
                continue
            try:
                destination = folder / f"ospi_candidate_{i}{suffix}"
                if suffix == ".xlsx" and args.expected_sha256 is not None:
                    entry = fetch(url, destination, args.expected_sha256)
                else:
                    entry = fetch(url, destination)
                entry["anchor_label"] = label
                evidence.append(entry)
            except (HTTPError, URLError, OSError, ValueError) as exc:
                evidence.append({"url": url, "status": "FETCH_FAILED",
                                 "error": str(exc)[:250]})
        result = {"publisher_page": OFFICIAL_PAGE, "status": "SOURCE_CANDIDATES_ONLY",
                  "candidates": evidence, "accepted_expectation_rows": 0}
        (folder / "acquisition.json").write_text(json.dumps(result, indent=2) + "\n")
        if not any(e.get("status") == "ACQUIRED_UNVERIFIED_SOURCE_BYTES" for e in evidence):
            raise RuntimeError("No official OSPI source bytes acquired")
    except Exception as exc:
        (folder / "failure.json").write_text(json.dumps({
            "status": "BLOCKED", "publisher_page": OFFICIAL_PAGE,
            "error": str(exc)[:350], "accepted_expectation_rows": 0
        }, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
