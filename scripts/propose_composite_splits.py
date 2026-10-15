"""Generate composite-skill split proposals for Math Review.

For each DECOMPOSE_REQUIRED seed canonical code (from the coverage audit),
produce one reviewable proposal per *local* skill that references it:

    local composite skill  →  claimed official expectations (from the checked-in
    expectation manifests' provisional crosswalks)  →  proposed atomic skills,
    one per claimed expectation, each carrying ranked catalog candidates.

Granularity rule: one atomic local skill per official expectation — the #293
review established that composite skills cannot transfer mastery, so an atomic
skill must not span two expectations.

Rows are NEEDS_MATH_REVIEW. Nothing here activates, registers, or mutates.

Usage:
  python scripts/propose_composite_splits.py            # markdown to stdout
  python scripts/propose_composite_splits.py --write    # write artifacts
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "decompose_seed_codes", ROOT / "scripts" / "decompose_seed_codes.py")
_dec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_dec)

# Branch-only manifests needed for a complete picture (DC 6-8 pending merge).
EXTRA_MANIFESTS = {
    "origin/draft/standards-dc-grades6-8-ccss":
        "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json",
}

STOPWORDS = {"the", "and", "with", "for", "in", "of", "to", "a", "an", "by",
             "will", "student", "using", "use", "within", "problems", "problem",
             "involving", "context", "given", "including", "such", "that",
             "their", "them", "e.g.", "or", "as", "on", "at", "be", "from"}


def _manifest_rows() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(ROOT / "docs/curriculum/standards/*expectations*.v1.json"))):
        rows += json.loads(Path(f).read_text()).get("expectations", [])
    for ref, path in EXTRA_MANIFESTS.items():
        try:
            raw = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{ref}:{path}"],
                capture_output=True, text=True, check=True).stdout
            rows += json.loads(raw).get("expectations", [])
        except subprocess.CalledProcessError:
            pass
    return rows


def _score(candidate: str, scope: str) -> int:
    words = {w for w in re.findall(r"[a-z]+", scope.lower())} - STOPWORDS
    toks = {t.lower() for t in candidate.split(".")[1:] for t in t.split("_")}
    syn = {"prob": "probabilit", "probabl": "probabilit", "stat": "statist",
           "eq": "equation", "expr": "expression", "frac": "fraction",
           "geo": "geometr|shape|triangle|angle", "ns": "number|rational",
           "rat": "rational", "int": "integer", "lin": "linear",
           "func": "function", "prop": "proportion", "mult": "multipl",
           "div": "divid|divis", "add": "add", "sub": "subtract",
           "poly": "polynomial", "quad": "quadratic", "exp": "exponent|express"}
    score = 0
    for t in toks:
        pat = syn.get(t, t)
        if any(re.search(pat, w) for w in words):
            score += len(t)
    return score


def propose() -> dict:
    dec = _dec.decompose()
    rows = [r for r in dec["rows"] if r["disposition"] == "DECOMPOSE_REQUIRED"]

    # local_code -> claimed expectations, inverted from manifest crosswalks
    claims: dict[str, list[dict]] = {}
    for e in _manifest_rows():
        for link in e.get("repository_existing_crosswalks") or []:
            # Manifests contain both legacy string codes and structured evidence.
            # Only explicit local-skill identities may enter split proposals.
            if isinstance(link, str):
                lc = link
            elif isinstance(link, dict):
                lc = link.get("local_skill_code") or link.get("local_code")
            else:
                lc = None
            if not isinstance(lc, str) or not lc.strip():
                continue
            claims.setdefault(lc, []).append(
                {"expectation_id": e["expectation_id"], "grade": e.get("grade"),
                 "scope": e.get("scope_summary") or ""})

    proposals = []
    for row in rows:
        seed_code = row["seed_code"]
        for ref in row["references"]:
            local = ref.get("local_code")
            if not local:
                continue
            seen_exp = set()
            claimed = []
            for c in claims.get(local, []):
                if c["expectation_id"] in seen_exp:
                    continue
                seen_exp.add(c["expectation_id"])
                claimed.append(c)
            atomics = []
            used_codes = set()
            for c in claimed:
                ranked = sorted(row["candidate_catalog_codes"],
                                key=lambda x: -_score(x, c["scope"]))
                leaf = ranked[0].split(".")[-1] if ranked else f"E{c['expectation_id'].split('.')[-1]}"
                proposed = f"{local}.{leaf}"
                n = 2
                while proposed in used_codes:  # distinct atomic identity per expectation
                    proposed = f"{local}.{leaf}_{n}"
                    n += 1
                used_codes.add(proposed)
                atomics.append({
                    "proposed_skill_code": proposed,
                    "covers_expectation": c["expectation_id"],
                    "expectation_scope": c["scope"][:200],
                    "catalog_candidates_ranked": ranked[:5],
                    "needs_math_review": True,
                })
            proposals.append({
                "local_skill_code": local,
                "seed": ref["seed"],
                "current_canonical_code": seed_code,
                "current_scope": (ref.get("scope") or "")[:200],
                "claimed_expectation_count": len(claimed),
                "proposed_atomic_skills": atomics,
                "status": "NO_OFFICIAL_CLAIMS_ALIGN_OR_RETIRE" if not claimed
                          else "PROPOSED_SPLIT_NEEDS_MATH_REVIEW",
            })
    return {
        "schema_version": "seed_composite_split_proposals.v1",
        "status": "DRAFT_PROPOSED_NOT_VERIFIED",
        "rule": "ONE_ATOMIC_SKILL_PER_OFFICIAL_EXPECTATION — composite skills "
                "cannot transfer mastery (#293 precedent)",
        "summary": {
            "composite_local_skills": len(proposals),
            "with_claims": sum(1 for p in proposals if p["claimed_expectation_count"]),
            "proposed_atomic_skills": sum(len(p["proposed_atomic_skills"]) for p in proposals),
            "no_official_claims": sum(1 for p in proposals if not p["claimed_expectation_count"]),
        },
        "proposals": proposals,
        "safety": "Proposals only. Atomic splits MUST pass Standards Mapping + "
                  "Math Review before any seed edit. No learner-evidence mutation.",
    }


def to_markdown(d: dict) -> str:
    s = d["summary"]
    out = [
        "# Composite Seed-Skill Split Proposals",
        "",
        f"Status: `{d['status']}` — {d['rule']}",
        "",
        (f"{s['composite_local_skills']} composite local skills → "
         f"{s['proposed_atomic_skills']} proposed atomic skills "
         f"({s['no_official_claims']} skills have no official expectation claims)."),
        "",
    ]
    for p in d["proposals"]:
        out.append(f"## `{p['local_skill_code']}` ({p['seed']})")
        out.append(f"canonical today: `{p['current_canonical_code']}` — "
                   f"{p['claimed_expectation_count']} claimed expectations — "
                   f"`{p['status']}`")
        if p["current_scope"]:
            out.append(f"\n> {p['current_scope']}")
        out.append("")
        if p["proposed_atomic_skills"]:
            out.append("| Proposed atomic skill | Covers | Top catalog candidate |")
            out.append("|---|---|---|")
            for a in p["proposed_atomic_skills"]:
                top = a["catalog_candidates_ranked"][0] if a["catalog_candidates_ranked"] else "—"
                out.append(f"| `{a['proposed_skill_code']}` | `{a['covers_expectation']}` | `{top}` |")
        else:
            out.append("*No manifest expectations claim this skill — align to "
                       "nearest expectations or retire.*")
        out.append("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    d = propose()
    if args.write:
        (ROOT / "docs/curriculum/standards/seed_composite_split_proposals.v1.json").write_text(
            json.dumps(d, indent=2) + "\n")
        (ROOT / "docs/curriculum/standards/seed_composite_split_proposals.v1.md").write_text(
            to_markdown(d))
        print("wrote seed_composite_split_proposals.v1.{json,md}")
    else:
        print(to_markdown(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
