#!/usr/bin/env python3
"""Generate the seed-code decomposition review table.

For every canonical code that seed scripts reference but the candidate catalog
(app/domains + app/canonical_*) does not contain, produce a review row:

  - which seed files / local skills reference it (auto-discovered)
  - candidate catalog codes that may cover the same mathematical scope
  - a proposed disposition:

      REMAP_CANDIDATES    catalog code(s) plausibly cover the scope; a reviewer
                          picks the exact target and the seed is repointed
      DECOMPOSE_REQUIRED  the seed skill is composite — its scope spans several
                          atomic catalog codes; the local skill must be split
                          before any mapping can be accepted
      TAXONOMY_CANDIDATE  the code is already atomic (typically mirroring an
                          official expectation id) but was never registered;
                          propose it through canonical_taxonomy_candidates or
                          remap to an existing catalog code

Every row is NEEDS_MATH_REVIEW. This artifact proposes; it does not decide.

Usage:
  python scripts/decompose_seed_codes.py            # markdown to stdout
  python scripts/decompose_seed_codes.py --write    # write docs/curriculum/standards artifacts
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "audit_cov", ROOT / "scripts" / "audit_curriculum_mapping_coverage.py"
)
_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_audit)

# Curated per-code candidate mapping (catalog codes that may cover the scope).
# Kept as data so math reviewers can edit the table directly.
CANDIDATES: dict[str, list[str]] = {
    "MATH.RP.RATIO": ["MATH.RP.RATIO.INTERPRET", "MATH.RP.RATIO.EQUIVALENT",
                     "MATH.RATIO.INTERPRET", "MATH.RATIO.EQUIVALENT", "MATH.RATIO.SCALE"],
    "MATH.RP.UNIT_RATE": ["MATH.RP.RATE.UNIT", "MATH.RATE.UNIT", "MATH.RATE.COMPARE", "MATH.RATE.DRT"],
    "MATH.RP.PERCENT": ["MATH.RP.PERCENT.OF", "MATH.RP.PERCENT.CONVERT", "MATH.RP.PERCENT.CHANGE",
                        "MATH.RP.PERCENT.APPLICATIONS", "MATH.FIN.PERCENT.DISCOUNT", "MATH.FIN.PERCENT.TAX"],
    "MATH.RP.PROPORTIONAL_RELATIONSHIPS": ["MATH.RP.PROPORTION.IDENTIFY", "MATH.RP.PROPORTION.SOLVE",
                                           "MATH.RP.PROPORTIONAL.REPRESENT", "MATH.RP.PROPORTIONAL.COMPARE",
                                           "MATH.PROP.IDENTIFY", "MATH.PROP.SOLVE_WORD"],
    "MATH.EE.EXPRESSIONS": ["MATH.EE.EXPR", "MATH.ALG.EXPR.EVALUATE", "MATH.ALG.EXPR.TRANSLATE"],
    "MATH.EE.ONE_VARIABLE_EQUATIONS": ["MATH.EE.EQUATION.ONE", "MATH.EE.EQUATION.MULTISTEP",
                                       "MATH.ALG.EQ.ONE.MULT", "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES"],
    "MATH.EE.EQUATIONS_INEQUALITIES": ["MATH.EE.EQUATION.ONE", "MATH.EE.EQUATION.MULTISTEP",
                                       "MATH.EE.INEQUALITY.ONE", "MATH.EE.INEQUALITY.MULTISTEP"],
    "MATH.NS.FRACTION_DIVISION": ["MATH.FRAC.DIV", "MATH.FRAC.WORD.DIVISION"],
    "MATH.NS.RATIONAL_ARITHMETIC": ["MATH.NS.RATIONAL.OPERATIONS", "MATH.RAT.ADD", "MATH.RAT.MUL",
                                    "MATH.RAT.DIV", "MATH.INT.ADD", "MATH.INT.SUB",
                                    "MATH.INT.MUL", "MATH.INT.DIV"],
    "MATH.NS.RATIONAL_EQUIVALENCE": ["MATH.NS.RATIONAL.COMPARE", "MATH.RAT.COMPARE",
                                     "MATH.FRAC.EQUIV.FIND", "MATH.FRAC.COMPARE"],
    "MATH.NS.RATIONAL_OPERATIONS": ["MATH.NS.RATIONAL.OPERATIONS", "MATH.RAT.ADD",
                                    "MATH.RAT.MUL", "MATH.RAT.DIV"],
    "MATH.G.MEASURE": ["MATH.GEO.MEASURE.AREA", "MATH.GEO.MEASURE.VOLUME",
                       "MATH.GEO.MEASURE.SURFACE_AREA", "MATH.GEO.AREA.TRI",
                       "MATH.GEO.AREA.TRAPEZOID", "MATH.GEO.AREA.PARALLELOGRAM",
                       "MATH.GEO.COORD.AXIS_DISTANCE"],
    "MATH.G.GEOMETRY_APPLICATIONS": ["MATH.GEO.SCALE.DRAWING", "MATH.GEO.SIMILARITY",
                                     "MATH.GEO.SIMILAR.SCALE", "MATH.GEO.CIRCLE.CIRCUMFERENCE",
                                     "MATH.GEO.CIRCLE.AREA", "MATH.GEO.ANGLES"],
    "MATH.SP.CENTER_SPREAD": ["MATH.DATA.MEAN", "MATH.DATA.MEDIAN", "MATH.DATA.RANGE",
                              "MATH.DATA.SPREAD", "MATH.DATA.CENTER", "MATH.DATA.OUTLIER.CENTER"],
    "MATH.SP.PROBABILITY": ["MATH.PROB.SIMPLE", "MATH.PROB.SAMPLE_SPACE", "MATH.PROB.INDEPENDENT.AND",
                            "MATH.PROB.DISJOINT.OR", "MATH.PROB.COMPOUND", "MATH.PROB.COMPLEMENT",
                            "MATH.PROB.EXPECTED_COUNT"],
    "MATH.SP.PROBABILITY_SAMPLING": ["MATH.DATA.SAMPLING", "MATH.DATA.SAMPLE.BIAS",
                                     "MATH.DATA.SAMPLE.REPRESENTATIVE", "MATH.PROB.EXPECTED_COUNT"],
    "MATH.ALGEBRA1.EXPR": ["MATH.EE.EXPR", "MATH.ALG.EXPR.EVALUATE", "MATH.ALG.EXPR.TRANSLATE",
                           "MATH.ALG.LIKE.COMBINE", "MATH.POLY.ADD", "MATH.POLY.MULT.BINOMIAL"],
    "MATH.ALGEBRA1.LINEAR_EQ": ["MATH.EE.EQUATION.ONE", "MATH.EE.EQUATION.MULTISTEP",
                                "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES", "MATH.ALG.EQ.MULTISTEP.DISTRIBUTE",
                                "MATH.EE.SYSTEMS"],
    "MATH.ALGEBRA1.LINEAR_FN": ["MATH.FUNC.LINEAR.MODEL", "MATH.FUNC.LINEAR.SLOPE.TABLE",
                                "MATH.F.LINEAR.COMPARE", "MATH.F.LINEAR.SEQUENCE"],
    "MATH.ALGEBRA1.LINEAR_FN_EVAL": ["MATH.FUNC.LINEAR.MODEL", "MATH.F.LINEAR.COMPARE",
                                     "MATH.F.LINEAR.SEQUENCE"],
    "MATH.ALGEBRA1.LINEAR_FN_SLOPE": ["MATH.FUNC.LINEAR.SLOPE.TABLE", "MATH.DATA.LINEFIT.SLOPE"],
    "MATH.ALGEBRA1": ["MATH.EE.EXPR", "MATH.EE.EQUATION.ONE", "MATH.FUNC.LINEAR.MODEL"],
}

# IA1 codes mirror official MSDE expectation numbering (atomic granularity) —
# strand-level candidate families are supplied instead of exact guesses.
IA1_STRAND_CANDIDATES = {
    "AT": ["MATH.EE.EXPR", "MATH.ALG.EXPR.EVALUATE", "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES",
           "MATH.FUNC.LINEAR.MODEL", "MATH.FUNC.LINEAR.SLOPE.TABLE", "MATH.EXPFUNC.MODEL",
           "MATH.EXPFUNC.EVALUATE", "MATH.F.QUADRATIC.INTERPRET", "MATH.POLY.FACTOR.GCF",
           "MATH.EE.SYSTEMS", "MATH.F.LINEAR.COMPARE"],
    "DS": ["MATH.DATA.FREQUENCY", "MATH.DATA.MEAN", "MATH.DATA.BIVARIATE",
           "MATH.DATA.SCATTER.ASSOCIATION", "MATH.DATA.LINEAR_MODEL", "MATH.DATA.SAMPLING",
           "MATH.PROB.COMPOUND", "MATH.DATA.TWOWAY.RELATIVE"],
    "GR": ["MATH.GEO.TRANSFORMATIONS", "MATH.GEO.TRANSFORM.DILATE", "MATH.GEO.SIMILARITY",
           "MATH.GEO.CONGRUENCE.SAS", "MATH.GEO.PYTHAGOREAN", "MATH.GEO.ANGLES"],
}

REF_RE = re.compile(
    r'"([A-Z][A-Z0-9.]*)"\s*,\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*\d+\s*,\s*"(MATH\.[A-Z0-9_.]+)"'
)
DYN_RE = re.compile(r'"(MATH\.[A-Z0-9_.]+)"\s*\+')  # string-concatenated code prefix

OPS = ("add", "subtract", "multiply", "divide", "area", "volume", "surface",
       "perimeter", "circumference", "mean", "median", "mode", "range",
       "probabilit", "sample", "equation", "inequalit", "slope", "transform",
       "exponent", "root", "simplif", "evaluat", "compare", "order", "convert",
       "factor", "solv", "represent", "graph", "interpret", "translate")


def _references(absent: list[str]) -> dict[str, list[dict]]:
    refs: dict[str, list[dict]] = {c: [] for c in absent}
    for path in sorted((ROOT / "scripts").glob("seed_*.py")):
        src = path.read_text()
        found = set()
        for m in REF_RE.finditer(src):
            local, name, desc, canon = m.groups()
            if canon in refs:
                found.add(canon)
                refs[canon].append({"seed": path.name, "local_code": local,
                                    "name": name, "scope": desc})
        for code in absent:
            if code in found:
                continue
            if f'"{code}"' in src:
                found.add(code)
                refs[code].append({"seed": path.name, "local_code": None,
                                   "name": None, "scope": "referenced without skill tuple"})
            for m in DYN_RE.finditer(src):
                if code == m.group(1).rstrip("."):
                    refs[code].append({"seed": path.name, "local_code": None, "name": None,
                                       "scope": "DYNAMIC_CODE_GENERATION — canonical code built by "
                                                "string concatenation; identity invisible to review"})
                    found.add(code)
    return refs


def decompose() -> dict:
    audit = _audit.audit()
    absent = audit["totals"]["seed_codes_not_in_catalog"]
    catalog = set()
    for pat in _audit.CANONICAL_GLOBS:
        import glob as _g
        for f in _g.glob(str(ROOT / pat)):
            catalog |= set(_audit.MATH_CODE_RE.findall(Path(f).read_text()))

    refs = _references(absent)
    rows = []
    for code in absent:
        if code.startswith("MATH.IA1."):
            strand = code.split(".")[2]
            cands = IA1_STRAND_CANDIDATES.get(strand, [])
            disposition = "TAXONOMY_CANDIDATE"
            note = ("Atomic code mirroring official MSDE expectation numbering; never "
                    "registered in the taxonomy catalog. Register via canonical_taxonomy_"
                    "candidates or remap to a listed catalog code after math review.")
        else:
            cands = [c for c in CANDIDATES.get(code, []) if c in catalog]
            r = refs.get(code) or []
            # family = first two code segments (FRAC.DIV vs FRAC.WORD, EE.EQUATION
            # vs EE.INEQUALITY) — a proxy for distinct atomic targets.
            fams = {".".join(c.split(".")[1:3]) for c in cands}
            scope = " ".join(x["scope"] or "" for x in r).lower()
            ops = {o for o in OPS if o in scope}
            composite = (len(fams) >= 3
                         or (len(fams) >= 2 and (len(ops) >= 2 or len(cands) >= 4)))
            disposition = ("DECOMPOSE_REQUIRED" if composite
                           else "REMAP_CANDIDATES" if cands
                           else "TAXONOMY_CANDIDATE")
            note = ""
        rows.append({
            "seed_code": code,
            "references": refs.get(code, []),
            "candidate_catalog_codes": cands,
            "disposition": disposition,
            "needs_math_review": True,
            "note": note,
        })
    rows.sort(key=lambda r: (r["disposition"], r["seed_code"]))
    return {
        "schema_version": "seed_canonical_decomposition.v1",
        "status": "DRAFT_PROPOSED_NOT_VERIFIED",
        "summary": {
            "absent_codes": len(rows),
            "decompose_required": sum(1 for r in rows if r["disposition"] == "DECOMPOSE_REQUIRED"),
            "remap_candidates": sum(1 for r in rows if r["disposition"] == "REMAP_CANDIDATES"),
            "taxonomy_candidates": sum(1 for r in rows if r["disposition"] == "TAXONOMY_CANDIDATE"),
        },
        "rows": rows,
        "safety": "Review-support artifact only. No row activates a mapping, mutates "
                  "learner evidence, or claims verified coverage. Every change MUST "
                  "pass Standards Mapping + Math Review acceptance before seeds are edited.",
    }


def to_markdown(d: dict) -> str:
    s = d["summary"]
    out = [
        "# Seed-Code Decomposition Review Table",
        "",
        f"Status: `{d['status']}` — proposals for Math Review; nothing here is decided.",
        "",
        f"{s['absent_codes']} seed-referenced codes absent from the candidate catalog — "
        f"{s['decompose_required']} composite (decompose), {s['remap_candidates']} remap "
        f"candidates, {s['taxonomy_candidates']} taxonomy candidates.",
        "",
        "| Seed code | Referenced by | Disposition | Candidate catalog codes |",
        "|---|---|---|---|",
    ]
    for r in d["rows"]:
        seeds = ", ".join(sorted({x["seed"] for x in r["references"]})) or "—"
        locals_ = sorted({x["local_code"] for x in r["references"] if x["local_code"]})
        if locals_:
            seeds += f" ({', '.join(locals_[:4])}{'…' if len(locals_) > 4 else ''})"
        cands = "<br>".join(f"`{c}`" for c in r["candidate_catalog_codes"]) or "*none*"
        out.append(f"| `{r['seed_code']}` | {seeds} | `{r['disposition']}` | {cands} |")
    out += [
        "",
        "## How to act on a row",
        "",
        "- `REMAP_CANDIDATES` — Math Review picks the atomic target; seeds repoint to it.",
        "- `DECOMPOSE_REQUIRED` — the local skill spans multiple catalog codes; split the",
        "  local skill first (composite skills cannot transfer mastery per the #293 precedent),",
        "  then map each atomic piece.",
        "- `TAXONOMY_CANDIDATE` — register through `canonical_taxonomy_candidates` review",
        "  or remap to a listed catalog code; `validate_identity_revision` rejects",
        "  unreviewed codes either way.",
    ]
    return "\n".join(out) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="write artifacts under docs/curriculum/standards/")
    args = p.parse_args()
    d = decompose()
    if args.write:
        (ROOT / "docs/curriculum/standards/seed_canonical_decomposition.v1.json").write_text(
            json.dumps(d, indent=2) + "\n")
        (ROOT / "docs/curriculum/standards/seed_canonical_decomposition.v1.md").write_text(to_markdown(d))
        print("wrote seed_canonical_decomposition.v1.{json,md}")
    else:
        print(to_markdown(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
