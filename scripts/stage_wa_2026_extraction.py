"""Stage the exact WA 2026 extraction in the repository without accepting mappings.

Usage:
  python scripts/stage_wa_2026_extraction.py /path/to/wa_2026_v3_1_source_extraction.json

The staged file must be committed and independently reviewed before use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.validate_wa_2026_source_extraction import validate

EXPECTED_WORKBOOK_SHA256 = "d522101f430758dcbc21d7ecc800977761b3ccdb224de2b3e6fd6217faa80875"
TARGET = Path("docs/curriculum/standards/wa_2026_v3_1_source_extraction.json")


def stage(source: Path, destination: Path = TARGET) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    if data["source"]["sha256"] != EXPECTED_WORKBOOK_SHA256:
        raise ValueError("Uploaded source checksum does not match audited workbook")
    report = validate(data)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing source: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    destination.write_text(payload, encoding="utf-8")
    report["staged_json_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    report["staged_path"] = str(destination)
    report["review_status"] = "AUTHOR_STAGED_PENDING_INDEPENDENT_REVIEW"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.source), indent=2))


if __name__ == "__main__":
    main()
