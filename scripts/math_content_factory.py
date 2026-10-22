"""Read-only Mihur mathematics content factory: research -> families -> QA evidence.

This pilot consumes EXISTING runtime canonical mathematics. It does not create
new family IDs, publish Ontario mappings, authorize modes, seed problems, read
learner records, score mastery, or make any question learner-selectable.

Usage:
    python -m scripts.math_content_factory \
      --blueprint docs/content_factory/mth1w_eq3_factory.v1.json \
      --seeds 96 --output /tmp/mihur-factory-report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from app.canonical_problem_families import FAMILIES, LearningMode, generate

X = sp.Symbol("x", real=True)
FAMILIES_IN_SLICE = frozenset({
    "MATH.ALG.EQ.MULTISTEP.DISTRIBUTE",
    "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES",
    "MATH.ALG.EQ.WORD.TARGET",
})
_PATTERN_DISTRIBUTE = re.compile(
    r"Solve (\d+)\(x \+ (\d+)\) \+ (\d+) = (\d+)\."
)
_PATTERN_BOTH_SIDES = re.compile(
    r"Solve (\d+)x \+ (\d+) = (\d+)x \+ (\d+)\."
)
_PATTERN_WORD = re.compile(
    r"Sam already has (\d+) points and earns (\d+) points each week\. "
    r"How many weeks are needed to reach exactly (\d+) points\?"
)
_REQUIRED_PHASES = (
    "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN",
    "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY",
)


def _reviewable_blueprint(blueprint: dict[str, Any]) -> None:
    if blueprint.get("schema_version") != "1.0.0":
        raise ValueError("unsupported factory blueprint revision")
    if blueprint.get("runtime_activation") is not False:
        raise ValueError("the content factory cannot authorize runtime activation")
    if blueprint.get("status") != "DRAFT_UNVERIFIED":
        raise ValueError("factory evidence must stay DRAFT_UNVERIFIED")
    if blueprint.get("canonical_skill") != "MATH.EE.EQUATION.MULTISTEP":
        raise ValueError("this bounded pilot requires its accepted shared math target")
    if blueprint.get("official_expectation_mapping") != "CANDIDATE_PENDING_STANDARDS":
        raise ValueError("official-source review is not approved mapping")
    sources = blueprint.get("research_sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise ValueError("a Ministry source and assessment-framework source are required")
    for source in sources:
        if (not isinstance(source, dict)
                or not str(source.get("url", "")).startswith("https://")
                or source.get("reuse_policy") != "REFERENCE_ONLY_DO_NOT_COPY"
                or source.get("permission_to_rehost_items") is not False):
            raise ValueError("no unknown source license or copied question permission")
    families = blueprint.get("families")
    if not isinstance(families, list) or len(families) != len(FAMILIES_IN_SLICE):
        raise ValueError("pilot must enumerate only its existing registered families")
    codes = [family.get("family_code") for family in families if isinstance(family, dict)]
    if len(set(codes)) != len(codes) or set(codes) != FAMILIES_IN_SLICE:
        raise ValueError("family scope or unique identities do not match")
    for family in families:
        spec = FAMILIES.get(family["family_code"])
        if spec is None or spec.canonical_skill_code != blueprint["canonical_skill"]:
            raise ValueError("family is not in the existing canonical runtime registry")
        if tuple(family.get("teaching_phases", [])) != _REQUIRED_PHASES:
            raise ValueError("missing Mihur instructional progression")
        if not family.get("misconception_focus") or not family.get("representation"):
            raise ValueError("missing independent pedagogical structure")
        if family.get("authoring_origin") != "EXISTING_CANONICAL_REUSE":
            raise ValueError("new authoring is not authorized in the baseline pilot")


def _exact_expected(problem: Any) -> tuple[Fraction, tuple[int, ...]]:
    """Independently derive expected answer with a SymPy equation.

    Uses a strict whitelist of stable original canonical prompts. This does
    not parse arbitrary user expressions and does not trust canonical_answer.
    """
    family = problem.family_code
    prompt = problem.prompt
    if family == "MATH.ALG.EQ.MULTISTEP.DISTRIBUTE":
        matched = _PATTERN_DISTRIBUTE.fullmatch(prompt)
        if matched is None:
            raise ValueError("unrecognized distributive equation")
        a, b, c, total = map(int, matched.groups())
        equation = sp.Eq(a * (X + b) + c, total)
        coefficients = (a, b, c, total)
    elif family == "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES":
        matched = _PATTERN_BOTH_SIDES.fullmatch(prompt)
        if matched is None:
            raise ValueError("unrecognized both-sides equation")
        a, b, c, d = map(int, matched.groups())
        equation = sp.Eq(a * X + b, c * X + d)
        coefficients = (a, b, c, d)
    elif family == "MATH.ALG.EQ.WORD.TARGET":
        matched = _PATTERN_WORD.fullmatch(prompt)
        if matched is None:
            raise ValueError("unrecognized word-model equation")
        start, rate, target = map(int, matched.groups())
        equation = sp.Eq(start + rate * X, target)
        coefficients = (start, rate, target)
    else:
        raise ValueError("no independent mathematical oracle for this family")
    solutions = sp.solve(equation, X)
    if len(solutions) != 1:
        raise ValueError("expected one unique exact solution")
    value = sp.Rational(solutions[0])
    left, right = equation.lhs.subs(X, value), equation.rhs.subs(X, value)
    if sp.simplify(left - right) != 0:
        raise ValueError("candidate does not satisfy original equality")
    return Fraction(int(value.p), int(value.q)), coefficients


def _submitted_answer(problem: Any) -> Fraction:
    raw = problem.canonical_answer
    if problem.family_code != "MATH.ALG.EQ.WORD.TARGET":
        if not raw.startswith("x="):
            raise ValueError("unrecognized answer expression")
        raw = raw[2:]
    try:
        return Fraction(raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("answer is not exact rational") from exc


def _learner_payload(problem: Any) -> dict[str, Any]:
    """Answer-free projection for review tests, NOT a runtime API response."""
    return {
        "family_code": problem.family_code,
        "canonical_skill": problem.canonical_skill_code,
        "variant_id": problem.variant_id,
        "mode": problem.mode.value,
        "prompt": problem.prompt,
        "answer_fields": ["solution"],
        "guidance": list(problem.hints) if problem.mode == LearningMode.GUIDED else [],
        "mastery_credit": False,
        "status": "DRAFT_UNVERIFIED",
        "runtime_activation": False,
    }


def run_factory(blueprint: dict[str, Any], *, seeds: int = 96) -> dict[str, Any]:
    """Produce an auditable, side-effect-free mathematical quality report."""
    _reviewable_blueprint(blueprint)
    if type(seeds) is not int or not 1 <= seeds <= 5_000:
        raise ValueError("seed count must be between 1 and 5000")
    per_family: dict[str, Any] = {}
    problems_checked = 0
    failures: list[str] = []
    all_mode_ids: set[str] = set()
    for family in blueprint["families"]:
        code = family["family_code"]
        tasks_by_mode: dict[str, set[tuple[int, ...]]] = defaultdict(set)
        wrong_signatures: set[tuple[str, str]] = set()
        for mode in (LearningMode.GUIDED, LearningMode.INDEPENDENT):
            for seed in range(seeds):
                try:
                    task = generate(code, seed=seed, difficulty=3, mode=mode)
                    replay = generate(code, seed=seed, difficulty=3, mode=mode)
                    if task != replay or task.variant_id in all_mode_ids:
                        raise ValueError("unstable or reused variant identity")
                    all_mode_ids.add(task.variant_id)
                    expected, signature = _exact_expected(task)
                    if _submitted_answer(task) != expected:
                        raise ValueError("independent SymPy oracle disagreement")
                    if not task.is_correct(task.canonical_answer):
                        raise ValueError("own answer contract rejects exact oracle")
                    tasks_by_mode[mode.value].add(signature)
                    public = _learner_payload(task)
                    encoded = json.dumps(public, sort_keys=True)
                    if ("canonical_answer" in encoded or "misconception_answers" in encoded
                            or "teacher_oracle" in encoded):
                        raise ValueError("public answer leakage")
                    if mode == LearningMode.INDEPENDENT and public["guidance"]:
                        raise ValueError("independent payload contains hints")
                    for misconception, answer in task.misconception_answers.items():
                        wrong_signatures.add((misconception, answer))
                        if task.is_correct(answer):
                            raise ValueError("misconception answer collides with correct answer")
                        if task.misconception_for(answer) != misconception:
                            raise ValueError("misconception attribution is ambiguous")
                    problems_checked += 1
                except (ValueError, TypeError, ZeroDivisionError, KeyError) as exc:
                    if len(failures) < 30:
                        failures.append(f"{code}:{mode.value}:{seed}:{exc}")
        per_family[code] = {
            "registered_canonical_family": True,
            "mathematical_target": blueprint["canonical_skill"],
            "unique_mathematical_tasks_by_mode": {
                mode: len(tasks) for mode, tasks in tasks_by_mode.items()
            },
            "observed_wrong_answer_signatures": len(wrong_signatures),
            "intended_misconception": family["misconception_focus"],
            "learner_delivery": "NOT_VERIFIED",
            "independent_math_approval": "NOT_CONFERRED_BY_FACTORY",
        }
    min_unique = blueprint["quality_policy"]["minimum_unique_per_mode"]
    checks = {
        "independent_sympy_oracle_and_replay": not failures,
        "seeded_mathematical_variety": all(
            all(count >= min_unique for count in entry["unique_mathematical_tasks_by_mode"].values())
            and len(entry["unique_mathematical_tasks_by_mode"]) == 2
            for entry in per_family.values()
        ),
        "source_references_present_not_copied": True,
        "approved_mapping": False,
        "independent_math_and_pedagogy": False,
        "backend_family_scoring_and_mode_grants": False,
        "frontend_mve_and_muse_qa": False,
        "actual_staging_and_production_selection": False,
    }
    return {
        "factory_revision": "MATH_CONTENT_FACTORY_V1",
        "source_canonical_skill": blueprint["canonical_skill"],
        "source_ontology": "ONTARIO_MTH1W_C1_5_CANDIDATE_ONLY",
        "status": "DRAFT_UNVERIFIED",
        "runtime_activation": False,
        "sampled_generated_questions": problems_checked,
        "registered_reused_families": len(per_family),
        "target_distinct_families": blueprint["quality_policy"]["target_distinct_families"],
        "observed_mathematical_failures": failures,
        "families": per_family,
        "quality_gates": checks,
        "automated_math_checks_passed": checks["independent_sympy_oracle_and_replay"]
            and checks["seeded_mathematical_variety"],
        "pilot_skill_ready": all(checks.values()),
        "release_authority": "NONE",
        "owner_handoff": {
            "content": "Extend to 8-12 genuinely distinct families without duplicating canonical IDs",
            "math_review": "Independently verify equations and symbolic equivalence",
            "pedagogy": "Verify Observe->Predict->Manipulate->Explain->Practice->Diagnose->Transfer->Verify",
            "assessment": "Approve typed response, server scorer and mode-scoped family manifest",
            "frontend_mve": "Implement interactive learner journey and accessible equivalent",
            "muse_engineering": "Execute synthetic repeated-session QA then separately authorize releases",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Mihur mathematics content factory")
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=96)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    blueprint = json.loads(args.blueprint.read_text(encoding="utf-8"))
    report = run_factory(blueprint, seeds=args.seeds)
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    if not report["automated_math_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
