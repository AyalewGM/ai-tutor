"""Parse the NYSED Next Generation Mathematics Learning Standards PDF into
expectation-inventory manifests.

Source: nys-next-generation-mathematics-p-12-standards.pdf (2017, updated
June 2019) — the authoritative P-12 document published by NYSED.

The PDF is a two-column document; pypdf interleaves main-column statements
with side-column marginalia (Coherence chains, e.g. examples, Notes, MP
connections). This parser:

* detects domain headers (``NY-{grade}.{DOM}`` / ``AI-{DOM}``) to open
  standards sections — overview prose carries no domain header, so it is
  never captured;
* starts a row on ``N.`` / ``Na.`` line-leading numbers inside an open
  domain;
* keeps the statement text separate from annotations: Coherence chains are
  preserved in ``coherence`` (official vertical-alignment content), and
  scope-relevant notes (shared-course annotations, fluency recommendations)
  in ``notes``;
* marks rows ``EXTRACTION_REVIEW_REQUIRED`` when the statement block is
  too short to trust — everything else is
  ``AUTHORITATIVE_STATEMENT_EXTRACTED``.

Cluster headings are unnumbered title lines. ``cluster_title`` is
best-effort and flagged as such in provenance.

Usage:
    python scripts/parse_ny_ngmls_inventory.py /path/to/nys-...-standards.pdf
"""

import json
import re
import sys
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
STANDARDS = ROOT / "docs" / "curriculum" / "standards"

PDF_URL = (
    "https://www.nysed.gov/sites/default/files/programs/"
    "curriculum-instruction/nys-next-generation-mathematics-p-12-standards.pdf"
)
CHECKED = "2026-10-16"
DOC_ID = "NYSED_NGMLS_P12_2017_UPDATED_2019"

JURISDICTION = {
    "country": "United States",
    "state": "New York",
    "authority": "New York State Education Department",
    "authority_code": "NYSED",
}

SAFETY = {
    "activation": "FORBIDDEN",
    "mapping_review_required": True,
    "new_canonical_ids_created": False,
    "learner_mastery_mutation": False,
    "verified_coverage_claim": False,
}

# Printed page numbers in the PDF == pypdf page index + 1.
SECTIONS = [
    {
        "manifest": "ny_ngmls_2019_grades1_5.expectations.v1.json",
        "manifest_id": "NY-NGMLS-2019-G1-G5-expectation-inventory-v1",
        "course_code": "NY_NGMLS_MATH_1_5",
        "course_title": (
            "New York State Next Generation Mathematics Learning "
            "Standards (2017, updated June 2019), Grades 1-5"
        ),
        "grades": {1: (25, 34), 2: (35, 44), 3: (45, 54), 4: (55, 66), 5: (67, 76)},
        "id_re": r"NY-(\d)\.([A-Z]+)\.(\d+[a-z]?)",
        "domain_hdr": r"^NY-{g}\.([A-Z]+)\s\s*(.+)$",
        "prefix": "NY-",
    },
    {
        "manifest": "ny_ngmls_2019_grades6_8.expectations.v1.json",
        "manifest_id": "NY-NGMLS-2019-G6-G8-expectation-inventory-v1",
        "course_code": "NY_NGMLS_MATH_6_8",
        "course_title": (
            "New York State Next Generation Mathematics Learning "
            "Standards (2017, updated June 2019), Grades 6-8"
        ),
        "grades": {6: (77, 88), 7: (89, 96), 8: (97, 104)},
        "id_re": r"NY-(\d)\.([A-Z]+)\.(\d+[a-z]?)",
        "domain_hdr": r"^NY-{g}\.([A-Z]+)\s\s*(.+)$",
        "prefix": "NY-",
    },
    {
        "manifest": "ny_ngmls_2019_algebra1.expectations.v1.json",
        "manifest_id": "NY-NGMLS-2019-ALGEBRA1-expectation-inventory-v1",
        "course_code": "NY_NGMLS_ALGEBRA_I",
        "course_title": (
            "New York State Next Generation Mathematics Learning "
            "Standards (2017, updated June 2019), Algebra I"
        ),
        "grades": {"AI": (108, 124)},
        "id_re": r"AI-([A-Z]+\.[A-Z]+)\.(\d+[a-z]?)",
        "domain_hdr": r"^AI-([A-Z]+\.[A-Z]+)\s\s*(.+)$",
        "prefix": "AI-",
    },
]

MARGINALIA_RE = re.compile(
    r"^\s*(Coherence:|e\.g\.|Note|Within-Grade Connections:|Connecting the "
    r"Standards|In the chart below|•|o\s|Grade \d students work|New York State|"
    r"Linked Navigation|Page \|)",
)
STD_START_RE = re.compile(r"^(\d+)([a-z])?\.\s+")
COHERENCE_CODE_RE = re.compile(r"(?:AII|GEO|NY|AI)-[A-Z]+\.?[A-Z]*\.?\d+[a-z]?")
SKIP_LINE_RE = re.compile(
    r"^\s*(New York State Next Generation|Linked Navigation:|"
    r"===PAGE|Page \||$)"
)


