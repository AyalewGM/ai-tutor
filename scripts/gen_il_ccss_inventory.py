"""Generate the Illinois CCSS expectation inventories from the DC CCSS set.

Illinois adopted the Common Core State Standards verbatim (ISBE rulemaking
effective 2010-10-28), so the expectation identifier set and official text are
identical to the DC CCSS inventories. This script clones the reviewed DC rows,
swaps jurisdiction/provenance to ISBE, and resets every mapping claim to
zero-candidate — Illinois has no repository packs, seeds, or skills.

Run: python scripts/gen_il_ccss_inventory.py
"""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STANDARDS = ROOT / "docs" / "curriculum" / "standards"

ISBE_MATH_PDF = "https://www.isbe.net/Documents/Math_common_core_standards.pdf"
ISBE_STANDARDS_PAGE = "https://www.isbe.net/Pages/Standards-Courses.aspx"
CCSS_TEXT = "https://www.thecorestandards.org/Math"
CHECKED = "2026-10-16"

JURISDICTION = {
    "country": "United States",
    "state": "Illinois",
    "authority": "Illinois State Board of Education",
    "authority_code": "ISBE",
}

UNMAPPED_BLOCKERS = [
    (
        "Independent standards and mathematical review must confirm the exact "
        "expectation-to-atomic-skill relationship before any mapping is accepted."
    ),
    "No repository-specific local skill candidate was located for this expectation.",
]

PROVENANCE = {
    "authoritative_source_url": ISBE_MATH_PDF,
    "adoption_authority_url": ISBE_STANDARDS_PAGE,
    "standards_text_url": CCSS_TEXT,
    "checked_date": CHECKED,
    "adoption_history": {
        "isbe_initial_review": "2010-06-24",
        "rulemaking_adopted": "2010-09-24",
        "jcar_certification_of_no_objection": "2010-10-19",
        "rulemaking_effective": "2010-10-28",
        "illinois_register_published": "2010-11-12",
    },
    "source_notes": [
        (
            "Illinois adopted the Common Core State Standards verbatim through "
            "ISBE rulemaking effective 2010-10-28; the Illinois Learning "
            "Standards for Mathematics incorporate the CCSS without identifier "
            "changes."
        ),
        (
            "Expectation identifiers, domain/cluster structure, and statement "
            "text are identical to the canonical CCSS set; per-expectation "
            "text is carried from the reviewed DC CCSS inventory (same source)."
        ),
        (
            "Jurisdiction isolation: identical CCSS identifiers appear in "
            "other adopters' inventories (DC, MD legacy crosswalk columns). "
            "Illinois rows must never merge with those rows by identifier "
            "similarity."
        ),
        (
            "Illinois has no repository packs, seeds, or skills; every row is "
            "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND pending Standards Mapping "
            "work."
        ),
    ],
}

SAFETY = {
    "activation": "FORBIDDEN",
    "mapping_review_required": True,
    "new_canonical_ids_created": False,
    "learner_mastery_mutation": False,
    "verified_coverage_claim": False,
}

VARIANTS = [
    {
        "src": "dc_grades1_5_ccss.expectations.v1.json",
        "dst": "il_grades1_5_ccss.expectations.v1.json",
        "manifest_id": "IL-G1-G5-CCSS-expectation-inventory-v1",
        "curriculum": {
            "course_code": "IL_CCSS_MATH_1_5",
            "course_title": (
                "Illinois Learning Standards for Mathematics "
                "(incorporating the Common Core), Grades 1-5"
            ),
            "standards_version": "CCSS 2010 (adopted verbatim by ISBE)",
            "note": (
                "Companion inventory to IL-G6-G8-CCSS. Illinois adopts Common "
                "Core verbatim; identifiers are canonical CCSS codes."
            ),
        },
    },
    {
        "src": "dc_grades6_8_ccss.expectations.v1.json",
        "dst": "il_grades6_8_ccss.expectations.v1.json",
        "manifest_id": "IL-G6-G8-CCSS-expectation-inventory-v1",
        "curriculum": {
            "course_code": "IL_CCSS_MATH_GRADES_6_8",
            "course_title": (
                "Illinois Learning Standards for Mathematics "
                "(incorporating the Common Core), Grades 6-8"
            ),
            "standards_version": "CCSS-2010 (current Illinois adoption)",
            "adopted_date": "2010-09-24 (ISBE rulemaking adopted)",
            "implementation_school_year": "2013-2014",
            "note": (
                "Illinois adopted CCSS verbatim through ISBE rulemaking "
                "effective 2010-10-28."
            ),
        },
    },
    {
        "src": "dc_algebra1_ccss.expectations.v1.json",
        "dst": "il_algebra1_ccss.expectations.v1.json",
        "manifest_id": "IL-CCSS-ALGEBRA1-expectation-inventory-v1",
        "curriculum": {
            "course_code": "IL_CCSS_ALGEBRA_I",
            "course_title": (
                "High School Algebra I — Illinois Learning Standards, "
                "CCSS Appendix A Traditional Pathway"
            ),
            "standards_version": "Common Core State Standards for Mathematics (2010)",
            "note": (
                "Illinois adopts CCSS verbatim; high-school course placement "
                "follows CCSS Appendix A (the official course-placement "
                "document) pending ISBE course-map verification."
            ),
        },
    },
]


def reset_row(row: dict, unmapped_template: dict | None) -> dict:
    """Strip every provisional mapping claim; mark the row zero-candidate."""
    out = copy.deepcopy(row)
    out["proposed_mapping_status"] = "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
    out["repository_existing_crosswalks"] = []
    out.pop("provisional_relations", None)
    out.pop("crosswalk_evidence", None)
    if unmapped_template is not None:
        out["classification"] = copy.deepcopy(unmapped_template["classification"])
        out["blockers"] = list(unmapped_template["blockers"])
    else:
        out["classification"]["standards_mapped"] = (
            "NO_REPOSITORY_CANDIDATE"
            if out["classification"].get("standards_mapped")
            == "REPOSITORY_ROW_EXISTS_NOT_ACCEPTED"
            else "NO"
        )
        out["blockers"] = list(UNMAPPED_BLOCKERS)
    return out


def build(variant: dict) -> dict:
    src = json.loads((STANDARDS / variant["src"]).read_text())
    unmapped_template = next(
        (r for r in src["expectations"] if not r["repository_existing_crosswalks"]),
        None,
    )
    expectations = [reset_row(r, unmapped_template) for r in src["expectations"]]
    count = len(expectations)
    return {
        "schema_version": src["schema_version"],
        "manifest_id": variant["manifest_id"],
        "status": "DRAFT_PROPOSED_NOT_VERIFIED",
        "jurisdiction": JURISDICTION,
        "curriculum": variant["curriculum"],
        "provenance": copy.deepcopy(PROVENANCE),
        "reconciliation": {
            "official_expectation_count": count,
            "expectations_with_provisional_links": 0,
            "unmapped_expectations": count,
            "warning": (
                "Illinois has zero repository coverage; identifier-set clone "
                "of the reviewed DC CCSS inventory establishes official scope "
                "only, not coverage."
            ),
        },
        "safety": copy.deepcopy(SAFETY),
        "expectations": expectations,
    }


def main() -> None:
    for variant in VARIANTS:
        manifest = build(variant)
        dst = STANDARDS / variant["dst"]
        dst.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"wrote {variant['dst']}: {len(manifest['expectations'])} expectations")


if __name__ == "__main__":
    main()
