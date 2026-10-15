"""Read-only curriculum mapping-coverage audit.

Computes the mapping pyramid from checked-in artifacts only (no DB access):

  1. INVENTORIED      official expectations enumerated in
                      docs/curriculum/standards/*expectations*.v1.json
  2. PROVISIONAL      expectations with repository candidate links
                      (proposed_mapping_status / repository_existing_crosswalks)
  3. ACCEPTED         expectation links with accepted_mapping_count > 0
                      (from wave1 seed-evidence artifacts)
  4. SEEDED           local skills + canonical-code references in scripts/seed_*.py
  5. CATALOG          candidate MATH.* identities in app/domains + canonical modules

Every count is fail-closed: a provisional link is never counted as accepted, and
absence of an inventory reports NOT_INVENTORIED rather than zero-gap.

Usage:
  python scripts/audit_curriculum_mapping_coverage.py            # markdown to stdout
  python scripts/audit_curriculum_mapping_coverage.py --json -   # JSON to stdout
  python scripts/audit_curriculum_mapping_coverage.py --json out.json --md out.md
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STANDARDS_DIR = ROOT / "docs" / "curriculum" / "standards"
PACKS_DIR = ROOT / "docs" / "curriculum" / "packs"
SEEDS_DIR = ROOT / "scripts"
CANONICAL_GLOBS = ["app/domains/*.py", "app/canonical_*.py"]

NO_CANDIDATE = "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
MATH_CODE_RE = re.compile(r"MATH\.[A-Z0-9_]+(?:\.[A-Z0-9_]+)*")
LOCAL_CODE_RE = re.compile(r'"([A-Z]{1,5}\d?\.[A-Z][A-Z0-9.]+)"')

_JURIS_TABLE = {
    "Maryland": "MD", "Virginia": "VA", "District of Columbia": "DC",
    "Ontario": "ON", "Washington": "WA", "California": "CA", "Texas": "TX",
    "MD": "MD", "VA": "VA", "DC": "DC", "ON": "ON",
    "WA": "WA", "CA": "CA", "TX": "TX",
}


def _juris_code(j) -> str:
    """Normalize a manifest jurisdiction field to a short code (MD/VA/DC/ON/...)."""
    if isinstance(j, dict):
        state = j.get("state") or j.get("code") or ""
    else:
        state = str(j or "")
    if state in _JURIS_TABLE:
        return _JURIS_TABLE[state]
    for name, code in _JURIS_TABLE.items():
        if len(name) > 2 and name.lower() in state.lower():
            return code
    return state[:2].upper() if state else "??"


def audit() -> dict:
    # ---- 1+2: expectation manifests -------------------------------------
    manifests = []          # one dict per (jurisdiction, grade)
    all_expectations = []
    for path in sorted(STANDARDS_DIR.glob("*expectations*.v1.json")):
        d = json.loads(path.read_text())
        juris = _juris_code(d.get("jurisdiction"))
        version = ""
        cur = d.get("curriculum") or {}
        version = cur.get("standards_version") or d.get("schema_version", "")
        for row in d.get("expectations", []):
            # Preserve ungraded standards without inventing a grade identity.
            raw_grade = row.get("grade")
            grade = (
                int(raw_grade) if isinstance(raw_grade, (int, str))
                and str(raw_grade).isdigit() else None
            )
            links = row.get("repository_existing_crosswalks") or []
            all_expectations.append(
                {
                    "jurisdiction": juris,
                    "grade": grade,
                    "expectation_id": row["expectation_id"],
                    "status": row.get("proposed_mapping_status"),
                    "candidates": links,
                    "manifest": path.name,
                }
            )
        manifests.append(
            {"jurisdiction": juris, "version": version, "file": path.name,
             "count": len(d.get("expectations", []))}
        )

    by_cell = {}  # (juris, grade) -> stats
    for e in all_expectations:
        cell = by_cell.setdefault(
            (e["jurisdiction"], e["grade"]),
            {"inventoried": 0, "with_candidate": 0, "no_candidate": []},
        )
        cell["inventoried"] += 1
        if bool(e["status"]) and e["status"] != NO_CANDIDATE or e["candidates"]:
            cell["with_candidate"] += 1
        else:
            cell["no_candidate"].append(e["expectation_id"])

    # ---- 3: accepted counts + course evidence from wave artifacts --------
    courses = {}  # path -> {jurisdiction, grade, course, official_ids, accepted}
    for path in sorted(STANDARDS_DIR.glob("*wave*.v1.json")):
        d = json.loads(path.read_text())
        for row in d.get("entries") or d.get("rows") or []:
            p = row.get("path")
            if not p:
                continue
            c = courses.setdefault(
                p,
                {
                    "jurisdiction": _juris_code(row.get("jurisdiction")),
                    "grade": row.get("grade"),
                    "course": row.get("course"),
                    "official_ids": set(),
                    "accepted": 0,
                },
            )
            c["jurisdiction"] = c["jurisdiction"] or _juris_code(row.get("jurisdiction"))
            c["grade"] = c["grade"] or row.get("grade")
            c["course"] = c["course"] or row.get("course")
            c["official_ids"] |= set(row.get("official_expectation_ids") or [])
            c["accepted"] += int(row.get("accepted_mapping_count") or 0)

    # ---- 4: seed-time skill + canonical references -----------------------
    seeds = {}
    for path in sorted(SEEDS_DIR.glob("seed_*.py")):
        src = path.read_text()
        canonical_codes = set(MATH_CODE_RE.findall(src))
        rel = str(path.relative_to(ROOT))
        ev = courses.get(rel, {})
        m_juris = re.search(r'jurisdiction="([^"]+)"', src)
        m_grade = re.search(r'grade_level="([^"]+)"', src)
        m_code = re.search(r'Curriculum\(code="([^"]+)"', src)
        seeds[rel] = {
            "course": m_code.group(1) if m_code else (ev.get("course") or path.stem),
            "jurisdiction": _juris_code(ev.get("jurisdiction") or (m_juris.group(1) if m_juris else None)),
            "grade": ev.get("grade") or (int(m_grade.group(1)) if m_grade and m_grade.group(1).isdigit() else None),
            "canonical_codes": sorted(canonical_codes),
            "mapping_rows": len(re.findall(r"CurriculumSkillMapping\(|_skill\(db", src)),
        }
    seeded_canonical = {c for s in seeds.values() for c in s["canonical_codes"]}

    # ---- 5: candidate catalog (taxonomy identities) ----------------------
    catalog = set()
    for pat in CANONICAL_GLOBS:
        for f in glob.glob(str(ROOT / pat)):
            catalog |= set(MATH_CODE_RE.findall(Path(f).read_text()))

    # ---- alias map --------------------------------------------------------
    alias_path = ROOT / "docs" / "curriculum" / "canonical_alias_map.v1.json"
    aliases = {}
    if alias_path.exists():
        d = json.loads(alias_path.read_text())
        for a in d.get("aliases", []):
            aliases[a.get("status", "UNKNOWN")] = aliases.get(a.get("status", "UNKNOWN"), 0) + 1

    # ---- assemble cell matrix --------------------------------------------
    cells = []
    pack_cells = set()  # packs prove a learning package exists, not an inventory
    for f in sorted(PACKS_DIR.glob("*.json")):
        m = re.match(r"([a-z]{2})-grade(\d+)", f.name)
        if m:
            pack_cells.add((m.group(1).upper(), int(m.group(2))))
    covered = {(e["jurisdiction"], e["grade"]) for e in all_expectations} | pack_cells
    for c in courses.values():
        covered.add((c["jurisdiction"], c["grade"]))
    for s in seeds.values():
        if isinstance(s["grade"], int) and s["jurisdiction"] not in (None, "??"):
            covered.add((s["jurisdiction"], s["grade"]))
    for (juris, grade) in sorted(covered, key=lambda x: (str(x[0]), x[1] or 0)):
        inv = by_cell.get((juris, grade), {"inventoried": 0, "with_candidate": 0, "no_candidate": []})
        linked = sum(len(c["official_ids"]) for c in courses.values()
                     if c["jurisdiction"] == juris and c["grade"] == grade)
        accepted = sum(c["accepted"] for c in courses.values()
                       if c["jurisdiction"] == juris and c["grade"] == grade)
        has_pack = (juris, grade) in pack_cells
        if inv["inventoried"] == 0:
            status = "PACK_ONLY_NOT_INVENTORIED" if has_pack else "NOT_INVENTORIED"
        elif accepted == inv["inventoried"] and accepted > 0:
            status = "ACCEPTED_FULL"
        elif accepted > 0:
            status = "ACCEPTED_PARTIAL"
        elif inv["with_candidate"] > 0 or linked > 0:
            status = "PROVISIONAL_ONLY"
        else:
            status = "INVENTORIED_NO_CANDIDATES"
        cells.append(
            {
                "jurisdiction": juris,
                "grade": grade,
                "inventoried_expectations": inv["inventoried"],
                "with_provisional_candidate": inv["with_candidate"],
                "no_candidate_ids": inv["no_candidate"],
                "seed_official_links": linked,
                "accepted_mappings": accepted,
                "status": status,
            }
        )

    return {
        "schema_version": "mapping_coverage_audit.v1",
        "status": "READ_ONLY_AUDIT_NO_ACTIVATION",
        "manifests": manifests,
        "cells": cells,
        "totals": {
            "inventoried_expectations": len(all_expectations),
            "with_provisional_candidate": sum(1 for e in all_expectations if bool(e["status"]) and e["status"] != NO_CANDIDATE or e["candidates"]),
            "no_candidate": sum(1 for e in all_expectations if (not e["status"] or e["status"] == NO_CANDIDATE) and not e["candidates"]),
            "accepted_mappings": sum(c["accepted_mappings"] for c in cells),
            "seed_courses": len(seeds),
            "seed_referenced_canonical_codes": len(seeded_canonical),
            "catalog_canonical_codes": len(catalog),
            "catalog_codes_unreferenced_by_seeds": len(catalog - seeded_canonical),
            "seed_codes_not_in_catalog": sorted(seeded_canonical - catalog),
            "alias_statuses": aliases,
        },
        "safety": "Counts provisional and accepted mappings separately. A provisional "
                  "link MUST NOT be reported as coverage; ACCEPTED_* requires "
                  "accepted_mapping_count > 0 in checked-in evidence artifacts.",
    }


def to_markdown(a: dict) -> str:
    t = a["totals"]
    out = [
        "# Curriculum Mapping Coverage Audit",
        "",
        f"Status: `{a['status']}` — read-only; provisional links are never coverage.",
        "",
        "## Pyramid totals",
        "",
        "| Layer | Count |",
        "|---|---:|",
        f"| Official expectations inventoried | {t['inventoried_expectations']} |",
        f"| With provisional candidate link | {t['with_provisional_candidate']} |",
        f"| No repository candidate | {t['no_candidate']} |",
        f"| **Accepted mappings** | **{t['accepted_mappings']}** |",
        f"| Seed courses scanned | {t['seed_courses']} |",
        f"| Canonical codes referenced by seeds | {t['seed_referenced_canonical_codes']} |",
        f"| Canonical codes in candidate catalog | {t['catalog_canonical_codes']} |",
        f"| Catalog codes unreferenced by any seed | {t['catalog_codes_unreferenced_by_seeds']} |",
        "",
        "## Per jurisdiction × grade",
        "",
        "| Juris | Grade | Inventoried | Provisional | Accepted | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for c in a["cells"]:
        out.append(
            f"| {c['jurisdiction']} | {c['grade']} | {c['inventoried_expectations']} | "
            f"{c['with_provisional_candidate']} | {c['accepted_mappings']} | `{c['status']}` |"
        )
    out += ["", "## Alias map", "", "| Status | Count |", "|---|---:|"]
    for k, v in sorted(a["totals"]["alias_statuses"].items()):
        out.append(f"| {k} | {v} |")
    if t["seed_codes_not_in_catalog"]:
        out += ["", "## Seed-referenced codes absent from catalog", ""]
        out += [f"- `{c}`" for c in t["seed_codes_not_in_catalog"]]
    out += ["", "## Inventoried manifests", ""]
    out += [f"- `{m['file']}` — {m['jurisdiction']} {m['version']} ({m['count']} expectations)" for m in a["manifests"]]
    return "\n".join(out) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", metavar="PATH", help="write machine-readable audit (or '-' for stdout)")
    p.add_argument("--md", metavar="PATH", help="write markdown report (or '-' for stdout)")
    args = p.parse_args()

    a = audit()
    md = to_markdown(a)
    js = json.dumps(a, indent=2, sort_keys=False)

    if args.json:
        (print(js) if args.json == "-" else Path(args.json).write_text(js + "\n"))
    if args.md:
        (print(md) if args.md == "-" else Path(args.md).write_text(md))
    if not args.json and not args.md:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
