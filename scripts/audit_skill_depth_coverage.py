"""Read-only, generator-derived skill-depth inventory.

This is an engineering evidence matrix, NOT a complete mathematical taxonomy,
approved curriculum coverage report, or verified teaching-quality assessment.

Run: python scripts/audit_skill_depth_coverage.py --output /tmp/mihur-skill-depth.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.canonical_problem_families import FAMILIES, LearningMode

DIMENSIONS = (
    "diagnostic", "guided", "independent", "mastery", "review",
)
REVIEW_STATE = "UNVERIFIED_CONTENT_DEPTH"


def build_report() -> dict:
    """Inventory exact merged runtime registry without changing application state."""
    grouped: dict[str, list] = defaultdict(list)
    for family in FAMILIES.values():
        grouped[family.canonical_skill_code].append(family)

    skills = []
    for code, families in sorted(grouped.items()):
        modes = {mode.value for family in families for mode in family.modes}
        dimensions = sorted({
            dim for family in families for dim in family.evidence_dimensions
        })
        skills.append({
            "canonical_skill_code": code,
            "generator_family_count": len(families),
            "generator_family_ids": sorted(family.code for family in families),
            "supported_modes": sorted(modes),
            "evidence_dimensions_declared": dimensions,
            "mode_flags": {
                mode.lower(): mode in modes for mode in (
                    LearningMode.DIAGNOSTIC.value,
                    LearningMode.GUIDED.value,
                    LearningMode.INDEPENDENT.value,
                    LearningMode.MASTERY.value,
                    LearningMode.REVIEW.value,
                )
            },
            "generator_available": True,
            "rich_content_review_status": REVIEW_STATE,
            "mathematical_review": "NOT_ASSESSED",
            "curriculum_mapping_review": "NOT_ASSESSED",
            "interactive_lesson_review": "NOT_ASSESSED",
            "assessment_quality_review": "NOT_ASSESSED",
            "priority_note": (
                "Review skill depth independently; registry mode support does not "
                "establish lesson quality, question variety or mastery validity."
            ),
        })

    return {
        "report_type": "GENERATOR_DERIVED_SKILL_DEPTH_INVENTORY",
        "authority_warning": (
            "The registry contains only skills with implemented generator families. "
            "It cannot reveal mathematically valid skills that have no generator. "
            "No canonical skill definitions, curriculum mappings, or draft content "
            "are approved by this report."
        ),
        "source": "app.canonical_problem_families.FAMILIES",
        "family_count": len(FAMILIES),
        "distinct_generator_backed_skill_codes": len(skills),
        "all_mathematical_skills_count": None,
        "verified_curriculum_coverage_count": None,
        "verified_rich_content_count": 0,
        "verified_rich_content_count_note": (
            "Zero items verified BY THIS AUDIT; not a claim that none were "
            "independently verified elsewhere."
        ),
        "skill_rows": skills,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
