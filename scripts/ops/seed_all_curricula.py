"""Seed every authored curriculum and content layer, in dependency order.

Every underlying seed is idempotent (it checks before inserting), so this is
safe on a fresh database after ``alembic upgrade head`` and on a live pilot
database — existing rows are skipped.

    python scripts/ops/seed_all_curricula.py            # everything
    python scripts/ops/seed_all_curricula.py --warm     # also deepen problem banks
    python scripts/ops/seed_all_curricula.py --list     # print the plan, run nothing

``--warm`` invokes ``warm_problem_banks`` for every seeded curriculum, which
can take several minutes; it is off by default so deploys stay fast.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Allow `python scripts/ops/seed_all_curricula.py` from any CWD (container
# entrypoint style) — repo root must be importable for `app`/`scripts`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# (module, label). Order is deliberate: jurisdiction curricula first, then the
# canonical cross-curriculum map needs the skills to exist, then authored
# content layers target skill codes across curricula, and elementary packs
# close the loop with their own cross-grade wiring + misconception loader.
STEPS: list[tuple[str, str]] = [
    ("seed_sprint1", "MCPS Math 8 pilot (SOLVE_EQUATION chain)"),
    ("seed_grade6", "MCPS Math 6"),
    ("seed_grade7", "MCPS Math 7"),
    ("seed_algebra1", "MCPS Algebra 1"),
    ("seed_mth1w", "Ontario MTH1W de-streamed Grade 9"),
    ("seed_dc_grade3", "DC Math 3"),
    ("seed_dc_grade6", "DC Math 6"),
    ("seed_dc_grade7", "DC Math 7"),
    ("seed_md_grade3", "Maryland Math 3"),
    ("seed_md_algebra1", "Maryland Algebra 1"),
    ("seed_md_integrated_algebra1", "Maryland Integrated Algebra 1"),
    ("seed_va_grade6", "Virginia Math 6"),
    ("seed_va_grade7", "Virginia Math 7"),
    ("seed_va_algebra1", "Virginia Algebra 1 (SOL)"),
    ("seed_dc_algebra1", "DC Algebra 1"),
    ("seed_all_elementary_packs", "DMV elementary packs grades 1-5 + cross-grade prerequisites"),
    ("map_canonical_curricula", "Canonical skill map across jurisdictions"),
    ("seed_word_problems", "Authored word problems (pilot skills)"),
    ("seed_mc_problems", "Multiple-choice problems with misconception-coded distractors"),
    ("seed_learn_content", "Learn-mode concept content (applied across curricula)"),
    ("ops.deepen_skill_breadth", "Companion problem types for type-thin skills"),
]


def main() -> int:
    args = set(sys.argv[1:])
    if "--list" in args:
        for module, label in STEPS:
            print(f"  {module:<32} {label}")
        return 0

    for module_name, label in STEPS:
        module = importlib.import_module(f"scripts.{module_name}")
        print(f"[seed-all] {label} ...", flush=True)
        module.seed()

    # Post-seed normalization: fraction/integer canonical answers get graded
    # answer kinds instead of raw FREE_TEXT.
    print("[seed-all] Backfilling answer kinds ...", flush=True)
    backfill = importlib.import_module("scripts.ops.backfill_answer_kinds")
    backfill.main()

    if "--warm" in args:
        print("[seed-all] Warming problem banks ...", flush=True)
        # warm_problem_banks parses curriculum codes from sys.argv — strip
        # our flags so "--warm" isn't mistaken for a code.
        sys.argv = sys.argv[:1]
        warm = importlib.import_module("scripts.ops.warm_problem_banks")
        warm.main()

    print("[seed-all] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
