"""Read-only per-skill question depth on an explicitly supplied synthetic DB.

This report is evidence for prioritization, not independent Math/Pedagogy,
standards, or learner-visible QA acceptance. It never reads attempts or students.

Usage:
  python -m scripts.audit_persisted_question_depth \
    --database-url "$TEST_DATABASE_URL" --source-sha "$(git rev-parse HEAD)" \
    --output /tmp/mihur-depth.json

Requires an isolated local PostgreSQL test database already migrated/seeded.
No seed scripts, migrations, activation or learner record writes occur here.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.canonical_problem_families import FAMILIES, LearningMode, generate
from app.content_models import ProblemContentMetadata
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Problem, Skill
from app.services.problem_generation import GENERATORS

MODES = ("diagnostic", "guided", "independent", "mastery")
MIN_UNIQUE_FOR_DEPTH_REVIEW = 6  # TRIAGE threshold, never mastery/readiness approval
# Explicit QA-only source fixture from scripts/seed_sprint1.py, not teaching depth.
NON_INSTRUCTIONAL_FIXTURES = {("MCPS_MATH_8", "M8.PROB.MARBLE_QA")}


def _text(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _task_key(problem: Any) -> tuple[str, str]:
    """A visual task can share prompt text but differ in parameters/image."""
    solution = problem.solution if isinstance(problem.solution, dict) else {}
    visual = {
        "parameters": solution.get("parameters"),
        "visual_spec": solution.get("visual_spec"),
        "choices": problem.choices,
    }
    return _text(problem.prompt), _json(visual)


def _family_code(problem: Any) -> str:
    solution = problem.solution if isinstance(problem.solution, dict) else {}
    return str(solution.get("problem_family") or problem.problem_type)


@lru_cache(maxsize=512)
def _sample_legacy(problem_type: str, difficulty: int, count: int) -> dict[str, Any]:
    generator = GENERATORS.get(problem_type)
    if generator is None:
        return {"status": "NOT_IMPLEMENTED", "sampled": 0, "distinct_tasks": 0}
    samples: list[tuple[str, str]] = []
    errors: list[str] = []
    for seed in range(count):
        try:
            value = generator(random.Random(f"depth:{problem_type}:{difficulty}:{seed}"), difficulty)
            if not value.prompt or not value.canonical_answer:
                raise ValueError("empty question/answer")
            samples.append((_text(value.prompt), _json(value.parameters)))
        except (ArithmeticError, AssertionError, KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(type(exc).__name__)
    return {
        "status": "SAMPLED_OK" if len(samples) == count else "SAMPLE_FAILED",
        "sampled": len(samples),
        "distinct_tasks": len(set(samples)),
        "error_types": sorted(set(errors)),
        "math_review": "NOT_ASSESSED",
        "rendering_review": "NOT_ASSESSED",
    }


@lru_cache(maxsize=512)
def _sample_canonical(canonical_code: str | None, count: int) -> dict[str, Any]:
    families = [f for f in FAMILIES.values() if f.canonical_skill_code == canonical_code]
    results: dict[str, dict[str, Any]] = {}
    for family in sorted(families, key=lambda f: f.code):
        difficulty = family.min_difficulty
        mode = (LearningMode.INDEPENDENT if LearningMode.INDEPENDENT in family.modes
                else min(family.modes, key=lambda m: m.value))
        keys: set[tuple[str, str]] = set()
        errors: set[str] = set()
        for seed in range(count):
            try:
                generated = generate(family.code, seed=seed, difficulty=difficulty, mode=mode)
                if not generated.prompt or not generated.canonical_answer:
                    raise ValueError("empty question/answer")
                keys.add((_text(generated.prompt), _json(generated.visual_spec)))
            except (ArithmeticError, AssertionError, KeyError, TypeError, ValueError, IndexError) as exc:
                errors.add(type(exc).__name__)
        results[family.code] = {
            "tested_seeds": count,
            "unique_sample_tasks": len(keys),
            "error_types": sorted(errors),
            "tested_mode": mode.value,
            "math_review": "NOT_ASSESSED",
            "learner_route": "NOT_VERIFIED",
        }
    return {"declared_families": len(families), "family_samples": results}


def summarize_skill(
    curriculum: Any,
    skill: Any,
    problems: list[Any],
    metadata_by_id: dict[Any, Any],
    canonical_code: str | None,
    mapping_type: str | None,
    *,
    samples: int = 3,
) -> dict[str, Any]:
    """Summarize one local skill without making coverage or scoring claims."""
    normal = [p for p in problems
              if not (metadata_by_id.get(p.id)
                      and metadata_by_id[p.id].extension_eligible)]
    task_keys = [_task_key(p) for p in normal]
    unique_tasks = len(set(task_keys))
    answers: dict[tuple[str, str], set[str]] = defaultdict(set)
    for p, key in zip(normal, task_keys):
        answers[key].add(_text(p.canonical_answer))
    ambiguous = sum(len(a) > 1 for a in answers.values())
    # Count FULL mathematical-task collisions, not only shared prompt text.
    # The same prompt may correctly differ by visual/parameters/choices.
    task_modes: dict[tuple[str, str], set[str]] = defaultdict(set)
    for problem, task_key in zip(normal, task_keys):
        metadata = metadata_by_id.get(problem.id)
        if metadata is None:
            continue
        for mode in MODES:
            if getattr(metadata, f"{mode}_eligible", False):
                task_modes[task_key].add(mode)
    exposed_to_independent = {"diagnostic", "guided"}
    independent_evidence = {"independent", "mastery"}
    assisted_independent_reuse = sum(
        bool(modes & exposed_to_independent) and bool(modes & independent_evidence)
        for modes in task_modes.values()
    )
    diagnostic_independent_reuse = sum(
        {"diagnostic", "independent"}.issubset(modes)
        for modes in task_modes.values()
    )
    guided_mastery_reuse = sum(
        {"guided", "mastery"}.issubset(modes)
        for modes in task_modes.values()
    )
    declared = {mode: sum(bool(getattr(metadata_by_id[p.id], f"{mode}_eligible"))
                           for p in normal if p.id in metadata_by_id)
                for mode in MODES}
    missing_metadata = sum(p.id not in metadata_by_id for p in normal)
    types = sorted({p.problem_type for p in normal})
    families = sorted({_family_code(p) for p in normal})
    distinct_difficulties = sorted({p.difficulty for p in normal})
    sampled_legacy = {t: _sample_legacy(t, min(p.difficulty for p in normal
                       if p.problem_type == t), samples)
                      for t in types if t in GENERATORS}
    canonical = _sample_canonical(canonical_code, samples)
    is_qa_fixture = (curriculum.code, skill.code) in NON_INSTRUCTIONAL_FIXTURES
    issue_flags = []
    if normal and unique_tasks < MIN_UNIQUE_FOR_DEPTH_REVIEW:
        issue_flags.append("THIN_STORED_UNIQUE_TASKS")
    if normal and len(families) < 2:
        issue_flags.append("ONE_STORED_FAMILY")
    if len(normal) > unique_tasks:
        issue_flags.append("REPEATED_MATHEMATICAL_TASK")
    if ambiguous:
        issue_flags.append("SAME_TASK_DIFFERENT_ANSWERS")
    if assisted_independent_reuse:
        issue_flags.append("SAME_TASK_IN_ASSISTED_AND_INDEPENDENT_POOLS")
    if missing_metadata:
        issue_flags.append("MISSING_MODE_METADATA")
    if normal and any(declared[m] == 0 for m in ("independent", "mastery")):
        issue_flags.append("MISSING_DECLARED_INDEPENDENT_OR_MASTERY_POOL")
    if any(s["status"] != "SAMPLED_OK" for s in sampled_legacy.values()):
        issue_flags.append("LEGACY_GENERATOR_SAMPLE_FAILURE")
    if any(f["error_types"] for f in canonical["family_samples"].values()):
        issue_flags.append("CANONICAL_GENERATOR_SAMPLE_FAILURE")
    if not normal:
        issue_flags.append("NO_NON_EXTENSION_STORED_QUESTIONS")
    return {
        "grade_or_course": curriculum.grade_level,
        "is_qa_fixture": is_qa_fixture,
        "instructional_priority_eligible": not is_qa_fixture,
        "curriculum_code": curriculum.code,
        "curriculum_version": curriculum.version,
        "jurisdiction": curriculum.jurisdiction,
        "skill_code": skill.code,
        "skill_name": skill.name,
        "canonical_code": canonical_code,
        "canonical_mapping_type": mapping_type,
        "canonical_mapping_approval": "NOT_ASSESSED",
        "stored_total": len(problems),
        "stored_non_extension": len(normal),
        "stored_distinct_tasks": unique_tasks,
        "duplicate_task_rows": len(normal) - unique_tasks,
        "conflicting_answer_task_groups": ambiguous,
        "assisted_independent_same_task_groups": assisted_independent_reuse,
        "diagnostic_independent_same_task_groups": diagnostic_independent_reuse,
        "guided_mastery_same_task_groups": guided_mastery_reuse,
        "stored_curated": sum(p.source_type != "GENERATED" for p in normal),
        "stored_generated": sum(p.source_type == "GENERATED" for p in normal),
        "stored_family_codes": families,
        "stored_problem_types": types,
        "difficulty_levels": distinct_difficulties,
        "declared_mode_pool_counts": declared,
        "missing_metadata_rows": missing_metadata,
        "learner_selectable_non_extension_upper_bound": len(normal),
        "learner_visible_integrated_status": "NOT_VERIFIED",
        "selection_mode_eligibility_enforcement": "IMPLEMENTED_METADATA_GATE_PER_STATE;LEARNER_ROUTE_NOT_VERIFIED",
        "cross_session_repetition": "AT_RISK_MATH_EQUIVALENCE_REUSE;STUDENT_ATTEMPT_IDS_EXCLUDED_ACROSS_SESSIONS",
        "legacy_generator_samples": sampled_legacy,
        "canonical_generator_samples": canonical,
        "math_oracle_review": "NOT_ASSESSED",
        "pedagogy_review": "NOT_ASSESSED",
        "scoring_rendering_qa": "NOT_ASSESSED",
        "issues_for_triage": issue_flags,
    }


def audit_database(db: Session, *, source_sha: str, samples: int = 3) -> dict[str, Any]:
    """Read-only database inventory including zero-question skills."""
    curricula = {row.id: row for row in db.scalars(
        select(Curriculum).where(Curriculum.active.is_(True))).all()}
    local_skills = list(db.scalars(select(Skill).order_by(Skill.code)).all())
    problems_by_skill: dict[Any, list[Any]] = defaultdict(list)
    for p in db.scalars(select(Problem)).all():
        problems_by_skill[p.primary_skill_id].append(p)
    metadata = {m.problem_id: m for m in db.scalars(select(ProblemContentMetadata)).all()}
    canonical = {c.id: c.code for c in db.scalars(select(CanonicalSkill)).all()}
    mappings = {m.skill_id: m for m in db.scalars(select(CurriculumSkillMapping)).all()}
    rows = []
    for skill in local_skills:
        curriculum = curricula.get(skill.curriculum_id)
        if curriculum is None:
            continue
        mapping = mappings.get(skill.id)
        code = canonical.get(mapping.canonical_skill_id) if mapping else None
        rows.append(summarize_skill(
            curriculum, skill, problems_by_skill[skill.id], metadata,
            code, mapping.mapping_type if mapping else None, samples=samples,
        ))
    ranked = sorted(
        (r for r in rows if r["stored_non_extension"] > 0 and r["instructional_priority_eligible"]),
        key=lambda r: (
            r["stored_distinct_tasks"],
            len(r["stored_family_codes"]),
            len(r["difficulty_levels"]),
            r["curriculum_code"],
            r["skill_code"],
        ),
    )
    by_grade: dict[str, dict[str, int]] = defaultdict(
        lambda: {"skills": 0, "populated": 0, "thin_populated": 0, "empty": 0, "qa_fixtures": 0})
    for row in rows:
        group = by_grade[str(row["grade_or_course"] or "UNKNOWN")]
        group["skills"] += 1
        if row["is_qa_fixture"]:
            group["qa_fixtures"] += 1
        if row["stored_non_extension"]:
            group["populated"] += 1
            if not row["is_qa_fixture"] and row["stored_distinct_tasks"] < MIN_UNIQUE_FOR_DEPTH_REVIEW:
                group["thin_populated"] += 1
        else:
            group["empty"] += 1
    return {
        "report_type": "SYNTHETIC_PERSISTED_PER_SKILL_QUESTION_DEPTH",
        "source_sha_supplied": source_sha,
        "scope": "ACTIVE_CURRICULA_ALL_LOCAL_SKILLS_AND_STORED_PROBLEMS",
        "not_covered": [
            "Live production content and private learner availability",
            "Cross-session learner-history analysis",
            "Approved standards source fidelity",
            "Independent mathematical answer verification",
            "Independent pedagogical and Muse QA",
        ],
        "selector_evidence": ("Current select_next_problem requires mode-specific ProblemContentMetadata and "
                             "extension eligibility; when student identity is available, it excludes "
                             "past Attempt and DiagnosticAttempt problem IDs across sessions. "
                             "Mathematically equivalent generated tasks and real learner routes "
                             "remain unverified."),
        "threshold_policy": {"thin_if_distinct_task_count_less_than": MIN_UNIQUE_FOR_DEPTH_REVIEW,
                             "not_a_mastery_or_release_standard": True},
        "grades": dict(sorted(by_grade.items())),
        "skill_count": len(rows),
        "qa_fixture_skill_count": sum(r["is_qa_fixture"] for r in rows),
        "thin_populated_priority": [
            {"grade_or_course": r["grade_or_course"],
             "curriculum_code": r["curriculum_code"], "skill_code": r["skill_code"],
             "stored_distinct_tasks": r["stored_distinct_tasks"],
             "issue_flags": r["issues_for_triage"]}
            for r in ranked if "THIN_STORED_UNIQUE_TASKS" in r["issues_for_triage"]
        ],
        "skill_rows": sorted(rows, key=lambda r: (str(r["grade_or_course"]), r["curriculum_code"], r["skill_code"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.source_sha) != 40 or any(c not in "0123456789abcdef" for c in args.source_sha.lower()):
        parser.error("--source-sha must be the exact 40-character hexadecimal commit")
    if not 1 <= args.samples <= 12:
        parser.error("--samples must be between 1 and 12")
    url = make_url(args.database_url)
    if not url.drivername.startswith("postgresql") or url.host not in {
        "localhost", "127.0.0.1", "::1", "postgres",
    }:
        parser.error("Only explicitly provided, isolated local PostgreSQL URLs allowed")
    engine = create_engine(url)
    try:
        with Session(engine) as db:
            db.execute(text("SET TRANSACTION READ ONLY"))
            report = audit_database(db, source_sha=args.source_sha, samples=args.samples)
            db.rollback()
    finally:
        engine.dispose()
    args.output.write_text(_json(report) + "\n", encoding="utf-8")
    print(f"Wrote {report['skill_count']} local-skill rows to {args.output}")


if __name__ == "__main__":
    main()