def clean_lines(page_text: str) -> list:
    out = []
    for raw in page_text.splitlines():
        line = raw.rstrip()
        if SKIP_LINE_RE.match(line):
            continue
        out.append(line.strip())
    return out


def parse_section(pages: dict, lo: int, hi: int, domain_hdr: str,
                  prefix: str, grade_key) -> list:
    """Extract standard rows from pages [lo, hi] of one grade/course."""
    rows = []
    domain = None
    domain_title = None
    current_cluster = None  # persists across all standards in one cluster
    orphans = []  # non-structural lines between clusters/standards
    cur = None    # current row under construction
    in_marginalia = False

    INLINE_MARGIN = re.compile(
        r"(Coherence:|Note:|Note on|e\.g\.,|e\.g\.|"
        r"\(Shared standard|Within-Grade Connections:)"
    )

    def split_inline(text: str, row: dict) -> str:
        """Cut statement text at inline marginalia; keep codes/notes."""
        m = INLINE_MARGIN.search(text)
        if not m:
            return text
        tail = text[m.start():]
        for c in COHERENCE_CODE_RE.findall(tail):
            if c != row["expectation_id"] and c not in row["coherence"]:
                row["coherence"].append(c)
        if "shared" in tail.lower():
            row["notes"].append(re.sub(r"\s+", " ", tail).strip("() "))
        return text[: m.start()].rstrip()

    def flush_standard():
        nonlocal cur
        if cur is None:
            return
        stmt = re.sub(r"\s+", " ", " ".join(cur["_stmt"])).strip()
        # ★ is NY's official modeling-standard glyph; quotes/parens may
        # legitimately follow terminal punctuation.
        s = stmt.rstrip("”’'\") ")
        truncated = not (
            s.endswith((".", ":", ";", "?", "!", "★"))
        )
        starts_mid_word = bool(stmt) and stmt[0].islower()
        if len(stmt) < 25 or truncated or starts_mid_word:
            cur["official_text_capture_status"] = "EXTRACTION_REVIEW_REQUIRED"
            cur["blockers"].append("STATEMENT_EXTRACTION_REQUIRES_MANUAL_REVIEW")
        else:
            cur["official_text_capture_status"] = "AUTHORITATIVE_STATEMENT_EXTRACTED"
        cur["scope_summary"] = stmt
        del cur["_stmt"]
        rows.append(cur)
        cur = None

    for pg in range(lo, hi + 1):
        for line in clean_lines(pages.get(pg, "")):
            m = re.match(domain_hdr, line)
            if m:
                flush_standard()
                domain, domain_title = m.group(1), m.group(2).strip()
                # strip trailing course tag e.g. "... Algebra I"
                domain_title = re.sub(r"\s+Algebra I\s*$", "", domain_title)
                orphans, in_marginalia = [], False
                current_cluster = None
                continue
            if domain is None:
                continue  # overview prose — never captured
            sm = STD_START_RE.match(line)
            if sm:
                flush_standard()
                if orphans:
                    joined = re.sub(r"\s+", " ", " ".join(orphans)).strip()
                    current_cluster = joined or current_cluster
                orphans = []
                in_marginalia = False
                ident = f"{prefix}{grade_key}.{domain}.{sm.group(1)}{sm.group(2) or ''}" \
                    if prefix == "NY-" else f"AI-{domain}.{sm.group(1)}{sm.group(2) or ''}"
                cur = {
                    "expectation_id": ident,
                    "grade": grade_key,
                    "domain": domain,
                    "domain_title": domain_title,
                    "cluster_title": current_cluster,
                    "source_locator": f"{PDF_URL}#page={pg}",
                    "scope_summary": "",
                    "official_text_capture_status": "",
                    "proposed_mapping_status": "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND",
                    "repository_existing_crosswalks": [],
                    "classification": {
                        "standards_mapped": "NO_REPOSITORY_CANDIDATE",
                        "mathematically_reviewed_skill": "NO_CURRENT_REVIEWED_IDENTITY",
                        "exact_target_generator": "NOT_AUDITED",
                        "validated_practice": "NOT_AUDITED",
                        "independent_assessment": "NOT_AUDITED",
                        "verified_mastery_evidence": "NO_AND_MUST_NOT_BE_INFERRED",
                    },
                    "blockers": ["NO_REPOSITORY_SKILL_CANDIDATE"],
                    "source_document_id": DOC_ID,
                    "coherence": [],
                    "notes": [],
                    "_stmt": [],
                }
                cur["_stmt"].append(split_inline(line[sm.end():].strip(), cur))
                continue
            if cur is None:
                orphans.append(line)
                continue
            # inside a standard block
            codes = COHERENCE_CODE_RE.findall(line)
            if "Coherence:" in line or "Shared standard" in line or "shared with" in line.lower():
                in_marginalia = True
                for c in codes:
                    if c != cur["expectation_id"] and c not in cur["coherence"]:
                        cur["coherence"].append(c)
                if "shared" in line.lower():
                    cur["notes"].append(re.sub(r"\s+", " ", line).strip("() "))
                continue
            if MARGINALIA_RE.match(line):
                in_marginalia = True
                if line.strip().startswith("Note:"):
                    cur["notes"].append(re.sub(r"\s+", " ", line).strip())
                continue
            if in_marginalia:
                # marginalia continuations (e.g. text, bullets, MP blocks);
                # still harvest coherence codes from multi-line chains
                for c in COHERENCE_CODE_RE.findall(line):
                    if c != cur["expectation_id"] and c not in cur["coherence"]:
                        cur["coherence"].append(c)
                continue
            kept = split_inline(line, cur)
            if kept:
                cur["_stmt"].append(kept)
            else:
                in_marginalia = True  # line was entirely marginalia
    flush_standard()
    return rows


