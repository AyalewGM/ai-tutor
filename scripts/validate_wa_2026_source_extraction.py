"""Validate author-extracted WA 2026 v3.1 standards JSON, without accepting coverage.

Usage: python scripts/validate_wa_2026_source_extraction.py /path/to/wa_2026_v3_1_source_extraction.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def validate(data: dict) -> dict:
    assert data["source"]["workbook_label"] == "August 2026 | v3.1"
    assert data["source"]["publisher_byte_match"] == "NOT_INDEPENDENTLY_VERIFIED"
    assert data["acceptance"]["activation"] == "FORBIDDEN"
    k8 = data["k8"]
    hs = data["high_school_course_rows"]
    crosswalk = data["crosswalk"]
    assert (len(k8), len(hs), len(crosswalk)) == (264, 464, 425)
    assert data["counts"] == {"k8": 264, "hs": 464, "crosswalk": 425}
    assert len({r["code"] for r in k8}) == 264
    assert len({r["code"] for r in hs}) == 160
    assert len({(r["course"], r["code"]) for r in hs}) == 464
    assert all(r["code"] and r["scope"] and r["grade"] for r in k8)
    assert all(r["code"] and r["scope"] and r["course"] for r in hs)
    assert set(r["grade"] for r in k8) == {"K", "1", "2", "3", "4", "5", "6", "7", "8"}
    known_codes = {r["code"] for r in k8} | {r["code"] for r in hs}
    missing = [r for r in crosswalk if r["wa_2026_code"] not in known_codes]
    assert len(missing) == 1
    removed = missing[0]
    assert removed["grade"] == "7"
    assert removed["ccss_code"] == "7.NS.A.3"
    assert removed["wa_2026_code"] is None
    assert "removed" in removed["wa_2026_scope"].lower()
    assert all(r["wa_2026_code"] in known_codes for r in crosswalk if r is not removed)
    return {
        "status": "AUTHOR_EXTRACTION_STRUCTURALLY_VALID_NOT_INDEPENDENTLY_ACCEPTED",
        "source_sha256": data["source"]["sha256"],
        "k8_unique_standards": len(k8),
        "hs_course_rows": len(hs),
        "hs_unique_standards": len({r["code"] for r in hs}),
        "crosswalk_rows": len(crosswalk),
        "removed_legacy_crosswalk_ids": [removed["ccss_code"]],
        "k8_grade_counts": dict(sorted(Counter(r["grade"] for r in k8).items())),
        "independent_source_fidelity": "PENDING",
        "canonical_equivalence": "UNVERIFIED",
        "assessment_and_mastery": "UNVERIFIED",
        "activation": "FORBIDDEN",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("extraction", type=Path)
    args = parser.parse_args()
    report = validate(json.loads(args.extraction.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