def build_manifest(section: dict, pages: dict) -> dict:
    expectations = []
    for grade_key, (lo, hi) in section["grades"].items():
        domain_hdr = section["domain_hdr"].format(
            g=grade_key if isinstance(grade_key, int) else "")
        rows = parse_section(pages, lo, hi, domain_hdr, section["prefix"], grade_key)
        expectations.extend(rows)
    # Column-boundary artifacts can emit a phantom row when a fraction
    # (e.g. "3/6") splits so a bare "N." begins a line inside a statement.
    seen, deduped, dropped = set(), [], []
    for row in expectations:
        if row["expectation_id"] in seen:
            dropped.append(row["expectation_id"])
            continue
        seen.add(row["expectation_id"])
        deduped.append(row)
    expectations = deduped
    return {
        "schema_version": "1.0.0",
        "manifest_id": section["manifest_id"],
        "status": "DRAFT_PROPOSED_NOT_VERIFIED",
        "jurisdiction": JURISDICTION,
        "curriculum": {
            "course_code": section["course_code"],
            "course_title": section["course_title"],
            "standards_version": "NYS NGMLS 2017 (updated June 2019)",
            "adoption": {
                "board_of_regents_adoption": "2017-09",
                "document_update": "2019-06",
                "full_implementation_3_8": "2020-09",
                "first_regents_algebra_i": "2024-06",
            },
        },
        "provenance": {
            "authoritative_source_url": PDF_URL,
            "authority_overview_url": "https://www.nysed.gov/standards-instruction/mathematics",
            "checked_date": CHECKED,
            "source_notes": [
                (
                    "Extracted programmatically from the official NYSED P-12 "
                    "standards PDF; two-column layout interleaves statements "
                    "with marginalia, so statement text and cluster headings "
                    "are best-effort pending Standards Mapping review."
                ),
                (
                    "Coherence chains are official vertical-alignment content "
                    "published inside the document and are preserved per-row."
                ),
                (
                    "NY identifiers are jurisdiction-native (NY- / AI- / "
                    "AII- / GEO- prefixes); they must never be merged with "
                    "CCSS identifiers from other states' inventories by "
                    "similarity."
                ),
                (
                    "New York has no repository packs, seeds, or skills; "
                    "every row is NO_REPOSITORY_SPECIFIC_MAPPING_FOUND "
                    "pending Standards Mapping work."
                ),
            ],
        },
        "reconciliation": {
            "official_expectation_count": len(expectations),
            "expectations_with_provisional_links": 0,
            "unmapped_expectations": len(expectations),
            "deduplicated_phantom_rows": dropped,
            "warning": (
                "Official count is derived from this extraction, not an "
                "independent NYSED count; reconciliation against a second "
                "authoritative source is a documented blocker."
            ),
        },
        "safety": dict(SAFETY),
        "expectations": expectations,
    }


def main() -> None:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nys_math_standards.pdf"
    reader = pypdf.PdfReader(pdf_path)
    pages = {i + 1: (p.extract_text() or "") for i, p in enumerate(reader.pages)}
    for section in SECTIONS:
        manifest = build_manifest(section, pages)
        dst = STANDARDS / section["manifest"]
        dst.write_text(json.dumps(manifest, indent=2) + "\n")
        n = len(manifest["expectations"])
        review = sum(
            1 for r in manifest["expectations"]
            if r["official_text_capture_status"] == "EXTRACTION_REVIEW_REQUIRED"
        )
        print(f"wrote {section['manifest']}: {n} expectations ({review} need review)")


if __name__ == "__main__":
    main()
